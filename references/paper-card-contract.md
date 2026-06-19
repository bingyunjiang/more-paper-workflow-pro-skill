# Paper Card Contract

`paper_card` 是 Step 4 到 Step 7 之间的轻量证据用途卡片，用来回答：这篇文献能怎么用、能支撑到什么强度、不能用于哪些 claim。它不是新的流程 Step，也不是最终展示层。

## 主存储

- 机器主源：`workflow_search_results.json` 中每条记录的 `paper_card`。
- Step 6 交接源：`文献-Zotero架构对照.json` 应完整保留或转写 `paper_card`。
- Zotero child note：人类可读同步副本，不能反向替代 JSON 主源。
- Zotero tag：只放短索引标签，不放 `primary_claim` 或 `content_fit_note` 等长文本。

## 字段

```json
{
  "paper_card": {
    "evidence_role": "method",
    "primary_claim": "这篇文献自身最核心的主张或发现",
    "main_methods_or_baselines": ["方法、模型、基线、数据集或标准"],
    "reading_depth": "abstract_only",
    "content_fit": "adjacent",
    "content_fit_note": "说明它与当前研究问题、章节或 claim 的关系",
    "usable_for": ["可用于的方法、章节或论证任务"],
    "not_usable_for": ["不可用于的强 claim 或证据场景"]
  }
}
```

## 枚举值

`evidence_role`：

- `method`
- `background`
- `theory`
- `review`
- `experiment`
- `data`
- `benchmark`
- `counterpoint`
- `standard_policy`
- `case_specific`
- `unknown`

`reading_depth`：

- `metadata_only`
- `abstract_only`
- `full_text`
- `zotero_note`
- `pdf_verified`

`content_fit`：

- `direct`
- `adjacent`
- `background_only`
- `mismatch`
- `unknown`

## Step 4 生成规则

- `content_relevance` 仍由五维评分中的主题匹配度和总分承担，不被 `evidence_role` 替代。
- `evidence_role` 只说明文献适合承担哪类证据角色。
- `content_fit` 说明文献内容与当前研究问题、章节或检索任务的贴合度。
- `reading_depth` 说明当前读取深度和后续可用强度上限。
- 高相关文献仍可能是 `background_only`；综述文献优先标为 `review/background/theory`；实验或方法文献可标为 `method/experiment/benchmark`。
- 标题相关但摘要或已读材料无法支持当前方向时，标为 `content_fit=mismatch` 或 `background_only`。
- Step 4 不做句子级引用裁决；句子级 claim-source fit 留给 Step 7。

## Zotero Child Note 模板

导入 Zotero 时，每篇 T1-T3 文献可创建或更新一个 child note，标题固定为 `More-Paper Evidence Card`。

```md
# More-Paper Evidence Card

record_id: <record_id>
citekey: <citekey>
paper_tier: <T1/T2/T3>
evidence_role: <role>
reading_depth: <depth>
content_fit: <fit>
trust_status: <VERIFIED/VERIFIED_LOCAL/WARN>

## Primary Claim
...

## Main Methods / Baselines
- ...

## Usable For
- ...

## Not Usable For
- ...

## Content Fit Note
...

## Workflow Trace
source_artifact: workflow_search_results.json
search_task_id: <id>
chapter_id: <id>
updated_at: <date>
```

推荐同步的 Zotero tags：

- `mp-role:<evidence_role>`
- `mp-fit:<content_fit>`
- `mp-depth:<reading_depth-with-hyphen>`
- `mp-tier:<T1/T2/T3>`

## Step 7 消费规则

- 写作前按章节优先筛选 `evidence_role` 合适、`content_fit` 不为 `mismatch` 的文献。
- `background_only` 只能用于背景、领域现状或综述性句子。
- `abstract_only` 只能用于低风险背景，不得支撑方法细节、实验数值、强因果结论或关键 claim。
- Step 7 正文引用必须显式暴露已读深度：`full_text / pdf_verified / zotero_note -> （已读全文）`，`abstract_only -> （已读摘要）`，`metadata_only -> （仅元数据）`。
- `metadata_only` 不得承载具体结论；`abstract_only` 不得承载实验结果、参数、机制、效果比较或强 claim；这些内容只能由 `（已读全文）` 文献支撑。
- 正文 claim 超出 `primary_claim` 或 `content_fit_note` 时，引用审计应标记为 `weak-support` 或 `not-supported`。
- 没有合适文献时，输出 `[待补证据: claim]` 或写入 `evidence_gap_list.md`，不得硬写强 claim。
- 缺少 `paper_card` 不阻塞 Step 7；按现有 Zotero/PDF/证据包规则降级运行，并记录缺口。
