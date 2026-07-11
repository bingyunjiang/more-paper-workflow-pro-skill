# Early Research Evidence Calibration

本合同用于 Step 1 互动选题和 Step 2 大纲/关键词校准。它只做小样本探索，不替代 Step 3 的正式检索计划或 Step 4 的系统检索、筛选与评分。

Step 4 direct-entry 不依赖本合同先行完成。若用户直接进入 Step 4，所需的最小主题、RQ、范围和查询依据由 Step 4 在当前步骤内重建；异常查询也在 Step 4 内局部修复，不要求补跑 Step 1/2/3。

## 数据源与执行顺序

1. 英文及跨语言方向：OpenAlex 为主，Crossref 做 DOI/题名交叉核验；Semantic Scholar 在额度可用时补摘要和引用信号。
2. 中文方向：先用中英文映射词跑 OpenAlex/Crossref，再在已登录的 CDP 浏览器中补 CNKI/万方样本。
3. 用户已有 Zotero、BibTeX、论文表或综述时，可作为 `user_supplied` 语料，但必须记录范围和时间边界。
4. 普通网页只用于发现术语、标准、机构报告或数据库入口，不用于虚构论文量、创新性或研究 gap。

推荐复用现有执行器：

```bash
python3 scripts/batch_chinese_search.py --open-login-tabs --port 9223

python3 scripts/search_by_topic.py "candidate query" \
  --t1 openalex --t2 crossref --parallel --limit 30 \
  --export-workflow-json candidate-results.json

python3 scripts/search_by_topic.py "中文候选词" \
  --t1 cnki --t2 wanfang --parallel --language zh --limit 30 \
  --export-workflow-json candidate-zh-results.json
```

Step 1 识别到中文论文库需求时，应在第一轮互动即执行 `--open-login-tabs`。该动作只打开登录页面并立即返回；用户可在回答选题问题的同时完成机构账号/CARSI 登录。不得因尚未登录而停止主题澄清，但 CNKI/万方真实结果只能在会话可用后计入 `evidence_calibration`。

## 禁止把截断样本当成总量

`--limit 20/30/50` 得到的是观察样本，不是数据库总命中量。除非数据源明确返回并保存 `total_hits`，否则不得写“该方向有 500+ 篇论文”。早期判断必须改用：

- `observed_count`：实际取得的去重记录数
- `relevant_count / relevance_ratio`：题名和摘要人工或规则复核后的相关记录数/比例
- `recent_count / recent_ratio`：近三年相关记录数/比例
- `source_agreement`：两个以上独立来源是否出现相同核心术语、方法或代表论文
- `representative_records`：至少 2-3 条可回查 DOI/source_id 的论文或综述
- `query_sensitivity`：换同义词、上位词后结论是否明显改变

## Step 1 校准

每个候选方向至少保存两组查询，并区分对象、方法、场景和指标。选择题目时比较：

- 证据支撑：样本相关率、代表论文、近三年活动
- 区分度：相邻题目的重叠与差异，而不是直接宣称“首次”
- 可验证性：研究问题能否映射到方法、数据和至少三个评价指标
- 脆弱性：更换查询或数据源后，题目判断是否仍成立

输出 `evidence_calibration`；外部检索失败时使用 `status=unavailable`，记录尝试来源、查询和限制，选题只能标为 `provisional`。

## Step 2 校准

大纲生成后，按核心章节各跑一个最小查询，检查：

- 每个核心 RQ 是否至少由一个章节承接
- 每个核心章节是否能召回相关方法、实验、比较或综述样本
- 章节之间是否因关键词高度重叠而重复
- 关键词是否同时包含对象、问题/现象、方法、场景和指标
- 同义词、缩写和中英映射是否在论文题名/摘要或受控词表中出现
- 歧义词是否需要限定词或排除词

每个关键词必须记录 `origin=user|topic|corpus|controlled_vocabulary`、`observed_in_records`、`ambiguity` 和 `action=keep|qualify|expand|exclude`。未被语料支持的词可以保留为实验/工程术语，但必须说明依据，不能伪装成领域通用词。

## 状态

- `executed`：真实检索已执行并保存可回查记录。
- `user_supplied`：使用用户提供的论文库/综述，并记录覆盖边界。
- `unavailable`：检索不可用或用户只要求快速草案；允许继续，但结果为 `provisional`。
