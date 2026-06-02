# ScienceDirect CDP 下载架构

## PDF 传递机制

SD 不在同一标签页中完成 PDF 重定向。相反：

```
① 创建标签页 → 导航到 /pii/{PII}/pdfft
② SD 服务器返回一个过渡页（URL 仍为 sciencedirect.com）
③ 过渡页在 3-5s 内通过 JS 触发 NEW TAB（新标签页）指向 PDF 主机
④ 新标签页 URL: https://pdf.sciencedirectassets.com/.../main.pdf
⑤ 若机构无此论文权限，步骤③→④不会发生，标签页停留在过渡页
```

**关键推论：** 不能只盯着创建的那个标签页等 URL 变化。必须 `list_tabs()` 检查**所有**标签页中是否有 URL 包含 `pdf.sciencedirectassets.com` 的。SD 的 PDF 标签页是多出来的子标签页，不是同一个标签页重定向。

## 会话二层结构

SD 有两个独立的访问检查层级：

| 层级 | 检查方式 | 通过条件 | 脚本检测 |
|------|---------|---------|---------|
| **首页访问** | `check_sd_access()` 加载 SD 首页 | IP 在机构范围内 → 自动通过 | 输出 `已登录 — 端口 XXXX` |
| **PDF 下载** | 打开 `/pii/{PII}/pdfft` 后的过渡页 | 需要 ① 有效 SD Cookie + ② 期刊在机构订阅包中 | PDF 标签页 3-5s 内出现 |
| **深层限制** | ~15 篇后可触发 Cloudflare 挑战 | 用户需在浏览器窗口中手动验证 | 连续多篇 ❌ 且耗时正常但不是 0s |

**关键推论：** `已登录 — 端口 XXXX` 只表示 SD 首页可达，**不代表 PDF 下载通道开放**。必须尝试实际下载才能判断权限。约 80% 的 SD 论文没有 pdf 标签页（机构未订阅对应期刊）。

## 标签页管理策略

### 错误做法：close_all_tabs（v2.0 前）

```
每个下载周期：
  create_tab(pdfft)          # 创建下载标签页
  wait_for_tab_url(PDF_HOST) # 等 PDF 标签页出现
  capture_pdf_via_fetch(...) # 捕获 PDF
  close_all_tabs()           # ❌ 关闭包括 SD 首页在内的所有标签页
```

**后果：** SD 首页标签页被关闭 → 浏览器上下文丢失 → 下次 PDF 请求触发新的 Cloudflare 挑战。

### 正确做法：仅关闭下载标签页（v2.0）

```
每个下载周期：
  create_tab(pdfft)           # 创建下载标签页（记住 tid）
  list_tabs() 找 PDF 主机标签  # SD 在新标签页渲染 PDF
  capture_pdf_via_fetch(...)  # 捕获 PDF
  close_tab(port, download_tid)  # ✅ 只关闭创建的下载标签页
  # SD 首页标签页保持打开
```

## Profile 持久化

### 位置

| 版本 | Profile 路径 | 特性 |
|------|-------------|------|
| v1.x | `/tmp/sd_chrome_profile` | 每次重启删除，需重新登录 |
| v2.0 | `~/.hermes/chrome_sd_profile` | 持久保留，重启后 Cookie 仍在 |

### Profile 内容

- SD Cookie（sessionid, cloudflare token, inst auth）
- 浏览器扩展配置
- 无需每次下载重新登录

### 重启时不删 Profile

```python
# ❌ 错误: 删掉 → 丢失登录
remove_profile_dir(profile_dir)

# ✅ 正确: 保留 → Cookie 持久化
# 不调用 remove_profile_dir
```

## 脚本退出时不应杀浏览器

```python
# ❌ 错误: 每次脚本结束杀浏览器 → 下次需重新 CDP 握手 + 可能触发挑战
for name, path, port, prof in browsers:
    kill_browser_by_port(port)
    kill_browser_by_profile(prof)

# ✅ 正确: 保持浏览器运行，下次直接连 CDP（或用 --no-restart 标志）
# 不调用 kill_* — 浏览器保持在线
```

## 关键反直觉点清单

1. **PDF 在新标签页** — 不是同一标签页重定向。`wait_for_tab_url` 能工作正是因为检查所有标签页
2. **首页登录 ≠ PDF 可下载** — 两个独立检查层级
3. **单次登录 ~15 篇 PDF** — 之后触发 Cloudflare 保护
4. **close_all_tabs 有害** — 会关闭 SD 首页标签页，丢失 session 上下文
5. **Profile 不应删** — 移到 `~/.hermes/` 持久化
6. **脚本结束不应杀浏览器** — 注释掉 cleanup 中的 kill 调用（或加 `--no-restart` 标志）
7. **连续 0s 失败 = 方法错误** — 代码抛异常被 silent try/except 吞掉；不是权限问题
8. **连续 ~9-15s 失败 = 权限不足** — quick-fail 路径触发；期刊未订阅
9. **连续 ~26-53s 失败 = 超时** — `wait_for_tab_url` 满额等待；旧版行为

## SD 双重 PDF 传递机制（2026-06 实测）

### 机制 A：直接重定向（约 30% 论文）

```
/pii/{PII}/pdfft  →  302 重定向 →  https://pdf.sciencedirectassets.com/.../main.pdf
```

**特征：** 3-5s 内 `list_tabs()` 中出现 URL 含 `pdf.sciencedirectassets.com` 的新标签页。捕获过程直接。

### 机制 B：SPA 在线阅读器（约 70% 论文）

```
/pii/{PII}/pdfft  →  200 HTML 页面（React SPA，SD 在线阅读器）
                     ↓ 需 JS 渲染后
                     <a href=".../pdfft?md5=fa5bb...&pid=...-main.pdf">View PDF</a>
```

**特征：**
- `/pdfft` 返回 HTML 而非 PDF 重定向
- "View PDF" 链接包含 `?md5=`（会话令牌）和 `&pid=...-main.pdf`（文件名）
- 链接在 JS 渲染后才出现在 DOM 中（需等待 5-8s）
- 点击该链接 → 在新标签页打开 PDF 或触发下载
- 直接对带 `?md5=` 参数的完整 URL 发起 `Page.navigate` 可能仍返回 HTML（需与初始页面在同一 session 中）

**检测方法：** 导航到文章页，等待 JS 渲染，用 `Runtime.evaluate` 提取 `a[href*="pdfft"]` 的 `href` 属性。

**当前局限：** CDP 自动下载流程仅处理机制 A（直接重定向）。机制 B 的论文需手动或通过额外提取流程处理。

## Cookie 访问层级

### 浏览器级 WS vs 标签页级 WS

```
浏览器级 WS（get_cdp_ws_url() → Target.createTarget）:
  Network.getAllCookies → 0 cookies ❌

标签页级 WS（get_tab_ws_url() → 连接具体标签页）:
  Network.enable → Network.getAllCookies → 49 cookies ✅（含 ~37 个 SD Cookie）
```

**原因：** CDP 的 `Network` 域需要绑定到一个具体标签页的 WebSocket 上才能访问其 Cookie 存储。浏览器级的 WebSocket 仅用于 `Target` 域操作（创建/关闭标签页），不持有页面上下文。

**实践建议：**
- 检查 Cookie 时务必通过标签页级 WS（先 `Network.enable`）
- `get_cdp_ws_url(port)` 只用于 `Target.createTarget` / `Target.closeTarget`
- 页面内容操作一律用标签页级 WS

## parallel_sd_download.py 稳定性说明

`parallel_sd_download.py` 是**最稳定的下载入口**，原因：
- 不管理浏览器生命周期（用户自行启动 CDP Chrome）
- 不重启浏览器（避免 session 丢失）
- 使用 `create_tab` + `wait_for_tab_url` + `capture_pdf_via_fetch` + `close_all_tabs`
- 代码简洁，未经过多轮修改

`auto_sd_downloader.py` 功能更全（自动重启、断点续跑、跳过机制）但经过多次修改，复杂度高。若遇到稳定性问题，优先回退到 `parallel_sd_download.py`。

**使用场景对照：**

| 场景 | 推荐脚本 |
|------|---------|
| 首次批量下载，需自动管理浏览器 | `auto_sd_downloader.py --no-restart` |
| 浏览器已在运行，只想下载剩余论文 | `parallel_sd_download.py` |
| 调试特定论文的下载问题 | 直接 `python3 -c` 测试 |
| 双浏览器并行加速 | `parallel_sd_download.py`（自动检测 Chrome+Edge） |
