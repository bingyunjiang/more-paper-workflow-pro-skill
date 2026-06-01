# 📚 More Paper Workflow Pro Skill `v1.0.0-20260601`

[![Claude Code Skill](https://img.shields.io/badge/Claude_Code-Skill-6B46F7?logo=anthropic&logoColor=white)](https://github.com/bingyunjiang/More-paper-workflow-pro)
[![Hermes](https://img.shields.io/badge/Hermes-Skill-FF6B35?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0tMSAxNy45M2MtMy45NS0uNDktNy0zLjg1LTctNy45MyAwLS40NC4wNC0uODcuMTEtMS4yOWwxLjg4IDEuODhjLjEuMTEuMjYuMjYuNDcuNDQgMi4yMiAxLjk3IDMuMjYgMi44NyAzLjI2IDIuODcuMjYgMCAuNTItLjEzLjc4LS4zOSAxLjI2LTEuMjYgMS4xMi0zLjI5LS4zMy00Ljg2bC0xLjg5LTEuODljLS4yMi0uMjItLjMzLS4zMy0uNDQtLjQ0LS40Ny0uNDctLjQ3LTEuMjQgMC0xLjcxLjQ3LS40NyAxLjI0LS40NyAxLjcxIDBsLjQ0LjQ0Yy4wMi4wMi4wNC4wNCAxLjQyIDEuNDJsLjIyLS4wNGMxLjY4LS4zMSAzLjI0LjQ2IDMuOTcgMi4wMi0xLjU5IDEuMTktMy4yOSAxLjg5LTQuOTcgMi4wOHoiLz48L3N2Zz4=)](https://github.com/nousresearch/hermes-skills)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-00B4D8?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0tMSAxNy45M2MtMy45NS0uNDktNy0zLjg1LTctNy45MyAwLS40NC4wNC0uODcuMTEtMS4yOWwxLjg4IDEuODhjLjEuMTEuMjYuMjYuNDcuNDQgMi4yMiAxLjk3IDMuMjYgMi44NyAzLjI2IDIuODcuMjYgMCAuNTItLjEzLjc4LS4zOSAxLjI2LTEuMjYgMS4xMi0zLjI5LS4zMy00Ljg2bC0xLjg5LTEuODljLS4yMi0uMjItLjMzLS4zMy0uNDQtLjQ0LS40Ny0uNDctLjQ3LTEuMjQgMC0xLjcxLjQ3LS40NyAxLjI0LS40NyAxLjcxIDBsLjQ0LjQ0Yy4wMi4wMi4wNC4wNCAxLjQyIDEuNDJsLjIyLS4wNGMxLjY4LS4zMSAzLjI0LjQ2IDMuOTcgMi4wMi0xLjU5IDEuMTktMy4yOSAxLjg5LTQuOTcgMi4wOHoiLz48L3N2Zz4=)](https://github.com/openclaw/openclaw)
[![Python](https://img.shields.io/badge/Python-3.9_~_3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/macOS_|_Windows_|_Linux-lightgrey?logo=apple)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

完整学术文献检索和写作工作流（8 步法）：①交互式确定研究主题 → ②生成大纲/关键词 → ③制定检索方案 → ④多渠道检索+评分 → ⑤多轮下载（Sci-Hub→SD） → ⑥Zotero 文库管理（架构生成+PDF 导入） → ⑦论文写作 → ⑧论文润色。

---

## 📖 简介

**More Paper Workflow Pro Skill** 是一套完整的学术文献工作流工具链，覆盖从研究方向确定到论文润色投稿的全过程。10 个 Python CLI 脚本 + 1 个共享模块，可独立使用或接入 Hermes/OpenClaw/Claude Code 等 AI Agent 实现对话式编排。

### 一句话概括

> 定题 → 检索 → 评分 → 下载 → 入库 → 写作 → 润色，一站式完成学术研究文献工作。

### 为什么需要这个工具

学术论文写作的文献准备工作通常十分繁琐：跨多个数据库手动检索、逐篇判断相关性、绕过出版商反爬下载 PDF、手动整理 Zotero 文库、写作时来回翻找引用原文。本工具将这一流程自动化，把研究者从重复劳动中解放出来。

### 核心能力

**🔧 文献检索与筛选（Step 1-4）**
- AI 辅助交互式定题，5 轮对话厘清研究方向
- Semantic Scholar / Crossref / OpenAlex 三源并行检索，DOI 去重合并
- 五维相关性评分（主题、方法、质量、时效、引用），T1-T4 自动分级

**📥 PDF 批量下载（Step 5）——核心突破**
- 通过 Chrome/Edge **CDP 协议**操控真实浏览器，绕过 Cloudflare/Akamai 反爬
- 两轮策略：Sci-Hub（老论文，免登录）→ ScienceDirect（新论文，需机构认证）
- 自动检测 13 个 Sci-Hub 镜像站可用性，仅使用可连接的站点
- Chrome + Edge **双浏览器并行下载**，速度翻倍，实际测试每分钟达下载5篇。
- 支持 **IP 认证**（全自动零干预）和 **SSO 机构登录**（仅首次需手动登录）
- 会话过期自动杀进程→重建 profile→重启浏览器→续跑，无人值守
- **实测 96% 成功率**（185 篇 SD 论文下载 180 篇）

**📚 Zotero 文库管理（Step 6）**
- 按论文大纲自动生成集合结构和标签方案
- 支持手动拖拽导入或 Zotero MCP 对话式导入
- 环境检测脚本一键诊断 Zotero 配置状态

**✍️ 论文写作与润色（Step 7-8）**
- 逐章按 Zotero 分类读取 PDF 原文作为知识库，交互确认引用
- 直接读 PDF 抑制大模型幻觉——引用精确性高于 RAG 分块方案
- PyMuPDF 多进程批量提取（<20 篇按需精读 / ≥20 篇全量并行）
- 论文润色：结构精炼 + 术语统一 + 去 AI 痕迹 + 引用校验

### 工程品质

| 特性 | 说明 |
|------|------|
| 🖥️ **全平台零配置** | macOS / Windows / Linux 自动检测 Chrome/Edge 路径，`CHROME_PATH` 环境变量可覆盖 |
| 📦 **共享代码模块** | `cdp_utils.py` 统一封装 CDP 连接、标签管理、PDF 捕获、跨平台浏览器管理、依赖检查 |
| 🔍 **依赖自检** | 启动时检查 `websocket-client`/`PyMuPDF`，缺失即打印安装指令 |
| 🧩 **分层可拆** | 每个 Step 独立可运行——有 DOI 可直接从 Step 5 开始，有 PDF 可直接从 Step 6 开始 |
| 💰 **零 API 费用** | Semantic Scholar / Crossref / OpenAlex / Sci-Hub 全部免费 |
| 🔄 **断点续跑** | PII 解析每 5 条增量保存；PDF 下载检测已有文件自动跳过 |
| 🛡️ **Cloudflare 应对** | 检测到 Turnstile 验证自动等待 60s 自行通过；IP 模式基本无需手动干预 |
| 🐍 **兼容性** | Python 3.9-3.14；纯标准库 + websocket-client 单一必选依赖 |

> 本项目的 Zotero MCP集成基于 [54yyyu/zotero-mcp](https://github.com/54yyyu/zotero-mcp) 项目，感谢原作者的开源贡献。

## ✨ 功能特性

| # | 功能 | 说明 |
|---|------|------|
| 1 | **交互式研究主题定义** | 多轮对话厘清研究方向，产出结构化主题文档 |
| 2 | **自动生成论文大纲与关键词** | 基于研究主题生成章节结构、中英文关键词清单 |
| 3 | **结构化检索方案设计** | 拆分子课题、构建关键词组合、选定检索源 |
| 4 | **多渠道论文检索** | Semantic Scholar / Crossref / OpenAlex 三源并行，去重合并 |
| 5 | **相关性评分与筛选** | 五维评分（主题、方法、质量、时效、引用），T1-T4 分级 |
| 6 | **多轮批量 PDF 下载** | Sci-Hub CDP → ScienceDirect CDP 两轮覆盖，成功率 96%+ |
| 7 | **Chrome + Edge 并行下载** | 双浏览器独立会话，速度翻倍，自动跳过 Cloudflare |
| 8 | **全自动断点续跑** | 会话过期自动杀进程→重建 profile→重启浏览器→继续下载 |
| 9 | **生成 Zotero 文库架构** | 按论文大纲自动生成集合结构和标签方案 |
| 10 | **PDF 批量导入 Zotero** | 按 DOI 导入 + 附加 PDF，自动分类 |
| 11 | **PDF 全文批量提取** | PyMuPDF 多进程并行提取，A/B 方案按文献量自动切换 |
| 12 | **跨平台浏览器管理** | `CHROME_PATH`/`EDGE_PATH` 环境变量或 `--browser-path` 参数覆盖 |
| 13 | **依赖自动检测** | 启动时检查 `websocket-client`/`PyMuPDF`，缺失即打印安装指引 |

## 🏆 核心优势

- **一站到底** —— 8 步全流程覆盖，从定题到润色一站式完成
- **反爬突破** —— 真实浏览器 CDP 协议绕过 Cloudflare/Akamai，96% 下载成功率
- **全平台零配置** —— Chrome/Edge 路径自动检测，macOS/Windows/Linux 即装即用
- **分层可拆** —— 每个 Step 独立运行，按需组合，不必从头开始
- **零 API 费用** —— Semantic Scholar / Crossref / OpenAlex / Sci-Hub 全部免费
- **双浏览器并行** —— Chrome + Edge 自动检测，有则加速，无则单浏览器正常运行
- **断点续跑** —— 中断恢复不重复工作，支持无人值守批量下载
- **抑制幻觉** —— 直接读 PDF 原文而非向量分块，引用精确性远高于 RAG 方案

###为什么选直接读文献PDF： 直接读 PDF vs RAG 分块

论文写作中引用精确性高于一切。本工具采用**直接读 PDF 原文**，而非 RAG 向量分块：

| 对比项 | 本工具：直接读 PDF | RAG 分块方式 |
|--------|-------------------|-------------|
| 引用精确性 | 整篇读取，上下文完整 | 分块后可能丢失上下文 |
| 每章文献量 | 按 Zotero 分类读取全部归属 PDF | 批量建索引，实际用得少 |
| 幻觉抑制 | 交互确认 + 读原文，源头保证 | 召回不完整时仍可能编造 |
| 部署成本 | 零依赖，直接文件读取 | 需 embedding 模型 + 向量库 |
| 维护成本 | 随时按需读取，无需预处理 | PDF 更新需重建索引 |

> 文献量巨大（>200 篇）时才值得做 RAG 预处理。本工具的 Step 4 检索文献表 + Step 6 Zotero 架构已完成分类，写作时按需精读即可。

---

## 📋 工作流一览

```
Step 1: 交互式确定研究主题           → 研究主题.md
Step 2: 生成论文大纲与关键词         → 大纲关键词.md
Step 3: 生成文献检索方案             → 检索方案.md
Step 4: 多渠道检索+相关性评分筛选     → 检索文献表.md / .xlsx
Step 5: 多轮批量下载（Sci-Hub → SD） → paper-temp/ PDFs
Step 6: Zotero 文库管理              → zotero-架构.md + Zotero 桌面端
Step 7: 论文写作                     → 论文初稿.md / .docx
Step 8: 论文润色                     → 论文润色稿.md
```

---

## 🚀 安装

### 方式一：Hermes/OpenClaw/Claude Code Skills

```bash
pip install hermes-agent
hermes skill install more-paper-workflow-pro
```

### 方式二：独立脚本

```bash
git clone https://github.com/bingyunjiang/More-paper-workflow-pro.git
cd more-paper-workflow-pro
pip install websocket-client
```

### 系统要求

| 组件 | 要求 | 说明 |
|------|------|------|
| 操作系统 | macOS / Windows 10+ / Linux | 全平台支持 |
| Python | 3.9+（推荐 3.11+） | 兼容至 3.14 |
| 浏览器 | Google Chrome（必选） | 自动检测路径，或设 `CHROME_PATH` 环境变量 |
| 浏览器（可选） | Microsoft Edge | 并行下载加速，自动检测或设 `EDGE_PATH` |
| Python 依赖 | `pip install websocket-client` | CDP 协议通信（脚本启动时自动检查） |
| Python 依赖（可选） | `pip install pymupdf` | Step 8 批量 PDF 文本提取 |
| 机构权限 | ScienceDirect 访问 | IP 或 SSO/CARSI/Shibboleth（仅 SD 下载需要） |

### 跨平台浏览器检测

脚本自动查找 Chrome/Edge，无需手动配置路径。检测顺序：

1. 环境变量 `CHROME_PATH` / `EDGE_PATH`
2. 系统 PATH（`shutil.which`）
3. 平台默认安装路径

未找到浏览器时会打印安装指引。也可以手动指定：

```bash
python3 scripts/auto_sd_downloader.py --browser-path "/custom/path/chrome"
```

---

## 📖 使用指南

### Step 1: 确定研究主题

与 AI 交互对话，厘清研究方向：

```
> 我正在研究某个方向，请帮我厘清研究方向。
```

**产出：** `研究主题.md`

```markdown
# 研究主题
- 领域：研究方向所属领域
- 研究问题：具体研究问题
- 方法论：采用的技术路线
- 应用场景：应用场景描述
```

### Step 2: 生成论文大纲与关键词

基于研究主题生成章节结构和关键词清单。

**产出：** `大纲关键词.md`

### Step 3: 生成检索方案

```markdown
# 检索方案
| 编号 | 子课题 | 关键词 | 来源 |
|------|--------|--------|------|
| S1 | 子课题一 | keyword1, keyword2 | Crossref |
| S2 | 子课题二 | keyword3, keyword4 | Semantic |
| S3 | 子课题三 | keyword5, keyword6 | Semantic |
```

**产出：** `检索方案.md`

### Step 4: 检索与评分

```bash
# 按子课题检索
python3 scripts/search_by_topic.py "cold plate liquid cooling optimization" --limit 50 --output s1.txt

# 合并结果 → 五维评分 → 分级
# ⭐ T1 ≥20 / 📘 T2 15-19 / 📄 T3 10-14 / ⬜ T4 <10
```

**产出：** `检索文献表.md`

### Step 5: 多轮下载

#### 第 1 轮：Sci-Hub（免登录，老论文更有效）

```bash
# 1. 启动 Chrome CDP 模式
# macOS:
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9223 --remote-allow-origins=http://127.0.0.1:9223 \
  --no-first-run --no-default-browser-check --disable-blink-features=AutomationControlled \
  --user-data-dir=/tmp/chrome_profile about:blank

# Windows:
# "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
#   --remote-debugging-port=9223 --remote-allow-origins=http://127.0.0.1:9223 ^
#   --no-first-run --no-default-browser-check --user-data-dir=%TEMP%\chrome_profile about:blank

# 2. 自动测试镜像站 + 下载
python3 scripts/download_via_scihub.py 检索文献表.md -o download/paper-temp
```

#### 第 2 轮：ScienceDirect（需机构认证）

| 方式 | 适用场景 | 命令 |
|------|----------|------|
| **A: 全自动** | 机构 IP 认证（校园网/VPN） | `python3 scripts/auto_sd_downloader.py -o download/paper-temp` |
| **B: 手动登录** | 机构 SSO 账号登录 | 先手动启动 Chrome CDP → 登录 SD → 再运行脚本 |

> **关于 Cloudflare "Verify you are human" 验证：**
>
> | 场景 | 需手动点击？ | 说明 |
> |------|:--:|------|
> | IP 认证（校园网/VPN） | 基本不需要 | CDP 真实浏览器 + `--disable-blink-features` 标记，Turnstile 通常自动放行 |
> | SSO 机构登录 | 仅首次需要 | 第一次启动浏览器时需手动登录 + 点击验证，通过后 session cookie 保留 |
> | 会话过期自动重启 | 不需要 | 使用固定 profile 目录，cookie 持久化，重启后自动复用 |
> | Sci-Hub 下载 | 不需要 | 已预过滤可用镜像站（9/13），自动跳过有 Turnstile 拦截的站点 |
>
> 脚本检测到 Cloudflare 验证页面时会自动等待 60 秒尝试让其自行通过，超时后提示用户在浏览器窗口手动操作。

**方式 A — IP 认证（全自动）：**

```bash
# 默认: 自动检测 Chrome，没有则尝试 Edge
python3 scripts/auto_sd_downloader.py -o download/paper-temp

# 指定 Edge
python3 scripts/auto_sd_downloader.py --browser edge -o download/paper-temp

# 脚本自动：启动浏览器 → 检测 SD 访问权限 → 下载 → 会话过期自动重启
# 启动时会自动检测 IP 认证是否有效，无效则提示手动登录
```

**方式 B — SSO 机构登录（手动启动浏览器）：**

```bash
# 1. 手动启动 Chrome（或 Edge）并登录 ScienceDirect
# Chrome:
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9223 --remote-allow-origins=http://127.0.0.1:9223 \
  --no-first-run --no-default-browser-check --disable-blink-features=AutomationControlled \
  --user-data-dir=/tmp/chrome_sd_profile \
  https://www.sciencedirect.com

# 2. 在浏览器中完成机构登录 + Cloudflare 验证

# 3. 运行下载（自动检测可用浏览器，支持单浏览器运行）
python3 scripts/parallel_sd_download.py -o download/paper-temp
```

> **提示：** `parallel_sd_download.py` 会自动检测 Chrome 和 Edge 是否已在运行。只有 Chrome 也能正常工作（单浏览器模式），两个都在则并行加速。

### Step 6: 生成 Zotero 架构

```bash
python3 scripts/organize_zotero.py 大纲关键词.md --output zotero-架构.md
```

### Step 7: 导入 Zotero

**方式一：手动拖拽（推荐）**
在 Zotero 桌面端拖拽 PDF 到对应集合，Zotero 自动识别元数据。

**方式二：Zotero MCP 对话操作**
通过 `zotero_add_by_doi` 等工具直接按 DOI 导入（Hermes / OpenClaw / Claude Code 内置）。

运行 `python3 scripts/setup_zotero.py` 检测环境。

> **为什么不用 Zotero 云端上传？** Zotero 免费版仅有 300MB 文件存储，批量下载的 PDF 总量可达 1.4GB+，远超免费额度。拖拽导入的 PDF 仅保存在本地，元数据同步到云端（几乎不占空间），不影响多设备同步。同时免去了申请和配置 API Key 的步骤，降低使用门槛。

### Step 8: 论文写作

按大纲逐章写作，每章读取归属的全部 PDF 原文作为知识库，交互确认引用，标注索引。

**方案 A（<20 篇）：按需精读**
**方案 B（≥20 篇）：批量预提取**

```bash
# 方案 B: 全库预提取（自动 6 进程）
python3 scripts/batch_read_pdfs.py paper-temp/ --output 文献库全文.md
```

---

## 📂 项目结构

```
more-paper-workflow-pro/
├── README.md                         ← 本文件
├── SKILL.md                          ← Hermes / OpenClaw / Claude Code Skill 定义
├── scripts/                          ← Python 可执行脚本
│   ├── cdp_utils.py                  ← 共享 CDP 模块（浏览器管理 + 依赖检查）
│   ├── search_by_topic.py            ← Step 4  三源检索
│   ├── batch_resolve_pii.py          ← Step 5  DOI → PII 批量解析（断点续跑）
│   ├── resolve_remaining_pii.py      ← Step 5  中断后 PII 解析续跑
│   ├── download_via_scihub.py        ← Step 5  Sci-Hub CDP 下载 + 镜像检测
│   ├── parallel_sd_download.py       ← Step 5  Chrome+Edge SD 并行下载
│   ├── auto_sd_downloader.py         ← Step 5  全自动单浏览器（断点续跑）
│   ├── organize_zotero.py            ← Step 6  生成 Zotero 文库架构
│   ├── setup_zotero.py               ← Step 7  Zotero 环境检测与配置
│   └── batch_read_pdfs.py            ← Step 8  PDF 批量提取全文文本
├── references/                       ← 模板与参考数据
│   ├── literature-table-template.md  ← 含评分列的文献表格模板
│   ├── zotero-structure-template.md  ← Zotero 集合结构示例
│   └── publisher-access-matrix.md    ← 各出版商下载策略
```

## 📜 脚本速查

| 脚本 | 步骤 | 用途 | CLI |
|------|------|------|-----|
| `cdp_utils.py` | — | 共享 CDP 模块（浏览器管理、标签操作、依赖检查） | — |
| `search_by_topic.py` | 4 | 三源检索（Semantic Scholar / Crossref / OpenAlex） | ✅ |
| `batch_resolve_pii.py` | 5 | DOI → PII 批量解析，每 5 条增量保存 | ✅ |
| `resolve_remaining_pii.py` | 5 | 中断后 PII 解析续跑，跳过已完成的 | ✅ |
| `download_via_scihub.py` | 5 | Sci-Hub CDP 下载 + 13 镜像站自动检测 | ✅ |
| `parallel_sd_download.py` | 5 | Chrome + Edge SD 并行下载，各管一半 | ✅ |
| `auto_sd_downloader.py` | 5 | 全自动版：启停浏览器 + 断点续跑 + 跨平台 | ✅ |
| `organize_zotero.py` | 6 | 解析大纲关键词 → Zotero 集合结构 | ✅ |
| `setup_zotero.py` | 7 | Zotero 环境检测（MCP/API Key/桌面端） | ✅ |
| `batch_read_pdfs.py` | 8 | PyMuPDF 多进程提取，A/B 方案自动切换 | ✅ |

---

## ❓ 常见问题

<details>
<summary><b>下载时遇到 Cloudflare "Verify you are human" 怎么办？</b></summary>

**IP 认证模式下通常不需要手动操作。** CDP 协议使用真实浏览器环境，Cloudflare Turnstile 会自动放行。

如果确实遇到验证页面：
1. 脚本会自动等待 60 秒让 Turnstile 自行通过
2. 超时后，在弹出的浏览器窗口中手动点击验证框
3. 通过后 session cookie 保留，后续下载自动复用

**SSO 登录模式**首次启动浏览器时需手动完成一次登录 + 验证，之后同一 profile 下不再需要。
</details>

<details>
<summary><b>为什么不用 HTTP 库直接下载？</b></summary>
主流学术出版商均部署了 Cloudflare / Akamai 等反爬系统。CDP Chrome 通过真实浏览器环境绕过检测，是当前唯一可靠的方式。
</details>

<details>
<summary><b>需要机构订阅吗？</b></summary>
ScienceDirect 下载需要机构订阅（IP 或 SSO）。Sci-Hub 下载不需要，对 2021 年前老论文更有效。
</details>

<details>
<summary><b>需要 Hermes Agent、OpenClaw 或 Claude Code 吗？</b></summary>
**不需要。** 所有脚本都是标准 Python 脚本，可直接命令行调用。Hermes / OpenClaw / Claude Code 提供的是智能调度层，非必需。
</details>

<details>
<summary><b>电脑休眠后下载卡住了？</b></summary>
脚本有 120 秒超时保护。单篇超过 120 秒自动标记为失败并跳过，不阻塞后续。
</details>

<details>
<summary><b>Python 版本问题？</b></summary>
macOS 系统 `python3` 默认是 3.9。本工具所有脚本兼容 Python 3.9-3.14。注意 Python 3.14 禁止单行 `try: ... ; except: pass`。
</details>

---

## 📋 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| **v1.0.0-20260601** | 2026-06-01 | 首发版本：8 步全流程（定题→检索→评分→下载→入库→写作→润色） |

**v1.0.0-20260601 特性：**
- 10 个 Python CLI 脚本 + 1 个共享 CDP 模块 (`cdp_utils.py`)
- Chrome/Edge CDP 协议双浏览器并行下载，96% 成功率
- 跨平台浏览器自动检测（macOS / Windows / Linux）
- Sci-Hub + ScienceDirect 两轮下载策略，IP 认证全自动零干预
- Semantic Scholar / Crossref / OpenAlex 三源免费检索
- Zotero 文库架构自动生成 + 环境检测
- PDF 全文多进程批量提取，A/B 方案自动切换
- 依赖自检、断点续跑、Cloudflare 自动等待
- Python 3.9-3.14 兼容

---

## 📄 许可

MIT License

## 🔗 相关链接

- [Hermes Agent](https://hermes-agent.nousresearch.com)
- [Zotero](https://www.zotero.org/)
