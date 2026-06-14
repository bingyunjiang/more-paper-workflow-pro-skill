# 错误日志 (Error Log)

> 跨会话积累的 AI 操作错误记录。每个 Step 的 agent 在收尾检查时如果发现新错误，
> 必须追加到此文件。Step 8（润色）的"术语统一"检查发现术语不一致时也记录于此。
>
> 设计原则：**不从零开始——每次错误都是一次学习机会。**
> 借鉴来源：ResearchWiki `memory/error_log.md`。
>
> ⚠️ 本文件为模板。运行时由 agent 自动复制到项目目录下的 `.skill-state/error_log.md`。
> 修改请到 `.skill-state/` 中进行，以免污染技能仓库。

## 记录格式

每条错误记录包含以下字段：

| 字段 | 说明 |
|------|------|
| **日期** | 发现日期 (YYYY-MM-DD) |
| **来源 Step** | 哪个步骤发现的 (Step 1-8 / 通用) |
| **Error** | 错误的具体表现（用户可观察到的现象） |
| **Cause** | 根本原因分析（为什么 AI 会犯这个错误） |
| **Correction rule** | 为避免重复，在对应 agent 文件或本文件中添加的规则 |
| **Impact** | 对产出的影响（低/中/高/关键） |
| **Fixed** | 是否已修复（✅ 是 / 🔧 部分 / ❌ 否） |

---

## 错误记录

### 2026-06-05 | Step 4 | 中
- **Error:** `search_by_topic.py` 的 OpenAlex 解析抛出 `AttributeError: 'NoneType' object has no attribute 'get'`（venue 字段），导致搜索中断
- **Cause:** OpenAlex API 返回的 `primary_location.source` 可能为 `None`，原链式调用在 `source=None` 时崩溃
- **Correction rule:** 代码已修复（`scripts/search_by_topic.py` line 224-226），改用 `primary_loc.get("source")` 判空后再调用 `.get("display_name", "?")`
- **Impact:** 高 — 脚本无法执行任何 OpenAlex 检索
- **Fixed:** ✅ 已修复

### 2026-06-05 | Step 4 | 中
- **Error:** Semantic Scholar 搜索频繁 429（即使遵守 1 req/sec 限流）
- **Cause:** S2 对突发请求敏感（第一个请求 SSL 错误后重试触发了速率限制），导致队列中后续所有请求均 429
- **Correction rule:** 首次响应 < 200 条时再尝试 S2，而非作为默认并行源。触发 SSL 错误后等待 5s 再重试。如连续 429，跳过 S2 仅用 OpenAlex。
- **Impact:** 中 — 部分结果可能缺失
- **Fixed:** 🔧 部分 — 需在 Step 4 agent 文档中增加重试策略

### 2026-06-05 | Step 4 | 中
- **Error:** OpenAlex 搜索结果噪声大（500 篇中仅 ~60 篇相关）
- **Cause:** `search=` 参数匹配全文 + 元数据，缺乏 title 级精度过滤
- **Correction rule:** 始终添加 `filter=type:article` + `title.search:` 子句。对于传统工科方向，优先使用 3 个 `AND` 块的 title-focused 查询
- **Impact:** 中 — 增加人工筛选工作量
- **Fixed:** 🔧 部分 — 需优化 query 构建策略

---

## 使用规则

1. **所有 agent 启动时读取本文件** — 检查是否有已知错误规则适用于当前任务
2. **每个 agent 收尾时写入本文件** — 如果本轮出现新错误或发现新规则缺口
3. **Step 7.15（引用审计）发现误引模式时** — 追加到本文件，关联到 `references/citation-audit-guide.md`
4. **Step 8（润色）发现系统性 AI 痕迹时** — 追加到本文件
5. **不记录一次性/偶发性错误** — 只记录可能重复出现的模式性错误
