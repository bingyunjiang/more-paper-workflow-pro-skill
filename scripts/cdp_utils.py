#!/usr/bin/env python3
"""
Shared CDP (Chrome DevTools Protocol) utilities for browser-based PDF downloads.

Used by download_via_scihub.py, parallel_sd_download.py, and auto_sd_downloader.py
to eliminate duplicated WebSocket connection and tab management logic.
"""
import json, os, sys, shutil, subprocess, urllib.request, time

# ---- websocket-client dependency check ----
_websocket_missing = None  # set to error message if import fails
try:
    import websocket
except ImportError as e:
    _websocket_missing = str(e)
    websocket = None  # type: ignore


def get_cdp_ws_url(port=9223):
    """Get the browser's WebSocket debugger URL."""
    resp = urllib.request.urlopen(
        f"http://127.0.0.1:{port}/json/version", timeout=5)
    return json.loads(resp.read())["webSocketDebuggerUrl"]


def check_cdp(port=9223):
    """Return True if a CDP browser is listening on the given port."""
    try:
        get_cdp_ws_url(port)
        return True
    except Exception:
        return False


def list_tabs(port=9223):
    """Return the list of open tabs from a CDP browser."""
    resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=5)
    return json.loads(resp.read())


def close_all_tabs(port=9223):
    """Close every open tab on the CDP browser (reuses one WebSocket connection)."""
    try:
        wu = get_cdp_ws_url(port)
        tabs = list_tabs(port)
        ws = websocket.create_connection(wu, timeout=5)
        for t in tabs:
            ws.send(json.dumps({"id": 1, "method": "Target.closeTarget",
                                "params": {"targetId": t["id"]}}))
            try:
                ws.recv()
            except Exception:
                pass
        ws.close()
    except Exception:
        pass


def close_tab(port, target_id):
    """Close a single tab by targetId."""
    try:
        wu = get_cdp_ws_url(port)
        ws = websocket.create_connection(wu, timeout=5)
        ws.send(json.dumps({"id": 1, "method": "Target.closeTarget",
                            "params": {"targetId": target_id}}))
        try:
            ws.recv()
        except Exception:
            pass
        ws.close()
    except Exception:
        pass


def send_cmd_and_wait(ws, method, params=None):
    """Send a CDP command and block until the matching response arrives.

    Returns the result dict, or None on timeout/error.
    """
    mid = int(time.time() * 1000) % 100000
    ws.send(json.dumps({"id": mid, "method": method,
                        "params": params or {}}))
    while True:
        try:
            ws.settimeout(15)
            msg = json.loads(ws.recv())
            if msg.get("id") == mid:
                return msg.get("result")
        except Exception:
            return None


def create_tab(port, url):
    """Create a new tab navigating to `url`.

    Returns (browser_ws_url, target_id). Caller should close the returned
    WebSocket after use.
    """
    wu = get_cdp_ws_url(port)
    ws = websocket.create_connection(wu, timeout=10)
    ws.send(json.dumps({"id": 1, "method": "Target.createTarget",
                        "params": {"url": url}}))
    tid = json.loads(ws.recv())["result"]["targetId"]
    ws.close()
    return wu, tid


def get_tab_ws_url(port, target_id):
    """Return the per-tab WebSocket debugger URL for a given target."""
    for t in list_tabs(port):
        if t.get("id") == target_id:
            return t.get("webSocketDebuggerUrl")
    return None


def wait_for_tab_url(port, url_prefix, timeout=10):
    """Poll open tabs until one's URL starts with `url_prefix`.

    Returns the matching tab dict, or None if timeout expires.
    """
    for _ in range(timeout):
        time.sleep(1)
        try:
            tabs = list_tabs(port)
        except Exception:
            break
        for t in tabs:
            u = t.get("url", "")
            if u.startswith(url_prefix):
                return t
    return None


def capture_pdf_via_fetch(port, tab_ws_url, url_pattern, request_path_hint=None):
    """Enable Fetch domain on a tab, reload, and capture the PDF response body.

    Args:
        port: CDP port (for cleanup).
        tab_ws_url: WebSocket debugger URL of the target tab.
        url_pattern: Fetch.enable pattern to match the PDF request.
        request_path_hint: If set, only capture requests whose URL contains this
                           substring (e.g. "main.pdf").

    Returns the raw PDF bytes, or None.
    """
    try:
        pws = websocket.create_connection(tab_ws_url, timeout=10)
    except Exception:
        close_all_tabs(port)
        return None

    pdf_data = None
    try:
        send_cmd_and_wait(pws, "Page.enable")
        send_cmd_and_wait(pws, "Fetch.enable", {
            "patterns": [{"urlPattern": url_pattern, "requestStage": "Response"}]
        })
        send_cmd_and_wait(pws, "Page.reload")

        deadline = time.time() + 25
        while time.time() < deadline:
            try:
                pws.settimeout(0.5)
                msg = json.loads(pws.recv())
            except Exception:
                continue
            if msg.get("method") == "Fetch.requestPaused":
                rid = msg["params"]["requestId"]
                req_url = (msg["params"].get("request") or {}).get("url", "")

                # Only capture if the URL matches our hint (or no hint given)
                should_capture = (
                    request_path_hint is None
                    or request_path_hint in req_url
                )

                if should_capture:
                    pws.send(json.dumps({"id": 100,
                        "method": "Fetch.getResponseBody",
                        "params": {"requestId": rid}}))
                    try:
                        pws.settimeout(8)
                        resp = json.loads(pws.recv())
                        if "result" in resp:
                            body = resp["result"].get("body", "")
                            b64 = resp["result"].get("base64Encoded", False)
                            if body:
                                import base64
                                d = base64.b64decode(body) if b64 else \
                                    body.encode("latin-1", errors="ignore")
                                if d[:4] == b"%PDF" and len(d) > 20000:
                                    pdf_data = d
                    except Exception:
                        pass

                pws.send(json.dumps({"id": 101,
                    "method": "Fetch.continueRequest",
                    "params": {"requestId": rid}}))

                # Once we've captured our target PDF, we can stop
                if should_capture and pdf_data:
                    break
    finally:
        try:
            pws.close()
        except Exception:
            pass

    return pdf_data


# ===== Cross-platform browser management =====

def _is_windows():
    return sys.platform == "win32"


def _is_macos():
    return sys.platform == "darwin"


def find_chrome_path():
    """Find the Chrome/Chromium executable for the current platform.

    Tries in order: CHROME_PATH env var → shutil.which → platform defaults.
    Returns the path string, or None if not found.
    """
    # User override via environment variable
    env_path = os.environ.get("CHROME_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    # shutil.which works on all platforms for PATH-resolvable executables
    for name in ["google-chrome", "google-chrome-stable", "chromium",
                 "chromium-browser", "chrome", "Google Chrome"]:
        found = shutil.which(name)
        if found:
            return found

    # Platform-specific fallback paths
    if _is_macos():
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    elif _is_windows():
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
    else:
        # Linux
        candidates = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
        ]

    for path in candidates:
        if os.path.isfile(path):
            return path

    return None


def find_edge_path():
    """Find the Microsoft Edge executable for the current platform.

    Tries in order: EDGE_PATH env var → shutil.which → platform defaults.
    Returns the path string, or None if not found.
    """
    env_path = os.environ.get("EDGE_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    for name in ["microsoft-edge", "microsoft-edge-stable", "msedge", "edge"]:
        found = shutil.which(name)
        if found:
            return found

    if _is_macos():
        candidates = [
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ]
    elif _is_windows():
        candidates = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
    else:
        candidates = [
            "/usr/bin/microsoft-edge",
            "/usr/bin/microsoft-edge-stable",
            "/opt/microsoft/msedge/msedge",
        ]

    for path in candidates:
        if os.path.isfile(path):
            return path

    return None


def start_browser(port, user_data_dir, url="about:blank", browser_path=None):
    """Start a Chromium-based browser with CDP remote debugging enabled.

    Args:
        port: CDP debugging port.
        user_data_dir: Path for the browser's temporary profile.
        url: Initial page to open.
        browser_path: Path to browser executable. Auto-detected if None.

    Returns a Popen object, or None if the browser couldn't be started.
    """
    if browser_path is None:
        browser_path = find_chrome_path()

    if browser_path is None:
        return None

    # Ensure profile directory exists
    os.makedirs(user_data_dir, exist_ok=True)

    try:
        proc = subprocess.Popen([
            browser_path,
            f"--remote-debugging-port={port}",
            f"--remote-allow-origins=http://127.0.0.1:{port}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-blink-features=AutomationControlled",
            f"--user-data-dir={user_data_dir}",
            url,
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        return None
    except Exception:
        return None

    # Wait for CDP to be ready
    for _ in range(15):
        time.sleep(1)
        if check_cdp(port):
            return proc
    return proc  # may have failed, caller should check_cdp


def kill_browser_by_port(port):
    """Kill the browser process listening on the given port.

    Cross-platform: uses netstat/ss to find the PID, then kills it.
    """
    try:
        if _is_windows():
            # Windows: netstat -ano | findstr :<port>
            result = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True, timeout=10)
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    pid = parts[-1]
                    subprocess.run(["taskkill", "/F", "/PID", pid],
                                   capture_output=True)
                    break
        else:
            # macOS/Linux: lsof or ss
            try:
                result = subprocess.run(
                    ["lsof", "-ti", f":{port}"], capture_output=True, text=True, timeout=5)
                pid = result.stdout.strip()
                if pid:
                    os.kill(int(pid), 9)
            except Exception:
                # Fallback: ss (Linux)
                try:
                    result = subprocess.run(
                        ["ss", "-tlnp"], capture_output=True, text=True, timeout=5)
                    for line in result.stdout.splitlines():
                        if f":{port}" in line:
                            import re
                            m = re.search(r"pid=(\d+)", line)
                            if m:
                                os.kill(int(m.group(1)), 9)
                except Exception:
                    pass
    except Exception:
        pass
    time.sleep(1)


def kill_browser_by_profile(profile_dir):
    """Kill browser processes that use the given profile directory.

    Platform-specific pkill/taskkill based on process command line.
    """
    try:
        if _is_windows():
            # Windows: kill processes whose command line contains the profile dir
            subprocess.run(
                ["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
            subprocess.run(
                ["taskkill", "/F", "/IM", "msedge.exe"], capture_output=True)
        else:
            # macOS/Linux
            subprocess.run(
                ["pkill", "-9", "-f", os.path.basename(profile_dir)],
                capture_output=True)
    except Exception:
        pass
    time.sleep(2)


def remove_profile_dir(profile_dir):
    """Remove a browser profile directory. Cross-platform."""
    try:
        if _is_windows():
            subprocess.run(
                ["cmd", "/c", "rmdir", "/s", "/q", profile_dir],
                capture_output=True)
        else:
            subprocess.run(["rm", "-rf", profile_dir], capture_output=True)
    except Exception:
        pass


# ===== Browser install guidance =====

CHROME_INSTALL_GUIDE = """
  ⚠ 未找到 Google Chrome 浏览器。

  请安装 Chrome 并确保其可在命令行中找到：
    macOS:   https://www.google.com/chrome/
    Windows: https://www.google.com/chrome/
    Linux:   sudo apt install google-chrome-stable
             或 sudo snap install chromium

  或设置环境变量指向你的 Chrome 可执行文件：
    export CHROME_PATH="/path/to/chrome"
"""

EDGE_INSTALL_GUIDE = """
  ⚠ 未找到 Microsoft Edge 浏览器（可选，用于并行加速下载）。

  请安装 Edge：
    macOS:   https://www.microsoft.com/edge
    Windows: 通常已预装
    Linux:   https://www.microsoft.com/edge

  或设置环境变量指向你的 Edge 可执行文件：
    export EDGE_PATH="/path/to/msedge"
"""


# ===== Cloudflare / Turnstile detection =====

def _is_cloudflare_challenge(title, url):
    """Detect if a page is showing a Cloudflare/Turnstile challenge."""
    challenge_keywords = [
        "checking your browser", "verifying you are human",
        "verify you are human", "are you a robot",
        "ddos protection", "under attack", "please wait",
        "just a moment", "attention required",
        "challenge", "captcha", "turnstile",
    ]
    title_lower = title.lower()
    url_lower = url.lower()
    for kw in challenge_keywords:
        if kw in title_lower or kw in url_lower:
            return True
    return False


def wait_for_cloudflare(port, tid, timeout=60):
    """Wait for a Cloudflare/Turnstile challenge to auto-resolve.

    Call after navigating to a page that might show a challenge.
    Periodically checks the tab until it either resolves or times out.

    Returns True if the challenge resolved (page loaded normally),
    False if it's still showing a challenge after timeout.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(3)
        try:
            tabs = list_tabs(port)
            for t in tabs:
                if t.get("id") != tid:
                    continue
                title = t.get("title", "")
                url = t.get("url", "")
                if not _is_cloudflare_challenge(title, url):
                    # Challenge resolved — page navigated away or loaded normally
                    return True
        except Exception:
            pass
    return False


# ===== ScienceDirect access check =====

# A known open-access SD paper used to probe whether the browser has access
_SD_TEST_DOI = "10.1016/j.jbusres.2023.113753"
_SD_TEST_URL = f"https://www.sciencedirect.com/science/article/pii/S0148296323001114/pdfft"
_SD_PDF_HOST = "https://pdf.sciencedirectassets.com"


def check_sd_access(port=9223, timeout=10):
    """Test whether ScienceDirect is accessible from the current browser session.

    Navigates to a known SD paper and watches for:
      - PDF redirect → IP-based access OK
      - Login/challenge page → needs manual login

    Returns ("ok", "ip") for IP access, ("ok", "login") for logged-in session,
    or ("blocked", reason_string) if access is blocked.
    """
    if not check_cdp(port):
        return "blocked", "CDP browser not running"

    wu = get_cdp_ws_url(port)
    ws = None
    tid = None

    try:
        ws = websocket.create_connection(wu, timeout=10)
        ws.send(json.dumps({"id": 1, "method": "Target.createTarget",
                           "params": {"url": _SD_TEST_URL}}))
        tid = json.loads(ws.recv())["result"]["targetId"]
        ws.close()
        ws = None
    except Exception:
        if ws:
            try:
                ws.close()
            except Exception:
                pass
        return "blocked", "failed to create browser tab"

    # Wait for redirect or login page
    time.sleep(4)

    try:
        tabs = list_tabs(port)
        for t in tabs:
            if t.get("id") != tid:
                continue
            url = t.get("url", "")
            title = t.get("title", "")

            # PDF redirect → access is working
            if url.startswith(_SD_PDF_HOST) and "main.pdf" in url:
                close_tab(port, tid)
                return "ok", "ip"

            # Still on ScienceDirect → check what happened
            if "sciencedirect.com" in url:
                if "login" in url.lower() or "signin" in url.lower():
                    close_tab(port, tid)
                    return "blocked", "redirected to login page — need SSO/institutional login"
                if "access" in url.lower() or "denied" in url.lower():
                    close_tab(port, tid)
                    return "blocked", "access denied — check institutional subscription"
                # Might still be loading or needs Cloudflare check
                if "challenge" in url.lower() or "captcha" in url.lower():
                    close_tab(port, tid)
                    return "blocked", "Cloudflare challenge detected — complete it in browser first"

            # Maybe Cloudflare challenge — wait for it to auto-resolve
            if _is_cloudflare_challenge(title, url):
                print(f"  ⏳ 检测到 Cloudflare 验证，等待自动完成（最多 60 秒）...", flush=True)
                resolved = wait_for_cloudflare(port, tid, timeout=60)
                if resolved:
                    close_tab(port, tid)
                    return "ok", "login"
                close_tab(port, tid)
                return "blocked", ("Cloudflare 验证未自动完成 —— "
                                   "请在浏览器中手动点击 'Verify you are human'")

            # Neither PDF nor challenge — might be logged-in session still loading
            close_tab(port, tid)
            return "ok", "login"

        # Tab not found in list — might have closed/redirected
        close_tab(port, tid)
        return "blocked", "tab disappeared — possible redirect loop"
    except Exception:
        close_tab(port, tid)
        return "blocked", "failed to check tab state"


SD_ACCESS_GUIDE_IP = """
  ✅ ScienceDirect 访问正常（IP 认证）—— 无需登录，可直接下载。
"""

SD_ACCESS_GUIDE_LOGIN = """
  ✅ 浏览器已登录 ScienceDirect —— 将复用当前会话下载。

  ⚠ 会话过期后，脚本会自动重启浏览器。届时需要重新登录。
"""

SD_ACCESS_GUIDE_BLOCKED = """
  ⚠ 无法访问 ScienceDirect。可能原因和解决方法：

  1. 未连接机构网络 — 连接校园网或 VPN 后重试
  2. 需要 SSO 登录 — 在浏览器中手动打开 https://www.sciencedirect.com
     完成机构登录（脚本启动的浏览器窗口可直接操作）
  3. Cloudflare 验证 — 如看到 "Verify you are human"：
     IP 模式通常自动通过；SSO 模式需在浏览器中手动点击一次
     （通过后会话 cookie 会保留，后续自动复用）
"""

SD_ACCESS_GUIDE_PARALLEL = """
  ⚠ 使用 parallel_sd_download.py 需要先手动准备浏览器：

  1. 启动 Chrome（和可选的 Edge）CDP 模式
  2. 在浏览器中访问 https://www.sciencedirect.com
  3. 完成机构登录 + 通过 Cloudflare 验证（仅需一次）
  4. 保持浏览器运行，然后执行 download 脚本
  5. 同一会话内后续下载不再需要手动操作
"""


# ===== Dependency checking =====

# Map of import name → pip package name + install hint
REQUIRED_DEPS = {
    "websocket": {
        "pip": "websocket-client",
        "hint": "CDP browser control (all download scripts)",
        "import_name": "websocket",
    },
}

OPTIONAL_DEPS = {
    "fitz": {
        "pip": "pymupdf",
        "hint": "PDF full-text extraction (batch_read_pdfs.py)",
        "import_name": "fitz",
    },
}


def _check_dep(pip_name, hint):
    """Print a dependency install instruction and return False."""
    print(f"\n  ⚠ 缺少 Python 依赖: {pip_name}", flush=True)
    print(f"     用途: {hint}", flush=True)
    print(f"     安装: pip install {pip_name}", flush=True)
    return False


def check_required_deps():
    """Check that all required dependencies are installed.

    Call this at startup in scripts that need CDP functionality.
    Returns True if all OK, False if any dependency is missing.
    """
    ok = True
    if _websocket_missing is not None:
        ok = _check_dep("websocket-client", REQUIRED_DEPS["websocket"]["hint"])
    return ok


def check_optional_dep(import_name):
    """Check and print guidance for an optional dependency.

    Returns True if installed, False with install hint if missing.
    Call this before using an optional feature (e.g. PyMuPDF).
    """
    if import_name not in OPTIONAL_DEPS:
        return True  # unknown dep, assume OK
    try:
        __import__(import_name)
        return True
    except ImportError:
        return _check_dep(OPTIONAL_DEPS[import_name]["pip"],
                          OPTIONAL_DEPS[import_name]["hint"])


def print_missing_deps_summary(missing_list):
    """Print a one-shot summary of all missing dependencies and how to install them."""
    if not missing_list:
        return
    print(f"\n{'='*55}", flush=True)
    print("缺少以下 Python 依赖，请先安装：", flush=True)
    print(f"{'='*55}", flush=True)
    for pip_name, hint in missing_list:
        print(f"  pip install {pip_name:25s} # {hint}", flush=True)
    print(f"{'='*55}\n", flush=True)
