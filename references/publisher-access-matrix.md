# Publisher Download Access Matrix

如何从各出版商下载 PDF，按自动化可行性排序。

## 图例

| 图标 | 含义 |
|------|------|
| ✅ 已验证 | 批量运行成功，>90% 成功率 |
| ⚠️ 可行但有局限 | 会话过期快，成功率中等 |
| 🔴 被拦截 | 自动化下载不可行（Akamai/Cloudflare） |
| ❓ 未测试 | 未用本工具链测试过 |

## Sci-Hub（✅ CDP 可用）

**仅 2021 年以前论文有收录。** HTTP 直连全部被 Cloudflare 封锁，但 CDP Chrome 方式可用。

| 镜像站 | HTTP 直连 | CDP Chrome | 说明 |
|--------|-----------|------------|------|
| sci-hub.st | 🔴 拦截 | ✅ 可用 | 提取 `<object>.data` → Fetch 捕获，~6s/篇 |
| sci-hub.ru | 🔴 拦截 | ✅ 可用 | |
| sci-hub.shop | 🔴 拦截 | ✅ 可用 | |
| sci-hub.vg | 🔴 拦截 | ✅ 可用 | |
| sci-hub.in | 🔴 拦截 | ✅ 可用 | |
| sci-hub.al | 🔴 拦截 | ✅ 可用 | |
| sci-hub.box | 🔴 拦截 | ✅ 可用 | |
| sci-hub.red | 🔴 拦截 | ✅ 可用 | |
| sci-hub.ren | 🔴 拦截 | ✅ 可用 | |
| sci-hub.se | 🔴 拦截 | 🔴 不可用 | 跳转 Chrome 错误页 |
| sci-hub.wf | 🔴 拦截 | 🔴 不可用 | 跳转到首页 |
| sci-hub.ee | 🔴 拦截 | 🔴 不可用 | Cloudflare Turnstile |
| sci-hub.mk | 🔴 拦截 | 🔴 不可用 | 跳转到首页 |

**CDP 下载流程：**
1. 启动 Chrome（`--remote-debugging-port=9223`）about:blank
2. 运行 `download_via_scihub.py 检索文献表.md`
3. 脚本自动测试镜像站 → 取可用站 → 提取 `<object>.data` → 新标签页 Fetch 捕获

```bash
python3 scripts/download_via_scihub.py dois.txt --output paper-temp/
```

**实测性能：**
| 项目 | 数值 |
|------|------|
| 可用镜像站（CDP） | **9/13 个** |
| 下载速度 | ~6s/篇 |
| PDF 大小 | 3-4MB |
| 失败原因 | 论文不在 Sci-Hub 数据库（主要是 2021 年后论文） |

## 出版商矩阵

| 出版商 | DOI 前缀 | 访问方式 | 状态 | 策略 |
|--------|----------|----------|------|------|
| **Elsevier/SD** | `10.1016/` | CDP Chrome + Fetch | ✅ 已验证 | Layer 3: DOI→PII → 导航到 pdfft → 等待 PDF 重定向 → Fetch.reload → 原始字节 |
| **MDPI** | `10.3390/` | 手动浏览器 | 🔴 被拦截 | Akamai Bot Manager 在 CDN。**手动方案：** 打开文章页 → 点 Download PDF |
| **IEEE** | `10.1109/` | CDP Chrome + 登录 | ✅ 已验证（100%，需会话） | `ieeexplore.ieee.org` — PDF按钮是JS驱动的（`.xpl-btn-pdf`, `.pdf-btn-container`），DOM中无直接PDF链接。**两步走策略（先A后B）：** `[Step A]` 导航到文章页(`/document/{arnumber}`) → 等待6s → 点击PDF按钮 → 等待4s（IEEE打开stamp新标签页）→ 扫描所有标签页，找到含 `stamp`/`getPDF` 的URL → 在该标签页中 Enable Fetch + Page.reload → 捕获PDF。`[Step B, A失败时回退]` 直接导航到 `stamp/stamp.jsp?tp=&arnumber=XXXXX` (或 `stampPDF/getPDF.jsp?tp=&arnumber=XXXXX`) → Enable Fetch + Page.reload → 捕获PDF。**关键实现细节：** Fetch.enable 用 `*` 通配符拦截所有请求，Page.reload 后轮询 `Fetch.requestPaused` 事件，对每个请求调用 `Fetch.getResponseBody` 检查是否以 `%PDF` 开头。注意 getPDF.jsp 的 `ref=` 参数可省略。**实测：** 3篇通过Step A成功，2篇通过Step B成功。PDF 0.4–7.6MB。失败原因：`?denied=` 参数表示该论文当前机构订阅未覆盖。 |
| **ASME** | `10.1115/` | CDP Chrome | ⚠️ 页面可加载，PDF按钮不可见 | `asmedigitalcollection.asme.org` — 无直接PDF链接/按钮在初始DOM中（可能需会话渲染），HTTP直连SSL错误 |
| **AIP** | `10.1063/` | CDP Chrome | ⚠️ 页面可加载，无PDF按钮 | `pubs.aip.org` — 无直接PDF链接，HTTP直连SSL `UNEXPECTED_EOF`。需机构认证 |
| **Wiley** | `10.1002/` | CDP Chrome | ⚠️ 有限成功 | `onlinelibrary.wiley.com` — **方式A:** 导航到 `doi/epdf/{doi}` + Fetch.enable + Page.reload可捕获（已验证 `ente.202301205` → 3.4MB）。**方式B:** DOM中有PDF下载按钮（`.pdf-download`）但需会话后可用。直接HTTP返回403。 |
| **Springer** | `10.1007/` | CDP Chrome | ⚠️ 书章节需访问 | `link.springer.com` 2020s书章节，HTTP直接请求失败 |
| **Nature/Springer OA** | `10.1038/` | 直连HTTP | ✅ 已验证（OA期刊） | `nature.com/articles/XXXX.pdf` 可直连下载。测试: `10.1038/s41467-024-45578-4` → 3.1MB PDF ✓ |
| **RSC** | `10.1039/` | CDP Chrome | ⚠️ 需会话 | `pubs.rsc.org` — HTTP直连失败，需浏览器会话 |
| **SSRN** | `10.2139/` | 直连HTTP | ❌ 超时 | `papers.ssrn.com` — 预印本但HTTP直连超时 |
| **Frontiers** | `10.3389/` | 直连 HTTP | ✅ 基本可行 | 开放获取 |
| **ACS** | `10.1021/` | CDP Chrome | ❓ 未测试 | `pubs.acs.org` |

## 实测命中率

### 首次（无机构会话）

| 出版商 | 尝试数 | 成功 | 无PDF/需会话 | 成功率 |
|--------|--------|------|-------------|--------|
| **Elsevier/SD** | 185 | 180 | 5 | **96%** |
| **MDPI** | 30 | 0（自动化） | 30 | **0%** |
| **Sci-Hub（2022+论文）** | 16 | 0 | 16（未收录） | **0%** |
| **多出版商CDP测试（无会话）** | 6 | 1（Nature OA） | 5（需机构会话） | **17%** |
| — IEEE (`10.1109/`) | 1 | 0 | PDF按钮需登录 | — |
| — AIP (`10.1063/`) | 1 | 0 | SSL错误，无PDF链接 | — |
| — ASME (`10.1115/`) | 1 | 0 | SSL错误，无PDF链接 | — |
| — Wiley (`10.1002/`) | 1 | 0 | epdf返回403 | — |
| — Nature OA (`10.1038/`) | 1 | **1** | — | — |
| — SSRN (`10.2139/`) | 1 | 0 | 超时 | — |

### 二次（机构会话已登录）

| 出版商 | 尝试数 | 成功 | 失败 | 成功率 | 说明 |
|--------|--------|------|------|--------|------|
| **IEEE** | 5 | 5 | 0 | **100%** | 点击PDF按钮→新标签页(stamp)→Fetch捕获, 或直接导航到getPDF.jsp。PDF大小0.4–7.6MB。 |
| **Wiley** | 2 | 0 | 2 | **0%** | 即使机构会话已登录，Cookie在CDP Chrome临时Profile中未持久化（Network.getCookies=0）。epdf URL + Fetch.reload在其云阅读器下无法捕获PDF（PDF通过JS流式加载，不在Fetch拦截范围内）。`Network.getResponseBody` 对chunked/streaming PDF返回空。`Page.setDownloadBehavior` 设置后下载文件去向不明（可能是浏览器隔离Sandbox导致）。**可尝试的方案：** 在epdf页加载完成后通过DOM检查PDF渲染状态，提取内嵌PDF URL。 |
| **Nature OA** | 1 | 1 | 0 | **100%** | 直连HTTP |

**结论（2026-06实验）：** 非SD出版商（IEEE/AIP/ASME/Wiley/RSC/Springer）的论文大多需要**有效的机构登录会话**才能通过CDP下载。仅有Nature Communications等OA期刊可直接HTTP下载。IEEE在有效机构会话下可实现**100%成功率**（5/5），PDF从0.4MB到7.6MB不等。Wiley的云阅读器（cloud-reader）使CDP Fetch捕获复杂化——epdf页面在浏览器中通过JS流式渲染PDF，`Network.getResponseBody` 和 `Fetch.getResponseBody` 对chunked编码的PDF响应体返回空。`Page.setDownloadBehavior` 在隔离CDP Chrome中也不可靠——下载文件可能因Chrome的Sandbox隔离而无法写入到指定的下载目录，或写入到宿主Chrome不可见的位置。**补救方案：** 尝试让用户在Zotero桌面端使用"通过DOI添加"功能自动补PDF，或手动在CDP Chrome中右键"另存为"下载。<br><br>**Cookie诊断结论：** 首次无机构会话时，17篇中仅1篇(Nature OA)可下(6%)。登录IEEE后，IEEE论文从0/5提升至5/5(100%)。Wiley登录后因云阅读器限制仍为0/2(0%)。

## 决策树

```
论文 DOI
├── 10.1016/ → Elsevier/SD → CDP Layer 3+4（已验证 96%）
├── 10.3390/ → MDPI        → 手动下载（Akamai）
├── 10.2139/ → SSRN        → 浏览器直连（超时则手动）
├── 10.3389/ → Frontiers   → 直连 HTTP 下载
├── 10.1038/ → Nature      → 尝试 `articles/XXXX.pdf` 直连（OA期刊可下）
├── 其他（近年小出版商）    → CDP浏览器 → 检查PDF按钮
│   ├── 有PDF按钮        → 点按钮 + Fetch捕获
│   └── 无PDF按钮/403    → 需机构会话登录
└── 2021年前论文          → 先试 Sci-Hub CDP（9个镜像站可用）
```

## CDP 通用方案（适用于任一家出版商）

SD CDP 方法理论上适用于任何满足以下条件的出版商：
1. 通过浏览器可访问的 URL 提供 PDF
2. 使用 Cloudflare 或类似机制拦截 HTTP 库
3. 可通过机构认证访问

### 先决条件：CDP 浏览器与会话管理

**⚠ 关键陷阱：CDP Chrome 使用隔离的临时 Profile**

通过 `start_browser()` 或 `scripts/cdp_utils.py` 启动的 Chrome 使用独立的临时用户数据目录（如 `/tmp/chrome_scidownload`、`/tmp/chrome_sd_profile`），**与你日常使用的 Chrome 完全隔离**。

这意味着：
- 即使你在**日常 Chrome** 中登录了机构账号 → CDP Chrome **没有这些 Cookie**
- CDP Chrome 的 Cookie 检查结果为 `0` → 需要**在 CDP Chrome 窗口中**单独完成机构登录

**两种启动策略：**

| 策略 | 做法 | 适用场景 |
|------|------|----------|
| **临时 Profile（默认）** | `--user-data-dir=/tmp/chrome_profile` | 快速测试，需要用户在 CDP 窗口中手动登录 |
| **真实 Profile** | `--user-data-dir=$HOME/Library/Application Support/Google/Chrome` | 用户已在日常 Chrome 中登录，希望复用 Cookie |

**从临时 Profile 切换到真实 Profile 的步骤：**

当用户已在日常 Chrome 中完成机构登录，但 CDP Chrome Cookie=0 时：

```
1. 让用户关闭日常 Chrome
2. 杀掉所有 Chrome 进程：pkill -9 -f "Google Chrome"
3. 检查并删除残留锁文件（强制关闭后可能残留）：
   rm -f ~/Library/Application\ Support/Google/Chrome/SingletonLock
   rm -f ~/Library/Application\ Support/Google/Chrome/SingletonSocket
   rm -f ~/Library/Application\ Support/Google/Chrome/SingletonCookie
4. 用真实 Profile 启动 CDP Chrome：
   /Applications/Google Chrome.app/Contents/MacOS/Google Chrome \
     --remote-debugging-port=9223 \
     --remote-allow-origins=http://127.0.0.1:9223 \
     --user-data-dir="$HOME/Library/Application Support/Google/Chrome" \
     https://onlinelibrary.wiley.com/doi/10.1002/ente.202301205
```

### 通用步骤

```
① 启动 Chrome + --remote-debugging-port
② 判断浏览器会话状态（见下方 CDP Cookie 诊断）
③ 若 Cookie 为空 → 先尝试用真实 Profile 重启（见上方切换步骤）
④ 若仍为空 → 在 CDP 浏览器窗口中手动完成机构登录
⑤ 在文章页找到 PDF 链接/按钮
⑥ 导航到 PDF URL + Fetch.enable + Page.reload
⑦ 通过 Fetch.getResponseBody 捕获
```

### CDP Cookie 诊断（关键前置步骤）

**任何多出版商 CDP 下载前，先检查浏览器 Cookie 状态：**

```python
import json, urllib.request, websocket
wu = json.loads(urllib.request.urlopen(
    "http://127.0.0.1:9223/json/version").read())["webSocketDebuggerUrl"]
ws = websocket.create_connection(wu, timeout=10)
ws.send(json.dumps({"id": 1, "method": "Network.getCookies"}))
cookies = None
while True:
    msg = json.loads(ws.recv())
    if msg.get("id") == 1:
        cookies = msg.get("result", {}).get("cookies", [])
        break

# 统计出版商 Cookie
publisher_cookies = {k:0 for k in ["ieee", "wiley", "aip", "asme", "springer", "nature", "sciencedirect", "elsevier"]}
for c in cookies:
    for pub in publisher_cookies:
        if pub in c.get("domain", ""):
            publisher_cookies[pub] += 1

if sum(publisher_cookies.values()) == 0:
    print("⚠ 浏览器无任何出版商 Cookie — 需手动登录机构账号后重试")
else:
    print(f"✅ 已有 {sum(publisher_cookies.values())} 个出版商 Cookie")
```

**诊断结论：**
| Cookie 结果 | 含义 | 处理 |
|-------------|------|------|
| 0 个出版商 Cookie | 全新浏览器实例，无任何登录会话 | 在 CDP 浏览器窗口中手动登录机构账号 |
| 有少数 Cookie | 部分网站有过交互，但可能未登录出版商 | 检查具体域的 Cookie 是否包含登录令牌 |
| 有对应的会话 Cookie | 已有有效机构登录 | 可直接开始 CDP Fetch 下载 |

### 出版商适配经验

每家出版商可能需要不同的 PDF URL 模式——发现后记录于此：

| 出版商 | 进入方式 | PDF URL 模式 | 注意事项 |
|--------|----------|-------------|----------|
| **Wiley** | 导航到 `doi/epdf/{doi}` | `doi/pdfdirect/{doi}?hmac=...` | 直接 HTTP 返回 403，但 CDP Fetch 拦截 + Page.reload 后可成功捕获（已验证 ente.202301205 → 3.4MB）。部分 Wiley 期刊可能仍在付费墙内。 |
| **IEEE** | 导航到 `ieeexplore.ieee.org/document/{arnumber}` → 点击PDF按钮 → 新标签页跳转到 `stamp/stamp.jsp` | `ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=XXXXX` (或 `stamp/stamp.jsp?tp=&arnumber=XXXXX`) | PDF按钮是JS驱动的（`.xpl-btn-pdf`, `.pdf-btn-container`），点击后打开新标签页。**成功方案A：** 在文章页点击PDF按钮，监听 `Target.attachedToTarget` 或轮询检测新标签页，在新标签页中启用Fetch + Page.reload。**成功方案B：** 直接导航到 `stampPDF/getPDF.jsp?tp=&arnumber=XXXXX`，启用Fetch + Page.reload。注意 getPDF.jsp 的 `ref=` 参数是base64编码的referer URL，可以省略。实测5篇全部成功。 |
| **AIP** | 导航到 `pubs.aip.org/...` | 需页面中提取 | HTTP SSL 错误（UNEXPECTED_EOF），页面中无可见 PDF 链接在初始 DOM。 |
| **ASME** | 导航到 `asmedigitalcollection.asme.org/...` | 需页面中提取 | HTTP SSL 错误。无 PDF 按钮在初始 DOM 中（可能需会话后渲染）。 |
| **Nature OA** | `nature.com/articles/{id}.pdf` | 直连 HTTP | 已验证。`10.1038/s41467-024-45578-4` → 3.1MB PDF。 |
| **Springer** | 导航到 `link.springer.com/chapter/{doi}` | 需页面中提取 | 书章节可能需单独购买权限。 |
| **RSC** | 导航到 `pubs.rsc.org/...` | 需机构会话 | HTTP 直连失败。 |
| **SSRN** | 导航到 `papers.ssrn.com/sol3/papers.cfm?abstract_id=...` | 直连 | 预印本，但 HTTP 直连可能超时。 |
