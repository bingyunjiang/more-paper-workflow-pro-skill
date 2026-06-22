#!/usr/bin/env python3
"""Cross-platform CDP browser launcher.

This is the primary entry point for Windows/macOS/Linux. Shell wrappers may
delegate here, but runtime automation should not depend on bash.
"""
from __future__ import annotations

import argparse
import sys

from cdp_utils import (
    cdp_browser_matches,
    check_cdp,
    get_cdp_browser_product,
    get_launch_log_path,
    get_persistent_profile_dir,
    start_persistent_cdp_browser,
)
from console_compat import configure_console_output


def _print_cdp_path_hint() -> None:
    if sys.platform == "win32":
        print(r"   PowerShell: $env:CHROME_PATH='C:\Program Files\Google\Chrome\Application\chrome.exe'")
        print(r"   PowerShell: $env:EDGE_PATH='C:\Program Files\Microsoft\Edge\Application\msedge.exe'")
        print(r"   CMD: set CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe")
        print(r"   CMD: set EDGE_PATH=C:\Program Files\Microsoft\Edge\Application\msedge.exe")
        return

    print("   Set CHROME_PATH or EDGE_PATH if browser auto-detection fails.")


def main() -> int:
    configure_console_output()

    parser = argparse.ArgumentParser(
        description="Start or reuse a persistent Chrome/Edge browser with CDP enabled."
    )
    parser.add_argument("--port", type=int, default=9223, help="CDP debug port")
    parser.add_argument(
        "--browser",
        choices=("chrome", "edge"),
        default="chrome",
        help="Browser to launch",
    )
    parser.add_argument(
        "--url",
        action="append",
        dest="urls",
        help="Initial URL to open. May be passed multiple times.",
    )
    args = parser.parse_args()

    urls = args.urls or ["https://www.sciencedirect.com/"]

    print(f"⏳ Waiting for CDP on port {args.port}...")
    if check_cdp(args.port) and not cdp_browser_matches(args.port, args.browser):
        product = get_cdp_browser_product(args.port) or "unknown browser"
        print(f"   Existing CDP is {product}; restarting {args.browser}.")
        start_persistent_cdp_browser(
            port=args.port,
            browser=args.browser,
            urls=urls,
        )
    elif not check_cdp(args.port):
        start_persistent_cdp_browser(
            port=args.port,
            browser=args.browser,
            urls=urls,
        )

    if check_cdp(args.port) and cdp_browser_matches(args.port, args.browser):
        print(f"✅ CDP ready on :{args.port}")
        print(f"   Profile: {get_persistent_profile_dir(args.browser)}")
        print(f"   Launch log: {get_launch_log_path(args.browser)}")
        return 0

    print(f"❌ CDP failed to start on port {args.port}")
    _print_cdp_path_hint()
    return 1


if __name__ == "__main__":
    sys.exit(main())
