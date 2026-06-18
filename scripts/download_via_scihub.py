#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""
Sci-Hub 批量下载器（第一轮下载）。

流程：
  1. 测试预置镜像站列表（13 个），反馈各站点状态
  2. 若全部不可用，用 CDP 重试一轮（排除暂时性网络波动）
  3. 用可用镜像站逐篇下载（轮询负载均衡）
  4. 仅对 2021 年前的老论文更有效

Usage:
  python3 scripts/download_via_scihub.py 检索文献表.md
  python3 scripts/download_via_scihub.py doi_list.txt --port 9223
  python3 scripts/download_via_scihub.py doi_list.txt --skip-test  跳过镜像测试
"""
import sys, os, time, re, json, urllib.request, urllib.parse, websocket, base64

# Ensure scripts/ is on the path so `from cdp_utils import ...` works
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cdp_utils import (check_cdp, get_cdp_ws_url, list_tabs, close_all_tabs,
                        close_tab, send_cmd_and_wait, check_required_deps,
                        create_tab, get_tab_ws_url)

# 预置镜像站列表（可用镜像站排前，经测试 2026-05-30）
DEFAULT_MIRRORS = [
    "https://sci-hub.st", "https://sci-hub.ru", "https://sci-hub.shop",
    "https://sci-hub.vg", "https://sci-hub.in", "https://sci-hub.al",
    "https://sci-hub.box", "https://sci-hub.red", "https://sci-hub.ren",
    "https://sci-hub.se", "https://sci-hub.wf", "https://sci-hub.ee",
    "https://sci-hub.mk",
]

CDP_PORT = 9223

# ===== 工具函数 =====

def extract_dois(input_path):
    """从文件提取 DOI 列表"""
    doid = set()
    with open(input_path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    for m in re.finditer(r"10\.\d{4,}/[^\s,;)\]}\"]+", text):
        doi = m.group(0).rstrip(".,")
        doid.add(doi)
    return sorted(doid)

def doi_to_filename(doi):
    return doi.replace("/", "_").replace(":", "_") + ".pdf"

def navigate_tab(port, tab_id, url, timeout=10):
    """Navigate an existing CDP tab instead of creating a new browser/page."""
    tab_ws_url = get_tab_ws_url(port, tab_id)
    if not tab_ws_url:
        return False
    ws = None
    try:
        ws = websocket.create_connection(tab_ws_url, timeout=timeout)
        ws.send(json.dumps({"id": 1, "method": "Page.navigate",
                            "params": {"url": url}}))
        # Loading events can arrive before the command response. Later fixed
        # sleeps/polls decide readiness, so a successful send is enough here.
        ws.close()
        return True
    except Exception:
        try:
            ws.close()
        except Exception:
            pass
        return False

# ===== 镜像站可用性测试 =====

def test_mirror_cdp(mirror_url, probe_tab=None):
    """
    通过 CDP Chrome 测试一个镜像站是否可用。
    导航到该镜像站首页，检查是否正常加载（非错误页、非 Cloudflare 挑战页）。
    返回: (ok, status_msg)
    """
    if not check_cdp(CDP_PORT):
        return False, "CDP Chrome 未运行"

    test_url = f"{mirror_url}/10.1016/j.jpowsour.2019.01.052"

    tid = probe_tab
    created_here = False
    if not tid:
        try:
            _, tid = create_tab(CDP_PORT, "about:blank")
            created_here = True
        except Exception:
            return False, "创建标签页失败"

    if not navigate_tab(CDP_PORT, tid, test_url):
        if created_here:
            close_tab(CDP_PORT, tid)
        return False, "导航标签页失败"

    time.sleep(5)

    try:
        tabs = list_tabs(CDP_PORT)
        for t in tabs:
            if t.get("id") != tid:
                continue
            title = t.get("title", "")
            url = t.get("url", "")

            # 检查结果
            if "Sci-Hub" in title and ("不可用" not in title):
                return True, f"可用（{title[:40]}）"
            elif "不可用" in title or "not available" in title.lower():
                return True, "可用（论文不存在，但站点正常）"
            elif "请稍候" in title or "challenge" in url.lower() or "captcha" in url.lower():
                return False, "Cloudflare 验证拦截"
            elif len(url) < 20 or url == test_url:
                return False, "重定向到首页/错误页"
            else:
                return False, f"异常: {title[:30]}"
    except Exception:
        return False, "页面检测超时"
    finally:
        if created_here:
            close_tab(CDP_PORT, tid)

    return False, "无法检测"

def test_mirror_http(mirror_url):
    """通过直连 HTTP 快速检测镜像站是否可达"""
    name = mirror_url.split("//")[-1]
    try:
        req = urllib.request.Request(mirror_url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        resp = urllib.request.urlopen(req, timeout=8)
        html = resp.read()
        if b"sci-hub" in html.lower() or b"Sci-Hub" in html or b"open" in html:
            return True, "HTTP 可达"
        return False, f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)[:30]

def test_all_mirrors(cdp_available):
    """测试所有预置镜像站，返回可用列表"""
    print("\n🔍 测试 Sci-Hub 镜像站可用性...", flush=True)
    print(f"{'镜像站':<25} {'直连状态':<18} {'CDP 状态':<25}", flush=True)
    print("-" * 68, flush=True)

    working = []
    probe_tab = None
    try:
        if cdp_available:
            _, probe_tab = create_tab(CDP_PORT, "about:blank")
        for m in DEFAULT_MIRRORS:
            name = m.split("//")[-1]
            # 直连测试
            http_ok, http_msg = test_mirror_http(m)
            # CDP 测试（如果 Chrome 在运行）
            cdp_ok, cdp_msg = False, "未测试"
            if cdp_available:
                cdp_ok, cdp_msg = test_mirror_cdp(m, probe_tab=probe_tab)

            status_icon = "✅" if (cdp_ok if cdp_available else http_ok) else "❌"
            cdp_display = cdp_msg[:22] if cdp_available else "Chrome 未运行"
            print(f"  {status_icon} {name:<20} {http_msg:<18} {cdp_display}", flush=True)

            # 判断是否可用（有 Chrome 用 CDP 结果，否则用直连结果）
            if cdp_available:
                if cdp_ok:
                    working.append(m)
            else:
                if http_ok:
                    working.append(m)
    finally:
        if probe_tab:
            close_tab(CDP_PORT, probe_tab)

    return working

# ===== 网络搜索可用镜像站 =====

def search_working_mirrors():
    """所有预置镜像站均不可用时，用 CDP 逐一重新测试（可能有暂时性网络波动）。"""
    print("\n🔎 预置镜像站全部不可用，尝试用 CDP 逐一验证镜像站...", flush=True)

    if not check_cdp(CDP_PORT):
        print("  ⚠ CDP Chrome 未运行，无法自动测试镜像站", flush=True)
        return []

    # 再次用 CDP 测试所有镜像站（可能有暂时性网络波动）
    print("  重新用 CDP 测试全部镜像站...", flush=True)
    working = []
    probe_tab = None
    try:
        _, probe_tab = create_tab(CDP_PORT, "about:blank")
        for m in DEFAULT_MIRRORS:
            ok, msg = test_mirror_cdp(m, probe_tab=probe_tab)
            if ok:
                working.append(m)
                print(f"  ✅ {m.split('//')[-1]} - {msg[:30]}", flush=True)
            else:
                print(f"  ❌ {m.split('//')[-1]} - {msg[:30]}", flush=True)
    finally:
        if probe_tab:
            close_tab(CDP_PORT, probe_tab)

    return working

# ===== CDP Chrome 下载 =====

def _extract_pdf_url_from_scihub(port, tid):
    """从 Sci-Hub 页面 DOM 中提取 PDF URL。

    策略: 先找 <object>.data，再扫描 <a> 标签中的 .pdf 链接。
    返回 PDF URL 或 None。
    """
    tab_ws_url = None
    for t in list_tabs(port):
        if t.get("id") == tid:
            tab_ws_url = t.get("webSocketDebuggerUrl")
            break

    if not tab_ws_url:
        return None

    pdf_url = None
    try:
        pws = websocket.create_connection(tab_ws_url, timeout=10)
        for expr in [
            "document.querySelector('object').data",
            "Array.from(document.querySelectorAll('a')).filter(a=>a.href.includes('.pdf')).map(a=>a.href)[0] || ''",
        ]:
            pws.send(json.dumps({"id":10,"method":"Runtime.evaluate",
                                 "params":{"expression":expr,"returnByValue":True}}))
            r = json.loads(pws.recv())
            raw = r.get("result",{}).get("result",{}).get("value","")
            if raw:
                # Handle relative URLs
                pdf_url = raw if raw.startswith("http") else None
                pdf_url = pdf_url.split("#")[0] if pdf_url else None
                if pdf_url:
                    break
        pws.close()
    except Exception:
        pass

    return pdf_url


def _fetch_pdf_via_navigate(port, pdf_url, pdf_tab=None):
    """复用或创建标签页导航到 PDF URL，用 Fetch 域捕获响应体。

    返回 PDF 字节数据或 None。
    """
    if not check_cdp(port):
        return None

    tid2 = pdf_tab
    created_here = False
    if not tid2:
        try:
            _, tid2 = create_tab(port, "about:blank")
            created_here = True
        except Exception:
            return None

    time.sleep(0.5)

    # 获取标签页的 WebSocket URL
    pwu2 = get_tab_ws_url(port, tid2)

    if not pwu2:
        if created_here:
            close_tab(port, tid2)
        return None

    pdf_data = None
    try:
        pws2 = websocket.create_connection(pwu2, timeout=10)

        # 清理上一次捕获状态后，在同一 tab 内重新启用 Fetch。
        try:
            pws2.send(json.dumps({"id":9,"method":"Fetch.disable"}))
            pws2.settimeout(1)
            pws2.recv()
        except Exception:
            pass

        pws2.send(json.dumps({"id":8,"method":"Page.navigate","params":{"url":"about:blank"}}))
        time.sleep(0.2)

        # 启用 Fetch 域捕获
        pws2.send(json.dumps({"id":10,"method":"Fetch.enable",
                              "params":{"patterns":[{"urlPattern":"*","requestStage":"Response"}]}}))
        try:
            pws2.settimeout(2)
            json.loads(pws2.recv())
        except Exception:
            pass

        # 导航到 PDF URL
        pws2.send(json.dumps({"id":11,"method":"Page.navigate","params":{"url":pdf_url}}))

        dl = time.time() + 20
        while time.time() < dl:
            try:
                pws2.settimeout(1)
                msg = json.loads(pws2.recv())
            except Exception:
                continue
            if msg.get("method") == "Fetch.requestPaused":
                rid = msg["params"]["requestId"]
                pws2.send(json.dumps({"id":20,"method":"Fetch.getResponseBody",
                                     "params":{"requestId":rid}}))
                try:
                    pws2.settimeout(5)
                    r2 = json.loads(pws2.recv())
                    body = r2.get("result",{}).get("body","")
                    b64 = r2.get("result",{}).get("base64Encoded",False)
                    if body:
                        d = base64.b64decode(body) if b64 else body.encode("latin-1",errors="ignore")
                        if d[:4] == b"%PDF" and len(d) > 20000:
                            pdf_data = d
                except Exception:
                    pass
                pws2.send(json.dumps({"id":21,"method":"Fetch.continueRequest",
                                     "params":{"requestId":rid}}))
                break
        try:
            pws2.send(json.dumps({"id":22,"method":"Fetch.disable"}))
        except Exception:
            pass
        pws2.close()
    except Exception:
        pass

    if created_here:
        close_tab(port, tid2)
    return pdf_data


def cdp_download(doi, output_dir, mirror, article_tab=None, pdf_tab=None):
    """通过 CDP Chrome 从指定镜像站下载一篇论文的 PDF。

    Flow:
      1. 在 Sci-Hub 页面提取 PDF URL (DOM)
      2. 新建标签页导航到 PDF URL 并捕获响应体
    """
    if not check_cdp(CDP_PORT):
        return None, "CDP Chrome 未运行"

    fname = doi_to_filename(doi)
    fpath = os.path.join(output_dir, fname)
    if os.path.exists(fpath) and os.path.getsize(fpath) > 10000:
        return fpath, "已存在"

    url = f"{mirror}/{doi}"

    # Step 1: 复用文章标签页并导航到 Sci-Hub
    tid = article_tab
    created_here = False
    if not tid:
        try:
            _, tid = create_tab(CDP_PORT, "about:blank")
            created_here = True
        except Exception:
            return None, "创建标签页失败"

    if not navigate_tab(CDP_PORT, tid, url):
        if created_here:
            close_tab(CDP_PORT, tid)
        return None, "导航标签页失败"

    time.sleep(5)

    # Step 2: 从 DOM 提取 PDF URL
    pdf_url = _extract_pdf_url_from_scihub(CDP_PORT, tid)

    if created_here:
        close_tab(CDP_PORT, tid)

    if not pdf_url:
        return None, "未找到 PDF 链接"

    # Step 3: 通过 Fetch 域捕获 PDF
    pdf_data = _fetch_pdf_via_navigate(CDP_PORT, pdf_url, pdf_tab=pdf_tab)

    if pdf_data:
        with open(fpath, "wb") as f:
            f.write(pdf_data)
        return fpath, f"{mirror.split('/')[-1]} {len(pdf_data)//1024}KB"
    return None, "无法捕获 PDF 数据"


# ===== 主流程 =====

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sci-Hub 批量下载器")
    parser.add_argument("input", help="DOI 列表文件")
    parser.add_argument("--output", "-o", default="paper-temp", help="输出目录")
    parser.add_argument("--port", type=int, default=9223, help="CDP Chrome 端口")
    parser.add_argument("--skip-test", action="store_true", help="跳过镜像站可用性测试")
    parser.add_argument("--mirror", help="指定镜像站 URL（跳过测试，直接使用）")
    args = parser.parse_args()

    if not check_required_deps():
        exit(1)

    CDP_PORT = args.port
    OUTPUT_DIR = args.output
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 检测 Chrome
    ch = f"http://127.0.0.1:{CDP_PORT}"
    cdp_available = False
    try:
        json.loads(urllib.request.urlopen(f"{ch}/json/version", timeout=5).read())
        cdp_available = True
    except:
        pass

    print(f"CDP Chrome (端口 {CDP_PORT}): {'✅ 运行中' if cdp_available else '❌ 未运行'}", flush=True)
    print(f"输出目录: {OUTPUT_DIR}", flush=True)

    # 确定可用镜像站
    working_mirrors = []

    if args.mirror:
        # 用户指定了镜像站
        working_mirrors = [args.mirror.rstrip("/")]
        print(f"使用指定镜像站: {working_mirrors[0]}", flush=True)
    elif not args.skip_test:
        # 测试镜像站
        working_mirrors = test_all_mirrors(cdp_available)
        if not working_mirrors:
            print("\n⚠ 所有预置镜像站均不可用", flush=True)
            working_mirrors = search_working_mirrors()

        if working_mirrors:
            print(f"\n✅ 可用镜像站 ({len(working_mirrors)} 个): {', '.join(m.split('//')[-1] for m in working_mirrors)}", flush=True)
        else:
            print("\n❌ 未能找到可用的 Sci-Hub 镜像站。建议:", flush=True)
            print("   1. 检查网络连接和代理设置", flush=True)
            print("   2. 在 Chrome 中打开 https://sci-hub.st 手动验证", flush=True)
            print("   3. 使用 --mirror 参数指定已知可用镜像站", flush=True)
            sys.exit(1)
    else:
        # 跳过测试，使用默认列表
        working_mirrors = DEFAULT_MIRRORS
        print("跳过镜像测试，使用默认镜像站列表", flush=True)

    # 加载 DOI
    dois = extract_dois(args.input)
    if not dois:
        print("未找到 DOI", flush=True)
        sys.exit(1)
    print(f"待下载 DOI 数: {len(dois)}", flush=True)
    print()

    # 逐篇下载。批次内固定复用 2 个标签页，避免每篇创建/关闭页面。
    ok, fail = 0, 0
    failed_list = []
    mirror_idx = 0  # 轮询镜像站
    article_tab = None
    pdf_tab = None
    if cdp_available:
        try:
            _, article_tab = create_tab(CDP_PORT, "about:blank")
            _, pdf_tab = create_tab(CDP_PORT, "about:blank")
            print("CDP 标签页复用: ✅ article tab + PDF fetch tab", flush=True)
        except Exception:
            article_tab = None
            pdf_tab = None

    try:
        for i, doi in enumerate(dois):
            mirror = working_mirrors[mirror_idx % len(working_mirrors)]
            mirror_idx += 1

            print(f"[{i+1}/{len(dois)}] {doi[:45]} → {mirror.split('//')[-1]}...", end=" ", flush=True)
            t0 = time.time()

            if cdp_available:
                fpath, msg = cdp_download(doi, OUTPUT_DIR, mirror,
                                          article_tab=article_tab, pdf_tab=pdf_tab)
            else:
                fpath, msg = "直连方式已禁用", "（Chrome 未运行）"

            elapsed = time.time() - t0

            if fpath and os.path.exists(fpath) and os.path.getsize(fpath) > 10000:
                ok += 1
                print(f"✅ {msg} ({elapsed:.0f}s)", flush=True)
            else:
                fail += 1
                failed_list.append(doi)
                print(f"❌ {msg} ({elapsed:.0f}s)", flush=True)

            time.sleep(0.3)
    finally:
        if article_tab:
            close_tab(CDP_PORT, article_tab)
        if pdf_tab:
            close_tab(CDP_PORT, pdf_tab)

    # 汇总
    print(f"\n{'='*50}", flush=True)
    print(f"完成: ✅ {ok} 成功, ❌ {fail} 失败", flush=True)
    print(f"总耗时: {(time.time()-t0)/60:.1f}分钟", flush=True)

    if failed_list:
        flist = os.path.join(OUTPUT_DIR, "scihub_failed_dois.txt")
        with open(flist, "w") as f:
            for d in failed_list:
                f.write(d + "\n")
        print(f"\n失败列表: {flist}", flush=True)
        print("提示: 失败论文可走第二轮 SD CDP 下载", flush=True)
