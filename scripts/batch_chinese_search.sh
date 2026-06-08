#!/bin/bash
# batch_chinese_search.sh — Interactive batch: CDP Chrome → login → CNKI+Wanfang search
#
# Keeps CDP alive in ONE command session. Use via exec_command + write_stdin.
#
# Usage:
#   bash scripts/batch_chinese_search.sh queries.json [--port PORT] [--output-dir DIR]
#   bash scripts/batch_chinese_search.sh --login-only [--port PORT]
#     (--login-only: start CDP Chrome + wait for login, skip search)
#
# queries.json format (for search mode):
# [
#   {"id":"S1","query":"冷板拓扑优化","source":"cnki","limit":50,"strategy":"relevance"},
#   {"id":"S2","query":"冷板拓扑优化","source":"wanfang","limit":50}
# ]
#
# Protocol markers (parsed by Agent via stdout):
#   CDP_ALIVE              → CDP already running, skipped startup
#   CDP_READY              → Fresh Chrome started and CDP ready
#   LOGIN_REQUIRED         → Waiting for user login (blocking on stdin)
#   SEARCH_START:<id>      → Beginning search for <id>
#   SEARCH_DONE:<id>:<n>   → Search <id> returned <n> results
#   ALL_DONE               → All searches complete

set -euo pipefail

PORT=9223
OUTPUT_DIR="."
QUERIES_FILE=""
LOGIN_ONLY=false

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --port) PORT="$2"; shift 2 ;;
        --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
        --login-only) LOGIN_ONLY=true; shift ;;
        --help|-h)
            echo "Usage: bash batch_chinese_search.sh queries.json [--port PORT] [--output-dir DIR]"
            exit 0 ;;
        *) QUERIES_FILE="$1"; shift ;;
    esac
done

if [[ "$LOGIN_ONLY" = false ]]; then
    if [[ -z "$QUERIES_FILE" ]]; then echo "ERROR: queries.json required"; exit 1; fi
    if [[ ! -f "$QUERIES_FILE" ]]; then echo "ERROR: file not found: $QUERIES_FILE"; exit 1; fi
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUTPUT_DIR"

# Validate JSON (skip in --login-only mode)
if [[ "$LOGIN_ONLY" = false ]]; then
    QUERY_COUNT=$(python3 -c "import json; q=json.load(open('$QUERIES_FILE')); print(len(q))" 2>/dev/null || echo 0)
    if [[ "$QUERY_COUNT" -eq 0 ]]; then
        echo "ERROR: No valid queries found in $QUERIES_FILE"
        exit 1
    fi
else
    QUERY_COUNT=0
fi

# ── Step 1: Check / start CDP Chrome ──────────────────────────────────────

CDP_STARTED=false
if curl -s "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1; then
    echo "CDP_ALIVE:$PORT"
else
    echo "CDP_CHROME_STARTING:$PORT"

    pkill -f "Google Chrome.*remote-debugging-port=$PORT" 2>/dev/null || true
    sleep 1

    open -na "Google Chrome" --args \
        --remote-debugging-port="$PORT" \
        --remote-allow-origins="http://127.0.0.1:$PORT" \
        --no-first-run --no-default-browser-check \
        --disable-blink-features=AutomationControlled \
        --user-data-dir="$HOME/.hermes/chrome_sd_profile" \
        "https://kns.cnki.net/kns8s/" \
        "https://www.wanfangdata.com.cn/"

    for i in $(seq 1 15); do
        if curl -s "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1; then
            echo "CDP_READY:$PORT"
            CDP_STARTED=true
            break
        fi
        sleep 1
    done

    if [[ "$CDP_STARTED" = false ]]; then
        echo "ERROR: CDP Chrome failed to start on port $PORT"
        exit 1
    fi
fi

# ── Step 2: Navigate first tab to CNKI (best-effort via CDP) ────────────────

python3 << PYEOF 2>/dev/null || true
import json, urllib.request, time
port = $PORT
try:
    targets = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=5).read())
    pages = [t for t in targets if t.get("type") == "page"]
    if pages:
        import websocket
        wu = pages[0]["webSocketDebuggerUrl"]
        ws = websocket.create_connection(wu, timeout=10)
        ws.send(json.dumps({"id":1,"method":"Page.navigate","params":{"url":"https://kns.cnki.net/kns8s/"}}))
        ws.recv()
        ws.close()
        if len(pages) > 1:
            wu2 = pages[1]["webSocketDebuggerUrl"]
            ws2 = websocket.create_connection(wu2, timeout=10)
            ws2.send(json.dumps({"id":1,"method":"Page.navigate","params":{"url":"https://www.wanfangdata.com.cn/"}}))
            ws2.recv()
            ws2.close()
except Exception:
    pass
PYEOF

# ── Step 3: Wait for login confirmation ────────────────────────────────────

echo ""
echo "=== LOGIN_REQUIRED ==="
echo "Chrome opened. Please complete CARSI institution login in the browser."
echo "  • CNKI:   kns.cnki.net/kns8s/  → 右上角「机构登录」"
echo "  • Wanfang: www.wanfangdata.com.cn → 右上角「登录」→ CARSI"
echo "Type 'go' and press Enter when logged in:"
read -p "" confirm

if [[ "$confirm" != "go" ]]; then
    echo "SKIPPED"
    exit 0
fi

# (--login-only mode: exit after login confirmation)
if [[ "$LOGIN_ONLY" = true ]]; then
    echo "CHINESE_CDP_READY"
    exit 0
fi

# ── Step 4: Run all searches (iterate via tmpfile to avoid subshell issue) ──

python3 -c "
import json, os, subprocess, sys

queries = json.load(open('$QUERIES_FILE'))
script_dir = '$SCRIPT_DIR'
output_dir = '$OUTPUT_DIR'
port = '$PORT'
total = len(queries)
success = 0
failed = 0

for idx, q in enumerate(queries):
    qid = q.get('id', f'Q{idx+1}')
    query = q.get('query', '')
    source = q.get('source', 'cnki')
    limit = str(q.get('limit', 50))
    strategy = q.get('strategy', '')

    if not query:
        continue

    print(f'SEARCH_START:{qid} ({idx+1}/{total})', flush=True)

    bib_file = os.path.join(output_dir, f'{qid}_{source}.bib')
    cmd = [
        'python3', os.path.join(script_dir, 'search_by_topic.py'),
        query, '--source', source, '--limit', limit,
        '--no-cache', '--language', 'zh',
        '--export-bib', bib_file,
    ]
    if strategy:
        cmd += ['--strategy', strategy]

    env = os.environ.copy()
    env['CDP_PORT'] = port

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
        if os.path.exists(bib_file):
            bib_count = 0
            with open(bib_file) as bf:
                for line in bf:
                    if line.startswith('@'):
                        bib_count += 1
            print(f'SEARCH_DONE:{qid}:{bib_count}', flush=True)
            success += 1
        else:
            print(f'SEARCH_DONE:{qid}:0 (no output)', flush=True)
            failed += 1
    except Exception as e:
        print(f'SEARCH_DONE:{qid}:0 (error: {e})', flush=True)
        failed += 1

# Write summary to a temp file that bash can read
summary = {'total': total, 'success': success, 'failed': failed}
with open(f'{output_dir}/.batch_summary.json', 'w') as sf:
    json.dump(summary, sf)
" 2>&1


if [[ "$LOGIN_ONLY" = true ]]; then
    echo "=== ALL_DONE ==="
    echo "CDP Chrome ready (login-only mode). Proceed with download."
else
    if [[ -f "$OUTPUT_DIR/.batch_summary.json" ]]; then
        SUCCESS=$(python3 -c "import json; print(json.load(open('$OUTPUT_DIR/.batch_summary.json'))['success'])" 2>/dev/null || echo "?")
        FAILED=$(python3 -c "import json; print(json.load(open('$OUTPUT_DIR/.batch_summary.json'))['failed'])" 2>/dev/null || echo "?")
        TOTAL=$(python3 -c "import json; print(json.load(open('$OUTPUT_DIR/.batch_summary.json'))['total'])" 2>/dev/null || echo "?")
        rm -f "$OUTPUT_DIR/.batch_summary.json"
    fi
    echo ""
    echo "=== ALL_DONE ==="
    echo "Results: $SUCCESS success, $FAILED failed (out of $TOTAL queries)"
    echo "Output: $OUTPUT_DIR/"
    if ls "$OUTPUT_DIR/"*.bib >/dev/null 2>&1; then
        ls -la "$OUTPUT_DIR/"*.bib 2>/dev/null | head -20
    fi
fi
