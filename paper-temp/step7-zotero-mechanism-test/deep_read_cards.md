# Deep Read Cards

- section_id: 1
- section_title: 热变形过程中动态再结晶驱动晶粒细化的多尺度机理
- selected_records: 3

## Liu2024_CDRX_AA2196 - A polycrystal plasticity-cellular automaton integrated modeling method for continuous dynamic recrystallization and its application to AA2196 alloy

- reading_depth: full_text
- evidence_role: unknown
- content_fit: direct
- text_source: zotero_fulltext
- image_source: none

### Claim Summary
CDRX 可由位错累积/回复、亚晶形成与旋转、储能和曲率驱动的界面迁移共同解释。

### Method Summary
VPSC；3D cellular automaton；CDRX model

### Experiment Summary
Continuous dynamic recrystallization usually dominates the microstructural evolution in hot working of aluminum alloys.

### Usable For
- 连续动态再结晶机理
- 晶体塑性-CA 多尺度建模

### Not Usable For
- AA2195 应力状态实验的直接结论

### Mechanism Hints
- phenomenon: Continual straining gradually increases the misorientation of subgrain boundaries, enabling the transition from low-angle grain boundaries into high-angle ones.
- state_variables: CDRX; stored energy; misorientation
- claim_limit: 可进入 mechanism_argument_plan；强 claim 仍需逐条绑定全文、图表或实验锚点。
- causal_chain:
  - Continual straining gradually increases the misorientation of subgrain boundaries, enabling the transition from low-angle grain boundaries into high-angle ones.
  - The stress response, dislocation accumulation and recovery, and evolution of crystal orientations are computed in the context of polycrystal plasticity; the formation and rotati...
- governing_model:
  - The stress response, dislocation accumulation and recovery, and evolution of crystal orientations are computed in the context of polycrystal plasticity; the formation and rotati...
- boundary_conditions:
  - The stress response, dislocation accumulation and recovery, and evolution of crystal orientations are computed in the context of polycrystal plasticity; the formation and rotati...
- evidence_anchor:
  - pdf: zotero://select/items/7BRJBXBL page=

### Risk Flags
- reading_depth_locked
- figure_candidates_missing

## Yu2025_AA2195_StressState - Effect of stress state on flow stress and grain refinement mechanisms during AA2195 hot deformation

- reading_depth: full_text
- evidence_role: unknown
- content_fit: direct
- text_source: zotero_fulltext
- image_source: none

### Claim Summary
应力状态改变低角度晶界形成方向、三叉晶界连接和亚晶旋转激活温度，从而改变晶粒细化机制。

### Method Summary
PSC；UC；torsion；EBSD；TEM；TKD

### Experiment Summary
The results show that grain refinement is highly dependent on stress state.

### Usable For
- 应力状态对晶粒细化机制的影响
- GF/GR 转换边界
- WH-DRV-DRX 竞争机理

### Not Usable For
- 镍基合金 DDRX 连续场模型验证

### Mechanism Hints
- phenomenon: For compressive-dominated stress states, the transition in the dominant grain refinement mechanism from grain fragmentation to subgrain rotation occurred at 350 C; for shear-dom...
- state_variables: DRV; DRX; stress state; grain fragmentation; subgrain rotation; temperature
- claim_limit: 可进入 mechanism_argument_plan；强 claim 仍需逐条绑定全文、图表或实验锚点。
- causal_chain:
  - For compressive-dominated stress states, the transition in the dominant grain refinement mechanism from grain fragmentation to subgrain rotation occurred at 350 C; for shear-dom...
  - The transition thresholds do not arise from a change in critical energy for nucleation itself; different stress states generate distinct precursor substructures such as shear ba...
- boundary_conditions:
  - Under shear-dominated conditions, low-angle grain boundaries preferentially formed along the short axis of the initial grains, facilitating their extension into triple junctions...
  - For compressive-dominated stress states, the transition in the dominant grain refinement mechanism from grain fragmentation to subgrain rotation occurred at 350 C; for shear-dom...
- evidence_anchor:
  - pdf: zotero://select/items/4VZ7PV7E page=

### Risk Flags
- reading_depth_locked
- figure_candidates_missing

## Chen2026_CPFE_CA_DDRX - A continuum-field-enabled multiscale framework coupling crystal plasticity and cellular automaton for discontinuous dynamic recrystallization: Application to a nickel-based superalloy

- reading_depth: full_text
- evidence_role: unknown
- content_fit: direct
- text_source: zotero_fulltext
- image_source: none

### Claim Summary
用连续转变分数替代 CA 离散状态跳变，可缓解 CPFE-CA 耦合中的非物理应力突跳并保持微观组织-力学响应一致。

### Method Summary
CPFE；cellular automaton；continuum-field sub-grid；bidirectional mapping

### Experiment Summary
The incompatibility between discrete microstructural transitions in cellular automaton and continuous mechanical fields in crystal plasticity finite element modeling leads to numerical instability and unphysical stres...

### Usable For
- DDRX 数值机理
- 连续场 CA-CPFE 耦合
- 形核和晶界迁移软化机制

### Not Usable For
- 铝合金 CDRX 特定滑移系结论

### Mechanism Hints
- phenomenon: The incompatibility between discrete microstructural transitions in cellular automaton and continuous mechanical fields in crystal plasticity finite element modeling leads to nu...
- state_variables: CPFE; CA; grain boundary migration; transformation fraction; dislocation density
- claim_limit: 可进入 mechanism_argument_plan；强 claim 仍需逐条绑定全文、图表或实验锚点。
- causal_chain:
  - The incompatibility between discrete microstructural transitions in cellular automaton and continuous mechanical fields in crystal plasticity finite element modeling leads to nu...
- governing_model:
  - The continuum-field-enabled framework integrates CPFE with a reformulated CA model through a sub-grid description and bidirectional mapping strategy.
  - Nucleation and grain boundary migration are modeled as gradual reordering of distorted lattices, described by an evolving transformation fraction rather than discrete state swit...
- boundary_conditions:
  - Nucleation and grain boundary migration are modeled as gradual reordering of distorted lattices, described by an evolving transformation fraction rather than discrete state swit...
  - Recrystallized regions act as local soft zones that release strain energy, reduce local driving force for further nucleation and grain boundary migration, and establish a dynami...
- evidence_anchor:
  - pdf: zotero://select/items/XRMSR8RX page=

### Risk Flags
- reading_depth_locked
- figure_candidates_missing
