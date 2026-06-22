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
