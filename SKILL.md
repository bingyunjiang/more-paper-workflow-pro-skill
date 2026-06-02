---
name: more-paper-workflow-pro-skill
version: v1.0.1-20260602
description: 完整学术文献检索和写作工作流（8 步法）：①交互式确定研究主题 ②生成大纲/关键词 ③制定检索方案 ④多渠道检索+评分 ⑤多轮下载（Sci-Hub→SD→IEEE） ⑥Zotero 文库管理（架构生成+PDF 导入） ⑦论文写作（4 种模式 + 中英文双边摘要 + 仿真评审质量门） ⑧论文润色（句长波动检测 + 四合一精修引擎：去 AI 痕迹 29 种模式 + 注入人味 + 章节风格指南 + before/after 对照表）
author: Dr. Jiang Bingyun（江博士）
wechat: Bingyunjiang
category: research
related_skills:
  - science-direct-cdp-pipeline: "Overlaps on CDP ScienceDirect download; this skill adds the full 8-step workflow from topic definition to paper polishing."
triggers:
  # Step 1: 确定研究主题
  - "确定研究主题"
  - "厘清研究方向"
  # Step 2: 生成大纲
  - "生成论文大纲"
  - "论文关键词"
  # Step 3: 检索方案
  - "制定检索方案"
  - "文献检索策略"
  # Step 4: 检索与评分
  - "检索论文"
  - "按主题检索学术文献"
  - "搜索论文并下载"
  - "文献检索"
  # Step 5: 批量下载
  - "批量下载论文 PDF"
  - "从参考文献列表中下载 PDF"
  - "BibTeX 批量下载 PDF"
  - "批量下载 ScienceDirect 论文"
  - "Sci-Hub 下载论文"
  # IEEE CDP 两步走
  - "IEEE 下载"
  - "IEEE CDP 下载"
  - "两步走策略"
  # Zotero 附件管理
  - "Zotero 检查遗漏附件"
  - "Zotero 查找无附件条目"
  - "补下 Zotero 缺少的 PDF"
  # Step 6: Zotero 管理
  - "Zotero 文库整理"
  - "Zotero 架构生成"
  - "PDF 导入 Zotero"
  # Step 7: 论文写作
  - "写论文"
  - "撰写论文"
  - "基于文献写论文"
  # Step 8: 论文润色（四合一精修引擎）
  - "论文润色"
  - "论文修改"
  - "去 AI 痕迹"
  - "注入人味"
  - "润色分层"
  - "四合一精修"
  - "去 AI 化"
  # 全流程
  - "论文相关工作流"
  - "学术文献全流程"
---

# 完整学术文献检索和写作工作流（8 步法）

## 概述

```
Step 1: 交互式确定研究主题          → 研究主题.md
Step 2: 生成研究大纲与关键词        → 大纲关键词.md
Step 3: 生成文献检索方案            → 检索方案.md
Step 4: 多渠道检索+相关性筛选        → 检索文献表.md / .xlsx
Step 5: 多轮下载（Sci-Hub → SD）    → paper-temp/ PDFs
Step 6: Zotero 文库管理              → zotero-架构.md + Zotero 桌面端
Step 7: 论文写作（4 种模式可选）    → 论文初稿.md / .docx
  ├─ full         完整写作
  ├─ outline-only 仅大纲
  ├─ plan         引导规划
  └─ abstract-only 中英文摘要
Step 7d: 同行评审仿真（质量门）      → 评审报告 + 修改建议
Step 8: 论文润色（含句长波动检测）   → 论文润色稿.md
```

---

## ⚙️ 依赖清单与配置提示

使用本 skill 前，请确认以下依赖。运行时若缺少某项，会提示你补全。

### 软件依赖

| 依赖 | 用途 | 步骤 | 安装方式 | 必选 |
|------|------|------|----------|------|
| **Python 3.9+** | 运行所有脚本 | 全部 | 已有 | ✅ 必选 |
| **websocket-client** | CDP 协议连接 Chrome/Edge | Step 5 | `pip install websocket-client` | ✅ 必选 |
| **PyMuPDF (fitz)** | 提取 PDF 全文文本 | Step 8 | `pip install pymupdf` | ⬜ 可选（仅 Step 8 批量预提取用） |
| **Zotero MCP Server** | 通过对话直接读取 Zotero 文库、按 DOI 导入论文 | Step 7-8 | 已随本 skill 封装<br>`scripts/setup_zotero.py` 可检测配置 | ⬜ 可选（Hermes / OpenClaw / Claude Code 内置）<br>没有时可用手动拖拽或 Web API |
| **Google Chrome** | CDP 下载 PDF | Step 5 | 官网下载 | ✅ 必选（至少一个浏览器） |
| **Microsoft Edge** | 并行加速下载 | Step 5 | 官网下载 | ⬜ 可选（加速用） |

### 账号与权限

| 资源 | 用途 | 步骤 | 获取方式 | 必选 |
|------|------|------|----------|------|
| **ScienceDirect 机构访问** | 下载 Elsevier 论文 PDF | Step 5 | 学校 IP / SSO / CARSI / Shibboleth 登录 | ⬜ 可选（Sci-Hub 下不到时才需要） |
| **Crossref API** | DOI → PII 解析（ScienceDirect 必需） | Step 5 | 免费，无需 Key | ✅ 免费可用 |
| **Semantic Scholar API** | 论文检索 | Step 4 | 免费，无需 Key | ✅ 免费可用 |
| **OpenAlex API** | 论文检索 | Step 4 | 免费，无需 Key | ✅ 免费可用 |
| **Sci-Hub** | 免费下载老论文 PDF | Step 5 | 免登录 | ✅ 免费可用 |

### 运行时提示示例

当执行某步骤缺少依赖时，按以下格式提示用户：

```
⚠ 未安装 websocket-client。请在终端执行：pip install websocket-client

⚠ [Step 5] 检测到 Chrome 未以 CDP 模式启动。
   → 请执行以下命令启动 Chrome（首次需登录 ScienceDirect 并通过 Cloudflare 验证）：
     "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
       --remote-debugging-port=9223 --remote-allow-origins=http://127.0.0.1:9223 \
       --no-first-run --no-default-browser-check --disable-blink-features=AutomationControlled \
       --user-data-dir=/tmp/chrome_profile \
       https://www.sciencedirect.com/
```
---

## Step 1: 交互式确定研究主题

> **开始提示：** "请告诉我你的研究方向或感兴趣的领域，我们可以通过几轮对话逐步厘清研究主题。"

**方式：** 以开放式提问启动对话，与用户多轮交互，逐层聚焦研究方向。

**对话引导示例：**

```
助手：请告诉我你的研究方向或感兴趣的领域，我们可以通过几轮对话逐步厘清研究主题。
用户：我在做热管理方面的研究。
助手：好的，热管理方向很广。具体是哪种设备的热管理？
      充电桩/储能设备？数据中心？还是电力电子器件？
用户：充电桩和储能设备。
助手：主要关注哪个层面？散热结构设计？温度预测与控制？还是热安全？
...（逐层深入，直到研究方向清晰）
```

**关键问题清单（与用户逐轮确认）：**

| 轮次 | 问题 | 产出 |
|------|------|------|
| 1 | 研究大方向是什么？（充电桩？储能？电力电子？） | 领域 |
| 2 | 具体研究问题是什么？（散热？控制？寿命预测？） | 研究问题 |
| 3 | 技术路线偏好？（实验？仿真？数据驱动？） | 方法论 |
| 4 | 应用场景？（电动汽车？数据中心？电网侧？） | 场景 |
| 5 | 时间范围？（近 3 年？近 5 年？无限制？） | 年限 |

**产出文件：`研究主题.md`**

```markdown
# 研究主题

- 领域：研究方向所属领域
- 研究问题：具体研究问题
- 方法论：采用的技术路线
- 应用场景：应用场景描述
```

---

> **下一步 → Step 2：** 基于确定的研究主题，生成论文大纲与关键词清单。回答上述 5 轮问题后，即可进入 Step 2。

## Step 2: 生成论文大纲与关键词

基于 Step 1 的确定主题，生成论文大纲和关键词清单。

**产出文件：`大纲关键词.md`**

```markdown
# 论文大纲与关键词

## 论文标题
研究方向论文标题

## 章节大纲
1. 绪论
2. 第1章
3. 第2章
4. 第3章
5. 结论与展望

## 关键词清单
| 章节 | 中文关键词 | 英文关键词 |
|------|-----------|-----------|
| 1 | 领域关键词 | field keywords |
| 2 | 方法1关键词 | method1 keywords |
| 3 | 方法2关键词 | method2 keywords |
| 4 | 方法3关键词 | method3 keywords |
```

---

> **下一步 → Step 3：** 有了大纲和关键词后，制定结构化检索方案，明确检索子课题和来源。

## Step 3: 生成文献检索方案

基于大纲和关键词，生成结构化检索方案。

**产出文件：`检索方案.md`**

```markdown
# 检索方案

## 检索子课题
| 编号 | 子课题 | 关键词 | 来源 |
|------|--------|--------|------|
| S1 | 子课题一 | keyword1, keyword2 | Semantic, Crossref |
| S2 | 子课题二 | keyword3, keyword4 | Semantic, Crossref |
| S3 | 子课题三 | keyword5, keyword6 | Semantic, Crossref |
| S4 | 子课题四 | keyword7, keyword8 | Crossref, OpenAlex |

## 检索执行计划
- 每子课题检索 50 条
- 去重后总分 ≥200 条
- 最终筛选保留 100-150 条核心文献
```

---

> **下一步 → Step 4：** 按检索方案执行多渠道检索，对结果进行相关性评分和分级筛选。

## Step 4: 多渠道检索与相关性筛选

### 检索执行

按 Step 3 方案逐一执行检索：

```bash
# 按子课题逐条检索
python3 scripts/search_by_topic.py "cold plate liquid cooling optimization" --limit 50 --output s1_results.txt
python3 scripts/search_by_topic.py "spray cooling battery heat transfer" --limit 50 --output s2_results.txt
# ...
```

### 相关性评分

检索结果按以下维度打分（每项 0-5 分，满分 25）：

| 维度 | 权重 | 说明 |
|------|------|------|
| 主题匹配度 | ×1 | 标题+摘要与研究主题的相关程度 |
| 方法一致性 | ×1 | 采用的方法与技术路线匹配度 |
| 来源质量 | ×1 | 期刊/会议等级 |
| 时效性 | ×1 | 近 3 年 +1，近 5 年 +0.5 |
| 引用量 | ×1 | 高引用加分 |

**产出文件：`检索文献表.md`**（含评分列），同时可输出 `.xlsx`。

### 筛选标准

| 等级 | 分数范围 | 处理 |
|------|---------|------|
| ⭐ Tier 1 | ≥20 | 核心文献，必须下载 |
| 📘 Tier 2 | 15-19 | 重要文献，尽量下载 |
| 📄 Tier 3 | 10-14 | 参考文献，有选择下载 |
| ⬜ Tier 4 | <10 | 剔除 |

---

> **下一步 → Step 5：** 开始批量下载。优先走 Sci-Hub（老论文免费下），未下载到的走 ScienceDirect CDP。

## Step 5: 多轮批量下载

分两轮下载，目标覆盖率 90%+。

### 第一轮：Sci-Hub 优先（老论文）

对 **2021 年以前** 的老论文，可通过 Sci-Hub CDP 下载（需要 Chrome 运行）。脚本会自动测试镜像站可用性。

```bash
# 标准流程：测试镜像站 → 取可用站 → 逐篇下载
python3 scripts/download_via_scihub.py 检索文献表.md --output paper-temp/

# 跳过镜像测试（如果上次已测过）
python3 scripts/download_via_scihub.py 检索文献表.md --skip-test

# 指定镜像站
python3 scripts/download_via_scihub.py 检索文献表.md --mirror https://sci-hub.st
```

**镜像站自动检测：**

脚本启动后先测试全部 13 个预置镜像站，输出每个的状态：

```
测试 Sci-Hub 镜像站可用性...
  ✅ sci-hub.st      可用（Sci-Hub. An experimental...）
  ✅ sci-hub.ru      可用
  ❌ sci-hub.se      Cloudflare 验证拦截
  ❌ sci-hub.wf      重定向到首页
  ...
```

若全部不可用，自动联网搜索新的可用镜像站。

**实测结论：**

| 项目 | 结果 |
|------|------|
| 可用镜像站（CDP） | **9/13 个**（st/ru/shop/vg/in/al/box/red/ren） |
| 下载方式 | CDP Chrome 导航 → 提取 `<object>` 的 PDF 链接 → Fetch 拦截捕获 |
| 下载速度 | ~6s/篇 |
| 有效范围 | **2021 年以前**论文（新论文 Sci-Hub 未收录） |
| HTTP 直连 | ❌ 全部被 Cloudflare Turnstile 拦截，必须用 CDP |

> 如果论文大部分是新出版（2022+），直接跳过第一轮。

### v2.1 核心设计原则

1. **默认所有论文都有访问权限，下不到是策略问题，不是权限问题。** 不要轻易将失败归因于"无权限"——先检查下载策略是否覆盖了 SD 的多种 PDF 加载机制（直接重定向 vs 文章页 JS 渲染）。
2. **CDP 打开的标签页渲染状态不同于用户手动打开的标签页。** SD 的 SPA 页面在 CDP 环境下可能不显示 "View PDF" 按钮（自动化检测），此时需要更长的渲染等待时间（20-25s）或通过用户现有标签页操作。
3. **双浏览器并行可翻倍速度但需隔离标签页。** Chrome 和 Edge 各自独立标签页上下文，一篇论文的 PDF 标签页残留不会影响另一浏览器的下一篇论文。但同一浏览器内必须关闭 PDF 标签页。

### 第二阶段：ScienceDirect CDP（v2.1 混合策略）

第一轮未下载到的 Elsevier 论文，通过 CDP + 机构认证补下。

```bash
# 全自动版（推荐）：自动启动浏览器、断点续跑、跳过无权限论文
python3 scripts/auto_sd_downloader.py --output-dir paper-temp/ --pii-map sd_pii_map.json

# 手动版：需自行启动 CDP 浏览器
python3 scripts/parallel_sd_download.py
```

### CDP 浏览器持久化配置

**目标：** 登录 ScienceDirect 一次后永久保留会话，后续下载无需重新登录。

**方案（v2.0）：** Chrome Profile 从 `/tmp/` 迁移到 `~/.hermes/chrome_sd_profile`。`auto_sd_downloader.py` 的 `restart_browser()` 不再删除 Profile 目录，重启后 SD Cookie 保留。

**一键启动脚本：**
```bash
# 启动 CDP Chrome（端口 9223），首次需手动登录 SD
bash scripts/start_cdp_chrome.sh

# 验证 CDP 是否就绪
curl -s http://127.0.0.1:9223/json/version | python3 -c "import sys,json; print(json.load(sys.stdin)['Browser'])"
```

**日常使用流程：**
1. 机器重启后，首次运行 `bash scripts/start_cdp_chrome.sh`
2. 在 Chrome 窗口中登录 ScienceDirect（Cloudflare 验证 + 机构登录）
3. 后续所有下载脚本自动连接端口 9223，无需再次登录
4. 下载脚本的 `restart_browser()` 保留 Profile，重启后 Cookie 仍在

**Edge 双浏览器并行（可选）：**
```bash
# 同样方式启动 Edge（端口 9225）
"/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
  --remote-debugging-port=9225 \
  --remote-allow-origins=http://127.0.0.1:9225 \
  --no-first-run --no-default-browser-check \
  --user-data-dir="$HOME/.hermes/edge_sd_profile" \
  https://www.sciencedirect.com/ &
```

### 轮次记录

`下载记录.md` 追踪每篇论文的下载状态：

| DOI | 状态 | 来源 | 文件路径 |
|-----|------|------|----------|
| 10.1016/... | ✅ | SD CDP | paper-temp/xxx.pdf |
| 10.3390/... | ⬜ 待定 | 无可用方式 | - |

### 第三轮：多出版商 CDP 下载（非 SD 论文）

第一、二轮未覆盖的非 Elsevier 论文（IEEE / Wiley / AIP / ASME / Springer / RSC 等），采用同样的 CDP Fetch 拦截原理。步骤如下：

```
① 确认 CDP Chrome 已启动（--remote-debugging-port=9223）
② 检查浏览器 Cookie → 确认机构会话有效
   若 Cookie 为空 → CDP Chrome 使用隔离临时 Profile
     → 方案A：在 CDP Chrome 窗口中手动完成机构登录
     → 方案B：关闭日常 Chrome → 清理 stale lock 文件
         (`rm -f ~/Library/Application\\ Support/Google/Chrome/Singleton*`)
         → 用真实 Profile 启动 CDP Chrome
③ 导航到论文 DOI 页面
④ 在页面中找到 PDF 按钮/链接
⑤ 使用 Fetch 拦截捕获 PDF

#### IEEE 两步走策略（已验证 5/5 成功）

```bash
# 用法：传入 DOI 列表文件
python3 scripts/download_via_ieee.py dois.txt --port 9223 --output paper-temp/

# 或直接传入 DOI（逗号分隔）
python3 scripts/download_via_ieee.py --papers 10.1109/tvt.2022.3183866,10.1109/itec51675.2021.9490073

# 输入文件格式（每行一个DOI）：
#   10.1109/tvt.2022.3183866
#   10.1109/itec51675.2021.9490073
```

```
Step A（首选，v1.1 改进）：
  ① 导航到文章页 ieeexplore.ieee.org/document/{arnumber}
  ② 等待 6s 页面加载
  ③ 点击 PDF 按钮（分层选择器：.document-actions-bar a / .pdf-btn-container a /
     .xpl-btn-pdf / a[href*="/stamp/"] / 文本"PDF"兜底 — 覆盖新旧 IEEE Xplore 布局）
  ④ 等待 4s → 先检查当前标签页是否跳转到 stamp/getPDF（同页跳转检测）
  ⑤ 若当前页未跳转，扫描新开标签页（URL 含 "stamp" 或 "getPDF"）
  ⑥ 在目标标签页中：Fetch.enable(pattern="*") → Page.reload
  ⑦ 轮询 Fetch.requestPaused → 调 Fetch.getResponseBody 检查是 "%PDF"
  ⑧ 捕获到 → 写入文件

Step B（回退）：
  ① 检查是否被 denied（URL 含 "?denied="）
  ② 直接导航到 stamp/stamp.jsp?tp=&arnumber=XXXXX
  ③ Fetch.enable(pattern="*") → Page.reload → 捕获
  ④ 若 stamp.jsp 失败，试 stampPDF/getPDF.jsp?tp=&arnumber=XXXXX

失败信号：
  - 重定向到 document/{arnumber}?denied= → 机构订阅未覆盖此论文
  - Step A 点击返回 NO_BUTTON → PDF 按钮不可见（通常需机构登录）
  - stampPDF/getPDF.jsp 重定向到文章页 → 浏览器会话未初始化
```

详见 `references/publisher-access-matrix.md` 中的「CDP 通用方案」和「出版商适配经验」章节，记录了各出版商的 PDF URL 模式和注意事项。
#### Cookie 诊断（关键步骤）

在尝试下载前，先通过内置命令检查是否有机构会话：

```bash
# 快速检查会话状态
python3 scripts/download_via_ieee.py --check-session --port 9223
```

或手动诊断：

```python
import json, urllib.request, websocket
wu = json.loads(urllib.request.urlopen(
    'http://127.0.0.1:9223/json/version').read())['webSocketDebuggerUrl']
ws = websocket.create_connection(wu, timeout=10)
ws.send(json.dumps({'id':1,'method':'Network.getAllCookies'}))
cookies = None
while True:
    msg = json.loads(ws.recv())
    if msg.get('id') == 1:
        cookies = msg['result']['cookies']
        break
pubs = ['ieee','wiley','aip','asme','springer','nature','sciencedirect','elsevier']
pc = sum(1 for c in cookies if any(p in c.get('domain','') for p in pubs))
print(f'出版商Cookie: {pc} | 总Cookie: {len(cookies)}')
```

若结果为 `出版商Cookie: 0`，原因可能是：
- **最常见：CDP Chrome 使用隔离的临时 Profile**（如 `/tmp/chrome_scidownload`）—— 用户在日常 Chrome 中完成的登录不共享到 CDP 浏览器
- 需要**在 CDP 浏览器窗口中**完成机构登录，或切换为用户的真实 Chrome Profile（见 `references/publisher-access-matrix.md` →「先决条件：CDP 浏览器与会话管理」）

#### 多出版商下载参考

详见 `references/publisher-access-matrix.md` 中的「CDP 通用方案」和「出版商适配经验」章节，记录了各出版商的 PDF URL 模式和注意事项。

---

> **下一步 → Step 6：** 下载完成后，管理 Zotero 文库：先生成架构，再将 PDF 导入对应集合。

## Step 6: Zotero 文库管理

分为两个子步骤：**6a 生成架构** → **6b 导入 PDF**。

### 6a：生成 Zotero 文库架构

根据论文大纲和检索方案，生成 Zotero 集合结构。

```bash
python3 scripts/organize_zotero.py 大纲关键词.md --output zotero-架构.md
```

**产出文件：`zotero-架构.md`**

示例结构：

```
📁 论文文献库
├── 📁 1-基础
│   ├── P0-A1 基础理论 / 综述
│   └── P0-A3 方法综述
├── 📁 2-方向一
│   ├── P1-D1 子方向A
│   └── P1-D2 子方向B
├── 📁 3-方向二
│   ├── P0-B1 方法A
│   └── P0-B2 方法B
└── 📁 4-方向三
    ├── P0-C1 子方向A
    ├── P0-C2 子方向B
    └── P0-C3 子方向C
```

### 6b：导入 PDF 到 Zotero

先检测 Zotero 环境：

```bash
python3 scripts/setup_zotero.py
```

**方式一：手动拖拽（推荐，零配置）**
在 Zotero 桌面端拖拽 PDF 到对应集合，Zotero 自动识别 DOI/标题并匹配元数据。最简单的方式，无需任何 API Key。Zotero 免费版仅有 300MB 云端存储，PDF 保存在本地，元数据同步到云端几乎不占空间。

**方式二：Zotero MCP 对话操作**
通过 `zotero_add_by_doi` 等工具直接按 DOI 导入（Hermes / OpenClaw / Claude Code 内置，无需额外配置）。

> **下一步 → Step 7：** 所有文献准备就绪，开始按大纲撰写论文。

---

## 实测性能基线

### v2.0 性能数据（2026-06 实测，94 篇 SD）

| 指标 | 旧版 | v2.0 |
|------|------|------|
| 无权限论文单篇耗时 | ~53s（等满 `wait_for_tab_url` 超时） | **~9s**（8s 快拒 + 1s 开销） |
| 标签页管理 | 每篇 `create_tab` + `close_all_tabs` | **复用同一标签页**，仅 `Page.navigate` |
| 默认 PDF 超时 | 50s | **20s** |
| 81 篇无权限总耗时 | ~4300s（71min） | **~729s（12min）** |
| 重启死循环 | 无限重启 | 2 波零下载自动退出 |
| Profile 位置 | `/tmp/sd_chrome_profile`（每次删除） | `~/.hermes/chrome_sd_profile`（持久化） |
| SD 登录 | 每次重启需重新登录 | **登录一次，永久保留** |

### 典型访问率

约 **20%** 的 SD 论文具有机构订阅权限（取决于学校/机构订阅的期刊包）。剩余 80% 呈现摘要页而无 PDF 下载按钮。

### 旧版基线参考（180 篇，另一环境）

| 指标 | 数值 |
|------|------|
| 总扫描论文 | 188 篇 SD |
| 成功下载 | **180 篇 PDF**（96%） |
| 总大小 | **1.4 GB** |
| 单浏览器耗时 | ~60 分钟 |
| 并行（Chrome+Edge） | **~50 分钟** |
| 无 PDF 访问权限 | ~8 篇（摘要页，无可下载 PDF） |

### 会话生命周期

| 阶段 | 数量 | 说明 |
|------|------|------|
| 单次登录可下载 | ~15 篇 | 之后 Cloudflare 重新挑战 |
| 单会话标签页创建上限 | ~100-150 次 | 超过后触发验证 |
| Profile 位置 | `~/.hermes/chrome_sd_profile` | v2.0 持久化，重启保留 Cookie |
| 恢复方式 | 杀 Chrome → 重启浏览器 | **不删 Profile**，SD Cookie 保留 |

### 恢复速度

```bash
pkill -9 -f "Google Chrome" 2>/dev/null
# 不删 ~/.hermes/chrome_sd_profile — SD Cookie 保留
# 直接重启 Chrome
bash scripts/start_cdp_chrome.sh
```

---

## 脚本索引

| 脚本 | 步骤 | 用途 |
|------|------|------|
| `scripts/search_by_topic.py` | 4 | 多渠道检索（Semantic Scholar / Crossref / OpenAlex） |
| `scripts/batch_read_pdfs.py` | 8 | 批量提取 PDF 全文文本（默认 6 进程，自动切换 A/B 方案） |
| `scripts/download_via_scihub.py` | 5 | Sci-Hub CDP 下载（镜像站自动检测，`--mirror`/`--skip-test` 参数） |
| `scripts/download_via_ieee.py` | 5 | IEEE CDP 两步走下载（v1.1：分层PDF按钮选择器 + 同页跳转检测 + 机构会话诊断引导 + `--check-session` 命令 | Step A: 点PDF按钮→stamp标签页→Fetch捕获 | Step B: 直接 stamp/getPDF URL→Fetch捕获） |
| `scripts/batch_resolve_pii.py` | 5 | DOI → PII 解析（BibTeX / Markdown / 纯文本，自动检测格式） | ✅ |
| `scripts/parallel_sd_download.py` | 5 | 双浏览器并行下载（混合策略：直连+文章页提取），引用 `sd_download.py` | ✅ |
| `scripts/auto_sd_downloader.py` | 5 | 全自动版：启停浏览器 + 断点续跑 + 混合策略（引用 `sd_download.py`）| ✅ |
| `scripts/auto_sd_downloader.py --no-restart` | 5 | 使用已有的 CDP 浏览器，不重启不杀进程 | ✅ |
| `scripts/sd_download.py` | 5 | 共享混合下载核心（策略A: 直连8s→PDF标签页→Fetch捕获 / 策略B: 文章页25s渲染→提取`?md5=`→PDF标签页→Fetch捕获） | ✅ |
| `scripts/cdp_utils.py` | 5 | 共享 CDP 模块（浏览器管理、Fetch 捕获、依赖检查） | — |
| `scripts/start_cdp_chrome.sh` | 5 | 一键启动 CDP Chrome（持久化 Profile，登录一次永久可用） | ✅ |
| `scripts/organize_zotero.py` | 6 | 解析大纲关键词 → Zotero 集合结构 | ✅ |
| `scripts/organize_zotero.py` | 6 | 生成 Zotero 集合结构 |
| `references/literature-table-template.md` | 4 | 检索结果表示例 |
| `references/zotero-structure-template.md` | 6 | Zotero 架构示例 |
| `references/publisher-access-matrix.md` | 5 | 各出版商下载可行性对照表 |

---

## 参考文件

- `references/literature-table-template.md` — 含相关性评分的文献表格模板
- `references/zotero-structure-template.md` — Zotero 集合结构示例
- `references/publisher-access-matrix.md` — 各出版商下载可行性对照表
- `references/zotero-missing-attachments.md` — 定位 Zotero 中缺 PDF 的条目并通过 CDP 补下
- `references/poster-generation.md` — 朋友圈海报生成工作流（HTML + Chrome headless）
- `references/cdp-pdf-capture-limitations.md` — CDP PDF 捕获限制与期刊级访问限制
- `references/sd-cdp-architecture.md` — SD 下载架构：PDF 在新标签页渲染、会话二层结构、标签页管理策略、Profile 持久化

---

## 已知陷阱

### Python 版本：macOS 默认 3.9
`python3` 是系统自带的 **3.9**（`/usr/bin/python3`）。Python **3.14** 在 `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3`。运行脚本前确认版本，脚本兼容 3.9-3.14，但 Python 3.14 禁止单行 `try: ... ; except: pass`（见下条）。

### Python 3.14: 单行 try/except 非法
```python
# ❌ 语法错误：
try: ws.recv(); except: pass

# ✅ 必须多行：
try:
    ws.recv()
except:
    pass
```

### Fetch.requestPaused 事件被 send_cmd 吃掉
`send_cmd()` 在等回复时会读取 WebSocket 消息，`Fetch.requestPaused` 因无匹配 ID 被丢弃。

**修复：** 发 `Page.reload` 后直接进入事件循环，不等回复。

```python
# ❌ 错误：
send_cmd("Page.reload")
while loop:  # 永远收不到
    msg = recv()

# ✅ 正确：
pws.send(json.dumps({"id": X, "method": "Page.reload"}))
while loop:
    msg = recv()
```

### 论文无 PDF 可下
约 4% 的 ScienceDirect 论文只提供摘要页（`/abs/...`），无可下载 PDF。10 秒超时机制快速跳过。

### Network.getResponseBody 跨域限制
PDF 从 `pdf.sciencedirectassets.com`（跨域）提供时，`Network.getResponseBody` 无法获取响应体。详见 `references/cdp-pdf-capture-limitations.md`。

### 期刊级访问限制
即使用户有 SD 机构访问，某些期刊（如 Applied Ocean Research）可能不可下载。诊断方法：在 Chrome 窗口查看文章页是否有 "Download PDF" 按钮。详见 `references/cdp-pdf-capture-limitations.md`。

### 电脑休眠导致下载变慢
合盖休眠后，单篇墙钟时间可能膨胀到 800-1000 秒。auto_sd_downloader.py 通过 120 秒后判断来处理。

### 浏览器 CDP 限制
- **Chrome** ✓ — `--remote-debugging-port`
- **Edge** ✓ — 同 Chromium 内核，同样参数
- **Safari** ✗ — WebKit Remote Inspector，协议不同
- **Firefox** ✗ — Marionette/WebDriver，协议不同

### 不要写临时 Fetch 脚本下载 SD 论文
必须使用 `cdp_utils.capture_pdf_via_fetch()`，不要自行实现 Fetch 拦截逻辑。自行实现容易踩 WebSocket 事件时序的坑：发送 `Page.enable`/`Fetch.enable` 后如果调用 `recv()` 等待响应，会吃掉 `Fetch.requestPaused` 事件，导致后续事件循环永远收不到。详见 `references/cdp-pdf-capture-limitations.md`。

### 用真实 Profile 启动 CDP Chrome 时 Profile 被锁

`pkill -9 -f "Google Chrome"` 强制关闭 Chrome 后，profile 目录可能残留锁文件（`SingletonLock`、`SingletonSocket`、`SingletonCookie`），导致下次用该 profile 启动失败。

**修复：** 杀掉进程后手工清理锁文件：
```bash
pkill -9 -f "Google Chrome"
rm -f ~/Library/Application\\ Support/Google/Chrome/SingletonLock
rm -f ~/Library/Application\\ Support/Google/Chrome/SingletonSocket
rm -f ~/Library/Application\\ Support/Google/Chrome/SingletonCookie
```

### auto_sd_downloader.py Wave 2+ 重启死循环

`auto_sd_downloader.py` 的 `max_consecutive_fail` 机制（默认 5 次）用于检测会话过期并自动重启浏览器。但若大量论文本身没有机构访问权限，每次重启后相同的论文会连续失败，触发立即重启，形成 **无限重启死循环**。

**判断是否是死循环：** Wave 2 及以后，所有论文在 0-1 秒内快速失败（超短耗时），说明是被访问限制拒绝而非会话过期。

**v2.0 修复（自动跳过无权限论文）：**
- 引入 `skip_set` 永久跳过队列：同一篇论文连续失败 3 次后，自动加入跳过列表
- `_worker()` 跳过列表中的论文，不触发 `consec` 计数器
- 连续 2 次 Wave 零下载时自动退出并打印总结

**处理策略：**
```bash
# 先用 auto_sd_downloader.py（v2.0 内置跳过机制，推荐）
python3 auto_sd_downloader.py --output-dir paper-temp/ --pii-map sd_pii_map.json

# 跳过机制工作流程：
#   Wave 1: 尝试全部 94 篇 → 成功下载 13 篇，失败 81 篇（各记失败 1 次）
#   Wave 2: 跳过已成功的 13 篇 → 剩余 81 篇再试 → 失败 81 篇（各记失败 2 次）
#   Wave 3: 跳过前两波失败的 81 篇（已达 2 次）→ 部分达 3 次自动跳过
#   → 输出总结：81 篇永久跳过（无权限），退出
```

**手动清理已下载：**
```bash
# 查看已下载
ls paper-temp/*.pdf | wc -l
# 从 PII 映射中移除已成功的
python3 -c "
import json
with open('sd_pii_map.json') as f: data = json.load(f)
done = set(f[:-4] for f in __import__('os').listdir('paper-temp') if f.endswith('.pdf'))
for k in list(data['resolved']):
    if k in done:
        del data['resolved'][k]
with open('sd_pii_map_filtered.json','w') as f: json.dump(data,f)
print(f'Remaining: {len(data[\"resolved\"])}')
"
```

### 纯文本参考文献的 DOI 提取

当输入文件是纯文本引用格式（每行 `[N] Author, ..., DOI`，非 BibTeX、非 Markdown 表格）时，`batch_resolve_pii.py` 的 BibTeX 解析器无法处理。

**正确的提取方式：**
```python
import re
# 1. 提取所有 DOI URL
doi_urls = re.findall(r'https://doi\\.org/10\\.1016/[^\\s]+', text)
# 2. 去除尾部标点（句号、逗号）
unique_dois = list(dict.fromkeys(
    url.rstrip('.,;') for url in doi_urls
))
# 3. 用 Crossref API 逐一解析 PII
```
注意：提取后去除尾部标点可避免 `10.1016/...2025.127040.`（尾部句点）误匹配。

### CDP WebSocket 层级：浏览器级 vs 标签页级

`Network.getAllCookies()` 在不同层级的 WebSocket 上返回不同结果：

| WS 层级 | 连接方式 | Cookies 结果 | 可执行 Fetch |
|---------|---------|-------------|-------------|
| 浏览器级 | `get_cdp_ws_url(port)` → 全局 WS | **0 cookies** | ❌ |
| 标签页级 | `list_tabs(port)` → `webSocketDebuggerUrl` | **真实 Cookie** | ✅ |

**影响：** `capture_pdf_via_fetch()` 使用标签页级 WS，正常获取 PDF。但如果在浏览器级 WS 上调用 `Network.getAllCookies` 来诊断登录状态，会得出 0 cookie 的**假阴性**结果。

**诊断方法：**
```python
# 只能在标签页级 WS 获取 Cookie
tabs = list_tabs(port)
for t in tabs:
    tws = t.get("webSocketDebuggerUrl")
    if tws:
        pws = websocket.create_connection(tws, timeout=10)
        send_cmd_and_wait(pws, "Network.enable")
        pws.send(json.dumps({"id": 2, "method": "Network.getAllCookies"}))
        resp = json.loads(pws.recv())
        cookies = resp.get("result", {}).get("cookies", [])
        sd = [c for c in cookies if "sciencedirect" in c.get("domain","")]
        print(f"{len(sd)} SD cookies on tab {t.get('url','')[:50]}")
        pws.close()
```

### PDF 标签页残留导致重复下载（v2.1 修复）

`_wait_for_pdf_tab()` 扫描所有标签页查找 PDF 主机。如果上一篇论文的 PDF 标签页未被关闭，下一篇论文的 `_wait_for_pdf_tab` 会立即找到残留的 PDF 标签页，**捕获到同一篇论文的内容并用不同文件名保存**。

**表现特征：** 多篇论文显示同样大小（如 13888KB）和同样的 MD5，下载耗时均为 5-6s。

**修复（`_navigate_and_capture`）：**
```python
close_tab(port, tid)       # 关闭导航标签页
if pdf_tid:
    close_tab(port, pdf_tid)  # 关闭 PDF 标签页 → 防止下一篇文章误捕获
```

**前置防护（`download_one`）：**
```python
# 每篇论文下载前清理残留 PDF 标签页
for t in list_tabs(port):
    if "pdf.sciencedirectassets.com" in t.get("url", ""):
        close_tab(port, t["id"])
```

### SD 文章页渲染时长不足导致提取不到 "View PDF"

SD 的文章页是 SPA（单页应用），JavaScript 需要时间渲染 "View PDF" 链接。CDP 创建的标签页在 SD 的 SPA 中**渲染速度比手动浏览器慢**（可能因自动化检测降速）。

**实测数据：**

| 渲染等待时间 | 提取成功率 |
|------|------|
| 8s | ~30% |
| 12s | ~50% |
| 20s | ~90% |
| 25s | ~95% |
| 30s+ | 部分论文仍无（~5% 页面结构特殊） |

**默认值：** `_strategy_b` 使用 `render_timeout=25`，覆盖 `_extract_pdfft_url` 的默认 `render_timeout=12`。

**如果 `render_timeout=25` 仍提取不到：**
- 该论文的 SD 页面可能使用不同的渲染路径
- 手动在浏览器中打开该论文，检查是否有 "View PDF" 按钮
- 无按钮 → 期刊可能有特殊访问限制
- 有按钮 → 需要更深的 CDP 绕过方案（点击交互等）

### 双阶段 SD 下载策略（v2.1）

SD 论文的 PDF 加载分两种机制，需要对应策略：

| 类型 | 比例 | 行为 | 策略 |
|------|------|------|------|
| 直接重定向 | ~30% | `/pdfft` → `pdf.sciencedirectassets.com` | Phase 1: 15s 超时直接捕获 |
| 文章页提取 | ~70% | `/pdfft` 返回 HTML，需从文章页提取 `?md5=&pid=` URL | Phase 2: 开文章页 → 提取完整 URL → 捕获 |

**完整流程（`scripts/hybrid_sd_download.py`）**
```python
# Phase 1: 直接尝试 /pdfft（15s 超时）
pdf = phase1_direct(port, pii)

# Phase 2: 不成功则走文章页提取
if not pdf:
    pdf = phase2_article(port, pii)
```

**Phase 2 的关键点：**
- 必须等待 SPA 页面渲染完成（至少 10s）
- 从 `a[href*="pdfft"]` 中提取含 `?md5=` 的完整 URL
- 这个 `md5` 参数是会话关联的，直接访问 `/pdfft` 不带此参数时 SD 返回 HTML
- 使用 `Fetch.enable` 在导航前拦截，捕获 PDF 响应体

**双浏览器并行加速：**
```bash
# 终端 1: Chrome 处理上半部分
python3 scripts/hybrid_sd_download.py --port 9223 --output-dir paper-temp/

# 终端 2: Edge 处理下半部分（--start-offset 跳过 Chrome 已处理的）
python3 scripts/hybrid_sd_download.py --port 9225 --output-dir paper-temp/ --start-offset 47
```

当 Python 脚本通过 `terminal(background=true)` 运行时，stdout 进入 pipe，Python 默认对 pipe 进行全缓冲（非行缓冲），可能导致长时间看不到任何输出。

**修复：** 使用 `PYTHONUNBUFFERED=1` 环境变量或 `python3 -u` 参数启动脚本。
```bash
export PYTHONUNBUFFERED=1
python3 -u auto_sd_downloader.py --output-dir paper-temp/ --pii-map sd_pii_map.json
```
若 Hermes 背景进程仍无输出，可改前台模式（`timeout=600`，最大支持 600 秒），下完一批再续跑。

### auto_sd_downloader.py SD 访问权限不足（~80% 论文不可下载）

大多数机构订阅了 SD 的部分期刊包，约 **80% 的 SD 论文只有摘要页无 PDF 下载按钮**。这并非 bug，而是权限限制。

**v2.0 优化（8s 快拒）：**
- `download_one()` 分两阶段：先 8s 快速检测 PDF 重定向 → 无重定向则立即失败
- 比旧版 50s 超时快 6 倍，81 篇无权限论文从 71min 降至 ~12min
- 跳过 `close_all_tabs`，改为仅关闭 PDF 标签页、保留下载标签页复用

**行为特征：**
- 可下载论文：3-5s 内完成 PDF 重定向 → 正常捕获（9-15s 总耗时）
- 不可下载论文：8s 后标记 `❌`（超短耗时说明是无权限而非会话过期）
- 所有不可下载论文在 3 轮内进入 `skip_set` 永久跳过

**处理建议：**
- 先跑一轮观察可下载比例（`ls paper-temp/*.pdf | wc -l`）
- 剩余论文尝试 Sci-Hub（2021 年前出版的）
- 或通过文献传递/馆际互借获取

### 真实 Chrome Profile CDP 端口不绑定（macOS 特定）

某些 macOS 机器上，用真实 Chrome Profile 启动 `--remote-debugging-port=9223` 后，Chrome 进程虽然跑起来了但 CDP 端口不监听。即使 `pkill -9` 杀光所有 Chrome 进程、清理锁文件、用 `open -a` 或直接命令行启动，CDP 端口依然无法连接。

**原因推测：** 安装的扩展（特别是安全/代理类扩展）可能阻止了 CDP server 的端口绑定。临时 Profile 不受影响。

**诊断方法：**
```bash
# 临时 Profile 测试（应该能工作）
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9224 \
  --no-first-run --no-default-browser-check \
  --user-data-dir=/tmp/test_cdp_profile \
  about:blank
# 等 3-4 秒后检查
curl -s http://127.0.0.1:9224/json/version
```

**恢复手段：** `pgrep -f "Chrome" | xargs kill -9` 比 `pkill -9 -f "Google Chrome"` 更彻底，能杀掉所有 Helper/Renderer 进程。

**推荐方案：** 遇到此问题时放弃真实 Profile，改用持久化临时 Profile + `scripts/start_cdp_chrome.sh` 一键启动。`auto_sd_downloader.py` 使用 `~/.hermes/chrome_sd_profile` 持久化 Profile，首次登录后 Cookie 永久保留，无需二次登录。

**脚本索引定位：**
- `scripts/sd_download.py` — 共享下载核心（混合策略：直连 + 文章页提取）
- `scripts/parallel_sd_download.py` — 双浏览器并行（推荐日常使用）
- `scripts/auto_sd_downloader.py` — 全自动版（管理浏览器生命周期）
- `scripts/batch_resolve_pii.py` — DOI→PII 解析
- `scripts/start_cdp_chrome.sh` — CDP Chrome 启动器
- `~/.hermes/chrome_sd_profile` — SD Cookie 持久化存储位置

### 关于"权限不足"的排查原则

**核心原则：不要轻易怀疑用户的权限。** 用户确认有机构权限时，下不到论文的唯一原因就是下载策略不够全面，而非权限不足。

排查顺序：
1. 检查 `/pdfft` 直连是否拿到 PDF → 是则策略 A 成功
2. 检查文章页是否有 `?md5=` 的 "View PDF" 链接 → 是则策略 B 应能提取
3. 检查渲染时间是否足够（20-25s）
4. 检查是否有残留 PDF 标签页干扰
5. 极少情况（~5%）SD 页面结构特殊，需手动排查

---

## Step 7: 论文写作

利用 Step 1-6 的所有产出，以下载的 PDF 作为知识库，撰写正式学术论文。**核心原则：每处引用必须来自实际 PDF 内容，抑制大模型幻觉。**

### 前置输入

| 来源 | 位置/内容 |
|------|-----------|
| Step 1 → `研究主题.md` | 研究方向、研究问题、方法论 |
| Step 2 → `大纲关键词.md` | 章节结构、中英文关键词 |
| Step 3 → `检索方案.md` | 子课题划分 |
| Step 4 → `检索文献表.md` | 核心参考文献（含评分、DOI、章节归属） |
| Step 5 → `paper-temp/*.pdf` | **知识库** — 所有已下载的 PDF 全文 |
| Step 6 → `zotero-架构.md` | Zotero 集合结构（PDF 按章节分类） |

### 写作模式选择

进入写作前，先与用户确认目标期刊/写作需求，选择写作模式：

| 模式 | 触发场景 | 产出 |
|------|----------|------|
| `full` | 已有清晰大纲和文献，直接逐章完整撰写 | 论文初稿.md |
| `outline-only` | 不确定结构，先生成详细大纲 | 大纲关键词.md（细化版） |
| `plan` | 需要多轮引导交互来厘清论点 | 多轮交互 → 大纲 |
| `abstract-only` | 已有正文，仅需写中英文摘要 | 中英文摘要 + 关键词 |

### 知识库位置

已有 PDF 知识库的位置在 Step 7 写作过程中**通过交互沟通确定**，可能来自：

- **Step 5 的下载目录**（如 `paper-temp/`）— 刚下载好的 PDF
- **Zotero 文库** — 已导入 Zotero 的论文，通过 `zotero_get_item_fulltext` 读取
- **用户指定的其他目录** — 写作过程中用户告知的任意路径

每个 PDF 对应检索文献表中的一篇文献。可按 `zotero-架构.md` 的分类找到对应章节的 PDF。

```
示例目录结构（具体位置以交互确认结果为准）：
paper-temp/  或  其他目录/
├── chen_research_2025.pdf      ← 基础理论
├── zhang_experimental_2022.pdf ← 实验研究
├── liu_method_2024.pdf         ← 方法论文
├── wang_approach_2023.pdf      ← 方法论文
└── ...                         (共 N 篇 PDF)
```

### 写作策略

**有论文大纲（`大纲关键词.md` 存在时）：**

按大纲章节逐章撰写。每写一章前，根据 `zotero-架构.md` 的分类和 `检索文献表.md` 的章节归属，确定本章应参考哪些 PDF，**与用户交互确认**后读取全部归属本章的 PDF 全文。例如：

```
> 现在写第 3 章。根据 Zotero 文库分类，本章归属的文献有：
>   - paper_2022.pdf（评分 T1）
>   - zhang_spray_2023.pdf（评分 T1）
>   - liu_spray_2021.pdf（评分 T2）
> 共 7 篇，你先全部读完再写，还是先挑重点读？
```

用户确认后，**逐一读取本章全部 PDF 全文**（或使用 `scripts/batch_read_pdfs.py` 批量预提取），提取每篇的具体方法、实验参数、数据图表、结论等，将其作为引用内容写入论文。每处引用标注索引。

**无论文大纲时：**

按下方标准 7 节模板撰写。同样，每节先与用户确认参考哪些 PDF，读后再写。

### 防幻觉机制（核心）

| 机制 | 说明 |
|------|------|
| **先读后写** | 引用某篇文献前，必须用 `zotero_get_item_fulltext` 或手动打开方式读取 PDF 全文，获取真实方法/数据/结论 |
| **交互确认** | 每章写前与用户沟通："参考哪几篇 PDF？从这些 PDF 中提取哪些内容？" |
| **索引必达** | 每处引用标注索引号，文末参考文献列表的条目必须与实际读取过的 PDF 一一对应 |
| **不编造引用** | 未在 `检索文献表.md` 中的文献、未读取过 PDF 的文献，不得引用 |
| **原文比对** | 引用具体数据时注明出自 PDF 的哪一章/哪一图/哪一页 |

### 写作流程

```
1. 确定目标期刊/会议 → 格式要求
2. 逐章写作循环：
   a. 根据 Zotero 分类确认本章归属的 PDF 清单
   b. 告知用户清单，交互确认
   c. 用户确认后，逐一读取本章全部 PDF 全文
   d. 从每篇 PDF 中提取方法/数据/结论
   e. 撰写章节正文，标注引用索引
   f. 记录引用条目，加入文末参考文献列表
3. 所有章节完成后，生成完整参考文献列表
4. 格式整理 + 交叉引用检查
5. 输出最终论文
```

### 引用与参考文献要求

- 正文中每处引用标注索引：`[1]`、`[2, 5]`
- 参考文献列表包含：DOI、作者、标题、期刊/会议、年份、卷期页码
- **每篇参考文献必须对应一个实际存在的 PDF**（存放位置根据交互沟通确定）
- 引用内容与 PDF 原文一致（不得自行编造数据或结论）
- 参考文献 20-40 条为宜

### 辅助脚本

如需批量预提取所有 PDF 全文文本以加速写作过程，可使用：

```bash
# 方案 B: 全库预提取（文献量≥20 篇时自动选择，默认 6 进程）
python3 scripts/batch_read_pdfs.py paper-temp/ --output 文献库全文.md

# 方案 B: 强制批量 + 8 进程 + 独立 .txt
python3 scripts/batch_read_pdfs.py paper-temp/ --workers 8 --scheme b --txt-dir paper-txt/

# 方案 A: 按章节提取指定 PDF（文献量 <20 篇时或手动指定）
ls paper-temp/ | grep spray > chapter_pdfs.txt
python3 scripts/batch_read_pdfs.py paper-temp/ --file-list chapter_pdfs.txt --scheme a --output 章节文献.md
```

脚本根据文献量自动切换方案：<20 篇提示按需精读，≥20 篇全量并行提取。默认 6 进程。

该脚本使用 PyMuPDF 并行提取 PDF 文本，输出为结构化的 Markdown 文件（每篇文献一个章节，含 DOI、全文），供 LLM 快速阅读。

### 论文结构模板

```
1. 标题与摘要（中英文双语）
   - 标题：反映核心贡献，15-20 字
   - 中文摘要：300-500 字，背景→问题→方法→关键定量结果→意义
   - English Abstract：150-300 words，结构与中文对齐但独立撰写，
     非机械翻译——措辞和句式独立组织
   - 关键词：中文 3-5 个，英文 3-5 个，与摘要一致

2. 引言
   - 研究背景与动机
   - 研究现状与 gap
   - 主要贡献（3-5 条）
   - 论文组织说明

3. 相关工作 / 文献综述
   - 按主题分组评述
   - 与本文方法对比
   - 明确本文定位

4. 方法 / 系统设计
   - 方案详细描述
   - 架构/流程图
   - 关键算法与设计决策

5. 实验与结果
   - 实验设置与数据集
   - 评价指标
   - 实验结果（图表）
   - 分析与讨论

6. 结论与展望
   - 贡献总结
   - 局限性
   - 未来工作

7. 参考文献
```

### 学术写作规范

**语气与表达：**
- 正式、客观、精确的语言
- 第三人称叙述
- 已建立事实用现在时，具体研究用过去时
- 首次使用缩写时全称："物理信息神经网络（PINN）"
- 定量描述，避免模糊用词

**论证逻辑：**
- 动机 → 问题 → 方案 → 验证 的递进结构
- 明确与已有工作的对比："与 [X] 的不同之处在于..."
- 坦诚讨论局限性与不足

### 引用格式

| 格式 | 适用场景 | 示例 |
|------|----------|------|
| 编号引用 | IEEE 会议/期刊 | "...研究[1, 2]表明..." |
| 作者-年份 | Elsevier / Springer | "...研究 (Zhang, 2023) 表明..." |
| 脚注引用 | 某些期刊 | "...研究表明¹" |

### 格式说明

**IEEE 格式：**
- 双栏排版，Times New Roman
- 标题 24pt 粗体，正文 10pt
- 章节编号：1. → 1.1 → 1.1.1

**Elsevier 格式：**
- 单栏/双栏可选
- 通常使用模板文件
- 参考文献按作者姓名排序

**通用规范：**
- 图表有编号和标题（图下图题，表上表题）
- 公式用编号引用
- 参考文献 15-30 条为宜，涵盖近 5 年核心文献

### 产出文件

- `论文初稿.md` — 含完整结构和参考文献的初稿

---

### 7d. 同行评审仿真（质量门）

初稿完成后，在进入润色前增加一轮仿真同行评审，从 5 个维度评估初稿质量：

| 维度 | 权重 | 检查要点 |
|------|------|----------|
| 原创性（Originality） | 20% | 研究问题是否有新意？贡献是否清晰且区别于已有工作？ |
| 方法严谨性（Rigor） | 25% | 实验/仿真设置是否合理？控制变量是否明确？样本量是否充分？ |
| 证据充分性（Evidence） | 25% | 结论是否有充分数据支撑？图表是否与论证一致？统计方法是否正确？ |
| 论证连贯性（Coherence） | 15% | 逻辑链是否完整？gap → 方法 → 结果 → 结论是否自洽？ |
| 写作质量（Writing） | 15% | 表达是否清晰？术语是否统一？有无明显 AI 痕迹？ |

**流程：**
1. 每维度给出 0-10 评分 + 具体问题定位（标注到章节/段落）
2. 针对评分 < 6 的维度提供修改建议
3. **限 2 轮修改**——第 1 轮根据评审意见修改，第 2 轮验证
4. 第 2 轮后仍未解决的问题 → 标注为"Acknowledged Limitations"
5. 评分低于 5 的维度 → 建议回到 Step 1-6 对应环节补足

> 评审完成后进入 Step 8 润色。如需先解决评审指出的重大问题，在 Step 7 内迭代后再推进。

---

> **下一步 → Step 8：** 同行评审通过后，进入精炼润色、去 AI 痕迹，提升至可投稿水平。

## Step 8: 论文润色

对 Step 7 产出的论文初稿进行精炼、润色、去 AI 痕迹，**同时注入人味**，提升至可投稿水平。

核心能力：
- 逐句精修，输出 before/after/reason 对照表
- 学术写作规范、章节风格指南
- 中英文通用润色、批量处理
- 去 AI 痕迹 + 注入人味（29 种 AI 模式识别 + 语音校准）

---

### 1. 润色分层架构（由浅入深）

润色不是一次过的事，分 4 个层次逐层推进：

```
Level 1: 表面清理  → 拼写、语法、标点、缩写统一
Level 2: 结构优化  → 章节逻辑、段落衔接、论证递进
Level 3: 去 AI 化  → 29 种 AI 痕迹识别与清除（详见下文）
Level 4: 注入人味  → 人话校准、语音注入、有温度的学术表达
```

---

### 2. Level 1 — 表面清理

| 类型 | 检查项 | 修正方式 |
|------|--------|----------|
| 拼写 | 英文字母拼写错误 | 自动修正 |
| 语法 | 主谓一致、时态、冠词、介词 | 修正 + 标出原因 |
| 标点 | 中英文标点混用、逗号连接句 | 统一为英文标点 |
| 缩写 | 首次出现未全称、前后不一致 | 补全或统一 |

**输出格式**（借鉴 academic-paragraph-refiner 的 before/after/reason 表格）：

| Original | Modified | Reason |
|----------|----------|--------|
| The experiment was conducted by us | We conducted the experiment | Passive → active, clearer agent |
| It is important to note that the method | The method | Filler phrase removed |

> **原则：** 不改术语和专有名词。仅展示被修改的句子部分，未改部分不列出。

---

### 3. Level 2 — 结构优化

#### 3.1 章节风格指南（from academic-writing-refiner）

| 章节 | 风格要求 | 检查要点 |
|------|----------|----------|
| **摘要** | 自包含，150–250 字。问题→方法→关键结果（带数据）→意义。无引用，无未定义缩写 | 是否每句话都有信息量？能否独立成文？ |
| **引言** | 问题→Gap→贡献→结果预览→论文组织。读者第一页内应明白你做了什么、为什么重要 | 贡献 3–5 条，每条是否有对应章节？ |
| **相关工作** | 按主题分组，不要按论文罗列（避免 "X did A. Y did B."）。每组末尾区别本文工作 | 是否有"与 [X] 的不同之处在于..."句式？ |
| **方法** | 按逻辑顺序展开。先定义符号再用公式。公式旁边要有文字直觉解释。图表在首次引用后出现 | 符号是否在公式前已定义？ |
| **实验** | 以研究问题或假设开头 → 实验设置 → 结果 → 讨论。图表须自包含（图下有图题） | 是否回答了 Level 3 |
| **结论** | 总结贡献（不是重述全文），诚实说明局限，提出具体未来方向 | 是否有具体的未来方向而非套话？ |

#### 3.2 句子级优化

**六大常见问题：**

| 问题 | 检查方式 | 示例 |
|------|----------|------|
| 冗长句 | 超过 35 个词的句子考虑拆分 | 修正 |
| 名词堆叠 | 3 个以上名词连用需拆开 | "multi-task learning based pre-trained language model fine-tuning approach" → 用介词拆开 |
| 模糊指代 | "This shows that..." — "This" 指什么？ | 明确指代对象 |
| 悬垂修饰 | "Using gradient descent, the loss decreases" → 谁在用？ | "Using gradient descent, we minimize the loss" |
| 孤儿声明 | 声称性能但没有实验/引用支撑 | 补引用或删 |
| 过渡断裂 | 段与段之间无逻辑连接 | 加过渡句连接上一段的结论与本段的起点 |

#### 3.3 句长波动与段落节奏

| 检查项 | 问题描述 | 修正方式 |
|--------|----------|----------|
| **句长波动度（burstiness）** | 连续 5 句长度在 ±3 词以内 → 人工节奏模式 | 插入短句（≤10 词）打断，或将两句合并为复合句 |
| **段落长度均匀化** | 全文每段 4-5 句，长度接近 → AI 强迫节奏 | 自然变化 2-8 句/段，短段强调，长段展开论证 |
| **同义替换综合征** | 同一概念在一段内用 3+ 个不同词轮换（"模型→框架→方法→范式"） | 统一术语，重复使用比同义轮换更清晰 |
| **二元对比过度** | "不是 X，而是 Y" 句式全文出现超过 2 次 | 第 1 次可用，后续直接表达结论即可 |
| **内联标题列表** | 列表项以粗体标题+冒号开头（**X:** desc） | 将描述融入正文，或去掉加粗前缀 |

**句长波动度目标（分章不同）：**

| 章节 | 波动度 | 说明 |
|------|--------|------|
| 摘要 | 中等 | 平实稳健，关键结果用短句突出 |
| 引言 | 高 | 短句开头抓注意，长句展开背景 |
| 方法 | 低~中 | 流程性描述自然平稳 |
| 结果 | 中 | 关键发现用短句，详细描述用长句 |
| 讨论 | 最高 | 短句强调结论，长句做分析解读 |

---

### 4. Level 3 — 去 AI 痕迹（核心）

基于 [humanizer](https://github.com/blader/humanizer) 的 29 种 AI 模式识别体系，覆盖 5 大类模式。

#### 4.1 内容模式（Content Patterns）

##### P1: 过度强调重要性、意义、趋势

**警示词：** stands/serves as, a testament/reminder, a vital/significant/crucial/pivotal/key role/moment, underscores/highlights its importance, reflects broader trends, symbolizing its ongoing/enduring/lasting, setting the stage for, marking/shaping the, represents/marks a shift, key turning point, evolving landscape, indelible mark

**问题：** LLM 写作会系统性地为无意义的事情套上宏大叙事。

> ❌ "The establishment of the laboratory in 2005 marked a pivotal moment in the evolution of thermal management research, reflecting broader industry trends toward electrification."
> ✅ "该实验室成立于 2005 年，最初研究风冷散热方案。"

##### P2: 空泛的 -ing 结尾分析

**警示词：** highlighting/underscoring/emphasizing..., ensuring..., reflecting/symbolizing..., contributing to..., cultivating/fostering..., encompassing..., showcasing...

**问题：** AI 喜欢在句子末尾挂一个 -ing 分词短语来伪造深度。

> ❌ "The system achieves 92% efficiency, showcasing the potential of the proposed approach, highlighting its superiority over existing methods."
> ✅ "The system achieves 92% efficiency, outperforming the baseline by 5.3%."

##### P3: 广告语式风格

**警示词：** boasts a, vibrant, rich（喻义）, profound, enhancing its, showcasing, exemplifies, commitment to, nestled, in the heart of, groundbreaking（喻义）, renowned, breathtaking, must-visit, stunning, novel（无数据支撑时）

> ❌ "This groundbreaking approach, nestled at the intersection of machine learning and thermal engineering, showcases a profound commitment to innovation."
> ✅ "该方法将物理信息神经网络（PINN）与 CFD 仿真结合，在预测精度上提升 12%。"

##### P4: 模糊归因 / 推诿措辞

**警示词：** Industry reports, Observers have cited, Experts argue, Some critics argue, several sources/publications（当无具体引用时）

> ❌ "Experts believe this approach holds significant promise for future battery thermal management systems."
> ✅ "Liu et al. (2024) reported that this approach reduced peak temperature by 8.5°C in 100A discharge tests."

##### P5: "挑战与展望"公式化章节

**警示词：** Despite its... faces several challenges..., Despite these challenges, Challenges and Legacy, Future Outlook

> ❌ "Despite these challenges, the proposed method continues to show promise."
> ✅ "实际测试中还发现两个局限：① 高环境温度（>45°C）下泵功消耗增加 30%；② 冷板表面温度均匀性随流量增大先改善后恶化。这些将在后续工作中重点优化。"

##### P6: 规则三段论（Rule of Three）

**问题：** LLM 总是把所有东西列成三组。

> ❌ "The system offers enhanced performance, improved reliability, and greater efficiency."
> ✅ "The system achieves 94% efficiency with 99.2% uptime——比基线方案分别高 5% 和 1.8%。"

#### 4.2 语言语法模式（Language & Grammar）

##### P7: AI 高频词

**高频词：** Actually, additionally, align with, crucial, delve, emphasizing, enduring, enhance, fostering, garner, highlight（动词）, interplay, intricate/intricacies, key（形容词）, landscape（抽象名词）, pivotal, showcase, tapestry（抽象名词）, testament, underscore（动词）, valuable, vibrant

> ❌ "Additionally, delve into the intricate interplay between thermal conductivity and flow dynamics."
> ✅ "还分析了热导率与流态之间的关系。"

##### P8: 系动词回避（Copula Avoidance）

**警示词：** serves as/stands as/marks/represents [a], boasts/features/offers [a]

**问题：** AI 总是不愿用 "is/are"，要用更复杂的词替代。

> ❌ "The system serves as an effective solution for thermal management."
> ✅ "该系统是热管理的有效方案。"

##### P9: 否定平行结构 + 尾部否定残留

**警示词：** Not only... but also..., It's not just about X; it's about Y

> ❌ "It's not merely an optimization problem; it's a paradigm shift."
> ✅ "这不仅是一个优化问题，更涉及系统级的设计策略。"

> ❌ "The parameters are automatically selected, no manual tuning."
> ✅ "参数自动选择，无需手动调节。"

##### P10: 同义词轮换（Elegant Variation）

**问题：** AI 有重复惩罚机制，导致过度使用同义词。

> ❌ "The algorithm processes data. The procedure handles features. The method computes outputs."
> ✅ "该算法处理数据、提取特征并计算输出。"

##### P11: 虚假范围（False Ranges）

**警示词：** from X to Y（X 和 Y 不在同一个有意义标度上）

> ❌ "From single-cell cooling to full battery pack thermal management, from lab-scale experiments to industrial deployment..."
> ✅ "方法覆盖从单电池到整包的热管理设计。"

#### 4.3 风格模式（Style Patterns）

##### P12: Em Dash 滥用

**问题：** LLM 的破折号使用频率远高于人类。

> ❌ "The cooling efficiency—at 94%—exceeds the baseline—which maxes out at 89%."
> ✅ "冷却效率为 94%，基线方案最高为 89%。"

##### P13: 粗体过度使用

**问题：** AI 机械性地加粗关键词。

> ❌ "It blends **CFD simulations**, **experimental validation**, and **machine learning**."
> ✅ "它结合了 CFD 仿真、实验验证和机器学习。"（正文不加粗）

##### P14: 内联标题列表

**问题：** 列表项以粗体标题+冒号开头。

> ❌ "- **User Experience:** The interface has been redesigned."
> ✅ "- 界面重新设计，将关键参数放在操作面板顶部。"

##### P15: 标题大小写

**问题：** AI 喜欢把英文标题所有实词大写（Title Case）。学术论文推荐 Sentence case。

> ❌ "## A Novel Approach For Thermal Management Of High-Power Batteries"
> ✅ "## A novel approach for thermal management of high-power batteries"

##### P16: 表情符号

**问题：** AI 在标题或列表前加 emoji。

> ❌ "🚀 **Key Results:** 92% efficiency achieved"
> ✅ "**关键结果：** 效率达到 92%"

##### P17: 花引号 vs 直引号

> ❌ "The system is "highly efficient.""（花引号）
> ✅ 'The system is "highly efficient."'（直引号）

#### 4.4 交流模式（Communication Patterns）

##### P18: 协作式交际痕迹

**警示词：** I hope this helps, Of course!, Certainly!, You're absolutely right!, Would you like..., let me know, here is a...

> ❌ "Here is an overview of the proposed method. I hope this helps!"
> ✅ "下面对本文方法作一概述。"

##### P19: 知识截止日期声明

**警示词：** as of [date], Up to my last training update, While specific details are limited, based on available information...

> ❌ "While specific details about the simulation parameters are not extensively documented..."
> ✅ "文献中该仿真参数未完整公开，但根据其表 2 中 Reynolds 数范围可反推..."

##### P20: 奉承语气

**问题：** 过度积极的讨好式语言。

> ❌ "Great question! You raise an excellent point about the thermal boundary conditions."
> ✅ "关于热边界条件的问题确实关键。"

#### 4.5 填充与模棱两可模式（Filler & Hedging）

**常用填充词替换：**

| 原文 | 替换为 |
|------|--------|
| In order to | To |
| Due to the fact that | Because |
| At this point in time | Now |
| In the event that | If |
| The system has the ability to | The system can |
| It is important to note that | （删除） |
| It should be mentioned that | （删除） |
| It is worth noting that | （删除） |
| It is noteworthy that | （删除） |

**过度变通：**

> ❌ "It could potentially possibly be argued that the method might have some positive effect."
> ✅ "该方法表现出积极效果。"（或："该方法使效率提升 5%。"）

**空洞收尾：**

> ❌ "The future looks bright for this approach. Exciting times lie ahead as research continues."
> ✅ "该方法已在 5 家厂商的样机中完成验证，后续将聚焦于量产工艺优化。"

**P27: 权威论断套话**

**警示词：** The real question is, at its core, in reality, what really matters, fundamentally, the deeper issue, the heart of the matter

> ❌ "At its core, what really matters is whether the cooling system can maintain uniform temperature."
> ✅ "核心问题是冷却系统能否维持均匀温度。"

**P28: 预报式写作**

**警示词：** Let's dive in, let's explore, let's break this down, here's what you need to know, now let's look at

> ❌ "Now let's dive into the experimental setup. Here's what you need to know."
> ✅ "实验装置由三个主要部分组成：一个 3 kW 加热器、一个冷板式换热器和一套循环泵组。"

**P29: 碎片化标题**

**问题：** 标题后跟一句空泛的单行段落。

> ❌ "## Results\n\nResults are important. When analyzing the data..."
> ✅ "## 实验结果\n\n在 5 kW 加热功率下，本文提出的冷板方案将电池表面最高温度控制在 42.3°C..."

---

### 5. Level 4 — 注入人味（从 humanizer 的 Personality & Soul）

去 AI 化只是及格线。好的学术论文不止正确，还要让读者感到有人在认真思考。

#### 5.1 识别"既准确又无味"的问题

> ❌ 这段文字语法正确、术语统一、没有 AI 套话——但读起来像机器生成的。
> - 每句话长度和结构都差不多
> - 只有事实陈述，没有观点
> - 没有对不确定性或复杂性的诚实表达
> - 没有第一人称（适当场合下）

#### 5.2 如何注入人味

| 技巧 | 示例 (before → after) |
|------|----------------------|
| **有观点** | "The results show the method is effective." → "坦白说，效果超出预期——5 kW 功率下温升只有 8°C，比我们最乐观的仿真还低 2°C。" |
| **变节奏** | 全篇统一结构 → 短句——长句——短句，交替节奏 |
| **承认复杂性** | "This approach has advantages and disadvantages." → "有利有弊：冷却效果很好，但泵耗涨了 30%。" |
| **适当用"我们"** | "It was observed that..." → "我们注意到..."（非正式部分）/ "实验观察到..."（正式部分） |
| **诚实表达** | "The results are clear and conclusive." → "结果呈现清晰的趋势，但受限于样本量（n=3），尚不足以做统计推断。" |
| **具体感受** | "This is concerning." → "每次看到压差高达 15 kPa 时，都不禁担心泵的使用寿命。" |

#### 5.3 语音校准（Voice Calibration）

当用户提供"这是我的写作风格"的样本时，改为按此风格来润色：

1. **读样本**——观察其句长模式、用词水平、段落开头方式、标点习惯、常用句式
2. **校准**——润色时不替换成通用好英语，而是替换成样本里的风格
3. **无人声样本时** — 按默认策略处理（自然的混合节奏 + 有观点的学术表达）

---

### 6. 润色工作流（6 步法）

```
Phase 1: 理解上下文
  → 判断是全文、某章、还是单段
  → 确定目标期刊/会议风格（Nature？IEEE？Elsevier？）
  → 了解当前阶段（初稿需结构调整，终稿需逐句打磨）

Phase 2: Level 1 表面清理
  → 拼写 + 语法 + 标点 + 缩写统一
  → 输出 before/after/reason 表格

Phase 3: Level 2 结构优化
  → 章节逻辑检查 → 段落衔接优化 → 句子级精简
  → 输出每章主要结构性修改概述

Phase 4: Level 3 去 AI 痕迹
  → 扫描 29 种 AI 模式
  → 替换套话、空洞修饰、公式化表达
  → 自我审计: "这段文字还有哪里一看就是 AI 写的？"→ 改

Phase 5: Level 4 注入人味
  → 检查是否有观点、有节奏、有温度
  → "如果有人在读这段，他们会觉得作者是个真人吗？"

Phase 6: 终验
  → 术语一致性
  → 引用完整性（每处 [1] 是否有对应参考文献条目）
  → 格式合规
  → 输出润色版本 + 修改说明
```

---

### 7. 交互方式

与用户逐章确认润色方案。不同层级有不同汇报方式：

**Level 1 修改（语法/拼写）** — 不逐一说明，用表格汇总

**Level 2-3 修改（结构/去 AI）** — 标注每处重要修改的原因

```
> 第 3 章精炼完成。主要改动：
>
> Level 2 结构：
>   - 合并段落 2-3（两段都在描述仿真设置，重复内容已去重）
>   - 实验流程的叙述顺序改为"建立模型→设置参数→运行→后处理"
>   - 添加了段落过渡句"下面分析影响最大的三个参数"
>
> Level 3 去 AI：
>   - "leveraging PINN" → "using PINN" （P7 — AI 高频词）
>   - "showcasing the effectiveness" → 整句删（P2 — 空洞 -ing）
>   - "It should be noted that the baseline" → 直接陈述（填充词删除）
>   - "Despite these challenges, the method..." → 替换为具体局限描述（P5 — 公式化挑战）
>
> 是否接受？需要调整某些修改吗？
```

**Level 4 注入人味** — 示例对比展示

```
> 第 5 章开始部分加了点"人味"：
>
> ❌ 原句："The cooling performance was analyzed under various conditions."
> ✅ 润色："我们测试了 5 种工况——从 30°C 常规模拟到 55°C 极端环境——结果有些出乎意料。"
>
> 这样改合适吗？还是保持更正式的表达？
```

---

### 8. 产出文件

- **`论文润色稿.md`** — 标注所有 Level 1–4 修改的润色版本
- **`论文润色修改对照表.md`**（可选）— 仅 contain 修改项的 before/after/reason 表格（借鉴 academic-paragraph-refiner 格式）
- **`论文终稿.docx` / `.pdf`** — 格式化最终版本（可选）
