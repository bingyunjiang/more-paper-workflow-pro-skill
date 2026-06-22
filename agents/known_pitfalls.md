# 已知陷阱 (Known Pitfalls)

> 跨步骤通用故障排除参考。所有 agent 的 Section 9（故障排除）均可引用本文件。
> 本文件从原 SKILL.md 已知陷阱章节迁移，按主题分类组织。

---

## 启动前读取 (Pre-read Checklist)

无需前置文件。本文件按需加载——当任何一个 Step 遇到技术问题时。

---

## 适用任务 (Applicable Tasks)

- 排查 Python 版本相关问题
- 诊断 CDP/WebSocket 下载失败
- 解决 Zotero MCP 配置问题
- 理解浏览器 Profile 和 Cookie 机制
- 修复 PDF 标签页残留、死循环等已知 bug

---

## 不适用任务 (Non-applicable Tasks)

- 不替代各 Step 的 Execution Flow——本文件是"出问题后查"，不是"执行前读"

---

## 4. 陷阱索引

### Python 版本

**macOS 默认 3.9：** `python3` 是系统自带的 3.9（`/usr/bin/python3`）。Python 3.14 在 `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3`。脚本兼容 3.9-3.14。

**Python 3.14 单行 try/except 非法：**
```python
# ❌ 语法错误：
try: ws.recv(); except: pass

# ✅ 必须多行：
try:
    ws.recv()
except:
    pass
```

### CDP / WebSocket 陷阱

**Fetch.requestPaused 事件被 send_cmd 吃掉：** `send_cmd()` 在等回复时会读取 WebSocket 消息，`Fetch.requestPaused` 因无匹配 ID 被丢弃。修复：发 `Page.reload` 后直接进入事件循环。

**CDP WebSocket 层级：浏览器级 vs 标签页级：** `Network.getAllCookies()` 在浏览器级 WS 上返回 0 cookies（假阴性），必须在标签页级 WS 上调用。

**PDF 标签页残留导致重复下载（v2.1 修复）：** 每篇下载后关闭 PDF 标签页，防止下一篇误捕获。

**真实 Chrome Profile CDP 端口不绑定（macOS 特定）：** 某些扩展阻止 CDP server 端口绑定。推荐使用持久化临时 Profile + `start_cdp_browser.py`；`start_cdp_chrome.sh` 仅作为 macOS/Linux wrapper 保留。

**Windows 不能依赖 macOS Chrome 启动命令：** 自动下载路径不要直接调用 `open -na "Google Chrome"` 或写死 `/Applications/...`。应使用 `scripts/start_cdp_browser.py` 或 `cdp_utils.start_persistent_cdp_browser()`，必要时通过 `CHROME_PATH` / `EDGE_PATH` 指定浏览器可执行文件。

**登录在 Chrome，下载却连到 Edge：** 旧逻辑只判断 9223 端口是否有 CDP 服务，不检查背后的浏览器。排查时先打开 `http://127.0.0.1:9223/json/version` 看 `Browser` 字段；下载命令必须与登录浏览器一致，例如 Chrome 登录用 `--browser chrome`，Edge 登录用 `--browser edge`。

**英文 Step 5 门控打印 `Enter 1/2/3:` 后立即结束，不等于用户跳过：** 在非交互宿主中，`input()` 可能抛 `EOFError` 或根本拿不到持续 stdin。此时应先检查 `paper-temp/login_checkpoint.json` 是否已生成，以及失败原因是否被写成 `pending_user_login`；不要把日志里的“等待恢复”误判为“用户选择了 skip”。

### SD 下载陷阱

**论文无 PDF 可下：** 约 4% 的 SD 论文只提供摘要页。10 秒超时快速跳过。

**SD 文章页渲染时长不足：** SPA 页面在 CDP 环境下渲染更慢（可能因自动化检测降速）。默认 `render_timeout=25`。

**双阶段 SD 下载策略：** ~30% 论文 `/pdfft` 直连成功；~70% 需从文章页提取 `?md5=` URL。

**auto_sd_downloader.py Wave 2+ 重启死循环：** v2.0 引入 `skip_set` 永久跳过队列，连续失败 3 次自动跳过。

### 浏览器 CDP 限制

- **Chrome** ✓ — `--remote-debugging-port`
- **Edge** ✓ — 同 Chromium 内核
- **Safari** ✗ — WebKit Remote Inspector
- **Firefox** ✗ — Marionette/WebDriver

### Zotero / 平台兼容性

**Zotero 本地模式连接失败（Step 6 常见）：**
当 `ZOTERO_LOCAL=true` 但 AI agent 无法连接到 Zotero 桌面端时，最常见的原因是 Zotero 桌面端未运行。
AI agent 应执行以下诊断步骤：
1. 检查配置：`python3 -c "import json; c=json.load(open('$HOME/.config/zotero-mcp/config.json')); print(c.get('ZOTERO_LOCAL','false'))"`
2. 如果返回 `true`，检测端口：`curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:23119/api/users/1/items?limit=1`
3. 如果端口不通 → 向用户提示「请打开 Zotero 桌面端」并等待确认后继续。

如果用户不方便运行本地 Zotero，可通过修改 `~/.config/zotero-mcp/config.json` 将 `ZOTERO_LOCAL` 改为 `false` 切换到云端模式。

**scripts/packages/ 目录的真实含义：** 当前应以 `scripts/packages/README.md` 为准。`0.5.0` 这套缓存可能同时包含纯 Python wheel 与平台相关 wheel；因此不要再假设“同一份缓存天然跨平台通用”。如果目标机器平台不同，或离线安装失败，应在目标平台重下 `zotero-mcp-server==0.5.0` 对应缓存。

### 其他

**generate_report_pdf.py 中文引号导致 JSON 解析失败：** 使用 `json.dump(data, f, ensure_ascii=False, indent=2)` 生成 JSON。

**纯文本参考文献的 DOI 提取：** 提取后去除尾部标点，避免误匹配。

**stdout 缓冲导致后台进程无输出：** 使用 `PYTHONUNBUFFERED=1` 或 `python3 -u`。

**关于"权限不足"的排查原则：** 核心原则——不要轻易怀疑用户的权限。排查顺序：直连 PDF → 文章页 `?md5=` → 渲染时间 → 残留标签页 → 特殊页面结构。

---

## 5. 关联参考文件

- `references/cdp-pdf-capture-limitations.md` — CDP PDF 捕获限制
- `references/sd-cdp-architecture.md` — SD 下载架构
- `references/publisher-access-matrix.md` — 各出版商下载可行性对照表
