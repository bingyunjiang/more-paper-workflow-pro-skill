# Step 5: 统一批量下载 (Unified Download Router)

> 单一命令自动路由，三轮顺序执行（Sci-Hub → SD CDP → Generic CDP），覆盖 24 家出版社。IEEE 走 Generic CDP 策略 B（文章页提取 stamp URL），专用 `download_via_ieee.py` 作为交互式 SSO 备用。

---

## 1. 启动前读取 (Pre-read Checklist)

执行本步骤前，必须确认以下文件已加载：

- [ ] `agents/step_4_search_score.md` — 检索文献表（含 DOI 和 Tier 分级）
- [ ] `config/publishers.toml` — 出版社下载策略配置
- [ ] `references/publisher-access-matrix.md` — 各出版商下载可行性对照表
- [ ] `references/error_log.md` — 已知下载错误及修复规则
- [ ] `references/decision_log.md` — 下载策略相关决策

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

**单一命令，自动路由到最优下载策略：**

```bash
# 标准入口 — 自动按出版商路由下载
python3 scripts/unified_download_router.py 检索文献表.md --output paper-temp/

# Dry-run 模式 — 只看路由决策，不实际下载
python3 scripts/unified_download_router.py 检索文献表.md --dry-run

# 单篇测试
python3 scripts/unified_download_router.py --test 10.1021/acsnano.4c00001 --port 9223
```

### 路由矩阵

路由器自动将每篇 DOI 分配到正确策略，三轮顺序执行：

| 轮次 | DOI 前缀 | 出版商 | 策略 | 成功率 |
|------|----------|--------|------|--------|
| **Round 1: Sci-Hub** | 不限（2021年前） | 全部 | Sci-Hub CDP | 9/13 镜像可用 |
| **Round 2: SD CDP** | `10.1016/` | Elsevier | 专有混合策略 | 96% (180/185) |
| **Round 3: Generic CDP** | `10.1109/` | IEEE | 文章页 stamp URL 提取 + getPDF.jsp 捕获 | 需 SSO，`download_via_ieee.py` 备用 |
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

### 命令参考

```bash
# 前检查：验证 CDP 浏览器 + 各出版商会话状态
python3 scripts/unified_download_router.py --check-session --port 9223

# 完整下载流程
python3 scripts/unified_download_router.py 检索文献表.md --output paper-temp/

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
| 3 | `10.3390/...` | ⏳ | — | - | - |

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

### v2.1 核心设计原则

1. **默认所有论文都有访问权限，下不到是策略问题，不是权限问题。**
2. **`Fetch.enable` 必须在 `Page.navigate` 之前调用**（IEEE v1.0.1 验证）——否则 Chrome PDF 查看器消费响应体导致捕获失败。
3. **双浏览器并行可翻倍速度但需隔离标签页。** Chrome 和 Edge 各自独立标签页上下文。

---

## 7. 质量门槛 (Quality Gates)

- [ ] CDP 浏览器已启动且端口可访问（`curl -s http://127.0.0.1:9223/json/version`）
- [ ] 会话状态已检查（`--check-session`）
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
  - 新的出版商屏障 → 追加到 `references/error_log.md` + 更新 `config/publishers.toml`
  - 新的 CDP 陷阱 → 追加到 `references/error_log.md` + 更新 `agents/known_pitfalls.md`
  - 会话过期的新触发条件 → 追加到 `references/error_log.md`

### 决策日志更新 🆕
- [ ] 是否调整了下载策略？（如新增 skip 规则）→ 记录到 `references/decision_log.md`

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
