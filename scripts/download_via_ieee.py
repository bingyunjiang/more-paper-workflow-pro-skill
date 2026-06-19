#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""
IEEE CDP 批量下载器 v1.0.1（已验证 6/6）。

两步走策略：
  Step A（首选）：导航到文章页 → 提取 stamp URL → Fetch 预启用 + Referrer 捕获
  Step B（回退）：直接构造 stamp/getPDF URL → Fetch 预启用 + Referrer 捕获

前置条件（必须）：
  - Google Chrome CDP（--remote-debugging-port=9223）
  - websocket-client（pip install websocket-client）
  - IEEE 机构 SSO 登录（在 CDP Chrome 窗口中完成 Institutional Sign In）
  ⚠ IEEE 不支持纯 IP 认证下载 PDF，必须通过 SSO/Shibboleth 登录。

Usage:
  # 交互式（自动弹出登录页）
  python3 scripts/download_via_ieee.py --papers paper1,paper2 --port 9223

  # 其他常用
  python3 scripts/download_via_ieee.py doi_list.txt --output paper-temp/
  python3 scripts/download_via_ieee.py --check-session --port 9223
  python3 scripts/download_via_ieee.py --login --port 9223
  python3 scripts/download_via_ieee.py --skip-session-check --papers paper1 --port 9223

输入文件格式（每行一个DOI）：
  10.1109/tvt.2022.3183866
  10.1109/itec51675.2021.9490073
"""

import sys, os, time, re, json, base64, urllib.request

# Ensure scripts/ is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cdp_utils import (check_cdp, get_cdp_ws_url, create_tab, close_tab,
                        list_tabs, send_cmd_and_wait, check_required_deps)
from console_compat import configure_console_output

configure_console_output()

CDP_PORT = 9223
OUTPUT_DIR = "paper-temp"


# ===== 工具函数 =====

def extract_dois(input_path):
    """从文件提取 DOI 列表。"""
    dois = set()
    with open(input_path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    for m in re.finditer(r"10\.\d{4,}/[^\s,;)\]}\\\"]+", text):
        doi = m.group(0).rstrip(".,;")
        dois.add(doi)
    return sorted(dois)


def doi_to_filename(doi):
    """DOI → 安全的文件名。"""
    safe = doi.replace("/", "_").replace(":", "_")
    return f"{safe}.pdf"


def get_tab_ws_url(port, tid):
    """获取标签页的 WebSocket 调试 URL。"""
    for t in list_tabs(port):
        if t.get("id") == tid:
            return t.get("webSocketDebuggerUrl")
    return None


def close_stale_stamp_tabs(port):
    """关闭所有残留的 stamp/getPDF 标签页（防止错误捕获旧 PDF）。"""
    closed = 0
    for t in list_tabs(port):
        u = t.get("url", "")
        if "stamp" in u or "getPDF" in u:
            close_tab(port, t["id"])
            closed += 1
    if closed:
        print(f"  [清理] 关闭了 {closed} 个残留的 stamp 标签页")


# ===== 两步走策略 =====

def step_a_click_pdf(port, doc_url, arnumber, timeout=30):
    """
    Step A（v1.2）：导航到文章页 → 提取 PDF 按钮的 stamp URL → 通过 _capture_stamp_pdf 下载。

    改进（v1.2）：
      - 不再依赖点击+新标签页扫描，直接从页面提取 stamp URL
      - 使用 _capture_stamp_pdf 创建新标签页，在导航前启用 Fetch 拦截
      - 解决了 PDF 被 Chrome 查看器消费后 getResponseBody 返回空的问题

    返回 PDF bytes，失败返回 None。
    """
    _, tid = create_tab(port, doc_url)
    time.sleep(8)  # 等待 SPA 页面完全渲染

    tws_url = get_tab_ws_url(port, tid)
    if not tws_url:
        close_tab(port, tid)
        return None

    ws = websocket.create_connection(tws_url, timeout=10)
    send_cmd_and_wait(ws, "Page.enable")
    send_cmd_and_wait(ws, "Runtime.enable")

    # 提取 PDF 按钮的 stamp URL（分层选择器，不点击，只读 href）
    ws.send(json.dumps({"id": 50, "method": "Runtime.evaluate",
        "params": {"expression": """
            (() => {
                var selectors = [
                    '.document-actions-bar a[href*="stamp"]',
                    '.document-actions a[href*="stamp"]',
                    '.xpl-btn-pdf',
                    'a[href*="/stamp/"]',
                    'a[href*="stamp.jsp"]',
                    'a[href*="getPDF.jsp"]',
                ];
                for (var s = 0; s < selectors.length; s++) {
                    var btn = document.querySelector(selectors[s]);
                    if (btn && btn.href && btn.href.indexOf('stamp') >= 0) {
                        return 'STAMP_URL:' + btn.href;
                    }
                }
                // 文本匹配兜底
                var all = document.querySelectorAll('a');
                for (var i = 0; i < all.length; i++) {
                    var t = (all[i].textContent || '').trim();
                    var h = (all[i].href || '');
                    if ((t === 'PDF' || t === 'Download PDF' || t === 'View PDF') &&
                        h.indexOf('stamp') >= 0) {
                        return 'STAMP_URL:' + h;
                    }
                }
                if (window.location.href.indexOf('denied') >= 0) {
                    return 'DENIED';
                }
                return 'NO_BUTTON';
            })()
        """, "returnByValue": True}}))

    try:
        ws.settimeout(5)
        msg = json.loads(ws.recv())
        click_result = (msg.get("result", {})
                        .get("result", {}).get("value", ""))
    except Exception:
        click_result = "TIMEOUT"

    print(f"  [Step A] 提取结果: {click_result[:120]}")

    if "denied" in click_result.lower():
        print(f"  ⚠ 访问被拒绝 — 机构订阅未覆盖此期刊")
        ws.close()
        close_tab(port, tid)
        return None

    if not click_result.startswith("STAMP_URL:"):
        print(f"  [Step A] 未找到 stamp URL — 可能未登录或无权限")
        ws.close()
        close_tab(port, tid)
        return None

    stamp_url = click_result[len("STAMP_URL:"):]
    print(f"  [Step A] 提取到 stamp URL: {stamp_url[:120]}")

    # 关闭文章页标签页
    ws.close()
    close_tab(port, tid)

    # 用文章页 URL 作为 Referrer（v1.0.1: IEEE 校验 Referer，缺失会 deny）
    print(f"  [Step A] 带 Referrer 捕获...")
    pdf = _capture_stamp_pdf(port, stamp_url, referrer=doc_url, timeout=timeout)
    if pdf:
        print(f"  [Step A] ✅ PDF 捕获成功 ({len(pdf)} bytes)")
    return pdf


def step_b_direct_stamp(port, arnumber, doc_url=None, timeout=25):
    """
    Step B（回退，v1.0.1）：通过 _capture_stamp_pdf 直接导航到 stamp URL。

    尝试 stamp/stamp.jsp → stampPDF/getPDF.jsp，都带 doc_url 作为 Referrer。
    """
    urls_to_try = [
        f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={arnumber}",
        f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={arnumber}",
    ]

    for url in urls_to_try:
        print(f"  [Step B] 尝试: {url[:80]}")
        pdf = _capture_stamp_pdf(port, url, referrer=doc_url, timeout=timeout)
        if pdf:
            print(f"  [Step B] ✅ PDF 捕获成功 ({len(pdf)} bytes)")
            return pdf

    return None


def _capture_stamp_pdf(port, stamp_url, referrer=None, timeout=25):
    """
    v1.0.1：创建新标签页 → 先启用 Fetch → 带 Referrer 导航 → 捕获 PDF。

    关键改进：
      - Fetch 必须在 Page.navigate 之前启用（否则 PDF 被 Chrome 查看器消费）
      - 必须带 Referrer（IEEE 校验 this，缺失则返回 denyReason=-501）
      - getResponseBody 超时 30s（适配 TPEL 等 5MB+ 大 PDF）

    返回 PDF bytes，失败返回 None。
    """
    try:
        _, tid = create_tab(port, "about:blank")
    except Exception:
        return None

    time.sleep(0.5)
    tws_url = get_tab_ws_url(port, tid)
    if not tws_url:
        close_tab(port, tid)
        return None

    pdf = None
    try:
        ws = websocket.create_connection(tws_url, timeout=10)

        # 2. 先启用 Fetch（关键：必须在 Page.navigate 之前）
        send_cmd_and_wait(ws, "Fetch.enable", {
            "patterns": [{"urlPattern": "*", "requestStage": "Response"}]
        })

        # 3. 带 Referrer 导航到 stamp URL（v1.0.1: IEEE 校验 Referer）
        nav_params = {"url": stamp_url}
        if referrer:
            nav_params["referrer"] = referrer
        ws.send(json.dumps({"id": 1, "method": "Page.navigate",
            "params": nav_params}))

        # 4. 等待 Fetch.requestPaused 并捕获 PDF
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                ws.settimeout(2)
                msg = json.loads(ws.recv())
            except Exception:
                continue

            if msg.get("method") == "Fetch.requestPaused":
                rid = msg["params"]["requestId"]

                # 检查是否是 PDF 响应
                resp_headers = msg["params"].get("responseHeaders", [])
                ct = ""
                for h in resp_headers:
                    if h.get("name", "").lower() == "content-type":
                        ct = h.get("value", "")

                rurl = msg["params"].get("request", {}).get("url", "")
                # stamp.jsp 返回 HTML 中间页，只有 getPDF.jsp 返回 application/pdf
                is_pdf = "application/pdf" in ct or "getPDF" in rurl

                if is_pdf:
                    ws.send(json.dumps({"id": 100, "method": "Fetch.getResponseBody",
                        "params": {"requestId": rid}}))
                    try:
                        ws.settimeout(30)  # 大 PDF 需要更长超时（TPEL 论文可达 5+ MB）
                        resp = json.loads(ws.recv())
                        if "result" in resp:
                            body = resp["result"].get("body", "")
                            b64 = resp["result"].get("base64Encoded", False)
                            if body:
                                d = base64.b64decode(body) if b64 else \
                                    body.encode("latin-1", errors="ignore")
                                if d[:4] == b"%PDF" and len(d) > 5000:
                                    pdf = d
                    except Exception:
                        pass

                ws.send(json.dumps({"id": 101, "method": "Fetch.continueRequest",
                    "params": {"requestId": rid}}))

                if pdf:
                    break

            elif msg.get("method") == "Fetch.authRequired":
                rid = msg["params"]["requestId"]
                ws.send(json.dumps({"id": 102, "method": "Fetch.continueWithAuth",
                    "params": {"requestId": rid}}))
    finally:
        try:
            ws.close()
        except Exception:
            pass
        close_tab(port, tid)

    return pdf


def resolve_arnumber(doi):
    """
    通过 DOI 解析 IEEE arnumber。
    导航到 doi.org，提取重定向目标 URL 中的 arnumber。
    """
    try:
        req = urllib.request.Request(
            f"https://doi.org/{doi}",
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                     "AppleWebKit/537.36"}
        )
        resp = urllib.request.urlopen(req, timeout=10)
        final_url = resp.geturl()
        m = re.search(r"/document/(\d+)", final_url)
        if m:
            return m.group(1), final_url
        return None, final_url
    except Exception as e:
        return None, str(e)


def check_session(port):
    """检查 CDP 浏览器是否有 IEEE 机构会话 Cookie。"""
    import websocket as _ws
    try:
        wu = get_cdp_ws_url(port)
        ws = _ws.create_connection(wu, timeout=10)
        ws.send(json.dumps({"id": 1, "method": "Network.getAllCookies"}))
        cookies = []
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == 1:
                cookies = msg.get("result", {}).get("cookies", [])
                break
        ws.close()
        ieee = [c for c in cookies if "ieee" in c.get("domain", "")]
        return len(cookies), len(ieee), cookies
    except Exception:
        return -1, -1, []


def print_session_guidance(port):
    """检查 IEEE 机构会话。无会话时给出登录指引并返回 False。"""
    total_c, ieee_c, _ = check_session(port)
    print(f"\n📋 CDP 浏览器会话状态: Cookie 总数={total_c}, IEEE Cookie={ieee_c}")
    if ieee_c == 0:
        print("╔══════════════════════════════════════════════════════════╗")
        print("║  ⚠ 未检测到 IEEE 机构会话                               ║")
        print("║                                                        ║")
        print("║  IEEE 不支持纯 IP 认证下载 PDF。                         ║")
        print("║  必须通过 SSO/Shibboleth 完成机构登录：                  ║")
        print("║                                                        ║")
        print("║  1. 在 CDP Chrome 窗口中打开 ieeexplore.ieee.org        ║")
        print("║  2. 点击 'Institutional Sign In'                        ║")
        print("║  3. 选择你的机构 → 完成 SSO/Shibboleth 登录            ║")
        print("║  4. 登录后重新运行本脚本                                ║")
        print("║                                                        ║")
        print("║  验证登录: python3 scripts/download_via_ieee.py \\       ║")
        print("║              --check-session --port 9223                ║")
        print("╚══════════════════════════════════════════════════════════╝")
        return False
    else:
        print(f"  ✅ 检测到 {ieee_c} 个 IEEE Cookie — 机构会话有效，可以下载")
        return True


# ===== 主入口 =====

def main():
    global CDP_PORT, OUTPUT_DIR

    # 解析命令行参数
    input_path = None
    inline_dois = []
    skip_session_check = False
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--port" and i + 1 < len(sys.argv):
            CDP_PORT = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--output" and i + 1 < len(sys.argv):
            OUTPUT_DIR = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--papers" and i + 1 < len(sys.argv):
            inline_dois = [d.strip() for d in sys.argv[i + 1].split(",")]
            i += 2
        elif sys.argv[i] == "--skip-session-check":
            skip_session_check = True
            i += 1
        elif sys.argv[i] == "--check-session":
            # 仅检查会话状态
            if not check_cdp(CDP_PORT):
                print(f"⚠ CDP Chrome（端口 {CDP_PORT}）未运行。")
                return
            has_s = print_session_guidance(CDP_PORT)
            if not has_s:
                print("\n💡 提示：运行以下命令在 CDP Chrome 中打开 IEEE 登录页：")
                print(f"   python3 scripts/download_via_ieee.py --login --port {CDP_PORT}")
            return
        elif sys.argv[i] == "--login":
            # 在 CDP Chrome 中打开 IEEE 页面以便登录
            if not check_cdp(CDP_PORT):
                print(f"⚠ CDP Chrome（端口 {CDP_PORT}）未运行。")
                return
            from cdp_utils import create_tab as _ct
            _ct(CDP_PORT, "https://ieeexplore.ieee.org/")
            print("✅ 已在 CDP Chrome 中打开 IEEE Xplore 首页")
            print("   请在窗口中完成 Institutional Sign In 后重新运行下载。")
            return
        elif sys.argv[i].startswith("--"):
            print(f"未知参数: {sys.argv[i]}")
            sys.exit(1)
        else:
            input_path = sys.argv[i]
            i += 1

    # 收集 DOI 列表
    dois = []
    if input_path:
        dois = extract_dois(input_path)
    elif inline_dois:
        dois = inline_dois
    else:
        print(__doc__)
        sys.exit(1)

    if not dois:
        print("没有找到待下载的 DOI。")
        return

    print(f"待下载论文数: {len(dois)}")

    # 检查依赖
    if not check_required_deps():
        print("\n请先安装依赖：pip install websocket-client")
        return

    # 检查 CDP 浏览器
    if not check_cdp(CDP_PORT):
        print(f"\n⚠ CDP Chrome（端口 {CDP_PORT}）未运行。")
        print("请先启动 Chrome（首次需在窗口中完成 Institutional Sign In）：")
        print(f"  {sys.executable} scripts/start_cdp_browser.py "
              f"--port {CDP_PORT} --url https://ieeexplore.ieee.org/")
        print("  macOS/Linux 兼容入口：bash scripts/start_cdp_chrome.sh "
              f"--port {CDP_PORT} --url https://ieeexplore.ieee.org/")
        return

    # 会话检查（交互式登录流程）
    if skip_session_check:
        print("\n⏭ 跳过会话检查（--skip-session-check）")
        has_session = True
    else:
        has_session = print_session_guidance(CDP_PORT)
        if not has_session:
            # 自动打开 IEEE 登录页，提示用户在对话中说"已登录"
            create_tab(CDP_PORT, "https://ieeexplore.ieee.org/")
            print("\n┌──────────────────────────────────────────────────────────┐")
            print("│  📌 已在 CDP Chrome 中打开 IEEE Xplore                     │")
            print("│                                                          │")
            print("│  请在 CDP Chrome 窗口中完成机构登录：                      │")
            print("│  1. 点击 'Institutional Sign In'                         │")
            print("│  2. 选择你的机构 → 完成 SSO/Shibboleth 登录             │")
            print("│  3. 确认页面右上角显示你的机构名称                        │")
            print("│                                                          │")
            print("│  IEEE 不支持纯 IP 认证下载 PDF，必须 SSO 登录。           │")
            print("│                                                          │")
            print("│  登录完成后，在对话中说「已登录」继续下载。                │")
            print("└──────────────────────────────────────────────────────────┘")
            print("\n⏸ 等待登录确认...（在对话中说「已登录」）")
            print("[HERMES_PAUSE] IEEE_SESSION_REQUIRED")
            return

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 逐篇下载
    results = []
    for idx, doi in enumerate(dois):
        print(f"\n{'='*50}")
        print(f"[{idx + 1}/{len(dois)}] {doi}")

        # 解析 arnumber
        arnumber, doc_url = resolve_arnumber(doi)
        if not arnumber:
            print(f"  ❌ 无法解析 arnumber (URL: {doc_url[:80]})")
            results.append((doi, "FAILED", "arnumber 解析失败"))
            continue

        print(f"  arnumber: {arnumber}")

        # 清理之前残留的 stamp 标签页（防止捕获错误的 PDF）
        close_stale_stamp_tabs(CDP_PORT)

        pdf = None

        # Step A: 访问文章页 → 提取 stamp URL → Fetch 预启用捕获
        print("  [Step A] 文章页 → 提取 stamp URL → Fetch 捕获...")
        pdf = step_a_click_pdf(CDP_PORT, doc_url, arnumber, timeout=30)

        # Step B（回退）：直接 stamp URL
        if not pdf:
            print("  [Step A] 失败，回退到 Step B...")
            pdf = step_b_direct_stamp(CDP_PORT, arnumber, doc_url=doc_url, timeout=25)

        if pdf:
            fname = f"{arnumber}_{doi_to_filename(doi)}"
            fpath = os.path.join(OUTPUT_DIR, fname)
            with open(fpath, "wb") as f:
                f.write(pdf)
            print(f"  ✅ 已保存: {fname} ({len(pdf)//1024} KB)")
            results.append((doi, "OK", len(pdf)))
        else:
            print("  ❌ 下载失败（会话可能已过期）")
            results.append((doi, "FAILED", "两步走策略均失败"))

    # 汇总
    print(f"\n{'='*50}")
    print("下载汇总:")
    ok = sum(1 for r in results if r[1] == "OK")
    for doi, status, detail in results:
        sz = f" ({detail//1024} KB)" if isinstance(detail, int) else f" ({detail})"
        icon = "✅" if status == "OK" else "❌"
        print(f"  {icon} {doi}{sz if status == 'OK' else ''}")
    print(f"\n共 {len(results)} 篇，成功 {ok} 篇，失败 {len(results)-ok} 篇")

    if ok < len(results):
        print("\n💡 下载失败的论文可能是会话过期。请尝试：")
        print(f"   1. 重新登录: python3 scripts/download_via_ieee.py --login --port {CDP_PORT}")
        print(f"   2. 验证会话: python3 scripts/download_via_ieee.py --check-session --port {CDP_PORT}")
        print(f"   3. 重试下载: 将会话检查通过后重新运行本命令")


if __name__ == "__main__":
    # 延迟导入 websocket（确保依赖检查优先）
    import websocket
    main()
