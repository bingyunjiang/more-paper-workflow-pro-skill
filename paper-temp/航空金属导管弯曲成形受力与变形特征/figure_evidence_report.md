# 图表证据报告：航空金属导管弯曲成形受力与变形特征

## figure_mode_decision

| 字段 | 内容 |
|---|---|
| figure_mode | `auto_insert` |
| 触发依据 | 用户要求根据修改后的 skill 重写论文；输入来自 Zotero 集合；集合存在 MinerU ZIP 图文资产 |
| 执行边界 | 只自动插入本地可读 MinerU ZIP 中已人工查看的图片；本地缺失 ZIP 的文献不自动插图 |
| 输出 | `论文初稿.md`、`figure_index.json`、`figure_evidence_report.md/json`、`figures/` |

## 附件检查

| Zotero Key | MinerU ZIP 状态 | 图文处理 |
|---|---|---|
| `P82NKUCE` | 本地可读：`LLM-for-Zotero-MinerU-cache-3VCP4VMT.zip` | 抽取并插入图 1、图 2、图 3 |
| `3VKND9N4` | 本地可读：`LLM-for-Zotero-MinerU-cache-EG96W6C2.zip` | 抽取并插入图 4 |
| `36SGIFAD` | Zotero 有 ZIP 子附件记录，本地缺失 | 不自动插图，仅用全文文字证据 |
| `99QWSQ5K` | Zotero 有 ZIP 子附件记录，本地缺失 | 不自动插图，仅用全文文字证据 |
| `36ANUFUI` | Zotero 有 ZIP 子附件记录，本地缺失 | 不自动插图，仅用全文文字证据 |
| `F98GDZSB` | Zotero 有 ZIP 子附件记录，本地缺失 | 不自动插图，仅用全文文字证据 |
| `MWXZS66W` | Zotero 有 ZIP 子附件记录，本地缺失 | 不自动插图，仅用全文文字证据 |
| `PSZJKCWU` | Zotero 有 ZIP 子附件记录，本地缺失 | 不自动插图，仅用全文文字证据 |
| `26T9U5ZA` | Zotero 有 ZIP 子附件记录，本地缺失 | 不自动插图，仅用全文文字证据 |
| `TSDA57M9` | Zotero 有 ZIP 子附件记录，本地缺失 | 不自动插图，仅用全文文字证据 |

## 图表-claim 绑定

| 图号 | 文件 | 来源 | 证据状态 | 绑定 claim | 风险边界 |
|---|---|---|---|---|---|
| 图1 | `figures/fig1_3d_free_bending_principle.jpg` | 于波等[6]，MinerU caption，页 2 | 可用图文证据 | 三维自由弯曲中推进力、弯曲模、导向结构和局部接触共同决定弯曲轨迹 | 只支撑自由弯曲，不外推为传统芯棒绕弯 |
| 图2 | `figures/fig2_bending_stress_strain_state.jpg` | 于波等[6]，MinerU caption，页 2 | 可用图文证据 | 中性层偏移、弯曲半径、偏距和截面变形在同一变形区内耦合 | 不用作具体应力数值证据 |
| 图3 | `figures/fig3_ur_curve_section_distortion.jpg` | 于波等[6]，MinerU caption，页 4 | 可用但需边界说明 | 自由弯曲中 U-R 关系和截面畸变测量需要联合评价 | 图像由复合图抽取，正文不写精确数值 |
| 图4 | `figures/fig4_push_bending_mises_stress.jpg` | 唐文献等[10]，MinerU caption，页 1 | 辅助图证 | 推弯仿真中弯曲区存在应力梯度，支撑多指标参数优化必要性 | 图像质量偏低，仅作辅助，不支撑定量判断 |

## 禁止外推项

- 不得根据图 1-3 直接判断绕弯芯棒参数。
- 不得根据图 4 写出新的 Mises 应力数值或推弯最优参数。
- 缺失本地 ZIP 的文献不得写“如图所示”。
- 图片只增强机理解释；强 claim 仍以全文、图注和原文证据共同约束。
