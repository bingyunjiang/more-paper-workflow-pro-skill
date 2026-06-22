#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""
Shared CDP (Chrome DevTools Protocol) utilities for browser-based PDF downloads.

Used by download_via_scihub.py, parallel_sd_download.py, and auto_sd_downloader.py
to eliminate duplicated WebSocket connection and tab management logic.
"""
try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import json, os, sys, shutil, subprocess, urllib.request, time


PROFILE_HOME_DIRNAME = ".more-paper-workflow"
LEGACY_PROFILE_HOME_DIRNAME = ".hermes"
CDP_STARTUP_TIMEOUT_SECONDS = 30

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


def get_cdp_browser_product(port=9223):
    """Return the CDP Browser product string, e.g. Chrome/... or Microsoft Edge/..."""
    resp = urllib.request.urlopen(
        f"http://127.0.0.1:{port}/json/version", timeout=5)
    return json.loads(resp.read()).get("Browser", "")


def cdp_browser_matches(port=9223, browser="chrome"):
    """Return True only when the CDP port is backed by the requested browser."""
    expected = (browser or "chrome").lower()
    product = get_cdp_browser_product(port).lower()
    if expected == "edge":
        return "edge" in product or "edg/" in product
    if expected == "chrome":
        is_edge = "edge" in product or "edg/" in product
        return not is_edge and ("chrome" in product or "chromium" in product)
    return False


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

        deadline = time.time() + 60
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
                        pws.settimeout(30)
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
        # The response body has been captured; close the PDF tab so batch
        # downloads do not accumulate already-finished pages.
        try:
            tabs = list_tabs(port)
            for t in tabs:
                if t.get("webSocketDebuggerUrl") == tab_ws_url or t.get("id") == tab_ws_url:
                    close_tab(port, t.get("id"))
                    break
        except Exception:
            pass

    return pdf_data


# ===== Cross-platform browser management =====

def _is_windows():
    return sys.platform == "win32"


def _is_macos():
    return sys.platform == "darwin"


def _profile_home() -> str:
    """Return the neutral home directory used to store persistent browser profiles."""
    return os.path.join(os.path.expanduser("~"), PROFILE_HOME_DIRNAME)


def _launch_log_path(user_data_dir: str) -> str:
    return os.path.join(user_data_dir, "cdp_launch.log")


def _append_launch_log(log_path: str, lines) -> None:
    try:
        with open(log_path, "a", encoding="utf-8") as fh:
            for line in lines:
                fh.write(f"{line}\n")
    except Exception:
        pass


def _macos_app_path_from_binary(browser_path: str) -> str | None:
    marker = ".app/"
    if marker not in browser_path:
        return None
    return browser_path.split(marker, 1)[0] + ".app"


def _windows_start_process_command(browser_path: str, args: list[str]) -> list[str]:
    quoted_args = ",".join("'" + arg.replace("'", "''") + "'" for arg in args)
    escaped_browser_path = browser_path.replace("'", "''")
    script = (
        "$argList = @(" + quoted_args + "); "
        f"Start-Process -FilePath '{escaped_browser_path}' "
        "-ArgumentList $argList"
    )
    return ["powershell", "-NoProfile", "-Command", script]


def _legacy_profile_home() -> str:
    """Return the previous profile home used by older releases."""
    return os.path.join(os.path.expanduser("~"), LEGACY_PROFILE_HOME_DIRNAME)


def _ensure_profile_dir(profile_name: str) -> str:
    """Return the active profile dir, migrating from the legacy location if present."""
    new_dir = os.path.join(_profile_home(), profile_name)
    legacy_dir = os.path.join(_legacy_profile_home(), profile_name)

    if os.path.exists(new_dir):
        return new_dir

    if os.path.exists(legacy_dir):
        try:
            os.makedirs(_profile_home(), exist_ok=True)
            shutil.move(legacy_dir, new_dir)
        except Exception:
            # Fall back to the legacy directory if migration fails.
            return legacy_dir
    return new_dir


def _profile_dir(browser="chrome"):
    """Return the persistent CDP profile directory for a browser."""
    name = "edge_sd_profile" if browser == "edge" else "chrome_sd_profile"
    return _ensure_profile_dir(name)


def get_persistent_profile_dir(browser="chrome") -> str:
    """Public helper for the active persistent CDP profile directory."""
    return _profile_dir(browser)


def get_launch_log_path(browser="chrome") -> str:
    """Public helper for the launch log path of a persistent CDP profile."""
    return _launch_log_path(_profile_dir(browser))


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
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
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

    Anti-detection flags (adapted from ref-downloader's CloakBrowser approach):
      - Disables AutomationControlled (hides navigator.webdriver)
      - Disables component extensions, translate UI, sync, crash reporter
      - Disables renderer backgrounding and hang monitor
      - Hides "Chrome is being controlled by automated software" infobar
    """
    if browser_path is None:
        browser_path = find_chrome_path()

    if browser_path is None:
        return None

    # Ensure profile directory exists
    os.makedirs(user_data_dir, exist_ok=True)

    # Anti-detection flags adapted from ref-downloader / CloakBrowser patterns
    anti_detection_flags = [
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-blink-features=AutomationControlled",
        # Remove "Chrome is being controlled by automated software" infobar
        "--disable-infobars",
        # Prevent extensions from adding detection vectors
        "--disable-component-extensions-with-background-pages",
        # Disable features that expose automation patterns
        "--disable-features=TranslateUI,BlinkGenPropertyTrees,IsolateOrigins,site-per-process",
        # Suppress crash/error reporting (avoids detection via crash patterns)
        "--disable-breakpad",
        "--disable-crash-reporter",
        # Suppress permission prompts
        "--deny-permission-prompts",
        # Disable backgrounding (prevents timing-based detection)
        "--disable-renderer-backgrounding",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        # Disable sync and field trials
        "--disable-sync",
        "--disable-field-trial-config",
        # Disable hang monitor (prevents detection via process monitoring)
        "--disable-hang-monitor",
        "--disable-ipc-flooding-protection",
        # Use a common window size (not a telltale automation size)
        "--window-size=1440,900",
        # Disable default browser check and metrics
        "--disable-default-apps",
        "--metrics-recording-only",
        # Password manager and form autofill (makes browser look used)
        "--disable-features=InfiniteSessionRestore",
    ]

    browser_args = [
        f"--remote-debugging-port={port}",
        f"--remote-allow-origins=http://127.0.0.1:{port}",
        *anti_detection_flags,
        f"--user-data-dir={user_data_dir}",
        url,
    ]
    log_path = _launch_log_path(user_data_dir)
    _append_launch_log(log_path, [
        "",
        f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Launching CDP browser",
        f"browser_path={browser_path}",
        f"port={port}",
        f"url={url}",
    ])

    try:
        log_fh = open(log_path, "a", encoding="utf-8")
    except Exception:
        log_fh = None

    proc = None
    try:
        if _is_macos():
            app_path = _macos_app_path_from_binary(browser_path)
            if not app_path:
                return None
            command = [
                "open",
                "-na",
                app_path,
                "--args",
                *browser_args,
            ]
        elif _is_windows():
            command = _windows_start_process_command(browser_path, browser_args)
        else:
            command = [browser_path, *browser_args]

        _append_launch_log(log_path, [f"command={command!r}"])
        proc = subprocess.Popen(
            command,
            stdout=log_fh or subprocess.DEVNULL,
            stderr=log_fh or subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return None
    except Exception as exc:
        _append_launch_log(log_path, [f"launch_exception={exc!r}"])
        return None
    finally:
        if log_fh:
            log_fh.close()

    # Wait for CDP to be ready
    cdp_ready = False
    for _ in range(CDP_STARTUP_TIMEOUT_SECONDS):
        time.sleep(1)
        if check_cdp(port):
            cdp_ready = True
            break

    if cdp_ready:
        return proc

    # CDP not bound after timeout — likely profile/policy/startup delay
    # Detect "real" profile by checking if user_data_dir is under ~/Library
    real_profile_hints = ["Library/Application Support", "AppData/Local",
                          "AppData/Roaming"]
    is_real_profile = any(h in user_data_dir for h in real_profile_hints)

    if is_real_profile:
        print(f"\n⚠  CDP 端口 {port} 在 {user_data_dir} 上未绑定!", flush=True)
        print(f"   这是用真实 Chrome Profile 启动时的已知问题。", flush=True)
        print(f"   原因：某些扩展或配置阻止了 CDP server 绑定端口。", flush=True)
        print(f"   建议：改用临时 Profile（不传 --user-data-dir，或使用 tempfile 目录）。", flush=True)
        print(f"   诊断：python3 -c \"import urllib.request,json; "
              f"d=json.load(urllib.request.urlopen('http://127.0.0.1:{port}/json/version')); "
              f"print(d.get('Browser','N/A'))\"\n", flush=True)
    else:
        print(f"\n⚠  CDP 端口 {port} 在 {CDP_STARTUP_TIMEOUT_SECONDS}s 内未就绪。", flush=True)

    print(f"   启动日志: {log_path}", flush=True)
    _append_launch_log(log_path, [f"cdp_not_ready_after={CDP_STARTUP_TIMEOUT_SECONDS}s"])

    return None  # signal to caller: CDP unavailable; leave browser for diagnosis


def start_persistent_cdp_browser(port=9223, browser="chrome", urls=None):
    """Start a persistent Chrome/Edge CDP browser across macOS/Windows/Linux.

    This is the cross-platform replacement for shelling out to
    start_cdp_chrome.sh from automation paths. The shell script remains useful
    for manual macOS sessions, but Python callers should use this function.
    """
    browser = (browser or "chrome").lower()
    if browser == "edge":
        browser_path = find_edge_path()
    else:
        browser = "chrome"
        browser_path = find_chrome_path()
        if _is_windows() and not browser_path:
            edge_path = find_edge_path()
            if edge_path:
                browser = "edge"
                browser_path = edge_path
                print("  ℹ 未找到 Chrome，Windows 下自动回退到 Edge。", flush=True)

    if not browser_path:
        print(f"  ❌ 未找到 {browser} 浏览器可执行文件", flush=True)
        print("     可设置 CHROME_PATH 或 EDGE_PATH 指向浏览器可执行文件。", flush=True)
        if _is_windows():
            print(r"     PowerShell: $env:CHROME_PATH='C:\Program Files\Google\Chrome\Application\chrome.exe'", flush=True)
            print(r"     PowerShell: $env:EDGE_PATH='C:\Program Files\Microsoft\Edge\Application\msedge.exe'", flush=True)
            print(r"     CMD: set CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe", flush=True)
            print(r"     CMD: set EDGE_PATH=C:\Program Files\Microsoft\Edge\Application\msedge.exe", flush=True)
        return None

    kill_browser_by_port(port)
    profile_dir = _profile_dir(browser)
    first_url = (urls or ["about:blank"])[0]
    proc = start_browser(port, profile_dir, url=first_url, browser_path=browser_path)
    if not proc:
        return None

    for url in (urls or [])[1:]:
        try:
            create_tab(port, url)
        except Exception:
            pass
    return proc


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
            # Windows: kill only Chromium processes whose command line points at
            # the target user-data-dir. Never blanket-kill all chrome.exe/msedge.exe,
            # or we will wipe the user's visible browser session and force re-login.
            escaped = profile_dir.replace("'", "''")
            ps_script = (
                "$needle = '" + escaped + "'; "
                "Get-CimInstance Win32_Process | "
                "Where-Object { "
                "($_.Name -in @('chrome.exe','msedge.exe')) -and "
                "($_.CommandLine -like ('*' + $needle + '*')) "
                "} | "
                "ForEach-Object { "
                "taskkill /F /PID $_.ProcessId | Out-Null "
                "}"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=20,
            )
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


def detect_available_browsers():
    """Detect which CDP-capable browsers are installed on this system.

    Returns a dict: {'chrome': path_or_None, 'edge': path_or_None}
    """
    return {
        "chrome": find_chrome_path(),
        "edge": find_edge_path(),
    }


def print_browser_setup_guide():
    """Print a setup guide based on which browsers are available."""
    browsers = detect_available_browsers()
    has_chrome = browsers["chrome"] is not None
    has_edge = browsers["edge"] is not None

    if has_chrome and has_edge:
        print(f"  🔵 Chrome:  {browsers['chrome']}")
        print(f"  🟢 Edge:    {browsers['edge']}")
        print(f"  ✅ 双浏览器就绪，可并行下载（速度翻倍）")
        return True
    elif has_chrome:
        print(f"  🔵 Chrome:  {browsers['chrome']}")
        print(f"  🟢 Edge:    未安装")
        print(f"  ⚠ 单浏览器模式（仅 Chrome）")
        print(f"  💡 安装 Edge 可启用并行加速: https://www.microsoft.com/edge")
        return True
    elif has_edge:
        print(f"  🔵 Chrome:  未安装")
        print(f"  🟢 Edge:    {browsers['edge']}")
        print(f"  ⚠ 单浏览器模式（仅 Edge）")
        print(f"  💡 安装 Chrome 可启用并行加速: https://www.google.com/chrome/")
        return True
    else:
        print(f"  ❌ 未找到 Chrome 或 Edge 浏览器")
        print(f"  💡 请安装 Chrome: https://www.google.com/chrome/")
        print(f"     macOS: /Applications/Google Chrome.app")
        print(f"     Windows: C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
        print(f"     或设置: export CHROME_PATH=/path/to/chrome")
        return False


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

    Phase 1: Wait `timeout` seconds for Turnstile to auto-resolve.
    Phase 2: If still blocked, print a clear prompt asking the user to
             manually click "Are you a robot?" in the CDP browser, then
             wait another 120s for the user to complete the action.

    Returns True if the challenge resolved, False if still blocked.
    """
    browser_name = _get_browser_name(port)

    # Phase 1: auto-resolve
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(3)
        try:
            tabs = list_tabs(port)
            for t in tabs:
                if t.get("id") != tid:
                    continue
                if not _is_cloudflare_challenge(t.get("title", ""), t.get("url", "")):
                    return True
        except Exception:
            pass

    # Phase 2: still blocked — ask user to click
    print(f"\n{'='*60}", flush=True)
    print(f"  🤖 {browser_name} 显示 Are you a robot? 验证", flush=True)
    print(f"  Cloudflare 未在 {timeout}s 内自解", flush=True)
    print(f"", flush=True)
    print(f"  👆 请在 {browser_name} CDP 窗口中手动点击验证框", flush=True)
    print(f"  通过后脚本自动检测并继续下载", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"  ⏳ 等待手动验证中...", flush=True)

    # Wait for user to click (up to 120s)
    manual_deadline = time.time() + 120
    while time.time() < manual_deadline:
        time.sleep(3)
        try:
            tabs = list_tabs(port)
            for t in tabs:
                if t.get("id") != tid:
                    continue
                if not _is_cloudflare_challenge(t.get("title", ""), t.get("url", "")):
                    print(f"  ✅ Cloudflare 验证通过！继续...\n", flush=True)
                    return True
        except Exception:
            pass

    print(f"  ⚠ 验证超时，跳过\n", flush=True)
    return False


def _get_browser_name(port):
    """Get a human-readable browser name from a CDP port."""
    try:
        browser = get_cdp_browser_product(port)
        if "Chrome" in browser and "Edg" not in browser:
            return f"Chrome (端口 {port})"
        elif "Edg" in browser:
            return f"Edge (端口 {port})"
        return f"浏览器 (端口 {port})"
    except Exception:
        return f"浏览器 (端口 {port})"


# ===== ScienceDirect access check =====

# A known accessible SD paper used to probe whether the browser has access.
# Keep DOI/PII in sync; the previous PII sample had gone stale and returned 404.
_SD_TEST_DOI = "10.1016/j.est.2024.113105"
_SD_TEST_URL = (
    "https://www.sciencedirect.com/science/article/pii/"
    "S2352152X24026914/pdfft"
)
_SD_PDF_HOST = "https://pdf.sciencedirectassets.com"


def check_sd_access(port=9223, timeout=10):
    """Probe whether a known ScienceDirect PDF is actually reachable.

    Navigates to a known SD paper and watches for:
      - PDF redirect -> PDF route is open
      - Login/challenge/unknown page -> needs manual confirmation

    Returns ("ok", "pdf_probe_ok") only when the PDF host appears, or
    ("blocked", reason_string) when the PDF route is not proven open.
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

            # PDF redirect -> the only reliable proof that this route is open.
            if url.startswith(_SD_PDF_HOST) and "main.pdf" in url:
                close_tab(port, tid)
                return "ok", "pdf_probe_ok"

            # Still on ScienceDirect → check what happened
            if "sciencedirect.com" in url:
                if "login" in url.lower() or "signin" in url.lower():
                    close_tab(port, tid)
                    return "blocked", "redirected to login page — need SSO/institutional login"
                if "access" in url.lower() or "denied" in url.lower():
                    close_tab(port, tid)
                    return "blocked", "access denied — check institutional subscription"
                # Might still be loading or needs Cloudflare check.
                if "challenge" in url.lower() or "captcha" in url.lower():
                    close_tab(port, tid)
                    return "blocked", "Cloudflare challenge detected — complete it in browser first"

            # Maybe Cloudflare challenge — wait for it to auto-resolve
            if _is_cloudflare_challenge(title, url):
                print(f"  ⏳ 检测到 Cloudflare 验证，等待自动完成（最多 60 秒）...", flush=True)
                resolved = wait_for_cloudflare(port, tid, timeout=60)
                if resolved:
                    close_tab(port, tid)
                    return "blocked", "pdf probe unknown after Cloudflare — retry PDF probe"
                close_tab(port, tid)
                return "blocked", ("Cloudflare 验证未自动完成 —— "
                                   "请在浏览器中手动点击 'Verify you are human'")

            # Neither PDF nor known challenge: do not treat page access as PDF access.
            close_tab(port, tid)
            return "blocked", "pdf probe unknown — no PDF redirect observed"

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


def ensure_sd_session(port, wait_for_login=True, login_timeout=120):
    """Ensure the CDP browser has a valid ScienceDirect session.

    Checks SD access on the given port. If blocked, prints guidance and
    optionally waits for the user to complete institutional login.

    Args:
        port: CDP debugging port.
        wait_for_login: If True, block until the user logs in or timeout.
        login_timeout: Max seconds to wait for manual login.

    Returns True if SD is accessible, False otherwise.
    """
    status, reason = check_sd_access(port)
    if status == "ok":
        tag = "IP 认证" if reason == "ip" else "已登录"
        print(f"  ✅ SD 会话有效 ({tag}) — 端口 {port}", flush=True)
        return True

    _print_sd_login_prompt(port, reason, wait_for_login, login_timeout)
    return False


def check_sd_redirect_blocked(port, interactive=True, login_timeout=300):
    """Check if the current browser tab was redirected away from SD PDF.

    Call this BEFORE close_all_tabs() after a failed wait_for_tab_url().
    Detects three failure modes and handles each appropriately:

    1. /abs/ redirect → no institutional access → navigate to SD login + wait
    2. Cloudflare "Are you a robot?" → call wait_for_cloudflare (auto + manual prompt)
    3. Other → unknown failure

    When interactive=True (default), BLOCKS until the issue is resolved or timeout.

    Returns True if blocked (and not resolved), False if resolved (caller should retry).
    """
    try:
        tabs = list_tabs(port)
        for t in tabs:
            u = t.get("url", "")
            title = t.get("title", "")

            # Case 1: redirected to abstract page — no institutional access
            if "/abs/" in u or ("/article/pii/" in u and "pdfft" not in u):
                _navigate_tab_to_sd_login(port, t["id"])
                if interactive:
                    return _wait_for_sd_login(port, login_timeout)
                else:
                    _print_sd_login_prompt(port, "被重定向到摘要页（无机构访问权限）",
                                           wait_for_login=False)
                    return True

            # Case 2: Cloudflare / Turnstile "Are you a robot?" challenge
            if _is_cloudflare_challenge(title, u):
                resolved = wait_for_cloudflare(port, t["id"], timeout=60)
                return not resolved  # False = resolved, True = still blocked

    except Exception:
        pass
    return False


def _wait_for_sd_login(port, timeout=300):
    """Block until the user completes SD institutional login or timeout expires.

    Navigates to SD login page, prints guidance, polls check_sd_access every 5s.
    Returns True if the user didn't log in (access still blocked), False if logged in.
    """
    reason = "pdfft 被重定向到摘要页（无机构访问权限）"
    print(f"\n╔{'═'*60}╗", flush=True)
    print(f"║  🔐 ScienceDirect 需要机构登录 (端口 {port:<5})                ║", flush=True)
    print(f"║  原因: {reason:<52}║", flush=True)
    print(f"╠{'═'*60}╣", flush=True)
    print(f"║  请在 CDP 浏览器窗口中完成机构登录：                       ║", flush=True)
    print(f"║  1. 登录页已自动打开                                       ║", flush=True)
    print(f"║  2. Sign in → Sign in through your institution            ║", flush=True)
    print(f"║  3. 完成 SSO 登录后，脚本自动检测并继续下载                ║", flush=True)
    print(f"╚{'═'*60}╝", flush=True)

    print(f"\n  ⏳ 等待登录中（每 5s 检测一次，{timeout}s 超时）...", flush=True)
    for i in range(timeout // 5):
        time.sleep(5)
        status, _ = check_sd_access(port)
        if status == "ok":
            print(f"  ✅ 检测到登录成功！继续下载...\n", flush=True)
            return False  # Not blocked anymore
        if i % 6 == 5:  # Every 30s, remind
            print(f"  ... 仍在等待（已等待 {(i+1)*5}s）", flush=True)

    print(f"  ⚠ 登录超时（{timeout}s），跳过此篇", flush=True)
    return True  # Still blocked


def _navigate_tab_to_sd_login(port, tab_id):
    """Navigate an existing tab to the SD institutional login page."""
    try:
        tws_url = get_tab_ws_url(port, tab_id)
        if not tws_url:
            return
        ws = websocket.create_connection(tws_url, timeout=5)
        ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
        # Drain enable response
        deadline = time.time() + 2
        while time.time() < deadline:
            try:
                ws.settimeout(0.5)
                msg = json.loads(ws.recv())
                if msg.get("id") == 1:
                    break
            except Exception:
                break
        ws.send(json.dumps({"id": 2, "method": "Page.navigate",
            "params": {"url": "https://www.sciencedirect.com/user/login?returnUrl=/"}}))
        ws.close()
    except Exception:
        pass


def _print_sd_login_prompt(port, reason, wait_for_login=False, login_timeout=120):
    """Print the SD institutional login guidance."""
    print(f"\n╔{'═'*58}╗", flush=True)
    print(f"║  🔐 ScienceDirect 需要机构登录 (端口 {port:<5})                ║", flush=True)
    print(f"║  原因: {reason:<52}║", flush=True)
    print(f"╠{'═'*58}╣", flush=True)
    print(f"║  请在 CDP 浏览器窗口中完成机构登录：                       ║", flush=True)
    print(f"║  1. 打开 https://www.sciencedirect.com                    ║", flush=True)
    print(f"║  2. 右上角 Sign in → Sign in through institution         ║", flush=True)
    print(f"║  3. 选择你的机构 → 完成 SSO 登录                          ║", flush=True)
    print(f"║  4. 看到机构名后回到终端，重新运行下载                     ║", flush=True)
    print(f"╚{'═'*58}╝", flush=True)

    if wait_for_login:
        print(f"  等待登录中（{login_timeout}s 超时）...", flush=True)
        for i in range(login_timeout // 5):
            time.sleep(5)
            status, _ = check_sd_access(port)
            if status == "ok":
                print(f"  ✅ 登录成功！继续下载", flush=True)
                return True
        print(f"  ⚠ 登录超时", flush=True)
        return False


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


# ── Profile Warming ─────────────────────────────────────────────────────────

# Common non-academic sites to visit before downloading.
# Building a mixed browsing fingerprint reduces bot detection triggers.
_WARMUP_URLS = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://en.wikipedia.org/wiki/Main_Page",
    "https://github.com/",
    "https://stackoverflow.com/",
]


def warmup_profile(port: int, delay: float = 2.0) -> bool:
    """Build natural browsing fingerprint before academic downloads.

    Navigates through common non-academic sites with short pauses between
    each visit. This creates a mixed browsing history that looks more like
    normal human behavior and less like automated academic scraping.

    Call once after browser startup, before batch downloads.

    Returns True if warming completed, False if CDP was unreachable.
    """
    if not check_cdp(port):
        return False

    try:
        wu = get_cdp_ws_url(port)
        ws = websocket.create_connection(wu, timeout=10)
        warmup_tab = None

        for i, warmup_url in enumerate(_WARMUP_URLS):
            try:
                mid = int(time.time() * 1000) % 100000
                if i == 0:
                    ws.send(json.dumps({
                        "id": mid, "method": "Target.createTarget",
                        "params": {"url": warmup_url}
                    }))
                    resp = json.loads(ws.recv())
                    warmup_tab = resp.get("result", {}).get("targetId")
                elif warmup_tab:
                    # Navigate existing tab
                    tab_ws = get_tab_ws_url(port, warmup_tab)
                    if tab_ws:
                        tws = websocket.create_connection(tab_ws, timeout=5)
                        tws.send(json.dumps({
                            "id": mid, "method": "Page.navigate",
                            "params": {"url": warmup_url}
                        }))
                        tws.close()
                time.sleep(delay)
            except Exception:
                continue

        ws.close()

        # Close warmup tab
        if warmup_tab:
            close_tab(port, warmup_tab)
    except Exception:
        return False

    return True
    print(f"{'='*55}\n", flush=True)
