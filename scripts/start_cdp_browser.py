#!/usr/bin/env python3
"""Cross-platform CDP browser launcher.

This is the primary entry point for Windows/macOS/Linux. Shell wrappers may
delegate here, but runtime automation should not depend on bash.
"""
from __future__ import annotations

import argparse
import sys

from cdp_utils import check_cdp, start_persistent_cdp_browser


def main() -> int:
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
    if not check_cdp(args.port):
        start_persistent_cdp_browser(
            port=args.port,
            browser=args.browser,
            urls=urls,
        )

    if check_cdp(args.port):
        print(f"✅ CDP ready on :{args.port}")
        return 0

    print(f"❌ CDP failed to start on port {args.port}")
    print("   Set CHROME_PATH or EDGE_PATH if browser auto-detection fails.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
