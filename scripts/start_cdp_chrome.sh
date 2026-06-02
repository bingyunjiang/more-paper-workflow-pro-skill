#!/bin/bash
# Start Chrome with CDP (Chrome DevTools Protocol) for ScienceDirect PDF downloads.
# Profile at ~/.hermes/chrome_sd_profile — login once, use forever.
#
# Usage:
#   bash scripts/start_cdp_chrome.sh                      # start Chrome on port 9223
#   bash scripts/start_cdp_chrome.sh --port 9224          # custom port
#   bash scripts/start_cdp_chrome.sh --browser edge       # use Edge instead

PORT=9223
BROWSER_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
EDGE_PATH="/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
USE_EDGE=false

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    --browser)
      if [[ "$2" == "edge" ]]; then USE_EDGE=true; fi
      shift 2 ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done

BROWSER="$BROWSER_PATH"
PROFILE_DIR="$HOME/.hermes/chrome_sd_profile"
if $USE_EDGE; then
  BROWSER="$EDGE_PATH"
  PROFILE_DIR="$HOME/.hermes/edge_sd_profile"
fi

# Kill existing Chrome on this port first
pkill -f "Google Chrome.*remote-debugging-port=$PORT" 2>/dev/null || true
sleep 1

mkdir -p "$PROFILE_DIR"

"$BROWSER" \
  --remote-debugging-port="$PORT" \
  --remote-allow-origins="http://127.0.0.1:$PORT" \
  --no-first-run --no-default-browser-check \
  --disable-blink-features=AutomationControlled \
  --user-data-dir="$PROFILE_DIR" \
  https://www.sciencedirect.com/ &

echo "⏳ Waiting for CDP on port $PORT..."
for i in $(seq 1 10); do
  if curl -s "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1; then
    echo "✅ CDP ready on :$PORT ($(curl -s "http://127.0.0.1:$PORT/json/version" | python3 -c 'import sys,json; print(json.load(sys.stdin)["Browser"])' 2>/dev/null || echo "?"))"
    exit 0
  fi
  sleep 1
done

echo "❌ CDP failed to start on port $PORT"
echo "   Try: pgrep -f Chrome | xargs kill -9  # kill all Chrome processes"
echo "   Then retry."
exit 1
