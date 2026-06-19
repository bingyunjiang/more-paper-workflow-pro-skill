#!/usr/bin/env bash
# Start a persistent Chromium-based browser with CDP enabled.
#
# Usage:
#   bash scripts/start_cdp_chrome.sh                      # Chrome on port 9223
#   bash scripts/start_cdp_chrome.sh --port 9224          # custom port
#   bash scripts/start_cdp_chrome.sh --browser edge       # use Edge instead
#
# Cross-platform notes:
#   - Browser detection is handled by scripts/cdp_utils.py.
#   - Override detection with CHROME_PATH or EDGE_PATH when needed.

set -euo pipefail

PORT=9223
BROWSER="chrome"
URL="https://www.sciencedirect.com/"

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    --browser) BROWSER="$2"; shift 2 ;;
    --url) URL="$2"; shift 2 ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

python3 - << PYEOF
import sys
from pathlib import Path

sys.path.insert(0, str(Path("$SCRIPT_DIR")))
from cdp_utils import check_cdp, start_persistent_cdp_browser

port = int("$PORT")
browser = "$BROWSER"
url = "$URL"

print(f"⏳ Waiting for CDP on port {port}...")
if not check_cdp(port):
    start_persistent_cdp_browser(port=port, browser=browser, urls=[url])

if check_cdp(port):
    print(f"✅ CDP ready on :{port}")
else:
    print(f"❌ CDP failed to start on port {port}")
    print("   Set CHROME_PATH or EDGE_PATH if browser auto-detection fails.")
    sys.exit(1)
PYEOF
