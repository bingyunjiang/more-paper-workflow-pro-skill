---
name: more-paper-workflow-pro-skill
version: v1.0.4-20260604
description: 完整学术文献检索和写作工作流（8 步法）：①交互式确定研究主题（v2.0 增强版：阶段诊断→广度探索+预检索→深度聚焦→选题预审，借鉴 academic-mentor/nature-academic-search/deep-research/nature-reviewer 等 10 个 skill） ②生成大纲/关键词 ③制定检索方案 ④多渠道检索+评分 ⑤多轮下载（Sci-Hub→SD→IEEE） ⑥Zotero 文库管理（架构生成+PDF 导入+大纲对齐一致性调整） ⑦论文写作（4 种模式 + 中英文双边摘要 + 仿真评审质量门） ⑧论文润色（句长波动检测 + 四合一精修引擎：去 AI 痕迹 29 种模式 + 注入人味 + 章节风格指南 + before/after 对照表）
author: Dr. Jiang Bingyun（江博士）
wechat: Bingyunjiang
category: research
related_skills:
  - science-direct-cdp-pipeline: "Overlaps on CDP ScienceDirect download; this skill adds the full 8-step workflow from topic definition to paper polishing."
triggers:
  # Step 1: 确定研究主题（v2.0 增强版）
  - "确定研究主题"
  - "厘清研究方向"
  - "采用 More Paper Workflow Pro Skill，我们开始确定研究选题"
  - "Using More Paper Workflow Pro Skill, let's define our research topic"
  # Step 1a: 研究阶段诊断
  - "研究阶段诊断"
  - "研究可行性评估"
  - "研究选题评估"
  # Step 1b: 广度探索 + 预检索
  - "选题预检索"
  - "研究趋势分析"
  - "文献量扫描"
  - "研究方向可行性"
  # Step 1c: 深度聚焦
  - "研究方向聚焦"
  - "创新点预判"
  # Step 1d: 选题预审
  - "选题预审"
  - "选题创新性评估"
  - "审稿人视角评估选题"
  # Step 2: 大纲
  - "生成论文大纲"
  - "论文关键词"
  - "大纲评审"
  - "评审大纲"
  - "Outline review"
  - "基于确定的研究主题，生成论文大纲和关键词清单"
  - "Based on the confirmed research topic, generate a paper outline and keyword list"
  # Step 3: 检索方案
  - "制定检索方案"
  - "文献检索策略"
  - "根据大纲和关键词，制定结构化文献检索方案"
  - "Based on the outline and keywords, design a structured literature search strategy"
  # Step 4: 检索与评分
  - "检索论文"
  - "按主题检索学术文献"
  - "搜索论文并下载"
  - "文献检索"
  - "按检索方案执行多渠道文献检索，并进行相关性评分和分级"
  - "Execute the multi-source literature search and perform relevance scoring and grading"
  # Step 5: 批量下载
  - "批量下载论文 PDF"
  - "从参考文献列表中下载 PDF"
  - "BibTeX 批量下载 PDF"
  - "批量下载 ScienceDirect 论文"
  - "Sci-Hub 下载论文"
  - "开始批量下载论文 PDF，按出版商自动路由"
  - "Start batch downloading paper PDFs, auto-routing by publisher"
  # IEEE CDP 两步走
  - "IEEE 下载"
  - "IEEE CDP 下载"
  - "两步走策略"
  # IEEE DOI 自动路由（10.1109/ 前缀自动识别）
  - "10.1109/*"
  - "doi:10.1109/*"
  # Zotero 附件管理
  - "Zotero 检查遗漏附件"
  - "Zotero 查找无附件条目"
  - "补下 Zotero 缺少的 PDF"
  # Step 6: Zotero 管理
  - "Zotero 文库整理"
  - "Zotero 架构生成"
  - "PDF 导入 Zotero"
  - "把下载的 PDF 导入 Zotero 文库，按大纲生成集合架构"
  - "Import the downloaded PDFs into Zotero and generate a collection architecture"
  # Step 6c: 文库一致性调整
  - "文库一致性"
  - "大纲对齐文库"
  - "文库结构调整"
  - "Zotero 大纲对齐"
  - "文库关联性"
  - "文献缺口"
  # Step 7: 论文写作
  - "写论文"
  - "撰写论文"
  - "基于文献写论文"
  - "基于 Zotero 文库中的文献，开始撰写论文"
  - "Based on the literature in Zotero, let's start writing the paper"
  # Step 8: 论文润色（四合一精修引擎）
  - "论文润色"
  - "论文修改"
  - "去 AI 痕迹"
  - "注入人味"
  - "润色分层"
  - "四合一精修"
  - "去 AI 化"
  - "对论文初稿进行润色，去 AI 痕迹、注入人味、优化句长波动"
  - "Polish the draft: remove AI traces, inject a human voice, and optimize sentence rhythm"
  # 全流程
  - "论文相关工作流"
  - "学术文献全流程"
  # 工程文档组合分析（非学术论文场景）
  - "文档组合分析"
  - "技术文档分析"
  - "工程文档分析"
  - "技术文档批量提取"
  - "分析现有技术文档报告"
  # 工程文档→大纲优化（Step 2c）
  - "大纲优化"
  - "工程文档优化大纲"
  - "结合工程文档优化大纲"
  - "基于技术报告优化大纲"
  - "用现有工程文档优化论文大纲"
---

# 完整学术文献检索和写作工作流（8 步法）

## 概述

```
Step 1: 交互式确定研究主题（v2.0 增强版） → 研究主题.md
  ├─ 1a 研究阶段诊断    确认用户画像 + 推荐入口
  ├─ 1b 广度探索+预检索  发散子方向 → 文献量/趋势/gap初判
  ├─ 1c 深度聚焦        方法论深化 + 创新点预判
  └─ 1d 选题预审        originality/importance/feasibility 三问
Step 2: 生成研究大纲与关键词        → 大纲关键词.md
Step 3: 生成文献检索方案（T1→T2→T3路由）→ 检索方案.md
Step 4: 多渠道检索+评分（引文验证+.bib导出） → 检索文献表.md / .xlsx / .bib
  ├─ 4a 引文验证    DOI有效性+元数据完整性
  ├─ 4b DOI去重     多源合并去重
  └─ 4c .bib导出    统一BibTeX格式+评分标签
Step 5: 多轮下载（Sci-Hub → SD）    → paper-temp/ PDFs
Step 6: Zotero 文库管理              → zotero-架构.md + Zotero 桌面端
  ├─ 6a 生成架构    首次按大纲生成
  ├─ 6b 导入 PDF    将 PDF 拖入对应集合
  └─ 6c 一致性调整  大纲修订后重对齐文库 🌟
Step 7: 论文写作（paper_type×language双轴）  → 论文初稿.md / .docx
  ├─ 7a 类型+语言识别  research/en/zh/zh-to-en
  ├─ 7b 写作模式       full/outline-only/plan/abstract-only/argument-first
  ├─ 7c 语言差异化     zh/en/zh-to-en 写作规范+章节命名
  ├─ 7d 章节写作规则   摘要/引言/相关工作/方法/实验/结论
  ├─ 7e 实时引文支撑   分段→搜索→评估→导出
  └─ 7f 中英文双边摘要
Step 7f: 同行评审仿真（质量门）      → 评审报告 + 修改建议
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
| **python-docx** | 提取 .docx 文本 + 生成优化版大纲 .docx | Step 2b/2c | `pip install python-docx` | ⬜ 可选（仅工程文档分析场景） |
| **fpdf2 (>=2.5.1)** | 生成中文 PDF 分析报告 | Step 2b/6d | `pip install fpdf2` | ⬜ 可选（仅需生成 PDF 报告时） |
|| **Zotero MCP Server** | 对话读写 Zotero 文库、按 DOI 导入 | Step 6-7 | 脚本一键安装+模式选择<br>`python3 scripts/setup_zotero.py --install`<br>  - Web API（远程，支持读写，需 API Key）<br>  - 本地 API（桌面端直连，仅读取，无需 Key）<br>含本地 wheel 优先离线安装 | ⬜ 可选 |
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

## Step 1: 交互式确定研究主题（v2.0 增强版）

> 旧版 Step 1 仅靠 5 轮问答让用户自述研究方向——用户不知道文献饱和度、不知道 gap 在哪里、不知道选题可行性。v2.0 借鉴 10 个学术 skill 的能力，在对话中注入外部信息（文献量/趋势/gap/创新性），让用户做有依据的决策。

### 增强架构总览

```
Step 1a: 研究阶段诊断      → 用户画像 + 推荐入口
Step 1b: 广度探索 + 预检索  → 发散子方向 → 文献量/趋势/gap初判
Step 1c: 深度聚焦          → 方法论深化 + 创新点预判
Step 1d: 选题预审          → originality/importance/feasibility 三问
                              🟢绿灯 / 🟡黄灯 / 🔴红灯

产出: 研究主题.md（增强版）
  含用户画像 + 可行性报告 + 创新点初判 + 预审结论
```

### 借鉴来源

| 借鉴 Skill | 借什么 | 用在哪里 |
|------------|--------|---------|
| **academic-mentor-1.0.0** | 研究阶段诊断、人物画像、可行性评估 | Step 1a |
| **nature-academic-search** | T1→T2→T3 多源路由检索 | Step 1b 预检索 |
| **academic-research-hub-pro-1.0.0** | 跨数据库搜索（arXiv, Google Scholar, Semantic Scholar） | Step 1b 数据源 |
| **scholar-search-1.0.4** | 学者/领域出版物扫描 | Step 1b |
| **deep-research** | 主题拆解为 3-5 个研究子问题 | Step 1b 发散 |
| **academic-deep-research-pro-1.0.0** | 双循环研究 + 3 检查点 | Step 1b/1c 结构 |
| **literature-review-2-0.1.0** | 研究 gap 识别 | Step 1b gap 初判 |
| **nature-reviewer** | originality/significance/readership 评估框架 | Step 1d 预审 |
| **nature-use-prompt-craft** | 启发式提问技巧 | 全步骤对话升级 |
| **academic-humanization-low-ai-1.0.0** | 去机械化表达 | 对话风格 |

---

### Step 1a: 研究阶段诊断 ← academic-mentor

> **目的：** 先了解用户是谁、处于什么阶段，再决定走哪条路。不是所有人都需要完整的 8 步流程。

**诊断维度：**

| 诊断项 | 选项 | 推荐入口 |
|--------|------|---------|
| **身份** | 硕士生 / 博士生 / 研究者 / 工程师 | — |
| **年级** | 博一（找方向）/ 博二（开题）/ 博三+（冲刺） | — |
| **当前阶段** | 刚入学，需要导师给方向 | → 先泛读综述，再走 Step 1-8 |
| | 已有大致方向，需精确选题 | → 完整走 Step 1-8 |
| | 已有具体题目，需文献支撑 | → 跳 Step 3（检索方案） |
| | 已有大纲，需下载文献写论文 | → 跳 Step 5（下载） |
| | 已有初稿，需润色 | → 跳 Step 8（润色） |
| **时间压力** | 3 个月内要投稿 / 6 个月 / 无紧迫 | 影响检索年限和下载策略 |
| **目标期刊** | 已有目标 / 不确定 / 毕业就行 | 影响写作和润色标准 |

**对话示例（启发式，非问卷式）：**

```
助手：在开始之前，先了解一下你的情况——你是硕士还是博士？目前几年级？
用户：博二，马上要开题了。
助手：博二开题节点很关键。你现在是有大致方向需要精确到具体题目，
      还是方向都还没定？
用户：方向大概有——充电桩热管理，但具体做什么还没想清楚。
助手：了解。那我们先做一轮快速文献扫描，看看近 3 年这个方向大家在做什么，
      哪些细分点还有空间——然后再聚焦。你觉得可以吗？
```

**产出：用户画像（嵌入研究主题.md）**

```markdown
## 用户画像
- 身份：博士生（博二）
- 阶段：开题准备，有大致方向，需精确选题
- 时间压力：6 个月内完成初稿
- 目标期刊：未确定
- 推荐路径：完整走 Step 1-8
```

---

### Step 1b: 广度探索 + 预检索 ← nature-academic-search + deep-research

> **目的：** 用户说出一个大致方向后，不是直接进入 5 轮问答，而是先做一次快速文献扫描——让数据说话。用户可能不知道这个方向已经发了 500 篇还是 5 篇。

**流程：**

```
用户说"充电桩热管理" →
  ① 发散 3-5 个子方向（帮用户看到更多可能）：
      ├── 冷板式液冷散热
      ├── 相变材料（PCM）热缓冲
      ├── 充电枪接口发热
      ├── 功率模块 IGBT 温升
      └── 整柜风道优化
  ② 逐个子方向快速预检索（Semantic Scholar / Crossref）：
      检索近 3 年论文数，抓前 10 篇高引论文的标题
  ③ 趋势判断：
      500+ 篇 → ⚠️ 热门但拥挤，需要更窄的切入点
      50-200 篇 → ✅ 适中，有足够文献又有创新空间
      <20 篇 → ⚠️ 太新/太小众，文献支撑不足
  ④ 输出对比表，让用户选择 1-2 个进入深度聚焦
```

**产出：选题可行性报告**

```markdown
## 选题可行性预检索

| 子方向 | 近3年论文数 | 趋势 | 高引关键词 | 判断 |
|--------|:----------:|------|-----------|:----:|
| 冷板式液冷散热 | ~180 | 上升 | microchannel, topology optimization, minichannel | ✅ 适中 |
| PCM 热缓冲 | ~350 | 平稳 | phase change material, thermal management, battery | ⚠️ 拥挤 |
| 充电枪接口发热 | ~45 | 上升 | connector, contact resistance, thermal runaway | ✅ 蓝海 |
| IGBT 功率模块温升 | ~90 | 下降 | SiC, wide bandgap, junction temperature | ⚠️ 降温中 |
| 整柜风道优化 | ~120 | 平稳 | air cooling, fan curve, pressure drop | ✅ 适中 |

> 建议优先聚焦「冷板式液冷散热」或「充电枪接口发热」——文献量适中且趋势向上。
```

**检索工具选择（参考 nature-academic-search 的 T1→T2→T3 路由）：**

| 优先级 | 工具 | 适用场景 |
|--------|------|---------|
| T1 | Semantic Scholar API | 快速扫量（免费，无需 Key） |
| T2 | Crossref API | DOI/元数据补全（免费） |
| T3 | OpenAlex API | 补充检索（免费） |
| T3 | Google Scholar | 引文追踪（需 skill 支持） |

---

### Step 1c: 深度聚焦 ← academic-deep-research-pro

> **目的：** 用户在 Step 1b 选择 1-2 个子方向后，进入深度聚焦——不只问"做什么"，还预判"创新点在哪"。

**双循环结构（借鉴 academic-deep-research-pro 的 2-cycle research）：**

```
Cycle 1: 方法论深化
  从"仿真" → 深化为 "CFD 参数化建模 + 代理模型优化 + 实验验证"
  从"实验" → 深化为 "正交试验设计 + 高速红外测温 + 不确定度分析"
  → 方法越具体，后续检索方案越精准

Cycle 2: 创新点预判
  基于该方向的 gap 初判，与用户讨论可能的创新切入：
  ├── 方法创新：新算法/新模型/新结构？
  ├── 应用创新：已知方法用于新场景？
  ├── 数据创新：新数据集/新实验发现？
  └── 组合创新：A+B 方法首次联合？
```

**对话示例：**

```
助手：「冷板液冷散热」方向，从预检索看，近 3 年高频词集中在
      microchannel 和 topology optimization。你手上有实验条件吗？
      还是主要做仿真？
用户：实验室有冷板测试台，可以做实验。
助手：那很好——有实验验证的文章比纯仿真高一个档次。
      我注意到近 3 年很少有人把「拓扑优化冷板」和「实验验证」结合起来做
      ——这可能是一个 gap。你觉得这个切入点怎么样？
```

**产出：聚焦后的研究方向（嵌入研究主题.md）**

```markdown
## 研究方向（聚焦后）
- 领域：充电桩热管理 → 冷板式液冷散热
- 研究问题：冷板流道拓扑优化设计 + 实验验证
- 方法论：CFD 参数化建模 + 代理模型（Kriging）+ 3D 打印冷板样件 + 台架实验
- 应用场景：直流快充桩（350kW+）
- 年限：近 5 年（2022-2026）
- 潜在创新点：拓扑优化冷板的实验验证 gap（预检索中罕见）
```

---

### Step 1d: 选题预审 ← nature-reviewer

> **目的：** 在投入数周时间检索和下载之前，先用审稿人视角审视选题——如果选题本身有硬伤，后面 7 步都是白做。

**三问预审框架（简化自 nature-reviewer 的五维评估）：**

| 维度 | 核心问题 | 评估 |
|------|---------|:---:|
| **Originality** | 这个方向最近 3 年被大量发表了吗？你的切入点与已有工作的本质区别是什么？ | 🟢/🟡/🔴 |
| **Importance** | 解决了什么实际问题？（不能是"填补空白"这种空话）谁会在乎这个结果？ | 🟢/🟡/🔴 |
| **Feasibility** | 数据/实验条件你能获取吗？文献量是否足够？方法论是否在可控范围内？ | 🟢/🟡/🔴 |

**预审结论：**

| 信号 | 含义 | 建议 |
|:----:|------|------|
| 🟢 绿灯（3 绿） | 选题可行 | 继续 Step 2 |
| 🟡 黄灯（1-2 红） | 有风险，需调整 | 回到 Step 1c 修正切入点，或标注为 acknowledged risk |
| 🔴 红灯（3 红） | 选题有硬伤 | 回到 Step 1b 换方向，或重新审视研究动机 |

**对话示例：**

```
助手：在正式开始检索之前，我先用审稿人的视角快速评估一下这个选题——

      Originality 🟡：拓扑优化冷板本身不是新概念，但"实验验证"这层
      确实少见——需要在论文中明确强调这一点。

      Importance 🟢：350kW 快充桩的热问题是工业界真实痛点，
      有明确的工程价值。

      Feasibility 🟢：有实验台、方法论清晰、文献量适中。

      总体 🟢 绿灯，可以继续。建议在写作时把「实验验证 gap」作为
      核心 narrative，而不是只说"我们做了一个拓扑优化冷板"。
```

**产出：预审结论（嵌入研究主题.md）**

```markdown
## 选题预审
- Originality: 🟡（需强调实验验证 gap）
- Importance: 🟢（工业界真实痛点）
- Feasibility: 🟢（有实验条件，文献充足）
- 总体: 🟢 绿灯
- 建议: 写作时以"实验验证 gap"为核心叙事线
```

---

### 产出文件：`研究主题.md`（增强版）

```markdown
# 研究主题

## 用户画像
- 身份：博士生（博二）
- 阶段：开题准备
- 推荐路径：完整走 Step 1-8

## 选题可行性预检索
| 子方向 | 近3年论文数 | 趋势 | 判断 |
|--------|:----------:|------|:----:|
| ... | ... | ... | ... |

## 研究方向（聚焦后）
- 领域：...
- 研究问题：...
- 方法论：...
- 应用场景：...
- 年限：...
- 潜在创新点：...

## 选题预审
- Originality: 🟢/🟡/🔴
- Importance: 🟢/🟡/🔴
- Feasibility: 🟢/🟡/🔴
- 总体: 🟢 绿灯 / 🟡 黄灯 / 🔴 红灯
```

---

### 交互原则（v2.0）

1. **不机械问卷** — 避免"你的研究方向是什么？具体研究什么问题？"的机械式连问。用启发式对话帮用户发现可能。
2. **让数据说话** — 用户不知道文献饱和度，你要帮他查。预检索结果比任何主观判断都有说服力。
3. **先发散再聚焦** — 不要用户说一个方向就钉死。发散 3-5 个子方向，用数据帮用户选。
4. **审稿人视角前置** — 选题阶段就用审稿人视角审视，避免写完才发现 innovation 不够。
5. **允许跳步** — 不是所有人都需要完整 8 步。Step 1a 诊断后直接推荐最优入口。

---

> **下一步 → Step 2：** 选题预审通过（🟢绿灯）后，基于聚焦的研究方向，生成论文大纲与关键词清单。

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

### 2b. 大纲评审（对已有大纲进行结构化评估）

> 适用场景：用户已有一份大纲草稿，需要评估其逻辑完整性、创新区分度、结构平衡性和工程可行性。**核心产出：评审报告 + 优化版大纲文档（.docx）**

#### 五维度评审框架（改编自 Step 7f）

| 维度 | 权重 | 大纲评审的检查要点 |
|------|------|-------------------|
| 逻辑连贯性（Coherence） | 25% | 章间有无清晰的递进/因果链？"背景→机理→方法→验证"是否完整？过渡段是否明确说明上一章结论与下一章起点的关系？ |
| 结构平衡性（Balance） | 20% | 各章子节数是否均衡？Ch2 是否有"一挑三"的臃肿感？Ch5 是否偏弱？建议目标分布 3:3:3:3 或 3:4:4:3。 |
| 创新区分度（Originality） | 20% | 创新点是否为"科学发现"而非"建立了方法"？三项创新之间是否有重叠？每项是否有具体章节对应？ |
| 工程可行性（Feasibility） | 20% | 实验验证中是否有对照基线？是否有理论-实验闭环验证环节？数据来源是否明确？ |
| 格式完备性（Completeness） | 15% | 绪论是否有针对选题独特性的综述？各章是否都有独立小结？参考文献在章节中的归属是否清晰？ |

#### 逐章诊断方法

对每章逐子节审查，记录三个指标：

```
✅ 一致（匹配大纲定位，逻辑合理）
⚠ 警示（定位模糊、工作量偏大或偏小、缺少关键环节）
❌ 问题（逻辑断裂、与整体不协调、创新点无法落地）
```

输出格式：表格 + 具体问题定位（标注到章/节/子节级）。

#### 创新点评审（关键质量门）

| 检查项 | 说明 |
|--------|------|
| **是发现还是方法？** | 科学发现（频率匹配规律、机理揭示）比"建立了XX方法"更具区分度 |
| **是否可证伪？** | 创新点必须能在 Ch5 实验中被验证——不能是一个无法检验的声明 |
| **是否独立？** | 三个创新点之间不应有重叠——每项对应不同的章节和工作量 |
| **是否有文献定位？** | 每一项创新点都应在绪论中明确其与已有工作的区别 |

#### 结构平衡性量化

计算各章子节数量（主节 + 子节），评估工作量分布：

```
Ch1 ──── ■■■  (绪论标准长度)
Ch2 ──── ■■■■■■■  (过重→建议精简或拆分)
Ch3 ──── ■■■■     (合理)
Ch4 ──── ■■■■     (合理)
Ch5 ──── ■■       (偏弱→建议充实)
```

#### 优先级排序（P0/P1/P2/P3）

| 优先级 | 含义 | 处理方式 |
|--------|------|----------|
| 🔴 P0 | 必须修改 | 影响逻辑完整性或创新区分度的关键问题 |
| 🟠 P1 | 建议修改 | 显著影响章节质量的问题 |
| 🟡 P2 | 可优化 | 提升工程实用性的补充内容 |
| 🟢 P3 | 细节打磨 | 措辞/格式/命名等精细化调整 |

#### 导师视角检查

> **为什么需要：** 五维评审从"论文本身好不好"出发，但导师关心的是"这个学生能不能顺利毕业"。两类问题有重叠但也有本质差异——前者评估论文质量，后者评估毕业风险。

在五维评审完成后，以导师视角做一轮独立的毕业可行性审查：

| 检查项 | 核心问题 | 红灯信号 🚩 |
|--------|---------|-----------|
| **工作量达标** | 题目够不够一个博士/硕士的工作量？ | Ch4（方法）只有 2 个子节 → 工作量不足；Ch5 只有一个对比实验 → 不够 |
| **风险识别** | 哪章可能卡半年出不来？ | 核心实验依赖未验证的设备/数据；方法 B 需要"突破性发现"才能成立 |
| **Plan B** | 如果核心实验失败，有没有退路？ | 三个创新点全压在同一个实验上 → 一损俱损；无替代方案 |
| **时间线与里程碑** | 能按时毕业吗？ | 无分阶段时间线；某章预估耗时远超正常范围；实验+写作总时长超过剩余学制 |
| **发表策略** | 够发几篇？哪些章可以拆成小论文先投？ | 全篇只能发一篇；Ch3 和 Ch4 的贡献重叠 → 无法拆分为独立小论文 |

**产出格式：**

```
## 导师视角检查

### 工作量评估
- 总章节数：6 章，子节总数：21
- 核心工作章（Ch2-4）：14 子节 → ✅ 博士论文达标 / ⚠️ 偏少
- 实验章（Ch5）：4 组实验 → ✅ 达标

### 风险矩阵
| 章节 | 风险 | 概率 | 影响 | Plan B |
|------|------|:--:|------|--------|
| Ch3 拓扑优化 | 算法收敛困难 | 🟡 中 | 核心方法失效 | 回退到参数化优化 + 实验验证 |
| Ch5 台架实验 | 设备采购延迟 | 🟢 低 | 延期 2 月 | 先做仿真对比，实验数据后续补 |

### 发表拆分建议
- 小论文 1：Ch3 拓扑优化方法 → 投 Applied Thermal Engineering
- 小论文 2：Ch4+Ch5 实验验证 → 投 International Journal of Heat and Mass Transfer
- 大论文：合并 + Ch2 综述扩展 → 博士学位论文

### 毕业时间线
  月 1-4   Ch3 方法搭建 + 仿真
  月 5-8   Ch4 实验台搭建 + 第一批数据
  月 9-11  Ch5 实验补全 + 数据分析
  月 12-13 写论文 + 小论文投稿
  → 13 个月可完成，风险 buffer 2 个月，总计 15 个月
```

**与五维评审的关系：**
- 五维说"结构可以"，导师问"但 Ch3 一个人做得完吗"
- 五维说"创新点清晰"，导师问"如果三个创新点全失败，你还有论文吗"
- 五维给 P0-P3 修改优先级，导师给"要不要换个题"级别的判断

#### 产出物

- **评审报告**（对话中直接输出）：含逐章问题表格、创新点评审、优先级列表
- **优化版大纲.docx**（python-docx 生成）：含格式规范的大纲全文 + 附录修改说明
- 优化版大纲每处修改用灰色楷体注释标注修改理由
- **通用 PDF 报告模板**：`references/outline-review-report-template.py` — 可复用的中文 A4 报告生成器，接受结构化 JSON 数据，一键生成评审报告 PDF

### 2c. 基于工程文档的大纲优化（新增流程）

> 适用场景：用户有一份论文大纲草稿 + 一组现有工程/技术文档（如设计报告、试验总结、改进报告等），需要从中提取数据和发现来充实大纲。**核心产出：优化版大纲.docx + 修改对照表。**

#### 工程文档→大纲优化三阶段

```
Stage 1: 文档组合分析
  → 遍历所有工程文档，提取：
     ① 文档关系拓扑（核心文档 vs 支撑文档 vs 验证文档）
     ② 每条技术路线的定量数据（设计参数、试验结果、优化效果）
     ③ 创新点对应的工程实现细节
  → 输出：文档全景总览 + 技术内容图谱

Stage 2: 大纲-文档交叉映射
  → 逐章、逐节检查大纲内容与工程文档的对应关系：
     ╔═══════════════╤════════════════╤══════════════╗
     ║ 大纲章节       │ 对应工程文档     │ 可注入的数据   ║
     ╠═══════════════╪════════════════╪══════════════╣
     ║ Ch2.2 CFD方法  │ 水力计算报告    │ 网格量、模型   ║
     ║ Ch3.2 叶片优化 │ 总报告§3.3-3.8 │ 六方案迭代     ║
     ║ Ch4.5 支架     │ 振动控制说明书  │ 三阶段设计     ║
     ╚═══════════════╧════════════════╝
  → 输出：交叉映射表

Stage 3: 逐章注入与优化
  → 按优先级填充：
     🔴 P0: 填补缺失章节（如装配工艺、实艇验证等整块内容缺位）
     🟠 P1: 补充定量数据（将工程文档中的具体数值注入对应子节）
     🟡 P2: 强化叙事线（如支架的三阶段设计演化、六方案迭代路径）
     🟢 P3: 对齐术语和标准（如GJB标准编号、产品型号参数）
  → 输出：优化版大纲.docx（含灰色楷体注释标注每处修改理由）
     + 附录：修改对照表（逐章列出原版vs优化版的差异）
```

#### 文档关系拓扑分析方法

```text
                   ┌──────────────────┐
                   │ 核心文档（总报告） │ ← 设计+制造+试验全流程
                   └───────┬──────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   ┌──────────┐    ┌──────────────┐    ┌──────────┐
   │ 设计支撑  │    │ 专题深入      │    │ 试验验证  │
   │ 水力计算  │    │ 振动噪声控制  │    │ 试验报告  │
   └──────────┘    └──────────────┘    └──────────┘
                           │                 │
                           └─────────────────┘
                                   │
                                   ▼
                            ┌──────────────┐
                            │ 改进迭代      │
                            │ + 实艇换装    │
                            └──────────────┘
```

#### 数据注入优先级矩阵

| 数据类型 | 注入位置 | 示例（GLG100-250案例） |
|----------|---------|----------------------|
| 设计参数 | Ch1背景、Ch方法 | Q=110m³/h, H=65m, n=3000rpm, ns=83.6 |
| CFD设置 | Ch2方法 | k-ε+SIMPLE+MRF, 305万网格, 5.556e-05s步长 |
| 监测数据 | Ch2结果、Ch5验证 | P10处2508.5Pa@347.6Hz, Cp<0.37% |
| 优化迭代 | Ch3方法 | 6方案(5/6/7/7+7)→最终7+7长短叶片 |
| 结构设计 | Ch4方法 | 支架三阶段演化, +93.5Hz, 22dB@1600Hz |
| 试验结果 | Ch5验证 | 1000h通过, GJB150全套环境试验 |
| 加工工艺 | Ch5验证 | 轴跳动≤0.01mm, 专用工装架 |
| 工程验证 | Ch5验证 | 实艇换装, 浮筏隔振≥35dB |

#### 产出物

- **优化版大纲.docx** — 含格式规范的大纲全文，每处修改用灰色楷体注释标注修改理由和数据来源
- **附录：修改对照表** — 逐章列出原版v1.0→优化版v2.0的变更清单
- **技术内容图谱** — 文档中提取的所有技术路线和定量数据汇总（可选嵌入大纲附录）

---

> **下一步 → Step 3：** 大纲优化完成（v2.0定稿）后，生成结构化检索方案，按T1→T2→T3路由执行文献检索。

## Step 3: 生成文献检索方案 ← nature-academic-search

> 旧版的检索来源是简单的"Semantic, Crossref"平面映射。nature-academic-search 提供 T1→T2→T3 三级回退路由规则——每个子课题不是挂一个来源，而是挂一条 fallback 链。

基于大纲和关键词，生成结构化检索方案。

### 检索源路由规则 ← nature-academic-search T1→T2→T3

按研究领域选择合适的检索源路由：

| 领域 | 首选 (T1) | 备选 (T2) | 最后手段 (T3) |
|------|----------|----------|-------------|
| 医学/临床 | PubMed | Semantic Scholar | Google Scholar |
| 跨学科/工程 | CrossRef | Semantic Scholar | Scopus |
| 预印本/CS/物理 | arXiv | bioRxiv / medRxiv | — |
| 全面综述 | PubMed + CrossRef + arXiv | Semantic Scholar + bioRxiv/medRxiv | WoS / Scopus |
| 需要引文量数据 | Semantic Scholar | CrossRef | — |
| 中文文献 | — | — | CNKI / 万方（手动） |

> T1 优先，无结果或结果不足时 fallback 到 T2，依然不足到 T3。每次 fallback 时记录原因。

**检索源能力速查（借鉴 nature-academic-search tools.md）：**

| 工具 | 覆盖范围 | API 限制 | 费用 |
|------|---------|---------|------|
| Semantic Scholar | 2 亿+ 论文，CS/生物医学最强 | 100 req/s（带 Key），1/s（不带） | 免费 |
| Crossref | 1.5 亿+ 元数据记录，全学科 | 50 req/s | 免费 |
| PubMed (NCBI) | 3700 万+ 生物医学引文 | 10 req/s（带 Key），3/s（不带） | 免费 |
| arXiv | 250 万+ 预印本，物理/CS/数学 | 1 req/3s（无 Key） | 免费 |
| OpenAlex | 2.5 亿+ 学术作品，全学科 | 100k/天 | 免费 |
| Google Scholar | 全学科 | 爬虫限制 | 需 skill 支持 |

### 产出文件：`检索方案.md`（增强版）

```markdown
# 检索方案

## 领域识别
- 研究领域：[医学/工程/CS/跨学科]
- 推荐路由：T1: [source] → T2: [source] → T3: [source]

## 检索子课题
| 编号 | 子课题 | 关键词 | T1 | T2 | T3 |
|------|--------|--------|----|----|-----|
| S1 | 子课题一 | keyword1, keyword2 | Semantic Scholar | Crossref | OpenAlex |
| S2 | 子课题二 | keyword3, keyword4 | CrossRef | PubMed | Semantic Scholar |
| S3 | 子课题三 | keyword5, keyword6 | Semantic Scholar | Crossref | — |
| S4 | 子课题四 | keyword7, keyword8 | arXiv | Semantic Scholar | Crossref |

## 检索执行计划
- 每子课题检索 50 条（T1 优先）
- T1 不足 30 条时自动 fallback 到 T2 补充
- 去重后总分 ≥200 条
- 最终筛选保留 100-150 条核心文献
```

### Pre-flight 检查（检索前）

检索开始前，快速验证各 API 端点可达：

```bash
# 检查各检索源 API 是否可达
python3 scripts/search_by_topic.py --preflight
# 输出:
#   ✅ Semantic Scholar — OK (200ms)
#   ✅ Crossref — OK (350ms)
#   ✅ OpenAlex — OK (280ms)
#   ⚠️ PubMed — Slow (1200ms)，will use as T2 only
```

---

> **下一步 → Step 4：** 按检索方案执行多渠道检索，对结果进行相关性评分和分级筛选。

## Step 4: 多渠道检索与相关性筛选 ← nature-academic-search

> 新增引用验证（DOI 有效性 + 元数据完整性）+ 统一 .bib 导出 + DOI 去重策略。

### 检索执行

按 Step 3 方案的 T1→T2→T3 路由逐子课题检索：

```bash
# 按子课题逐条检索，每个子课题自动走 T1→T2→T3 fallback
python3 scripts/search_by_topic.py "cold plate liquid cooling optimization" \
  --t1 semantic_scholar --t2 crossref --t3 openalex \
  --limit 50 --output s1_results.bib

python3 scripts/search_by_topic.py "spray cooling battery heat transfer" \
  --t1 crossref --t2 pubmed --t3 semantic_scholar \
  --limit 50 --output s2_results.bib
# ...
```

### 4a: 引文验证

> 借鉴 nature-academic-search 的 citation-verification workflow。在评分之前先验证——剔除 DOI 无效、元数据残缺的条目，避免后续下载白费功夫。

```
检索结果 → 逐条验证：
  ① DOI 格式合法性（正则 + Crossref API 校验）
  ② 元数据完整性：title / authors / year / journal 是否在结果中存在
  ③ 标记问题条目：
     ⚠️ DOI 无效 → 跳过（无法下载）
     ⚠️ 缺作者/年份 → 尝试从 Crossref 补全
     ✅ 完整 → 进入评分
```

### 4b: DOI 去重

多源检索会产生重复（同一篇论文从 Semantic Scholar 和 Crossref 各返回一次）：

```
去重策略（借鉴 nature-academic-search dedup）：
  - 主键：DOI（大小写 + 前缀统一后比对）
  - 无 DOI 时：title + first_author + year 组合键
  - 冲突时保留元数据最完整的条目
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

### 4c: 统一 .bib 导出

> 借鉴 nature-academic-search 的 citation-file-mgmt workflow。所有检索结果统一导出为 .bib 格式，可直接导入 Zotero。

```bash
# 将检索文献表转换为 .bib（含评分注释）
python3 scripts/search_by_topic.py --export-bib 检索文献表.md --output 文献库.bib

# 转换格式（如需要）
python3 scripts/search_by_topic.py --convert 文献库.bib --to ris  # → Zotero/EndNote
python3 scripts/search_by_topic.py --convert 文献库.bib --to nbib # → PubMed
```

**.bib 文件含评分标签：**
```bibtex
@article{liu_topology_2025,
  title     = {Topology Optimization of Cold Plate Flow Channels...},
  author    = {Liu, ... and Zhang, ...},
  journal   = {Applied Thermal Engineering},
  year      = {2025},
  doi       = {10.1016/j.applthermaleng.2025.127040},
  note      = {Tier 1 | Score: 22/25 | S1: 冷板拓扑优化}
}
```

> `note` 字段保留了 Tier 等级、评分和子课题归属，导入 Zotero 后可在 Extra 字段中查看。

---

> **下一步 → Step 5：** 开始批量下载。按出版商自动路由：全部论文先走 Sci-Hub（老论文免费下）；未下载到的按 DOI 前缀分流 → `10.1016/` 走 SD CDP，`10.1109/` 走 IEEE CDP，其余走多出版商 CDP。

## Step 5: 多轮批量下载

按出版商自动路由下载，目标覆盖率 90%+：

| 轮次 | 目标 | DOI 前缀 | 脚本 |
|------|------|----------|------|
| **第一轮：Sci-Hub** | 所有论文（优先，免费） | 不限 | `download_via_scihub.py` |
| **第二轮：SD CDP** | Elsevier 论文 | `10.1016/` | `auto_sd_downloader.py` |
| **第三轮：IEEE CDP** | IEEE 论文 | `10.1109/` | `download_via_ieee.py` |
| **第四轮：多出版商 CDP** | 其他出版商 | 其余 | 按需适配 |

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

### 第三轮：IEEE CDP 下载（10.1109/ 论文）

第一轮（Sci-Hub）未下载到的 IEEE 论文，走专用 IEEE CDP 脚本（已固化，v1.0.1）。**跳过 ScienceDirect 和其他出版商。**

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

#### IEEE 两步走策略（v1.0.1，已验证 6/6）

```bash
# 交互式：自动检测会话，无登录时弹出登录页
python3 scripts/download_via_ieee.py --papers DOI1,DOI2 --port 9223

# 从文件读取 DOI 列表
python3 scripts/download_via_ieee.py dois.txt --output paper-temp/

# 其他命令
python3 scripts/download_via_ieee.py --check-session --port 9223   # 检查会话
python3 scripts/download_via_ieee.py --login --port 9223           # 打开登录页
python3 scripts/download_via_ieee.py --skip-session-check ...      # 跳过检查（调试用）
```

```
Step A（首选，v1.0.1）：
  ① 导航到文章页 ieeexplore.ieee.org/document/{arnumber}
  ② 等待 8s SPA 渲染
  ③ 提取 PDF 按钮的 stamp URL（分层选择器，不点击，只读 href）
  ④ 关闭文章页标签页
  ⑤ 创建新空白标签页 → 先启用 Fetch.enable → 再 Page.navigate 到 stamp URL
     （关键：Fetch 必须在导航之前启用，否则 PDF 被 Chrome 查看器消费后捕获不到）
  ⑥ 导航时带 Referrer（文章页 URL，IEEE 校验 Referer，缺失则 denyReason=-501）
  ⑦ 在 Fetch.requestPaused 中检查 content-type=application/pdf
  ⑧ 调用 Fetch.getResponseBody 获取原始 PDF 字节（超时 30s，适配大 PDF）

Step B（回退，v1.0.1）：
  ① 直接尝试 stamp/stamp.jsp?tp=&arnumber=XXXXX（带 Referrer）
  ② 若失败，试 stampPDF/getPDF.jsp?tp=&arnumber=XXXXX（带 Referrer）

失败信号：
  - getPDF 重定向到 document/{arnumber}?denied= → 机构订阅未覆盖此论文
  - Step A NO_BUTTON → 页面未渲染 PDF 按钮（通常需机构登录）

前置条件：
  - IEEE 不支持纯 IP 认证下载 PDF，必须通过 SSO/Shibboleth 登录。
  - 首次使用需在 CDP Chrome 窗口中点击 "Institutional Sign In" → 选择机构 → SSO。
  - 登录会话在 Chrome 关闭前保持有效，重启后需重新登录。
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

若结果为 `出版商Cookie: 0`，原因及处理：
- **最常见：CDP Chrome 使用隔离的临时 Profile**（如 `/tmp/chrome_scidownload`）—— 用户在日常 Chrome 中完成的登录不共享到 CDP 浏览器
- 需要**在 CDP 浏览器窗口中**完成机构登录，或切换为用户的真实 Chrome Profile
- **注意：IEEE 不支持纯 IP 认证下载 PDF，必须通过 SSO/Shibboleth 登录。**

### 第四轮：多出版商 CDP 下载（Wiley / AIP / ASME / Springer / RSC 等）

第一至三轮未覆盖的其他出版商论文，采用通用 CDP Fetch 拦截方案。
详见 `references/publisher-access-matrix.md` 中的「CDP 通用方案」和「出版商适配经验」章节。

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

> **Zotero MCP 连接模式说明**：`setup_zotero.py --install` 提供两种模式选择。
> - **Web API 模式（默认）**：需从 zotero.org 获取 API Key，支持完整的读写操作（创建/修改/删除集合和条目），适合需要管理文库的用户。
> - **本地 API 模式**：直接连接 Zotero 桌面端（localhost:23119），无需 API Key，但**仅支持读取**（不能创建/移动/删除），适合只需读文献写论文的用户。
>
> 任何时候可重新运行 `--install` 切换模式。

先检测 Zotero 环境：

```bash
python3 scripts/setup_zotero.py
```

**方式一：手动拖拽（推荐，零配置）**
在 Zotero 桌面端拖拽 PDF 到对应集合，Zotero 自动识别 DOI/标题并匹配元数据。最简单的方式，无需任何 API Key。Zotero 免费版仅有 300MB 云端存储，PDF 保存在本地，元数据同步到云端几乎不占空间。

**方式二：Zotero MCP 对话操作**
通过 `zotero_add_by_doi` 等工具直接按 DOI 导入（Hermes / OpenClaw / Claude Code 内置，无需额外配置）。

### 6c：大纲修订后的文库一致性调整

> 适用场景：大纲经 Step 2b 评审优化后，已有 Zotero 文库需要重新对齐新大纲结构。**核心原则：先提方案确认，再执行操作。**

#### 步骤 1：映射现有文库结构与优化大纲

逐层对比 Zotero 集合树与优化大纲的章节树，记录：

| 检查项 | 诊断方法 |
|--------|----------|
| **对应关系** | 每个集合是否明确映射到对应章/节？ |
| **子集完整度** | 每子集论文数量是否合理（太少则分类过细，太多则未细分）？ |
| **跨集合重叠** | 同一篇论文是否被合理分配到多个相关集合？ |
| **集合根下未归类** | 父集合根下的未归类论文数（应尽量少，趋近于0） |

#### 步骤 2：诊断三端关联性（关键质量门）

评估**机理→源控制→路径控制→验证**的文献链是否闭合：

```
1-流致低频振动机理 ──→ 2-水力设计方法 ──→ 3-路径控制与减振 ──→ 4-工程验证
       │                      │                      │                    │
    发现什么规律           怎么改设计             怎么阻断             怎么验证
```

每个连接带（→）检查：

| 连接带 | 检查焦点 | 信号 |
|--------|---------|------|
| 1→2 | 1中的频谱/机理分析能否直接支撑2的设计目标？ | 若1含大量非振动相关的通用流场论文→需筛选核心子集 |
| 2→3 | 2中有无讨论"优化后残余激励"的论文？ | **通常缺乏**，需标注为论文自创填补的空白 |
| 3→4 | 3中的控制方案在4中有无对应实验验证论文？ | 若3无对应4的验证论文→需补检索 |

#### 步骤 3：文献缺口定位

基于关联分析，识别三类缺口：

| 缺口类型 | 含义 | 处理方式 |
|----------|------|----------|
| **库内冗余** | 集合中存在与主题不匹配的论文（如故障诊断论文出现在机理集合中） | 移入正确的集合 |
| **连接带空白** | 两集合间缺少过渡性文献（如"优化后残余激励"无文献覆盖） | **标注为论文自身贡献空间**，无需补文献 |
| **整体缺项** | 优化大纲中某章节完全无对应文献 | 补检索方案→Step 3~4→Step 5下载 |

#### 步骤 4：执行调整（先确认再执行）

1. 向用户提交调整方案（含移入/移出清单 + 新建/删除集合说明）
2. 用户在 Zotero 桌面端删除空集合（API 不支持删除集合操作）
3. 通过 Zotero MCP 执行论文跨集合移动

```
典型操作序列：
1. 创建新子集合：zotero_create_collection(name, parent_collection=key)
2. 移动论文：
   zotero_manage_collections(item_keys=[...], add_to=[new_key], remove_from=[old_key])
3. 用户自行在桌面端删除空集合/重命名
```

#### 交互方式

向用户说明方案时，先给简洁的变更清单："改什么、为什么改"，得到确认后再执行。

```
> **建议调整方案：**
> A. 1-机理→移出3篇故障诊断论文到4-验证 → 库内冗余清理
> B. 3-路径控制→将45篇根下论文归入3a/3b/3c子集 → 完善分类
> C. 2↔3衔接空白（残余激励）→ 无需补文献，标注为论文原创贡献
>
> 是否按此方案执行？
```

---

### 6d：生成文库-大纲对照表 PDF（大纲对齐后使用）

> 适用场景：文库调整完成后，生成一份 PDF 清晰地展示 Zotero 集合与论文大纲的完整对应关系，便于导出给合作者或导师审查。

**操作流程：** 逐章对比 Zotero 集合树与大纲章节树 → 记录每节对应的集合名、篇数、覆盖等级（✅充足/🟡偏少/🔴缺口/🔵原创） → 生成覆盖热力图 → 输出为带色彩标注的对照表 PDF。

**技术方案：** 使用 `fpdf2`（纯 Python PDF 库，pip install fpdf2）生成含背景色的表格。每行一条映射记录，最后一列用绿/黄/红/蓝底色标注覆盖度。包含创新点映射表 + 热力图总览 + 附录文库结构。

**产出文件：** `Zotero-大纲对应关系_论文名.pdf`

---

> **下一步 → Step 7：** 所有文献准备就绪，开始按大纲撰写论文。

---

## 脚本索引

| 脚本 | 步骤 | 用途 |
|------|------|------|
| `scripts/search_by_topic.py` | 4 | 多渠道检索（Semantic Scholar / Crossref / OpenAlex） |
| `scripts/batch_read_pdfs.py` | 8 | 批量提取 PDF 全文文本（默认 6 进程，自动切换 A/B 方案） |
| `scripts/download_via_scihub.py` | 5 | Sci-Hub CDP 下载（镜像站自动检测，`--mirror`/`--skip-test` 参数） |
| `scripts/download_via_ieee.py` | 5 | IEEE CDP 两步走下载（v1.0.1：提取 stamp URL → Fetch 预启用 + Referrer 捕获 + 交互式登录 / 带 # --skip-session-check | Step A: 提取 stamp URL → 新标签 Fetch 预启用捕获 | Step B: 直连 getPDF + Referrer） |
| `scripts/batch_resolve_pii.py` | 5 | DOI → PII 解析（BibTeX / Markdown / 纯文本，自动检测格式） | ✅ |
| `scripts/parallel_sd_download.py` | 5 | 双浏览器并行下载（混合策略：直连+文章页提取），引用 `sd_download.py` | ✅ |
| `scripts/auto_sd_downloader.py` | 5 | 全自动版：启停浏览器 + 断点续跑 + 混合策略（引用 `sd_download.py`）| ✅ |
| `scripts/auto_sd_downloader.py --no-restart` | 5 | 使用已有的 CDP 浏览器，不重启不杀进程 | ✅ |
| `scripts/sd_download.py` | 5 | 共享混合下载核心（策略A: 直连8s→PDF标签页→Fetch捕获 / 策略B: 文章页25s渲染→提取`?md5=`→PDF标签页→Fetch捕获） | ✅ |
| `scripts/cdp_utils.py` | 5 | 共享 CDP 模块（浏览器管理、Fetch 捕获、依赖检查） | — |
| `scripts/start_cdp_chrome.sh` | 5 | 一键启动 CDP Chrome（持久化 Profile，登录一次永久可用） | ✅ |
| `scripts/organize_zotero.py` | 6 | 解析大纲关键词 → Zotero 集合结构 | ✅ |
| `scripts/setup_zotero.py` | 6 | Zotero MCP Server 一键安装 + 模式选择（Web API / 本地） | ✅ |
| `scripts/extract_docs.py` | 2c | 批量提取 .docx/.doc 文本（去重 + TOC 域代码清理） ← `references/docx-doc-extraction-and-pdf-report.md` | |
| `scripts/generate_report_pdf.py` | 2b/6d | 通用中文 PDF 报告生成器（fpdf2 + 系统中文字体，结构化 JSON 输入） ← `references/docx-doc-extraction-and-pdf-report.md` | |
| `scripts/generate_outline_docx.py` | 2c | 生成优化版大纲 .docx（灰色楷体修改注释 + 附录修改对照表） ← `references/outline-optimization-with-engineering-docs.md` | |
| `references/literature-table-template.md` | 4 | 检索结果表示例 |
| `references/zotero-structure-template.md` | 6 | Zotero 架构示例 |
| `references/publisher-access-matrix.md` | 5 | 各出版商下载可行性对照表 |

---

## 参考文件

- `references/literature-table-template.md` — 含相关性评分的文献表格模板
- `references/zotero-structure-template.md` — Zotero 集合结构示例
- `references/publisher-access-matrix.md` — 各出版商下载可行性对照表
- `references/zotero-missing-attachments.md` — 定位 Zotero 中缺 PDF 的条目并通过 CDP 补下
- `references/outline-optimization-with-engineering-docs.md` — 基于现有工程文档（.docx/.doc技术报告）优化论文大纲的三阶段工作流：文档组合分析→大纲-文档交叉映射→逐章注入与优化。含普适化案例和数据注入矩阵。配套脚本 `generate_outline_docx.py`。
- `references/cdp-pdf-capture-limitations.md` — CDP PDF 捕获限制与期刊级访问限制
- `references/sd-cdp-architecture.md` — SD 下载架构：PDF 在新标签页渲染、会话二层结构、标签页管理策略、Profile 持久化
- `references/docx-doc-extraction-and-pdf-report.md` — 批量提取 .docx/.doc 中文技术文档文本 + 用 fpdf2 + 系统中文字体生成中文 PDF 分析报告。配套脚本 `extract_docs.py` 和 `generate_report_pdf.py`。

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

### scripts/packages/ 目录的平台兼容性

`scripts/packages/` 目录缓存了 `zotero-mcp-server` 的全部依赖 wheel 文件，用于离线安装。但其中约 16 个是 **macOS ARM64 平台专用**的二进制 wheel（如 `onnxruntime`、`numpy` 等），约 40MB。如果 skill 需要在 Linux/Windows 上使用，应删除此目录下的所有 `.whl` 文件，改为：

```bash
pip download zotero-mcp-server --dest scripts/packages/
```

在目标平台上重新下载对应平台的 wheel。`setup_zotero.py --install` 会自动检测本地 wheel 并优先使用，不存在时回退到 PyPI。

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

### 7a: 论文类型与语言双轴识别 ← nature-writing

> paper_type 轴（research / methods / hypothesis / algorithmic / review）决定章节骨架；language 轴（en / zh / zh-to-en）决定章节命名、引用格式和写作规范。两个轴组合出 15 种写作场景。

#### 轴一：论文类型（paper_type）

| paper_type | 特征 | 典型章节骨架 | 论证链 |
|------------|------|-------------|--------|
| **research** | 有明确的实验/仿真研究，完整展示方法+结果 | intro → related-work → method → experiments → discussion → conclusion | gap → 方法 → 结果 → 分析 → 意义 |
| **methods** | 侧重方法/工具创新，验证相对轻量 | intro → problem-statement → design → implementation → validation → comparison | 问题 → 设计 → 实现 → 验证 → 对比 |
| **hypothesis** | 先提假设再做实验检验 | background → hypothesis → test-design → results → implications | 背景 → 假设 → 检验 → 结果 → 推论 |
| **algorithmic** | 算法/模型为核心贡献 | intro → preliminaries → algorithm → analysis → experiments → related-work | 基础 → 算法 → 分析 → 实验 |
| **review** | 系统综述/调研 | intro → methodology → thematic-review → synthesis → gaps → conclusion | 方法 → 主题 → 综合 → gap → 结论 |

#### 轴二：语言 / 投稿目标（language）

| language | 场景 | 章节命名 | 引用格式 | 写作规范 |
|----------|------|---------|---------|---------|
| **en** | 直接用英文撰写，投国际期刊（Nature/IEEE/Elsevier） | Introduction, Related Work, Method, Experiments, Conclusion | IEEE / APA / Nature | Anglo-American academic prose（Step 7d 英文规则） |
| **zh** | 用中文撰写，投中文期刊（知网/管理世界/经济研究等） | 引言/绪论、文献综述、方法、实验、结论 | GB/T 7714 | 中文学术写作规范（Step 7d 中文规则） |
| **zh-to-en** | 用中文写草稿/笔记，最终输出英文成稿 ← nature-writing zh-to-en mode | 英文命名（Introduction 等） | IEEE / APA / Nature（按目标期刊） | 中文思维→英文表达的翻译转换规则 |

#### 识别流程

```
1. 先问 paper_type（决定骨架）
2. 再问 language（决定命名+引用+规范）
3. 两个轴组合 → 确定完整写作方案

示例组合：
  research × en   → 英文实验研究论文（最常见）
  research × zh   → 中文学术论文（知网投稿）
  research × zh-to-en → 中文草稿→英文成稿（中国研究者最常用场景）
  review × en     → 英文系统综述
  hypothesis × zh → 中文假设驱动型论文
```

**对话示例：**

```
助手：在开始写作前，先确认两件事——

      第一，你的论文是什么类型？
      research（完整实验研究） / methods（方法创新为主） /
      hypothesis（假设驱动） / algorithmic（算法模型） / review（综述）？

用户：research，实验部分完整。

助手：第二，你打算用什么语言写、投什么类型的期刊？
      en（直接写英文，投国际期刊） /
      zh（写中文，投国内期刊） /
      zh-to-en（中文思路/草稿转英文成稿）？

用户：zh-to-en。我手上有中文的实验笔记和思路，但最终要投 IEEE。

助手：明白——research × zh-to-en。
      骨架用英文命名（introduction → method → experiments...），
      引用用 IEEE 格式，你的中文笔记我来帮你转成英文。
      先从一句话核心论点开始，确认方向正确再展开。
```

### 7b: 写作模式选择

在 paper_type 的基础上，选择写作模式：

| 模式 | 触发场景 | 产出 |
|------|----------|------|
| `full` | 已有清晰大纲和文献，直接逐章完整撰写 | 论文初稿.md |
| `outline-only` | 不确定结构，先生成详细大纲 | 大纲关键词.md（细化版） |
| `plan` | 需要多轮引导交互来厘清论点 | 多轮交互 → 大纲 |
| `abstract-only` | 已有正文，仅需写中英文摘要 | 中英文摘要 + 关键词 |
| `argument-first` | 先写一句话核心论点，确保方向正确再展开 ← nature-writing | 一句话论点 → 大纲确认 → 展开 |

**`argument-first` 模式（借鉴 nature-writing stance.md 的 8-step workflow）：**

nature-writing 强调"不要跳过 planning 阶段直接写文字"。在动手写正文之前，先用一句话写清楚核心论点：

```
> 在开始写作之前，请用一句话总结这篇论文的核心论点——
>   "本文证明了/提出了/发现了______，与已有方法的不同在于______。"
>
> 这一句话将成为整篇论文的北极星，每一章都应该在回答它的某一部分。
```

只有用户确认了核心论点，才进入逐章写作。

### 7c: 语言差异化规则 ← nature-writing language 轴

> **核心原则：** zh、en、zh-to-en 三种语言模式的写作规范有本质差异——不能把英文论文的写法直接翻译成中文来投稿，也不要把中文思维直接翻译成英文投稿。

#### 7c.1 章节命名对照

| 英文 (en) | 中文 (zh) | 中文场景说明 |
|-----------|----------|-------------|
| Abstract | 摘要 | 中文期刊通常要求中文摘要 + 英文摘要双语 |
| Introduction | 引言 / 绪论 | 工学多用"绪论"，理学多用"引言"。博士论文用"绪论" |
| Related Work | 文献综述 / 相关工作 | 中文期刊常将综述并入绪论（不独立成章），博士论文独立成章 |
| Method | 方法 / 实验方案 / 系统设计 | 按学科习惯：工学→"实验方案"，理学→"方法"，计算机→"系统设计" |
| Experiments | 实验与结果 / 结果与分析 | 中文期刊常将"结果"和"分析"拆为独立两节 |
| Discussion | 讨论 / 分析与讨论 | 中文期刊常将 Discussion 并入 Conclusion 或与 Results 合并 |
| Conclusion | 结论 / 结论与展望 | 必须包含"展望/不足"子节 |
| References | 参考文献 | GB/T 7714 格式 |

#### 7c.2 写作规范差异

| 维度 | en（英文投稿） | zh（中文期刊） | zh-to-en（中转英） |
|------|--------------|---------------|-------------------|
| **人称** | 第三人称为主，方法/实验部分可用 "we" | 第一人称"本文/笔者"或第三人称"本研究"均可 | 中文草稿中的人称需在英文输出中转第三人称或 we |
| **句长** | 15-25 words/句，自然波动 | 中文不适用，关注句子"信息密度"而非字数 | 中文长句需拆分为 2-3 句英文，每句 15-25 words |
| **被动/主动** | 主动态优先（"We conducted..."），非"it was conducted" | 被动态常见（"实验由...完成"），不加"我们"也通顺 | 中文被动态→英文主动态 |
| **段落结构** | 一段一个论点，首句即主题句（topic sentence） | 一段可含多论点，主题句不一定在段首 | 中文段落需重新组织为英文的"一段一论点" |
| **文献引用密度** | 引言/相关工作部分引用密集（每 2-3 句一次引用） | 相对稀疏；中文期刊综述部分引用密度较低 | 转英文时需补充引用（可能需要追加检索） |
| **批判性表达** | 直接指出已有工作的局限："However, [X] does not address..." | 更含蓄："[X] 的研究主要关注...，对于...讨论较少" | 中文含蓄→英文直接的批判表达 |
| **贡献表述** | 显式列出："This paper makes the following contributions: (1)...(2)..." | 通常融入叙述中，不单独列编号清单 | 中文叙述→英文显式贡献列表 |

#### 7c.3 zh-to-en 特殊规则 ← nature-writing zh-to-en mode

这是中国研究者最常用的场景——手上有中文思路/笔记/数据，最终要输出英文成稿。特殊规则如下：

```
1. 术语锁定：写作开始前先列出"中→英关键术语对照表"
   - 宁可一开始多花 5 分钟对术语，不要写到一半才发现用词不一致
   示例：
     冷板 → cold plate
     拓扑优化 → topology optimization
     努塞尔数 → Nusselt number
     泵功 → pump power (NOT pump work/pump effort)

2. 中文笔记→英文翻译四步法（非机械翻译）：
   ① 读中文草稿，提取核心论点（不是逐句翻）
   ② 按英文论文的论证逻辑重新排序（gap→method→result→conclusion）
   ③ 用英文撰写（不是翻译），参考中文的数据和结论
   ④ 检查：英文版的论点顺序是否和中文版不同？（如果相同，可能是翻译腔）

3. 识别中文写作特有的"英文不该有"的模式：
   - "这是...的问题，因此具有重要的理论意义和工程应用价值。" → 英文不要这种总结式句子，改为具体数据
   - "国内外学者对此进行了大量研究。" → 英文中不要说"A lot of research has been done..."，直接说gap是什么
   - "随着...的发展"（With the development of...）→ 英文中最泛滥的开头，避免使用

4. 中文数字和单位的英文转换：
   - 中文"约5kW" → "approximately 5 kW"（数字和单位间有空格）
   - 中文"提高了30.5%" → "increased by 30.5%"
   - 中文"降低了8.5°C" → "decreased by 8.5°C" 或 "reduced the temperature by 8.5°C"
```

#### 7c.4 中文期刊特有规范 (zh)

```
1. 中文标题要求：
   - 不宜超过 20 字，不设副标题（除非绝对必要）
   - 包含研究主题和方法关键词
   - "...研究"、"基于...的...分析"是常见标题模式

2. 中文摘要结构：
   - 目的/背景 → 方法 → 结果（带关键数据） → 结论
   - 300-500 字，不分段
   - 关键词 3-8 个，用《汉语主题词表》标准词

3. 参考文献：
   - GB/T 7714-2015 格式（见下文引用格式表）
   - 中文文献在前、英文在后（或按引用顺序统一编号）
   - 期刊论文：作者. 题名[J]. 刊名, 年, 卷(期): 起止页码.
   - 学位论文：作者. 题名[D]. 城市: 学校, 年.
```

### 7d: 章节级写作规则 ← nature-writing section-specific rules

> 以下规则面向 **en** 模式，**zh** 模式对应修改为中文规范（章节命名对照见 7c.1），**zh-to-en** 模式先用中文笔记走英文规则再对照 7c.3 转换。

#### 摘要

| 规则 | 要求 |
|------|------|
| 长度 | **en:** 150-250 words / **zh:** 300-500 字 |
| 结构 | 问题 → 方法 → 关键结果（带具体数据） → 意义 |
| 自包含 | 不依赖正文，独立可读；无引用编号；无未定义缩写 |
| 中英文 | **en 模式：** 仅英文 / **zh 模式：** 中英双语，独立撰写非机械翻译 / **zh-to-en：** 写英文即可 |

> ❌ "The experimental results demonstrate the effectiveness of the proposed method."
> ✅ "在 5 kW 加热功率下，冷板方案将电池最高温度控制在 42.3°C，较基线降低 8.5°C。"

#### 引言 / 绪论

| 规则 | 要求 |
|------|------|
| 三层递进 | 大背景（行业/领域问题）→ 子领域现状与 gap → 本文贡献（3-5 条） |
| 第一页即可读 | 读完引言后能回答：做了什么？为什么重要？与别人有何不同？ |
| 贡献条目 | 3-5 条，每条不超过两行；每条标注对应章节 |
| 结尾导航 | 简述后续各节内容 |

> ❌ "With the rapid development of electric vehicles, thermal management has become increasingly important."
> ✅ "直流快充桩在 350 kW 功率下，充电枪接口温度可在 15 分钟内升至 120°C 以上——这是制约充电速度提升的瓶颈。"

#### 相关工作 / 文献综述

| 规则 | 要求 |
|------|------|
| 按主题分组 | 按子问题/方法流派分组评述，**禁止按论文逐条罗列**（"X did A. Y did B." 是典型 AI 模式） |
| 每组末尾对比 | 明确"本文与这些工作的不同之处在于..." |
| 不贬低 | 指出已有工作的优劣势，不要为抬高自己贬低他人 |

> ❌ "Zhang (2019) proposed X. Li (2020) used Y. Wang (2021) combined X and Z."
> ✅ "冷板流道设计已有工作分为两类：基于经验公式的参数化优化（Zhang, 2019; Li, 2020），以及基于数值仿真的拓扑优化方法（Liu, 2022; Kim, 2023）。本文的方法在以下方面与这些工作不同..."

#### 方法 / 实验方案

| 规则 | 要求 |
|------|------|
| 先符号，后公式 | 所有符号在公式出现前先定义；公式旁有文字直觉解释 |
| 按逻辑顺序 | 不按时间线写；按逻辑递进组织 |
| 图表在引用后出现 | 正文第一次引用后才出现图或表 |
| 可复现 | 提供足够参数/设置让读者能复现 |

> ❌ "The loss function is L = MSE(y, y') + λ‖w‖²"
> ✅ "损失函数由两部分组成：均方误差（MSE）衡量预测偏差，L2 正则化项 ‖w‖² 防止过拟合——"
>    `L = MSE(y, y') + λ‖w‖²  (1)`

#### 实验与结果

| 规则 | 要求 |
|------|------|
| 以研究问题开头 | 先陈述要回答什么问题，再给数据 |
| 图表自包含 | 图题（Figure caption）写完整：什么实验、什么条件、什么观察、什么结论 |
| 数据→分析→解释 | 三层递进：给数据 → 分析趋势 → 解释物理/工程含义 |
| 与 baseline 对比 | 每个实验有明确对比基线，说明选基线的理由 |

> ❌ "The results are shown in Figure 3."
> ✅ "图 3 展示了不同流量下冷板表面温度分布。当流量从 2 L/min 增至 5 L/min 时，最高温度从 52.3°C 降至 42.1°C——但继续增至 8 L/min 时温度仅再降 1.2°C，说明泵功的边际收益在 5 L/min 后急剧下降。"

#### 结论

| 规则 | 要求 |
|------|------|
| 不是摘要的复读 | 总结贡献（与引言中贡献条目一一对应），非重述全文 |
| 诚实说局限 | 明确列出 2-3 条局限性或未解决问题 |
| 具体未来方向 | 不说"未来将探索更多应用"——说具体的下一步计划 |

> ❌ "In conclusion, this paper presents a novel approach. Future work will explore more applications."
> ✅ "本文提出了一种冷板流道拓扑优化方法，在 5 kW 加热功率下将电池温升降低 8.5°C。两个局限：① 高环境温度（>45°C）下泵功消耗增加 30%；② 温均性拐点的物理机制尚不清楚。后续将建立流固耦合多尺度模型以揭示这一现象。"

#### 7d.1 段落与句子级自查 ← nature-writing workflow Steps 3/5/6/7

> **与防幻觉机制的关系：** 防幻觉管"内容真实不真实"（数据不能编、引用不能虚构），以下检查管"表达准确不准确"（动词是否夸大、段落是否清晰）。前者是地基——假的不能写；后者是装修——真的也要写得好。

写完每节后，做四件事：

**① 每段一个工作（One paragraph, one job）← nature-writing Step 3**

每段只做一件事。可选的工作类型只有 8 种：

```
context / gap / approach / result / comparison / mechanism / implication / limitation
```

如果一段做了两件事（比如既讲方法又讲结果），拆成两段：

> ❌ "The simulation used a k-ε turbulence model with 2M mesh elements. The results showed a 12% reduction in pressure drop compared to the baseline."
> ✅ 拆为两段：
>   [approach] "The simulation used a k-ε turbulence model with a 2M-element unstructured mesh..."
>   [result] "Under these conditions, the pressure drop was reduced by 12% compared to the baseline (Figure 5a)."

**② 从证据向外写（Draft from evidence outward）← nature-writing Step 4**

不要把观点堆在段首、证据扔在段尾。每段的顺序是：证据/数据 → 解释 → 结论，或者 结论 → 证据 → 解释，但不能"结论 → 结论 → 结论"而不展示证据。

> ❌ "Our method outperforms all baselines. It achieves state-of-the-art results. The improvements are significant across all metrics."
> ✅ "Table 2 compares our method with three baselines on five metrics. Our method achieves the highest score on four of five metrics—the exception being metric E where baseline B leads by 1.2%. The consistent improvement suggests that the topology-optimized channel geometry is the primary driver."

**③ 校准动词强度（Calibrate verbs to evidence strength）← nature-writing Step 5**

| 证据强度 | 可用动词 | 不可用 |
|---------|---------|--------|
| 有统计显著性 + 大样本 + 严格对照 | show, demonstrate, establish | — |
| 有趋势但样本量不足 / 无统计检验 | suggest, indicate, point to | show, demonstrate, prove |
| 有间接证据或理论推导 | may, could, is consistent with | show, suggest |
| 纯推测 / 无数据支撑 | 不写，或显式标注为 speculation | 所有事实性动词 |

> ❌ "The results prove that topology optimization is the best approach for cold plate design."
> ✅ "The results suggest that topology optimization outperforms parametric optimization in pressure-drop-constrained designs (p < 0.05, n=15). However, this conclusion is specific to the Reynolds number range tested (Re=500-2000) and may not generalize to laminar regimes."

**④ 清除虚假新颖性声明（Remove unsupported novelty claims）← nature-writing Step 6**

扫描全文，检查以下词是否被滥用：

```
first, first-ever, unprecedented, unique, revolutionary, groundbreaking,
comprehensive, complete, fully, always, never, for the first time
```

每个出现的地方，自问：**"有没有文献可以反驳这个声明？"**

> ❌ "This is the first study to apply topology optimization to cold plate design."
> ✅ "To our knowledge, topology optimization has been applied to heat sinks and microchannel heat exchangers, but its application to electric-vehicle cold plates with manufacturing constraints is new. The closest work is Kim (2023), who used density-based topology optimization for a generic liquid-cooled heat sink without manufacturing considerations."

**⑤ 段落流检查（Paragraph flow check）← nature-writing Step 7**

每段检查三点：

```
- 一段一个信息。首句是该段的主题/声明。
- 后续每句与上一句有显式关系：因果 / 对比 / 限制条件 / 举例。
- 如果没有关系，删掉或移到别的段。
```

快速自检：遮住首句，后面还能看懂这段说什么吗？能看懂 → 首句不是主题句，需要改。

### 论文结构模板（通用回退）

当用户跳过 paper_type 选择或需要快速启动时：

```
en 模式：
1. Title & Abstract
2. Introduction (3-layer: background → gap → contributions)
3. Related Work (thematic grouping, no laundry list)
4. Method (symbols before equations, intuition alongside)
5. Experiments (start with research question, self-contained figures)
6. Conclusion (contributions + limitations + specific future work)
7. References

zh 模式：
1. 摘要（中英双语，独立撰写）
2. 绪论/引言（三层递进 → 贡献 3-5 条）
3. 文献综述（按主题分组）
4. 方法/实验方案（先符号后公式）
5. 实验与结果/结果与分析
6. 结论与展望（贡献 + 局限 + 未来方向）
7. 参考文献（GB/T 7714 格式）
```

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

### 7e: 实时引文支撑 ← nature-citation

> 当前的引用流程是"写完一章→手动回想哪个 PDF 能支撑→贴引用"。nature-citation 提供了"分段→解析→搜索→保守评估→导出"的七步引文工作流。将引文搜索前移到写作过程中——写完一段，实时匹配引用，不只限于已下载的 PDF。

#### 引文支撑的两种模式

| 模式 | 适用场景 | 引用来源 | 触发时机 |
|------|---------|---------|---------|
| **已下载库匹配** | 用户已有大量 PDF（Step 5 产出），从已读文献中匹配 | 仅已下载的 PDF + 检索文献表 | 每段写完后快速匹配 |
| **扩展搜索** | 已下载文献不够，或某条声明需要更权威/更新/更高分的支撑 | 已下载 PDF + 目标期刊范围实时搜索（Nature/CNS/目标期刊） | 用户表示"这里需要更强的引用"时 |

#### 分段引用工作流（借鉴 nature-citation 的 7 步）

```
写完一段正文 →
  ① Segment（分段）: 将段落拆为可引用的声明（claim）片段
     例: "冷板流道拓扑优化可降低泵功" → claim 1
         "但高流量下温均性出现拐点" → claim 2
         "这与 Zhang (2023) 的 CFD 仿真结果一致" → claim 3（已有引用）
  ② Parse（解析）: 每个 claim 提取关键词 + 判断是否需要新引用
     - claim 1: 已有检索文献表中的 [liu_topology_2025] 支撑 → ✅ 已有引用
     - claim 2: 是新发现，已下载文献中无对应支撑 → ⚠ 需要搜索
  ③ Search（搜索）: 对需要新引用的 claim，按期刊范围搜索
     - 默认范围：已下载文献（Step 5 产出）
     - 扩展搜索：按 target_journal_scope 扩大范围
  ④ Evaluate（保守评估）: 不因标题相关就推荐——必须打开摘要验证
     每个候选文献标注 Support Level:
       ✅ Strong: 摘要直接支撑该 claim，可引用具体数据
       🟡 Moderate: 主题相关但需谨慎引用
       ❌ Weak: 标题相关但摘要不支撑（不推荐）
  ⑤ Export（导出）: 输出为 Zotero RDF / .bib / RIS 格式
  ⑥ Report（报告）: 每段写完后简要报告引文匹配结果
      "本段 3 个声明，2 个已有引用支撑，1 个需要新引用——
       以下是找到的 2 篇候选文献..."
  ⑦ 用户确认后写入引用标注
```

#### 对话示例

```
助手：这段关于"温均性拐点"的结论——检索文献表中没有直接支撑这个发现的文献。
      我搜索了一下，找到 2 篇候选：

      ① [Strong] Kim et al. (2024) "Flow uniformity limits in minichannel
         cold plates" — 在 5 L/min 附近观察到了类似的温均性拐点
         → 可以作为对比讨论的引用
      ② [Moderate] Chen et al. (2023) "Temperature distribution in
         liquid-cooled battery packs" — 主题相关但讨论的是电池包层级
         → 可以引用但需要说明与本研究的差异

      建议引用①在讨论部分，②可选。要加到参考文献列表吗？
用户：加①，②不要了。
助手：好的，已标注 [Kim-2024] 并加入参考文献列表。继续下一段？
```

#### 引用密度指南

| 章节 | 建议引用密度 | 说明 |
|------|:---:|------|
| 引言 | 每 2-3 句 1 条引用 | 背景陈述和 gap 识别需要密集引用 |
| 相关工作 | 每段 3-8 条引用 | 按主题分组引用，非每句必引 |
| 方法 | 每段 1-2 条引用 | 仅引用直接相关的方法论文 |
| 实验 | 每段 1-3 条引用 | baseline 方法和对比结果需要引用 |
| 讨论 | 每段 2-4 条引用 | 与已有结论对比，需引用支撑 |
| 结论 | 0-1 条引用 | 通常不引用新文献，引自己的贡献即可 |

### 引用与参考文献要求

> 以下要求与 7e 实时引文支撑配合使用。

- 正文中每处引用标注索引：`[1]`、`[2, 5]`
- 参考文献列表包含：DOI、作者、标题、期刊/会议、年份、卷期页码
- **优先引用已下载的 PDF**（防幻觉），**补充引用实时搜索的新文献**（经摘要验证后）
- 引用内容与原文一致（不得自行编造数据或结论）
- 参考文献 20-40 条为宜，其中至少 60% 来自 Step 5 已下载文献

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

### 引用格式

| language | 格式 | 适用场景 | 示例 |
|----------|------|----------|------|
| **en** | 编号引用 [1] | IEEE 会议/期刊 | "...research [1, 2] shows..." |
| **en** | 作者-年份 (Author, Year) | Elsevier / Springer | "...research (Zhang, 2023) shows..." |
| **zh** | 顺序编码制 [1] | 多数中文理工科期刊 | "...研究[1, 2]表明..." |
| **zh** | 著者-出版年 (作者, 年) | 部分中文社科期刊 | "...（张三, 2023）指出..." |
| **zh-to-en** | 按目标期刊选择 | IEEE / APA / Nature | 基于 7a 确定的投稿目标 |

**GB/T 7714-2015 常见条目格式 (zh)：**
```
期刊论文：  作者. 题名[J]. 刊名, 年, 卷(期): 起止页码.
学位论文：  作者. 题名[D]. 城市: 学校, 年.
会议论文：  作者. 题名[C]// 会议录名. 出版地: 出版者, 年: 起止页码.
专著：      作者. 书名[M]. 版本. 出版地: 出版者, 年.
电子文献：  作者. 题名[EB/OL]. (发布日期)[引用日期]. URL.
```

### 产出文件

- `论文初稿.md` — 含完整结构和参考文献的初稿，标注 paper_type + language + 引用格式
- **zh-to-en 模式额外产出：** `中→英术语对照表.md`

---

### 7f. 同行评审仿真（质量门） ← nature-response

> 保留原有的五维量化评分框架（0-10 分 + 权重），补充 rebuttal letter 预演——投稿前逐条预演审稿回复，暴露"以为能说服审稿人、实际说服不了"的薄弱环节。

#### 7f.1 五维度评审框架

初稿完成后，从 5 个维度量化评估初稿质量：

| 维度 | 权重 | 检查要点 |
|------|------|----------|
| 原创性（Originality） | 20% | 研究问题是否有新意？贡献是否清晰且区别于已有工作？ |
| 方法严谨性（Rigor） | 25% | 实验/仿真设置是否合理？控制变量是否明确？样本量是否充分？ |
| 证据充分性（Evidence） | 25% | 结论是否有充分数据支撑？图表是否与论证一致？统计方法是否正确？ |
| 论证连贯性（Coherence） | 15% | 逻辑链是否完整？gap → 方法 → 结果 → 结论是否自洽？ |
| 写作质量（Writing） | 15% | 表达是否清晰？术语是否统一？有无明显 AI 痕迹？ |

> 注：五维度框架已被 Step 2b 大纲评审复用——两处使用同一套评分体系，保持一致性。

#### 7f.2 三审稿人视角 ← nature-reviewer

> **与五维评分的关系：** 五维评分告诉你"哪里弱"（量化），三审稿人告诉你"审稿人会怎么描述这个问题"（叙事）。两者互补——评分定位问题维度，审稿人报告模拟真实审稿场景。

在五维评分完成后，从三个不同的审稿人视角重新审视论文：

| 审稿人 | 侧重维度 | 核心问题 |
|--------|---------|---------|
| **Reviewer A** | 方法严谨性（对应 Rigor 维度） | 实验/仿真设置是否合理？控制变量是否明确？是否可复现？ |
| **Reviewer B** | 创新性与意义（对应 Originality 维度） | 贡献是否清晰区别于已有工作？谁会读这篇论文？ |
| **Reviewer C** | 清晰度与完整性（对应 Coherence + Writing 维度） | 论证链是否完整？非本领域读者能看懂吗？图表是否自包含？ |

**每份审稿人报告格式：**

```
Reviewer [A/B/C]

## Overall Assessment
[一段话总体评价——与五维评分对应维度的分数呼应]

## Major Concerns（必须修改）
1. [具体问题，标注到章节/段落]
2. ...

## Minor Concerns（建议修改）
1. [具体问题，标注到章节/段落]
2. ...

## Questions to Authors
1. [审稿人不理解/需要澄清的问题]
2. ...
```

**边界规则（遵循 nature-reviewer 的 default stance）：**
- 三位审稿人仅侧重点不同——不编造审稿人身份、专业、机构或履历
- 不声称编辑的最终决定或对特定期刊的适合性
- 区分三类判断：有支撑 / 薄弱 / 无法从现有材料中评估
- 如果提供的材料不完整（仅某章/节），标注评估边界

#### 7f.3 评审流程

1. 每维度给出 0-10 评分 + 具体问题定位（标注到章节/段落）
2. 针对评分 < 6 的维度提供修改建议
3. **限 2 轮修改**——第 1 轮根据评审意见修改，第 2 轮验证
4. 第 2 轮后仍未解决的问题 → 标注为"Acknowledged Limitations"
5. 评分低于 5 的维度 → 建议回到 Step 1-6 对应环节补足

#### 7f.4 Rebuttal Letter 预演 ← nature-response

> **核心思路：** 不等真实投稿被审稿人指出问题，在质量门阶段就预演 rebuttal——暴露论文中"你以为能说服审稿人、实际上说服不了"的薄弱环节。

**预演流程：**

```
1. 基于五维评分中 < 6 的问题 + 三审稿人报告中的 Major Concerns，
   逐条生成 rebuttal 草稿：
   ┌──────────────────────────────────────────────────────┐
   │ 问题: 样本量 n=3 不足以支持结论 (Evidence 维度, 5/10)  │
   │                                                        │
   │ Response:                                              │
   │   We agree that n=3 is limited. However, each sample   │
   │   was tested under 5 independent thermal cycles with   │
   │   <2% variance between cycles per sample, suggesting   │
   │   high within-sample consistency. We have added a note │
   │   on sample-size limitations to Section 5.2.            │
   │                                                        │
   │   [self-check: Does this response actually address the │
   │    concern? → Partially. The n IS small.               │
   │    → 建议在修改中补充 n=5 的额外实验]                   │
   └──────────────────────────────────────────────────────┘

2. Self-check 是核心价值——
   如果预演时发现"这个回复说服不了人"，就回到论文补充修改

3. 遵守 nature-response 的红线：
   - 不含对抗性语言（"The reviewer is wrong"）
   - 不承诺未做的工作（"We will do X" → 改为"We have added X"）
   - 每条回复都标注在文稿中做了哪些具体修改
```

**对话示例：**

```
助手：Evidence 维度（5/10）——样本量 n=3 是主要扣分项。预演一下 rebuttal：
      "...We acknowledge the limited n=3. However, each sample underwent
      5 independent cycles with <2% intra-sample variance, suggesting
      the observed trends are robust within the tested range."

      Self-check: "intra-sample variance low" 能说服审稿人吗？
      → 不太能。审稿人会说你仍然只测试了 3 个独立样本。
      → 建议：在修改阶段补做 n=5 的实验（如果能），否则在 Limitations
        中明确标注这是论文的主要局限。
用户：n=5 来不及了... 先标 Limitations 吧。
助手：好，那这条 rebuttal 就如实写"n=3 is a limitation we acknowledge"，
      不走"intra-sample variance" 的辩护路线——后者会被审稿人看穿。
```

#### 产出文件

- `评审报告.md` — 五维评分表 + 逐维度问题定位 + 修改优先级
- `rebuttal-预演.md` — 逐条问题 → response 草稿 + self-check 结论
- 修改后的 `论文初稿.md`（第 2 轮后）

---

> **下一步 → Step 8：** 同行评审通过 + rebuttal 预演无遗漏后，进入精炼润色、去 AI 痕迹，提升至可投稿水平。

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
