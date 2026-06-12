# Step 5: 统一批量下载 (Unified Download Router)

> **默认串行可靠：** 英文三轮顺序（Sci-Hub → SD CDP → Generic CDP），中文 CDP（CNKI/万方）与英文 CDP 默认串行执行，避免共享浏览器状态互相干扰。需要加速时可显式使用 `--parallel-phase1`，但不作为默认策略。IEEE 已归入 Generic CDP，`download_via_ieee.py` 保留作为手动 fallback。

---

## 1. 启动前读取 (Pre-read Checklist)

执行本步骤前，必须确认以下文件已加载：

- [ ] `agents/step_4_search_score.md` — 检索文献表（含 DOI 和 Tier 分级；直达下载模式下可缺失）
- [ ] `config/publishers.toml` — 出版社下载策略配置
- [ ] `references/publisher-access-matrix.md` — 各出版商下载可行性对照表
- [ ] `.skill-state/error_log.md` — 已知下载错误及修复规则
- [ ] `.skill-state/decision_log.md` — 下载策略相关决策

---

## 2. 适用任务 (Applicable Tasks)

- 从检索文献表批量下载 PDF
- 用户直接提供 DOI 列表、论文标题列表、BibTeX、URL 或混合参考文献时，先归一化为下载清单再下载
- 按 DOI 前缀自动路由到最优下载策略
- 单篇测试下载
- 会话状态检查
- 下载记录追踪

---

## 3. 不适用任务 (Non-applicable Tasks)

- 文献检索 → 路由到 `agents/step_4_search_score.md`
- Zotero 文库管理 → 路由到 `agents/step_6_zotero.md`
- 浏览器中人工逐篇点击下载 → 使用各专用脚本或用户手动处理

---

## 4. 输入要求 (Input Requirements)

| 输入 | 来源 | 格式 | 必选 |
|------|------|------|:--:|
| 检索文献表 | Step 4 | .md | 批量模式必选 |
| workflow search results | Step 4 / 用户提供 | workflow JSON | 可直接作为下载入口 |
| DOI/标题/URL/参考文献列表 | 用户直接提供 | pasted text / .txt / .md / .bib | 直达下载模式必选其一 |
| direct_download_manifest | Step 5 生成 / 用户提供 | .md/.json | 标题/混合输入时必选 |
| 中文论文元数据 | Step 4 或 Step 5 生成 | 中文论文元数据.json | 中文下载必选 |
| CDP Chrome 浏览器 | 用户启动 | 端口 9223 | ✅ |

---

## 5. 标准输出 (Standard Outputs)

| 输出 | 格式 | 说明 |
|------|------|------|
| 下载的 PDF | .pdf | 保存到 paper-temp/ |
| 下载记录 | paper-temp/download_log.md | 逐篇追踪状态 |
| direct_download_manifest.md/json | .md/.json | 直达下载模式的临时归一化清单 |
| unresolved_download_items.md | .md | 标题无法唯一解析、缺少 URL 或需要人工确认的条目 |

---

## 6. 执行流程 (Execution Flow)

### 6a. 直达下载入口判定 🆕

当用户没有经过 Step 1-4，直接发送 DOI、论文标题、URL、BibTeX 或参考文献列表时，不要求用户补跑完整检索流程。Agent 必须先把输入归一化为可下载清单，再进入原有下载路由。

| 输入类型 | 识别方式 | 处理路径 | 是否需要用户确认 |
|----------|----------|----------|------------------|
| DOI 列表 | `10.xxxx/...`、`doi:`、`https://doi.org/...` | 归一化 DOI → `--papers` 或 DOI 文件 → 英文路由 | 不需要，除非 DOI 异常 |
| 英文论文标题 | 无 DOI，英文标题/参考文献文本 | 先查 DOI / OA URL / 出版社页 → 生成 manifest | 多候选或低置信度时需要 |
| 中文论文标题 | 中文题名、无 DOI | 先查 CNKI/万方 article_url/source_id → 生成 `中文论文元数据.json` | 多候选或缺链接时需要 |
| BibTeX / RIS / 参考文献段落 | 含 title/doi/url/year/journal | 优先抽 DOI；无 DOI 的标题进入解析队列 | 解析不唯一时需要 |
| 出版社 URL / CNKI / 万方 URL | URL 域名可识别 | 英文 URL 尝试抽 DOI；中文 URL 直接生成中文元数据 | 通常不需要 |

**直达模式原则：**

1. DOI 是最高优先级下载键；能抽到 DOI 时，不再要求用户提供 Step 4 的检索文献表。
2. 标题不能直接进入下载器，必须先解析为 DOI、OA PDF URL、出版社 article URL，或中文 `article_url`。
3. 不得为了推进下载猜测 DOI。标题匹配到多个候选、年份/作者冲突或置信度不足时，写入 `unresolved_download_items.md` 并请用户确认。
4. 中文论文多数没有真实 DOI，必须以 `source=cnki|wanfang` + `article_url` 或 `source_id` 路由，不把 `cnki.xxx` / `wanfang.xxx` 当作英文 DOI。
5. 直达模式只做“用户指定文献下载”，不生成 Step 4 的评分、Tier、饱和度或 PRISMA 报告。
6. 直达模式只需要确认下载清单和登录状态；不得要求用户补跑 Step 1-4。
7. 所有入口先归一化为 `DownloadManifestItem` 语义：`item_id`、`title`、`doi`、`source`、`source_id`、`article_url`、`route_key`、`status`、`confidence`。旧 `direct_download_manifest.md/json` 可继续使用，但内部语义以 workflow contract 为准。

**Direct-entry input contract：**

| 可接受输入 | 推荐命令/处理 | 降级规则 |
|------------|---------------|----------|
| DOI 列表或 `--papers` | `unified_download_router.py --papers "...“ --dry-run` | DOI 异常进入 unresolved |
| `workflow-contracts.v1` search results JSON | `unified_download_router.py --workflow-results results.json --dry-run` | 缺 DOI 但有中文 article_url 仍可下载 |
| direct download manifest JSON | `unified_download_router.py --download-manifest manifest.json --dry-run` | 只下载 `status=ready` |
| CNKI/Wanfang URL | 转为 `source=cnki|wanfang` + `article_url` | 缺 URL 不猜测，进入 unresolved |
| 标题或参考文献文本 | 先解析 DOI/article_url/source_id | 多候选或低置信度时等待用户确认 |

**direct_download_manifest 推荐格式：**

```markdown
# Direct Download Manifest

| item_id | input_text | title | doi | source | article_url | publisher | confidence | status |
|---------|------------|-------|-----|--------|-------------|-----------|------------|--------|
| dd-001 | 10.1016/... | ... | 10.1016/... | doi |  | Elsevier | 1.00 | ready |
| dd-002 | 中文论文标题 | ... | wanfang.xxxx | wanfang | https://... | 万方 | 0.92 | ready |
| dd-003 | ambiguous title | ... |  | unresolved |  |  | 0.55 | needs_user_confirm |
```

**执行分流：**

- DOI-only：直接运行 `python3 scripts/unified_download_router.py --papers "10.x,10.y" --dry-run` 预览路由。
- workflow JSON：直接运行 `python3 scripts/unified_download_router.py --workflow-results workflow_search_results.json --dry-run` 预览 DOI + 中文 URL 混合路由。
- DOI + 中文 URL：优先生成 manifest JSON 后用 `--download-manifest`；兼容路径是英文 DOI 用 `--papers`，中文条目写入 `中文论文元数据.json` 后用 `--chinese-input`。
- 标题-only：先完成解析和 manifest，再只对 `status=ready` 的条目启动下载。

### 6b. CHECKPOINT W — CP-DOWNLOAD-LOGIN 🚧 精准触发规则

> **两个独立门控，分阶段触发。Sci-Hub 不需要门控。中文和英文各自独立确认。门控由 access_probe 结果触发，不由 publisher strategy 一刀切触发。**

**不触发范围：** Sci-Hub、OA / `direct_http`、`skip`、校园 IP 已可访问、已有 cookie/session 已可访问。

**触发范围：** login wall、access denied、CARSI required、PDF link 缺失且页面显示权限不足。

**access_probe 判定表：**

| access_probe | 含义 | 是否触发 CP-DOWNLOAD-LOGIN |
|--------------|------|:--:|
| `scihub` | Sci-Hub 轮次处理，免费路径 | 否 |
| `direct_http` / `oa` | OA 或直接 HTTP 下载 | 否 |
| `skip` | 自动化不可行或需人工下载 | 否 |
| `ip_access_ok` | 校园 IP / VPN 已授权，可访问 PDF | 否 |
| `cookie_access_ok` | CDP 中已有可用登录 cookie/session | 否 |
| `login_required` | 出版商登录墙或 SSO 页面 | 是 |
| `access_denied` | 页面显示无权限/未订阅/无法下载 | 是 |
| `carsi_required` | CNKI/万方需要 CARSI 机构登录 | 是 |

> **重要：** 没有 cookie 不等于没有权限。校园网 IP 授权通常没有个人 cookie，只要实际 article/PDF probe 可访问，就应判为 `ip_access_ok`，不得要求用户登录。

**中文门控（Phase 1）：** 仅当 CNKI/万方 preflight 或 article probe 返回 `carsi_required` / `login_required` / `access_denied` 时触发。

**英文门控（Phase 2）：** Sci-Hub 完成后，仅对剩余英文论文中 `access_probe` 需要登录的 publisher 触发。

**执行流程：**

```
Phase 1:
1. Sci-Hub 后台启动（免费，不阻塞）
2. 🔍 中文源 access_probe
   ├─ ip_access_ok / cookie_access_ok → 直接执行中文下载
   └─ carsi_required / login_required / access_denied → 显示中文登录门控
3. 🚧 中文登录门控（仅 probe 需要时显示）
   "CNKI/万方需要 CARSI 机构登录。
    🚀 Agent 将自动启动交互式 CDP 会话（同一条命令内，不会断连）。"
4. 🚀 Agent 执行交互式 CDP 启动（使用 batch_chinese_search.sh --login-only）：
   a) Agent 启动一条长驻 exec_command（yield_time_ms=60000）：
        bash scripts/batch_chinese_search.sh --login-only
   b) 脚本自动处理：
      ├─ 端口 9223 已有 CDP → 复用
      └─ 无 CDP → 自动启动 Chrome → 导航到 CNKI/万方 → 等待就绪
   c) 脚本打印 === LOGIN_REQUIRED === 后阻塞等待 stdin
   d) Agent 告知用户：「Chrome 已自动打开并导航到 CNKI/万方，请完成 CARSI 登录后回复「已登录」」
   e) 用户完成登录后回复「已登录」
   f) Agent 调用 write_stdin("go\n")，脚本继续
   g) 脚本打印 CHINESE_CDP_READY → Agent 确认 CDP 可用
5. Agent 执行 Chinese CDP 下载（unified_download_router.py 连接同一 9223 端口）

Phase 2:
6. 等待 Sci-Hub 完成
7. 对剩余英文 CDP 论文执行 access_probe
   ├─ direct_http / oa / ip_access_ok / cookie_access_ok → 直接下载
   └─ login_required / access_denied → 🚧 英文登录门控
   Agent 执行同样的交互式 CDP 启动，导航到对应出版社首页：
   "[ScienceDirect CDP]  elsevier (sciencedirect.com)
    [Generic CDP]  ieee (ieeexplore.ieee.org), acs (pubs.acs.org), ..."
8. 🚀 Agent 自动启动交互式 CDP 会话（同一条命令内）：
   a) 启动 exec_command：检查/启动 CDP Chrome → 导航到出版社首页
   b) 打印 === LOGIN_REQUIRED === → 用户登录后告知 → Agent write_stdin("go\n")
   c) 脚本确认 CDP 可用后退出
9. Agent 执行 English CDP 下载（R2 SD → R3 Generic）
```

**强制要求：**
- Agent 禁止在用户确认登录前调用 `unified_download_router.py`（除 `--dry-run` 外）
- Agent 必须先运行 `--dry-run` / `--test` / `--check-session` 或等价 article/PDF access probe，再提示登录
- 推荐使用 `--require-login-confirm` 参数启动路由器，由脚本层面再次门控
- **CDP 启动和下载如果跨命令，必须在同一条 exec_command session 内完成**
- checkpoint 块的 `entry_mode` 可为 `normal_chain` 或 `direct_entry`；`status` 必须在用户明确“已登录，确认 CP-DOWNLOAD-LOGIN”或等价明确语义后才可视为 confirmed。

**命令示例：**

```bash
# 子阶段 A：先 dry-run 查看需要登录的出版社
python3 scripts/unified_download_router.py 检索文献表.md --dry-run

# 子阶段 B：交互式启动 CDP + 登录 (Phase 1 中文门控)
#   Agent 启动长驻命令，等待用户登录后 write_stdin 继续
bash scripts/batch_chinese_search.sh --login-only

# 子阶段 C：用户确认后 (同一条命令内) 执行中文下载
#   Agent 新开命令（CDP 端口仍然存活）
python3 scripts/unified_download_router.py 检索文献表.md \
  --chinese-input 中文论文元数据.json \
  --output paper-temp/ --require-login-confirm

# 子阶段 D：同上方式处理英文 CDP (Phase 2 英文门控)
#   Agent 先交互式确认登录 → 再执行下载（同一 CDP 端口）

# 完整下载流程（跳过交互式登录，仅 OA/免费来源时使用）
python3 scripts/unified_download_router.py 检索文献表.md --output paper-temp/

# 单篇测试
python3 scripts/unified_download_router.py --test 10.1021/acsnano.4c00001 --port 9223

```
Phase 1 ──────────────────────────────────────────────────
  Sci-Hub 启动（后台线程，免费，不需登录）
  🔍 中文源 access_probe
     ip_access_ok / cookie_access_ok → Chinese CDP 启动
     carsi_required / login_required / access_denied → 用户确认 → Chinese CDP 启动
     Sci-Hub 和 Chinese CDP 可能同时跑

Phase 2 ──────────────────────────────────────────────────
  等待 Sci-Hub 完成
  若剩余英文 CDP 论文（SD / Generic）:
    🔍 英文 access_probe
       ip_access_ok / cookie_access_ok → 直接执行 CDP
       login_required / access_denied → 用户确认
       → English CDP 启动（R2 SD → R3 Generic）

Phase 3 ──────────────────────────────────────────────────
  合并 Sci-Hub + Chinese CDP + English CDP 结果
  → download_log.md + final summary
```

> **Sci-Hub 不受任何门控。** 中文门控和英文门控各自独立，分阶段触发。共享同一 CDP 端口 9223。

### 6c. 英文路由矩阵（DOI 前缀驱动）

| 轮次 | DOI 前缀 | 出版商 | 策略 | 成功率 |
|------|----------|--------|------|--------|
| **R1: Sci-Hub** | 不限（2021年前） | 全部 | Sci-Hub CDP | 9/13 镜像可用 |
| **R2: SD CDP** | `10.1016/` | Elsevier | 专有混合策略 | 96% (180/185) |
| **R3: Generic CDP** | `10.1109/` | IEEE | Generic CDP 策略 B（文章页 stamp URL 提取） | 需 SSO |
| | `10.1002/` | Wiley | pdfdirect URL → 文章页选择器 | 策略A优先 |
| | `10.1021/` | ACS | 直连 PDF URL → 文章页选择器 | 策略A优先 |
| | `10.1039/` | RSC | 文章页 articlepdf 选择器 | 策略B为主 |
| | `10.1007/` | Springer | 直连 content/pdf URL | 策略A优先 |
| | `10.1063/` | AIP | 文章页 + 加载页等待 | 含"请稍候"检测 |
| | `10.1038/` | Nature | 直连 article.pdf / OA HTTP | OA可直连 |
| | `10.1126/` | Science | 直连 PDF URL | 策略A优先 |
| | `10.1073/` | PNAS | 直连 PDF URL | 策略A优先 |
| | `10.1103/` | APS | 文章页 slug 解析 + 选择器 | slug解析 |
| | `10.1088/` | IOP | 直连 article/pdf URL | 策略A优先 |
| | `10.1080/` | T&F | 文章页选择器提取 | 策略B为主 |
| | `10.1116/` | AVS | AIP平台 加载页等待 | 同AIP |
| | `10.1149/` | ECS | IOP平台 文章页提取 | IOP族 |
| | `10.1364/` | OSA | 文章页选择器提取 | 策略B为主 |
| | `10.3762/` | Beilstein | 直连 OA | 开源 |
| | `10.31635/` | CCS Chem | 文章页选择器提取 | Cloudflare风险 |
| | `10.3389/` | Frontiers | 直连 HTTP（OA） | 无需认证 |
| | `10.3390/` | MDPI | **SKIP** | Akamai封锁 |
| | `10.2139/` | SSRN | 文章页选择器提取 | 预印本 |

### 6d. 中文路由矩阵（source 字段驱动）🆕

| 数据库 | 识别方式 | 下载入口 | 登录方式 |
|--------|----------|----------|----------|
| 中国知网 (CNKI) | `source=cnki` + `文章链接` 列 | 文章详情页 → CSS 选择器 → CDP Fetch | 校园网 IP 或 CARSI SSO |
| 万方数据 (Wanfang) | `source=wanfang` + `文章链接` 列 | 文章详情页 → CSS 选择器 → CDP Fetch | 校园网 IP 或 CARSI SSO |

> **中文论文路由说明：** CNKI/万方论文多数无真实 DOI（使用 `cnki.{hash}` / `wanfang.{hash}` 合成标识符），不进入英文 DOI 路由器。**优先使用 Step 4 产出的 `中文论文元数据.json`**（字段显式、无 Markdown 解析歧义；旧名 `chinese_papers.json` / `chinese_metadata.json` 仍可作为兼容输入），与英文管道通过 `ThreadPoolExecutor` 并行启动，共享同一 CDP 端口。若 JSON 缺失，回退到 Markdown 表格解析（`--chinese-input 检索文献表.md`）。缺少 `article_url` 的论文将被跳过。

### 6e. 命令参考

```bash
# 前检查：验证 CDP 浏览器 + 各出版商会话状态
python3 scripts/unified_download_router.py --check-session --port 9223

# 查看路由决策（不下载，不受登录门控限制）
python3 scripts/unified_download_router.py 检索文献表.md --dry-run

# 完整下载流程（带登录门控） 🆕
python3 scripts/unified_download_router.py 检索文献表.md --output paper-temp/ --require-login-confirm

# 跳过登录门控（仅 OA/免费来源，Agent 需确认无付费墙出版社）
python3 scripts/unified_download_router.py 检索文献表.md --output paper-temp/

# 中文+英文下载（推荐，使用 Step 4 产出的 中文论文元数据.json） 🆕
python3 scripts/unified_download_router.py 检索文献表.md --chinese-input 中文论文元数据.json --output paper-temp/ --require-login-confirm

# 仅中文下载（无英文 DOI）
python3 scripts/unified_download_router.py --chinese-input 中文论文元数据.json --output paper-temp/

# 中文下载兜底（JSON 缺失时，从 Markdown 表格解析）
python3 scripts/unified_download_router.py 检索文献表.md --chinese-input 检索文献表.md --output paper-temp/ --require-login-confirm

# 中文单篇测试 🆕
python3 scripts/unified_download_router.py --test-cnki "https://kns.cnki.net/kcms2/article/abstract?..." --port 9223
python3 scripts/unified_download_router.py --test-wanfang "https://www.wanfangdata.com.cn/details/..." --port 9223

# 跳过某些轮次
python3 scripts/unified_download_router.py 检索文献表.md --skip-scihub   # 全是新论文
python3 scripts/unified_download_router.py 检索文献表.md --skip-sd       # 无 Elsevier 论文

# 下载辅助材料（Supplementary Info）
python3 scripts/unified_download_router.py 检索文献表.md --include-si

# 内联 DOI 列表
python3 scripts/unified_download_router.py --papers "10.1021/x,10.1002/y,10.1016/z"

# 直达下载：用户只给 DOI 列表时先 dry-run，再正式下载
python3 scripts/unified_download_router.py --papers "10.1021/x,10.1002/y" --dry-run
python3 scripts/unified_download_router.py --papers "10.1021/x,10.1002/y" --output paper-temp/ --require-login-confirm

# 不同 CDP 端口
python3 scripts/unified_download_router.py 检索文献表.md --port 9225
```

### 6f. 下载记录

路由器自动生成 `paper-temp/download_log.md`，逐篇追踪：

| # | DOI | Status | Source | Size | Path |
|---|-----|--------|--------|------|------|
| 1 | `10.1016/...` | ✅ | SD CDP | 1024KB | paper_001.pdf |
| 2 | `10.1002/...` | ✅ | Generic CDP | 856KB | paper_002.pdf |
| 3 | `cnki.a1b2c3d4...` 🆕 | ✅ | Chinese CDP (CNKI) | 512KB | paper_003.pdf |
| 4 | `10.3390/...` | ⏳ | — | - | - |

### 6g. 出版社配置

所有出版社的下载策略（URL 模板、CSS 选择器、屏障检测规则）集中维护在：
[`config/publishers.toml`](config/publishers.toml)

新增出版商时，只需在该文件中添加一个 `[publishers.xxx]` 段落即可。

### 6h. 保留的专用脚本

以下脚本保持不变，路由器通过子进程调用它们（也可单独使用）：

| 脚本 | 用途 | 何时单独使用 |
|------|------|-------------|
| `download_via_scihub.py` | Sci-Hub 批量下载 | 只缺老论文时 |
| `download_via_ieee.py` | IEEE CDP 下载 | 只下 IEEE 论文时 |
| `auto_sd_downloader.py` | SD 全自动下载 | 只下 Elsevier 论文时 |
| `generic_publisher_downloader.py` | 通用CDP下载引擎 | 测试特定非SD/IEEE论文 |

### 6i. 核心设计原则

1. **默认所有论文都有访问权限** — 下不到是策略问题，不是权限问题
2. **默认串行，显式并行** — CNKI/万方和英文 CDP 默认串行，只有用户明确接受共享 CDP 风险时才使用 `--parallel-phase1`
3. **英文按 DOI 前缀路由，中文按 source 字段路由** — 两条线泾渭分明，互不污染
4. **`Fetch.enable` 必须在 `Page.navigate` 之前调用**（IEEE v1.0.1 验证）— 否则 Chrome PDF 查看器消费响应体
5. **出版商知识库集中维护** — `config/publishers.toml`，新增出版商只需加一个 `[publishers.xxx]` 段落
6. **IEEE 已归入 Generic CDP**，`download_via_ieee.py` 保留作为手动 fallback
7. **直达下载先归一化、再下载** — DOI 可直接路由，标题必须先解析为 DOI/URL/中文 article_url
8. **checkpoint 不是入口锁** — `CP-DOWNLOAD-LOGIN` 只阻塞需要登录态的下载执行，不阻塞 manifest 生成、dry-run、OA/Sci-Hub/direct_http 路径

---

## 7. 质量门槛 (Quality Gates)

- [ ] 如为直达下载模式：输入已分类为 DOI / 英文标题 / 中文标题 / URL / BibTeX
- [ ] 如含标题：已生成 `direct_download_manifest.md/json`，且仅下载 `status=ready` 条目
- [ ] 如有无法唯一解析条目：已写入 `unresolved_download_items.md`，未擅自猜 DOI
- [ ] CDP 登录门控已执行：Agent 已提示用户完成机构登录，用户已确认"已登录" 🆕
- [ ] CDP 浏览器已启动且端口可访问（`curl -s http://127.0.0.1:9223/json/version`）
- [ ] 会话状态已检查（`--check-session`）
- [ ] 下载已通过 `--require-login-confirm` 门控参数启动（或 Agent 已手动确认登录） 🆕
- [ ] 下载记录完整追踪每篇论文状态
- [ ] 下载失败的论文有明确的失败原因（非"未知错误"）

---

## 8. 收尾检查 (Closing Checks)

### 8a. 产出完整性
- [ ] PDF 已保存到 paper-temp/
- [ ] `paper-temp/download_log.md` 已生成
- [ ] 如为直达下载模式：`direct_download_manifest.md/json` 已保存；未解析条目已进入 `unresolved_download_items.md`
- [ ] 下载成功率和失败原因统计已输出

### 8b. 错误日志更新 🆕
- [ ] 本轮执行中是否出现新的下载失败模式？
  - 新的出版商屏障 → 追加到 `.skill-state/error_log.md` + 更新 `config/publishers.toml`
  - 新的 CDP 陷阱 → 追加到 `.skill-state/error_log.md` + 更新 `agents/known_pitfalls.md`
  - 会话过期的新触发条件 → 追加到 `.skill-state/error_log.md`

### 8c. 决策日志更新 🆕
- [ ] 是否调整了下载策略？（如新增 skip 规则）→ 记录到 `.skill-state/decision_log.md`

### 8d. 下一步提示
- [ ] 向用户明确说明下一步：管理 Zotero 文库（Step 6）
  > **下一步 → Step 6：** 下载完成后，管理 Zotero 文库：先生成架构，再将 PDF 导入对应集合。

---

## 9. 故障排除 (Troubleshooting)

常见问题参见 `agents/known_pitfalls.md`。本 Step 特有的问题：

- **CDP 端口无法连接**：检查 Chrome 是否以 `--remote-debugging-port=9223` 启动
- **用户只给标题**：先解析 DOI/URL；无法唯一匹配时不要下载，写入 `unresolved_download_items.md`
- **中文标题没有 DOI**：先通过 CNKI/万方补 `article_url`，再走中文 CDP，不进入英文 DOI 路由
- **会话过期**：`auto_sd_downloader.py` 自动检测并重启浏览器
- **PDF 标签页残留**：已修复（v2.1），每篇下载后自动关闭 PDF 标签页
- **重启死循环**：`skip_set` 机制自动跳过无权限论文
