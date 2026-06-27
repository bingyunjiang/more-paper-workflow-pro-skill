# Step 7 Execution Card

## Task Boundary

- writing_scope: full-document
- target_genre: journal
- writing_mode: full-document
- language_mode: zh
- output_dir: outputs/step7-writing/aviation-metal-tube-bending-2-2
- draft_target: journal_paper_draft.md
- requested_action: 删除旧 output 后从头重新撰写，并生成含图片 PDF

## Evidence Entry

- evidence_entry_mode: zotero_mineru
- zotero_collection: 2.2 航空金属导管弯曲成形受力与变形特征 [6XC8JBW8]
- evidence_pack: not_used
- local_pdf_dir: zotero_attachments
- existing_draft: deleted_before_rewrite
- evidence_mapping_artifact: evidence_matrix.md, deep_read_cards.md/json

## Mechanism Gate

- checked_text: 航空金属导管弯曲成形受力与变形特征
- candidate_terms_hit: 受力, 变形特征, 影响规律, 耦合
- confirmed_triggers: 当前题目需要解释外侧减薄、内侧起皱、截面畸变、摩擦和芯棒支撑之间的变量传导关系
- mechanism_trigger_decision: enter_mechanism_analysis
- reason: 命中机制路径类触发，且核心 claim 涉及变量如何传导到缺陷响应
- required_artifacts:
  - deep_read_cards: deep_read_cards.md/json
  - mechanism_cards: mechanism_cards.md/json
  - mechanism_argument_plan: mechanism_argument_plan.md/json
  - mechanism_claim_audit: mechanism_claim_audit.md/json

## Figure Gate

- figure_asset_check: figure_asset_check.md
- figure_mode: auto_insert
- checked_assets:
  - zotero_child_attachments: checked for 99QWSQ5K, F98GDZSB, MWXZS66W, P82NKUCE
  - mineru_zip: available and extracted for 99QWSQ5K, F98GDZSB, MWXZS66W, P82NKUCE
  - figure_index: generated
  - local_figures: generated under figures/
  - readable_pdf: available through Zotero PDF attachments
- figure_completion_requirement: Markdown must include real relative image paths, and PDF export must preserve images.

## Claim Boundary

- allowed_claim_strength: fulltext-supported mechanism/trend/parameter claims only for four fulltext-read sources; abstract-only sources limited to background
- fulltext_supported_claims: 受力状态、壁厚减薄阶段性、相对弯曲半径敏感性、芯棒支撑折中、间隙/摩擦影响、自由弯曲摩擦路径
- abstract_only_claims: 工艺参数敏感性、弯曲速度趋势、21-6-9 高强管参数影响背景
- metadata_only_claims: 仅作为研究背景线索
- forbidden_claims: 本文实验结果、本文仿真结果、内部加压弯曲确定性机制、首次/首创性 claim

## Required Artifacts

- step7_execution_card.md: done
- evidence_matrix.md: done
- deep_read_cards.md/json: done
- mechanism_cards.md/json: done
- mechanism_argument_plan.md/json: done
- mechanism_claim_audit.md/json: done
- figure_asset_check.md: done
- figure_index.md/json: done
- figure_evidence_report.md/json: done
- citation_audit.md: done
- draft_risk_summary.md: done
- draft_md: journal_paper_draft.md

## Blocked Until

- blocked_until: none_for_text_and_image_pdf
- remaining_risks: 正式投稿前仍需按目标期刊格式重排参考文献，并确认是否允许复用原文献图表。
