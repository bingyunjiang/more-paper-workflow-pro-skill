#!/bin/bash
# 海报生成脚本：统一用 Chrome headless 批量生成 6 张海报
# Usage: bash posters/gen-posters.sh

OUTDIR="$(cd "$(dirname "$0")" && pwd)"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

for html in "$OUTDIR"/*.html; do
  name=$(basename "$html" .html)
  png="$OUTDIR/$name.png"
  echo "Generating $png ..."
  "$CHROME" --headless --disable-gpu --no-sandbox \
    --screenshot="$png" --window-size=1080,1080 \
    "file://$html" 2>/dev/null
  echo "  $(ls -lh "$png" | awk '{print $5}')"
done
echo "Done: $(ls "$OUTDIR"/*.png | wc -l) posters"
