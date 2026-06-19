#!/usr/bin/env bash
# macOS/Linux compatibility wrapper.
# Primary cross-platform entry point: python scripts/batch_chinese_search.py

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/batch_chinese_search.py" "$@"
