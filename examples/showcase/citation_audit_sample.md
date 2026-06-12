# 引用审计报告样例

| cite_label | claim_excerpt | format_status | mapping_status | evidence_status | conclusion | note |
|---|---|---|---|---|---|---|
| [12] | “该方法在所有测试集上都达到最优性能” | pass | matched | abstract_only | downgrade | 只有摘要，无 PDF，不能支撑强 claim |
| [18] | “该参数设置来源于 Wang et al. (2024)” | pass | matched | VERIFIED | retain | Zotero 笔记和 PDF 标注均可回溯 |
| [27] | “已有研究普遍忽略该问题” | pass | missing_mapping | supplement | supplement | 正文引用未映射回 BibTeX / Zotero 条目 |
| [31] | “实验结果证明其具有因果效应” | pass | matched | REJECT | replace_or_remove | Step 4 已标记 REJECT，禁止进入关键 claim |
