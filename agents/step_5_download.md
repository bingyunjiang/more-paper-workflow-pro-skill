# Step 5: 统一批量下载 (Unified Download Router)

> **中英文双管道并行：** 登录门控后分叉启动。英文三轮顺序（Sci-Hub → SD CDP → Generic CDP），中文独立 CDP（CNKI/万方）。覆盖 24 家英文出版社 + 2 个中文数据库。IEEE 已归入 Generic CDP，`download_via_ieee.py` 保留作为手动 fallback。

---

## 1. 启动前读取 (Pre-read Checklist)

执行本步骤前，必须确认以下文件已加载：

- [ ] `agents/step_4_search_score.md` — 检索文献表（含 DOI 和 Tier 分级）
- [ ] `config/publishers.toml` — 出版社下载策略配置
- [ ] `references/publisher-access-matrix.md` — 各出版商下载可行性对照表
- [ ] `.skill-state/error_log.md` — 已知下载错误及修复规则
- [ ] `.skill-state/decision_log.md` — 下载策略相关决策

---

## 2. 适用任务 (Applicable Tasks)

- 从检索文献表批量下载 PDF
- 按 DOI 前缀自动路由到最优下载策略
- 单篇测试下载
- 会话状态检查
- 下载记录追踪

---

## 3. 不适用任务 (Non-applicable Tasks)

- 文献检索 → 路由到 `agents/step_4_search_score.md`
- Zotero 文库管理 → 路由到 `agents/step_6_zotero.md`
- 手动逐篇下载（非批量场景）→ 使用各专用脚本

---

## 4. 输入要求 (Input Requirements)

| 输入 | 来源 | 格式 | 必选 |
|------|------|------|:--:|
| 检索文献表 | Step 4 | .md | ✅ |
| CDP Chrome 浏览器 | 用户启动 | 端口 9223 | ✅ |

---

## 5. 标准输出 (Standard Outputs)

| 输出 | 格式 | 说明 |
|------|------|------|
| 下载的 PDF | .pdf | 保存到 paper-temp/ |
| 下载记录 | paper-temp/download_log.md | 逐篇追踪状态 |

---

## 6. 执行流程 (Execution Flow)

### 6.0 CDP 登录门控 🚧 硬性规则

### 6.0 CDP 登录门控 🚧 硬性规则

> **两个独立门控，分阶段触发。Sci-Hub 不需要门控。中文和英文各自独立确认。**

**中文门控（Phase 1）：** Sci-Hub 后台启动的同时立即触发。仅提示 CNKI/万方。

**英文门控（Phase 2）：** Sci-Hub 完成后触发。仅对剩余需 CDP 的英文论文提示。

**不适用范围：** Sci-Hub（免费访问）、OA 直连 HTTP 下载（Frontiers、Beilstein 等）。

**执行流程：**

```
Phase 1:
1. Sci-Hub 后台启动（免费，不阻塞）
2. 🚧 中文登录门控立即显示
   "CNKI/万方需要 CARSI 机构登录。
    🚀 Agent 将自动打开 Chrome 并导航到目标网站。
    • cnki (kns.cnki.net)
    • wanfang (www.wanfangdata.com.cn)
    Type '已登录' to proceed, 'q' to skip Chinese: "
3. 🚀 Agent 自动执行以下操作（确认用户选择后）：
   a) 如果 CDP 端口 9223 无响应，自动启动 Chrome：
      open -na "Google Chrome" --args --remote-debugging-port=9223 \
        --remote-allow-origins=http://127.0.0.1:9223 \
        --no-first-run --no-default-browser-check \
        --disable-blink-features=AutomationControlled \
        --user-data-dir="$HOME/.hermes/chrome_sd_profile" \
        https://kns.cnki.net/kns8s/
   b) 等待 CDP 就绪（轮询 http://127.0.0.1:9223/json/version）
   c) 通过 CDP Page.navigate 跳转到 CNKI/万方（若需）
   d) 告知用户：「浏览器已自动打开并导航到 CNKI/万方，请完成 CARSI 机构登录后告知」
4. 用户确认 → Chinese CDP 启动

Phase 2:
5. 等待 Sci-Hub 完成
6. 若有剩余英文 CDP 论文 → 🚧 英文登录门控
   "[ScienceDirect CDP]  elsevier (sciencedirect.com)
    [Generic CDP]  ieee (ieeexplore.ieee.org), acs (pubs.acs.org), ..."
7. 🚀 Agent 自动打开对应出版社首页（同上方式），用户登录后告知
8. 用户确认 → English CDP 启动（R2 SD → R3 Generic）
```

**强制要求：**
- Agent 禁止在用户确认登录前调用 `unified_download_router.py`（除 `--dry-run` 外）
- Agent 必须先运行 `--dry-run` 或 `--test` 确认路由，再提示登录
- 推荐使用 `--require-login-confirm` 参数启动路由器，由脚本层面再次门控

**命令示例：**

```bash
# Step 1: 先 dry-run 查看需要登录的出版社
python3 scripts/unified_download_router.py 检索文献表.md --dry-run

# Step 2: Agent 根据 dry-run 输出，自动打开对应出版社首页
#    CNKI:   open -na "Google Chrome" --args --remote-debugging-port=9223 ... https://kns.cnki.net/kns8s/
#    Wanfang: open -na "Google Chrome" --args --remote-debugging-port=9223 ... https://www.wanfangdata.com.cn/
#    ScienceDirect: open -na "Google Chrome" --args --remote-debugging-port=9223 ... https://www.sciencedirect.com/

# Step 3: 用户确认后，带门控参数执行
python3 scripts/unified_download_router.py 检索文献表.md --output paper-temp/ --require-login-confirm

# Dry-run 模式 — 只看路由决策，不实际下载（不受门控限制）
python3 scripts/unified_download_router.py 检索文献表.md --dry-run

# 单篇测试
python3 scripts/unified_download_router.py --test 10.1021/acsnano.4c00001 --port 9223
```

### 三阶段执行架构

```
Phase 1 ──────────────────────────────────────────────────
  Sci-Hub 启动（后台线程，免费，不需登录）
  🚧 中文登录门控（立即显示）
     CNKI/万方 → 用户确认 → Chinese CDP 启动
     Sci-Hub 和 Chinese CDP 可能同时跑

Phase 2 ──────────────────────────────────────────────────
  等待 Sci-Hub 完成
  若剩余英文 CDP 论文（SD / Generic）:
    🚧 英文登录门控
       Elsevier, IEEE, Wiley, ACS, ... → 用户确认
       → English CDP 启动（R2 SD → R3 Generic）

Phase 3 ──────────────────────────────────────────────────
  合并 Sci-Hub + Chinese CDP + English CDP 结果
  → download_log.md + final summary
```

> **Sci-Hub 不受任何门控。** 中文门控和英文门控各自独立，分阶段触发。共享同一 CDP 端口 9222。

### 英文路由矩阵（DOI 前缀驱动）

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

### 中文路由矩阵（source 字段驱动）🆕

| 数据库 | 识别方式 | 下载入口 | 登录方式 |
|--------|----------|----------|----------|
| 中国知网 (CNKI) | `source=cnki` + `文章链接` 列 | 文章详情页 → CSS 选择器 → CDP Fetch | 校园网 IP 或 CARSI SSO |
| 万方数据 (Wanfang) | `source=wanfang` + `文章链接` 列 | 文章详情页 → CSS 选择器 → CDP Fetch | 校园网 IP 或 CARSI SSO |

> **中文论文路由说明：** CNKI/万方论文多数无真实 DOI（使用 `cnki.{hash}` / `wanfang.{hash}` 合成标识符），不进入英文 DOI 路由器。**优先使用 Step 4 产出的 `chinese_papers.json`**（字段显式、无 Markdown 解析歧义），与英文管道通过 `ThreadPoolExecutor` 并行启动，共享同一 CDP 端口。若 JSON 缺失，回退到 Markdown 表格解析（`--chinese-input 检索文献表.md`）。缺少 `article_url` 的论文将被跳过。

### 命令参考

```bash
# 前检查：验证 CDP 浏览器 + 各出版商会话状态
python3 scripts/unified_download_router.py --check-session --port 9223

# 查看路由决策（不下载，不受登录门控限制）
python3 scripts/unified_download_router.py 检索文献表.md --dry-run

# 完整下载流程（带登录门控） 🆕
python3 scripts/unified_download_router.py 检索文献表.md --output paper-temp/ --require-login-confirm

# 跳过登录门控（仅 OA/免费来源，Agent 需确认无付费墙出版社）
python3 scripts/unified_download_router.py 检索文献表.md --output paper-temp/

# 中文+英文下载（推荐，使用 Step 4 产出的 chinese_papers.json） 🆕
python3 scripts/unified_download_router.py 检索文献表.md --chinese-input chinese_papers.json --output paper-temp/ --require-login-confirm

# 仅中文下载（无英文 DOI）
python3 scripts/unified_download_router.py --chinese-input chinese_papers.json --output paper-temp/

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

# 不同 CDP 端口
python3 scripts/unified_download_router.py 检索文献表.md --port 9225
```

### 下载记录

路由器自动生成 `paper-temp/download_log.md`，逐篇追踪：

| # | DOI | Status | Source | Size | Path |
|---|-----|--------|--------|------|------|
| 1 | `10.1016/...` | ✅ | SD CDP | 1024KB | paper_001.pdf |
| 2 | `10.1002/...` | ✅ | Generic CDP | 856KB | paper_002.pdf |
| 3 | `cnki.a1b2c3d4...` 🆕 | ✅ | Chinese CDP (CNKI) | 512KB | paper_003.pdf |
| 4 | `10.3390/...` | ⏳ | — | - | - |

### 出版社配置

所有出版社的下载策略（URL 模板、CSS 选择器、屏障检测规则）集中维护在：
[`config/publishers.toml`](config/publishers.toml)

新增出版商时，只需在该文件中添加一个 `[publishers.xxx]` 段落即可。

### 保留的专用脚本

以下脚本保持不变，路由器通过子进程调用它们（也可单独使用）：

| 脚本 | 用途 | 何时单独使用 |
|------|------|-------------|
| `download_via_scihub.py` | Sci-Hub 批量下载 | 只缺老论文时 |
| `download_via_ieee.py` | IEEE CDP 下载 | 只下 IEEE 论文时 |
| `auto_sd_downloader.py` | SD 全自动下载 | 只下 Elsevier 论文时 |
| `generic_publisher_downloader.py` | 通用CDP下载引擎 | 测试特定非SD/IEEE论文 |

### 核心设计原则

1. **默认所有论文都有访问权限** — 下不到是策略问题，不是权限问题
2. **中英文双管道并行** — 登录门控后 `ThreadPoolExecutor` 同时启动英文和中文管道，共享 CDP 端口
3. **英文按 DOI 前缀路由，中文按 source 字段路由** — 两条线泾渭分明，互不污染
4. **`Fetch.enable` 必须在 `Page.navigate` 之前调用**（IEEE v1.0.1 验证）— 否则 Chrome PDF 查看器消费响应体
5. **出版商知识库集中维护** — `config/publishers.toml`，新增出版商只需加一个 `[publishers.xxx]` 段落
6. **IEEE 已归入 Generic CDP**，`download_via_ieee.py` 保留作为手动 fallback

---

## 7. 质量门槛 (Quality Gates)

- [ ] CDP 登录门控已执行：Agent 已提示用户完成机构登录，用户已确认"已登录" 🆕
- [ ] CDP 浏览器已启动且端口可访问（`curl -s http://127.0.0.1:9223/json/version`）
- [ ] 会话状态已检查（`--check-session`）
- [ ] 下载已通过 `--require-login-confirm` 门控参数启动（或 Agent 已手动确认登录） 🆕
- [ ] 下载记录完整追踪每篇论文状态
- [ ] 下载失败的论文有明确的失败原因（非"未知错误"）

---

## 8. 收尾检查 (Closing Checks)

### 产出完整性
- [ ] PDF 已保存到 paper-temp/
- [ ] `paper-temp/download_log.md` 已生成
- [ ] 下载成功率和失败原因统计已输出

### 错误日志更新 🆕
- [ ] 本轮执行中是否出现新的下载失败模式？
  - 新的出版商屏障 → 追加到 `.skill-state/error_log.md` + 更新 `config/publishers.toml`
  - 新的 CDP 陷阱 → 追加到 `.skill-state/error_log.md` + 更新 `agents/known_pitfalls.md`
  - 会话过期的新触发条件 → 追加到 `.skill-state/error_log.md`

### 决策日志更新 🆕
- [ ] 是否调整了下载策略？（如新增 skip 规则）→ 记录到 `.skill-state/decision_log.md`

### 下一步提示
- [ ] 向用户明确说明下一步：管理 Zotero 文库（Step 6）
  > **下一步 → Step 6：** 下载完成后，管理 Zotero 文库：先生成架构，再将 PDF 导入对应集合。

---

## 9. 故障排除 (Troubleshooting)

常见问题参见 `agents/known_pitfalls.md`。本 Step 特有的问题：

- **CDP 端口无法连接**：检查 Chrome 是否以 `--remote-debugging-port=9223` 启动
- **会话过期**：`auto_sd_downloader.py` 自动检测并重启浏览器
- **PDF 标签页残留**：已修复（v2.1），每篇下载后自动关闭 PDF 标签页
- **重启死循环**：`skip_set` 机制自动跳过无权限论文
