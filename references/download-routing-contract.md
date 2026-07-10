# 下载路由契约

本文件只定义下载策略层，不覆盖现有脚本实现细节。

## 目标

- 统一 Step 5 的入口判断
- 显式声明 fallback chain
- 输出下载 readiness，而不是只报告成功/失败

## 推荐 fallback chain

1. DOI 直连或出版商入口
2. 会话内页面抓取
3. CDP 浏览器辅助
4. 备用下载器/人工干预

## 输出字段

- requested_items
- downloaded_items
- unresolved_items
- session_status
- readiness

## Step 5 stable download manifest

真实下载入口必须在输出目录写出 `download_manifest.json`，schema 为
`step5-download.v1`。该产物用于 Step 6 Zotero 规划、Step 7 证据边界和
失败恢复，不替代既有 `download_log.md`。

```json
{
  "schema_version": "step5-download.v1",
  "run_id": "",
  "generated_at": "",
  "readiness": "blocked | partial | complete",
  "recommended_next_step": "",
  "summary": {
    "total": 0,
    "downloaded": 0,
    "remaining": 0,
    "failed_or_pending": 0,
    "publisher_summary": {},
    "domain_summary": {},
    "preflight": {}
  },
  "recovery_buckets": {
    "retryable": [],
    "needs_login": [],
    "needs_user_action": [],
    "not_available": [],
    "needs_metadata_fix": []
  },
  "items": [
    {
      "id": "",
      "doi": "",
      "title": "",
      "source": "",
      "article_url": "",
      "publisher": "",
      "status": "downloaded | invalid_pdf | pending_user_login | manual_required | access_denied | unresolved | skipped | blocked",
      "quality": "pdf_verified | pdf_unverified | metadata_only | none",
      "pdf_path": "",
      "verification_status": "verified | invalid | not_checked",
      "verification_reason": "",
      "verified_at": "",
      "sha256": "",
      "failure_reason": "",
      "next_action": "",
      "attempts": []
    }
  ]
}
```

同一输出目录还应写出：

- `download_attempts.jsonl`: append-only 逐轮尝试记录；每条包含 `attempt_id/run_id/item_id/route/stage/status/verification_status/timestamp`。
- `pdf-附件池索引.json`: 当前输出目录可复用 PDF 附件索引。
- `step5-debug/`: 仅在验证码、人工处理、PDF 探测未知等失败时写入轻量定位信息。

重跑时应先读取/扫描本地 PDF；命中有效 PDF 的条目标记为
`status=downloaded`，并记录 `stage=local_index,status=verified` 的 attempt。仅文件存在、文件够大或下载器返回成功，不足以进入 `downloaded`。

## Manual reconcile

手动补下 PDF 后，不应重跑全部下载。使用：

```bash
python scripts/step5_reconcile_pdf_pool.py --output paper-temp
```

该命令只扫描本地 PDF、更新 `download_manifest.json` 和
`pdf-附件池索引.json`，并追加 `stage=manual_reconcile,status=verified|invalid` 的 attempt；
不得改名或移动用户已有 PDF。

DOI/source_id 文件名匹配可视为 `confirmed`；仅标题相似只能进入 `probable_pdf_match_requires_confirmation`，不得自动清空原失败原因。

## PDF diagnostics

PDF pool item 可包含 `pdf_diagnostics`，用于诊断 HTML 伪 PDF、过小 PDF、
无可读页、损坏或无法读取的文件。只有 `verification_status=verified` 且
`quality=pdf_verified` 才能计入下载成功。

完成声明前运行：

```bash
python3 scripts/validate_step5_output.py paper-temp
```
