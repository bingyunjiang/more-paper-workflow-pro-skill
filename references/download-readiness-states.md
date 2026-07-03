# 下载 readiness 状态

## 状态定义

- `blocked`
  - 没有输入、没有会话、没有可用下载路径
- `partial`
  - 已下载一部分，但仍有缺口
- `complete`
  - 本批目标均已完成或已明确不可下载

## 常见 warning

- 登录状态不稳定
- DOI 无 PDF
- 页面仅摘要
- 附件命名待人工整理

## Step 5 下载原因状态

- `captcha_required`
  - CNKI 等页面命中安全验证；不是登录失败，也不是普通下载失败。Agent 应保留页面并要求用户完成验证。
- `login_required` / `institution_login_required`
  - 需要机构登录、CARSI、SSO 或出版社登录。
- `pdf_probe_unknown`
  - 只看到文章页或详情页，尚未证明 PDF 链接或 PDF bytes 可访问。
- `manual_required`
  - 自动化入口不稳定，但人工下载路径明确；可改为用户手动点击下载，Agent 监视落盘并归档。
- `chapter_download_mode`
  - CNKI 未识别到 `PDF下载`，但页面出现章节/分页入口；不自动点击，留给人工判断。
- `access_denied`
  - 页面明确显示无权限、未订阅或不可下载。

## Step 5 manifest readiness

`download_manifest.json` 使用 `step5-download.v1`：

- `blocked`: 本批没有可用 PDF，且存在登录、验证码、锁、CDP 或配置阻断。
- `partial`: 至少有一部分 PDF 可用，但仍有未解决条目。
- `complete`: 全部条目已下载，或未下载项已明确不可下载并可进入人工/审计处理。

## 失败恢复分桶

- `retryable`: `generic_failed`, `sd_failed_unknown`, transient OA fetch failures.
- `needs_login`: `pending_user_login`, `institution_login_required`, `login_required`.
- `needs_user_action`: `captcha_required`, `manual_required`, `manual_verification_required`.
- `not_available`: `access_denied`, `no_url`, `fulltext_delivery_mode`, `not_subscribed_or_referencework`.
- `needs_metadata_fix`: `pii_resolution_failed`, `invalid_oa_candidate`, `oa_whitelist_but_verification_failed`.

推荐下一步由分桶决定：先处理登录，再处理验证码/人工下载，再修复元数据，最后重试 transient failure。

## 手动归并状态

当用户已在浏览器或机构页面手动保存 PDF 后，Step 5 不应强制重新下载。
`step5_reconcile_pdf_pool.py` 负责把本地 PDF 归并回：

- `download_manifest.json`
- `download_attempts.jsonl`
- `pdf-附件池索引.json`

命中后，原先的 `manual_required`、`captcha_required` 等条目可转为
`status=downloaded`，并保留 `manual_reconcile` attempt 作为恢复轨迹。

## 站点级诊断

manifest `summary.publisher_summary` 和 `summary.domain_summary` 用于区分：

- 单篇文献失败。
- 单一 publisher/session 失效。
- 某类失败原因集中出现，例如验证码、机构登录或元数据缺失。

这些摘要只辅助诊断，不改变 Step 5 下载路由。
