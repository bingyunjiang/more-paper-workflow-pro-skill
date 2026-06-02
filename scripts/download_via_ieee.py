#!/usr/bin/env python3
"""
IEEE CDP 批量下载器。

流程（两步走策略）：
  Step A（首选）：导航到文章页 → 点击PDF按钮 → 检测新标签页/同页跳转 → Fetch捕获
  Step B（回退）：直接导航到 stamp/getPDF URL → Fetch捕获

依赖：
  - Google Chrome CDP（--remote-debugging-port=9223）
  - websocket-client（pip install websocket-client）
  - IEEE 机构访问（通过 CDP Chrome 窗口登录，或 IP 认证）

Usage:
  python3 scripts/download_via_ieee.py doi_list.txt --port 9223
  python3 scripts/download_via_ieee.py doi_list.txt --output paper-temp/
  python3 scripts/download_via_ieee.py --papers paper1,paper2

输入文件格式（每行一个DOI）：
  10.1109/tvt.2022.3183866
  10.1109/itec51675.2021.9490073
"""

import sys, os, time, re, json, base64, urllib.request

# Ensure scripts/ is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cdp_utils import (check_cdp, get_cdp_ws_url, create_tab, close_tab,
                        list_tabs, send_cmd_and_wait, check_required_deps)

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
    Step A：导航到文章页 → 点击PDF按钮 → 在新标签页或同页跳转中 Fetch 捕获。

    改进（v1.1）：
      - 点击后先检测当前标签页是否跳转到 stamp/getPDF
      - 再扫描新开的标签页
      - 过滤非当前 arnumber 的标签页（防止捕获残留旧标签页）
      - 分层 PDF 按钮选择器（覆盖新旧 IEEE Xplore 布局）

    返回 PDF bytes，失败返回 None。
    """
    wu, tid = create_tab(port, doc_url)
    time.sleep(6)  # 等待页面加载

    tws_url = get_tab_ws_url(port, tid)
    if not tws_url:
        close_tab(port, tid)
        return None

    ws = websocket.create_connection(tws_url, timeout=10)
    send_cmd_and_wait(ws, "Page.enable")
    send_cmd_and_wait(ws, "Runtime.enable")

    # 点击 PDF 按钮（分层选择器，适配新旧 IEEE Xplore 布局）
    ws.send(json.dumps({"id": 50, "method": "Runtime.evaluate",
        "params": {"expression": """
            (() => {
                var selectors = [
                    '.document-actions-bar a[href*="stamp"]',
                    '.document-actions a[href*="stamp"]',
                    '.pdf-btn-container a',
                    '.xpl-btn-pdf',
                    'a[href*="/stamp/"]',
                    'a[class*="pdf"]',
                ];
                for (var s = 0; s < selectors.length; s++) {
                    var btn = document.querySelector(selectors[s]);
                    if (btn && btn.href && btn.href.indexOf('stamp') >= 0) {
                        btn.click(); return 'CLICKED:' + selectors[s];
                    }
                }
                var all = document.querySelectorAll('a');
                for (var i = 0; i < all.length; i++) {
                    var t = (all[i].textContent || '').trim();
                    var h = (all[i].href || '');
                    if ((t === 'PDF' || t === 'Download PDF' || t === 'View PDF') &&
                        h.indexOf('stamp') >= 0) {
                        all[i].click(); return 'CLICKED:text:' + t;
                    }
                }
                if (window.location.href.indexOf('denied') >= 0) {
                    return 'DENIED';
                }
                return 'NO_BUTTON';
            })()
        """, "returnByValue": True}}))
    time.sleep(4)

    # 检查点击结果 + 当前页面 URL
    ws.send(json.dumps({"id": 51, "method": "Runtime.evaluate",
        "params": {"expression": "window.location.href", "returnByValue": True}}))
    time.sleep(0.5)

    click_result = None
    url_after = ""
    try:
        ws.settimeout(3)
        msg = json.loads(ws.recv())  # id=50
        click_result = (msg.get("result", {})
                        .get("result", {}).get("value", ""))
        _ = json.loads(ws.recv())    # id=51
        url_after = _.get("result", {}).get("result", {}).get("value", "")
    except Exception:
        pass

    print(f"  [Step A] 点击结果: {click_result}")
    if "denied" in url_after:
        print(f"  ⚠ 访问被拒绝（{url_after[:80]}）— 机构订阅未覆盖此期刊")
        ws.close()
        close_tab(port, tid)
        return None

    # v1.1: 先检查当前标签页是否跳转到 stamp/getPDF（同页跳转）
    pdf = None
    if ("stamp" in url_after or "getPDF" in url_after) and \
       str(arnumber) in url_after:
        print(f"  [Step A] 当前标签页已跳转: {url_after[:100]}")
        tws2 = get_tab_ws_url(port, tid)
        if tws2:
            pdf = _fetch_capture_on_tab(tws2, ["*"], timeout=15)
            if pdf:
                print(f"  [Step A] ✅ PDF 捕获成功（同页跳转, {len(pdf)} bytes）")
                ws.close()
                close_tab(port, tid)
                return pdf

    # 扫描新开的 stamp/getPDF 标签页（v1.1: 按 arnumber 过滤，防止捕获残留旧标签）
    if not pdf:
        for t in list_tabs(port):
            u = t.get("url", "")
            if (("stamp" in u or "getPDF" in u) and t["id"] != tid
                    and str(arnumber) in u):
                print(f"  [Step A] 检测到新标签页: {u[:100]}")
                time.sleep(2)  # 等待新标签页完全加载
                ptws_url = get_tab_ws_url(port, t["id"])
                if ptws_url:
                    pdf = _fetch_capture_on_tab(ptws_url, ["*"], timeout=15)
                    if pdf:
                        print(f"  [Step A] ✅ PDF 捕获成功（新标签页, {len(pdf)} bytes)")
                close_tab(port, t["id"])
                if pdf:
                    break

    ws.close()
    close_tab(port, tid)
    return pdf


def step_b_direct_stamp(port, arnumber, timeout=25):
    """
    Step B（回退）：直接导航到 stamp/getPDF URL → Fetch 捕获。

    按以下顺序尝试：
      1. stamp/stamp.jsp?tp=&arnumber=XXXXX
      2. stampPDF/getPDF.jsp?tp=&arnumber=XXXXX
    """
    urls_to_try = [
        f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={arnumber}",
        f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={arnumber}",
    ]

    for url in urls_to_try:
        print(f"  [Step B] 尝试: {url[:80]}")
        wu, tid = create_tab(CDP_PORT, url)
        time.sleep(5)

        # 检查是否被 denied
        denied = False
        tabs = list_tabs(CDP_PORT)
        for t in tabs:
            if t.get("id") == tid:
                loaded_url = t.get("url", "")
                if "denied" in loaded_url:
                    print(f"  ⚠ 访问被拒绝（denied）— 机构订阅未覆盖此论文")
                    denied = True
                break

        if denied:
            close_tab(CDP_PORT, tid)
            continue

        tws_url = get_tab_ws_url(CDP_PORT, tid)
        if tws_url:
            pdf = _fetch_capture_on_tab(tws_url, ["*"], timeout=timeout)
            if pdf:
                print(f"  [Step B] ✅ PDF 捕获成功 ({len(pdf)} bytes)")
                close_tab(CDP_PORT, tid)
                return pdf
        close_tab(CDP_PORT, tid)

    return None


def _fetch_capture_on_tab(tws_url, patterns, timeout=20):
    """
    在指定标签页上启用 Fetch → reload → 捕获 PDF 响应。
    返回 PDF bytes，失败返回 None。
    """
    try:
        ws = websocket.create_connection(tws_url, timeout=10)
    except Exception:
        return None

    pdf = None
    try:
        send_cmd_and_wait(ws, "Page.enable")
        pats = [{"urlPattern": p, "requestStage": "Response"} for p in patterns]
        send_cmd_and_wait(ws, "Fetch.enable", {"patterns": pats})

        # Page.reload（不用 send_cmd_and_wait，避免吃掉 Fetch.requestPaused 事件）
        ws.send(json.dumps({"id": 99, "method": "Page.reload"}))

        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                ws.settimeout(1)
                msg = json.loads(ws.recv())
            except Exception:
                continue

            if msg.get("method") == "Fetch.requestPaused":
                rid = msg["params"]["requestId"]
                ws.send(json.dumps({"id": 100, "method": "Fetch.getResponseBody",
                    "params": {"requestId": rid}}))
                try:
                    ws.settimeout(5)
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
    finally:
        try:
            ws.close()
        except Exception:
            pass
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
    """输出机构登录引导信息。"""
    total_c, ieee_c, _ = check_session(port)
    print(f"\n📋 CDP 浏览器 Cookie 状态: 总数={total_c}, IEEE={ieee_c}")
    if ieee_c == 0:
        print("╔══════════════════════════════════════════════════════════╗")
        print("║  ⚠ 未检测到 IEEE 机构会话                               ║")
        print("║                                                        ║")
        print("║  请在 CDP Chrome 窗口中完成机构登录：                    ║")
        print("║  1. CDP Chrome 已自动打开 ieeexplore.ieee.org           ║")
        print("║  2. 点击页面上的 'Institutional Sign In'                ║")
        print("║  3. 选择你的机构 → 完成 SSO/Shibboleth 登录            ║")
        print("║  4. 登录成功后回到此终端继续                            ║")
        print("║                                                        ║")
        print("║  如果使用 IP 认证（校园网/VPN），Cookie 应为 0，         ║")
        print("║  下载仍会尝试，但成功率取决于 IEEE 是否识别 IP。         ║")
        print("╚══════════════════════════════════════════════════════════╝")
    else:
        print(f"  ✅ 检测到 {ieee_c} 个 IEEE Cookie — 机构会话有效")
    return ieee_c > 0


# ===== 主入口 =====

def main():
    global CDP_PORT, OUTPUT_DIR

    # 解析命令行参数
    input_path = None
    inline_dois = []
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
        elif sys.argv[i] == "--check-session":
            # 仅检查会话状态
            if not check_cdp(CDP_PORT):
                print(f"⚠ CDP Chrome（端口 {CDP_PORT}）未运行。")
                return
            print_session_guidance(CDP_PORT)
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
        print("请先启动 Chrome：")
        print(f'  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \\')
        print(f"    --remote-debugging-port={CDP_PORT} \\")
        print(f"    --remote-allow-origins=http://127.0.0.1:{CDP_PORT} \\")
        print(f"    --no-first-run --no-default-browser-check \\")
        print(f"    --disable-blink-features=AutomationControlled \\")
        print(f"    --user-data-dir=/tmp/chrome_ieee \\")
        print(f"    https://ieeexplore.ieee.org/")
        return

    # 会话检查与引导
    has_session = print_session_guidance(CDP_PORT)

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

        # Step A: 访问文章页 → 点击 PDF 按钮
        print(f"  [Step A] 文章页 → 点击 PDF → 捕获...")
        pdf = step_a_click_pdf(CDP_PORT, doc_url, arnumber, timeout=30)

        # Step B（回退）：直接 stamp URL
        if not pdf:
            print(f"  [Step A] 失败，回退到 Step B...")
            pdf = step_b_direct_stamp(CDP_PORT, arnumber, timeout=25)

        if pdf:
            fname = f"{arnumber}_{doi_to_filename(doi)}"
            fpath = os.path.join(OUTPUT_DIR, fname)
            with open(fpath, "wb") as f:
                f.write(pdf)
            print(f"  ✅ 已保存: {fname} ({len(pdf)//1024} KB)")
            results.append((doi, "OK", len(pdf)))
        else:
            print(f"  ❌ 下载失败")
            if not has_session:
                print(f"  💡 提示：尝试在 CDP Chrome 窗口中登录机构账号后重试")
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

    # 未登录时给出后续指引
    if not has_session and ok < len(results):
        print("\n💡 如需通过机构访问下载失败的论文：")
        print("   1. 在 CDP Chrome 窗口中完成 IEEE 机构登录")
        print("   2. 登录后重新运行本脚本重试失败项")
        print("   3. 或运行: python3 scripts/download_via_ieee.py --check-session 检查状态")


if __name__ == "__main__":
    # 延迟导入 websocket（确保依赖检查优先）
    import websocket
    main()
