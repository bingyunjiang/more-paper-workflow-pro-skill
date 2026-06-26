# Deep Read Cards

- section_id: 1
- section_title: 热变形过程中动态再结晶驱动晶粒细化的多尺度机理
- selected_records: 3

## Liu2024_CDRX_AA2196 - A polycrystal plasticity-cellular automaton integrated modeling method for continuous dynamic recrystallization and its application to AA2196 alloy

- reading_depth: full_text
- evidence_role: unknown
- content_fit: direct
- text_source: zotero_mineru
- image_source: MinerU ZIP / Zotero 图文资产

### Claim Summary
CDRX 可由位错累积/回复、亚晶形成与旋转、储能和曲率驱动的界面迁移共同解释。

### Method Summary
VPSC；3D cellular automaton；CDRX model

### Experiment Summary
The comparison of predicted and experimental results with respect to the flow stress, average subgrain diameter, average grain diameter and average misorientation angle of boundaries is given in Fig.

### Usable For
- 连续动态再结晶机理
- 晶体塑性-CA 多尺度建模

### Not Usable For
- AA2195 应力状态实验的直接结论

### Mechanism Hints
- phenomenon: The initial random grain orientations gradually converge with increasing strain, ultimately resulting in a strong $< 0 1 1 > | | \mathrm { C D }$ texture which is typical shown...
- state_variables: CDRX; DRV; DRX; DDRX; VPSC; CA; CPFEM; EBSD
- claim_limit: 可进入 mechanism_argument_plan；强 claim 仍需逐条绑定全文、图表或实验锚点。
- causal_chain:
  - Most dislocations are consumed through dynamic annihilation mechanism, without the necessity to generate a large number of geometrically necessar dislocations and subgrain bound...
  - 7$ To better understand the mechanisms underlying the development of distinct deformation textures, the orientations of 60 randomly selected grains at different strains are pres...
- governing_model:
  - Integrating VPSC model within the CA-CDRX frameworks The 3D CA framework is established based on the MATLAB platform, followed by embedment of the modified CDRX relevant equatio...
  - The physics-based CDRX equations and dislo cation density-based VPSC subroutine are constructed, followed by integration with CA framework at the grain level.
- boundary_conditions:
  - At higher deformation temperature and lower strain rate, fewer subgrain boundaries are formed due to enhanced boundary mobility and increased time available for boundary migration.
  - grain boundary migration during deformation must be considered, which is more pronounced as ln(Z) decreases (higher deformation temperature or lower strain rate).
- validation_path:
  - Validation by additional compression tests To further validate the model, hot compression experiments at $4 2 5 ^ { \circ } \mathrm { C }$ and strain rate of 0.001 and 1 $s ^ {...
  - The proposed simulation framework is validated through simulating the isothermal uniaxial compression process of AA2196 alloy under different tem peratures and strain rates.
- alternative_explanations:
  - However, the primary shortcomings of CPFEM are the limitation in computational efficiency and difficulties in simulating industry-scale deformation processes, such as hot extrus...
  - However, the involvement of {110}<110> slip mode can reverse their rotating directions, eventually shifting them towards the <001>, and an orientation turbulence zone appears (Fig.
- evidence_anchor:
  - pdf: zotero://select/items/7BRJBXBL page=
  - figure_or_table: Fig. 1 page=3
  - figure_or_table: image-2 page=4
  - figure_or_table: image-3 page=5

### Risk Flags
- reading_depth_locked

### Figure Candidates
- Fig. 1 | page=3 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/35080a0d0d13edb0e85cc6718b89eafadf22bbe83db29ccfdaa5d213d4c57a04.jpg
- image-2 | page=4 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/232b9493879e4e03f0835eb5e47e868b56afba577d73fdc966a1f916ceb88c1c.jpg
- image-3 | page=5 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/eedd9646ee3f703cb121568cbd69c6e684de85b02b6d6fc50134c1ab1065970c.jpg
- image-4 | page=5 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/ee900e3b5dedc63eb8ea3990126813dcad03a3483e7209928338231c49d699b7.jpg
- image-5 | page=5 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/3fda09e70ad3512d2d1175ee9798a5321f1674f8f606ec3b9de6da38ef27a662.jpg
- image-6 | page=5 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/f31765dae5943d5e67f54c45b05ff1ed6415c06735df56f63ba490ad1ac61298.jpg
- image-7 | page=5 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/a503724f0d8e9dd3704a295084b7680eba50363b5114bc8ee1c921ce9a5d316f.jpg
- Fig. 4 | page=5 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/f363f198dbb0e80530243803cb29538de02ff7cc1d0b8ff6434f2f7fdd607bd7.jpg
- image-9 | page=5 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/f3c79a2f9f71b73a5305c7be00ecbae13eb539c92a096acdfa5c7b8d4e5abc94.jpg
- image-10 | page=7 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/d5a21b0c6b8bc290345127802aca9329b6e6cbb23e1dc708e7a3d4cefaf27ea1.jpg
- image-11 | page=12 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/0800da78528aa50a4751d09e398dba70a23910c39c4feda8bd143bd1dedd4688.jpg
- Fig. 12 | page=18 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/c57b5985eea423bcfad08e01aa89537fe578b2043ec9c4ffbd8a52ad7ba3a4c3.jpg
- image-13 | page=19 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/393704db4e725f8db3f4fe66828321c17d315daf0aa10f6db15deed339fadac1.jpg
- image-14 | page=19 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/0462c4a389e798d301d59a1cbbdd2aaf402b9c200f266bafc41c2cdb0bbe8a70.jpg
- image-15 | page=19 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/f329fa3b645be22c9a4f18101a2e73aa0769ae7c8c913c73daa523c1650baf73.jpg
- image-16 | page=19 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/82b81c9f8dedb9d9919a0140b304e4a79619bd22c8b06f9957a16cc60bcea525.jpg
- image-17 | page=19 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/f78379fd7b8a3d7b6e523ce956ad0a9db630ea1e028ea0bdf51d91e6a848d9f3.jpg
- Fig. 13 | page=19 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/cbda1eca6099bf7f623fa37a79d0cde3f9f4fb99aed94672e879a699cd2fe031.jpg
- image-19 | page=19 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/ef94197823cf6803c9680da13842d4759ff6b3bf7516dbd2b930da659ee9c5cf.jpg
- image-20 | page=19 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/98807e9f1659ec3a1ee2dcb50b895b9f19f3d39c51def4db5b0471e5190af46f.jpg
- image-21 | page=19 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/bf5a5d6f563651ccb6d090c9139b0a01bf5926b1a1fc424a9a3a4433afa3e5a4.jpg
- image-22 | page=19 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/676be343ecce4d7c8a28d9655365debb1b2f4b230b67de635fe9dbb2a78d6630.jpg
- Fig. 14 | page=19 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/861df5675dbc1ebc765a809f29f3f0596a2168dc5a36db224591fdfd7c89a3bf.jpg
- Fig. 18 | page=21 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/396624f0f8aa8eac92860d3460fc14b62c6b930c9a726c50cd6c481040ae97d8.jpg
- image-25 | page=22 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/c2d10e808f2f71288259d41f2fab7f9b1e845d4c8897a9651141b45f2c462012.jpg
- Fig. 19 | page=22 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/054b10e375187c31b42d7f137ddc46770172617aa24c31e92c1c6126b0dd4f89.jpg
- image-27 | page=23 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/1b8a4344d245c51e533e1059e676d1f14696da5b6a3a60acc1550ecf31c1ac69.jpg
- image-28 | page=23 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/e0713630cbf325e12e8939ddb6d8171a1e353f889da0f5c27f278e182f4dbd6b.jpg
- image-29 | page=23 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/44e73314fa2efa9a5a33253061c518f1237c18cfc0c6deb4885f27d1ca32a780.jpg
- image-30 | page=23 | path=/Users/Bing/Zotero/storage/X68AN72W/LLM-for-Zotero-MinerU-cache-KX8NMMDF.zip::images/c4920a19348b56024549a95d113568cd5f13101e54ca97570ec2b379c2f85fcb.jpg

## Yu2025_AA2195_StressState - Effect of stress state on flow stress and grain refinement mechanisms during AA2195 hot deformation

- reading_depth: full_text
- evidence_role: unknown
- content_fit: direct
- text_source: zotero_mineru
- image_source: MinerU ZIP / Zotero 图文资产

### Claim Summary
应力状态改变低角度晶界形成方向、三叉晶界连接和亚晶旋转激活温度，从而改变晶粒细化机制。

### Method Summary
PSC；UC；torsion；EBSD；TEM；TKD

### Experiment Summary
These results were used to evaluate deformation homogeneity and verify the experimental design.

### Usable For
- 应力状态对晶粒细化机制的影响
- GF/GR 转换边界
- WH-DRV-DRX 竞争机理

### Not Usable For
- 镍基合金 DDRX 连续场模型验证

### Mechanism Hints
- phenomenon: The results show that grain refinement is highly dependent on the stress state, and that for the compressive-dominated stress state (PSC and UC), the transition in the dominant...
- state_variables: PSC; UC; TR; WH; DRV; DRX; CDRX; DDRX
- claim_limit: 可进入 mechanism_argument_plan；强 claim 仍需逐条绑定全文、图表或实验锚点。
- causal_chain:
  - 0 1 { - } 1 0 s ^ { - 1 }$ Subsequently, the relationship among the transition in grain refinement mechanisms, the resultant flow stress characteristics and the applied stress s...
  - The dominant mechanism transitions from GF to GR as the Zener-Hollomon parameter decreases (i.e., with increasing temperature or decreasing strain rate).
- governing_model:
  - The equivalent stress data were calculated using formulas (4)\~(6) and subsequently corrected for friction using the equations provided in Ref.
  - Lai, A continuous dynamic recrystallization constitutive model combined with grain fragmentation and subgrain rotation for aluminum alloy 2219 under hot deformation, Model.
- boundary_conditions:
  - Conditions such as high strain, elevated temperature and low strain rate collectively promote a greater extent of DRX, leading to significant levels of dynamic softening.
  - The increased strain rate kinetically suppresses dynamic recovery, leading to a higher LAB density and pronounced grain boundary serrations, features reminiscent of the lower-te...
- validation_path:
  - The aforementioned studies predomi nantly conducted thermal simulation tests using a single, predefined loading mode.
  - Experiments and simulations ## 2.1.
- alternative_explanations:
  - However, the literature presents conflicting findings: Tang et al.
  - Due to equipment limitations, the 10 $\mathsf { s } ^ { - 1 }$ strain rate was not achievable for the TR test.
- evidence_anchor:
  - pdf: zotero://select/items/4VZ7PV7E page=
  - figure_or_table: image-1 page=
  - figure_or_table: image-2 page=1
  - figure_or_table: image-3 page=1

### Risk Flags
- reading_depth_locked

### Figure Candidates
- image-1 | page= | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/379c40d3ad10f90e2a19b221dec35d5c409bb8a823b6b3935e4fe3063e5cfd8c.jpg
- image-2 | page=1 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/64caa27ca02e05129a6411234c5558ab3ed140d6b4dc64e9b08210cddb557c02.jpg
- image-3 | page=1 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/02371344d1077bf95c235719779574905c6e36638e81f1cd6362f475a1c4e10b.jpg
- image-4 | page=1 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/7f3f67fdabf1f52a51f781a8201c353ead8f389d45782ca873a8380a131e4d5e.jpg
- image-5 | page=1 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/c40e56226664079013ddb90c6fdf05563a86fe102c5e9050e5e809de6c42383b.jpg
- image-6 | page=1 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/db54ff5e1b89f4da2e2e59eed953e6467fef16f2c6a881d96065971fc9e3b955.jpg
- image-7 | page=1 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/d9dee2199a3a8fd56335a3a69a8cdcf32da29a54774ca82e8839a2402a2f9ae5.jpg
- image-8 | page=1 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/bd394299c8039e288f09a9ebe25a5b93ca86fd5c29b1cee0f5917067e86a9dda.jpg
- image-9 | page=3 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/e91bd8dac3f73de0916aae36aa576464567789756faaa92f3b2f17a1ec252566.jpg
- image-10 | page=3 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/e5f6191f4df6eb2eba49c5f8d884a813ccbaa01f21a128b61ca0d99093fb40a7.jpg
- image-11 | page=3 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/627640eacb0645a0b45505507c64c72c1bab8ad081bd61410e271cc17008ee5a.jpg
- image-12 | page=4 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/092361367b0c053fe64b26183a6aacb1598c1c2321243bee1fb3bff1f130493b.jpg
- image-13 | page=4 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/5590209a07ac845ff5bd25815338dfc668d38bf6474c39c02733b2ed592f4541.jpg
- image-14 | page=4 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/ce0674432606765c0e49a57393372c8d965f518bcf90c26d9d3192c46ecbe043.jpg
- image-15 | page=4 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/367bfbf2a4ce46736501bee0c3993428a310e3a12a12a8499d7feb8021d4a6c8.jpg
- image-16 | page=5 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/f078218faa57b882c060675b03ba6ac15f59d113c879d8d6cb8470fad418ba0f.jpg
- image-17 | page=5 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/7018199825176f91974c316057e3b88a772acd28fe4baaa934efd2a79b7307e7.jpg
- image-18 | page=5 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/f18c5ebb941dfdb47b8cdc7d92512bebde75b09d2e334ee63f41cbb8272d253d.jpg
- image-19 | page=5 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/5872896d1cae38b7454b5eeb4a90d87e4c55daea211fdeb6120f200b5541505b.jpg
- image-20 | page=5 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/3462dbd681d56154172551a602bf4a065cb5fff3ee8c8276d90dbdcebd8de125.jpg
- image-21 | page=5 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/203b1509752c25be23a2e84e56447994bed381289a479c0f73dffe97fc2fd906.jpg
- image-22 | page=5 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/bca3abe1a291065b8e0ea8b5dd6c94c12361c197a99e1d317f8d7affc87d3e3f.jpg
- image-23 | page=6 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/e7853fff7e6f4de62fc305024e4739dbef6215e85a812628fa5165e0c0bb6c85.jpg
- image-24 | page=6 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/79e3e4a523b32356c441ee82eb8580853627647bd6c4126d4dce12ca4b531e11.jpg
- image-25 | page=6 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/f94bffdc5e88e60d93e03ebacd44f35831b55675a54cc235327cfc6798edab1b.jpg
- Fig. 7 | page=6 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/66563c5c32d82642e81212700e8a7acfb0a21124073cd332213426b538376271.jpg
- image-27 | page=7 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/323025dd391f19b41fca0c5c333f414c83b1a4b6a15f8c99aa85af878333b400.jpg
- image-28 | page=7 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/c9e9ed78780613e35f9821693883619ccb2fdf7815d20e769949c993dceec506.jpg
- image-29 | page=7 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/22dec1c9e70dc13d077d5b932ab117d9248e8a2869992a63870b1a8402dd4a83.jpg
- image-30 | page=7 | path=/Users/Bing/Zotero/storage/T57SPPQ3/LLM-for-Zotero-MinerU-cache-HMGU44G5.zip::images/67224d64114a14bc57a36f166e587795be0d7fedb93c4a2d82fc4f942af24328.jpg

## Chen2026_CPFE_CA_DDRX - A continuum-field-enabled multiscale framework coupling crystal plasticity and cellular automaton for discontinuous dynamic recrystallization: Application to a nickel-based superalloy

- reading_depth: full_text
- evidence_role: unknown
- content_fit: direct
- text_source: zotero_mineru
- image_source: MinerU ZIP / Zotero 图文资产

### Claim Summary
用连续转变分数替代 CA 离散状态跳变，可缓解 CPFE-CA 耦合中的非物理应力突跳并保持微观组织-力学响应一致。

### Method Summary
CPFE；cellular automaton；continuum-field sub-grid；bidirectional mapping

### Experiment Summary
Correlation between experiment and simulation results for: (a,c) X ; (b,d) $d _ { \mathrm { a v g } } .$ ![](images/5d64bac12b3abdb81e1b0766cd5814f442aeeb6fd2f18f6b4e025dba02993feb.jpg) Fig.

### Usable For
- DDRX 数值机理
- 连续场 CA-CPFE 耦合
- 形核和晶界迁移软化机制

### Not Usable For
- 铝合金 CDRX 特定滑移系结论

### Mechanism Hints
- phenomenon: Initially, the nucleation of a recrystallized grain provides a rapid pathway for releasing localized elastic distortion energy, resulting in an immediate stress relaxation at th...
- state_variables: CA; CPFE; DDRX; GBM; DRX; WH; DRV; CDRX
- claim_limit: 可进入 mechanism_argument_plan；强 claim 仍需逐条绑定全文、图表或实验锚点。
- causal_chain:
  - This coupled approach links detailed microstructure evolution driven by crystallographic mechanisms with macro scopic stress and strain fields, providing critical understanding...
  - Wang, Analysis of the mechanism of orientations evolution during hot rolling and mechanical properties of TiBw/TA15 composites based on crystal plasticity finite element model, J.
- governing_model:
  - this study develops a continuum-field-enabled multiscale framework that seamlessly integrates CPFE with a reformulated continuum-field CA model via a sub-grid description and a...
  - Thus, this work integrates a CA model within a CP framework to simulate mesoscopic DRX kinetics, balancing physical representativeness and computational efficiency.
- boundary_conditions:
  - (a) Representative volume element and (b) boundary conditions used for the numerical performance analysis.
  - The RVE was subjected to a macroscopic true strain of 0.51 under periodic boundary conditions (Fig.
- validation_path:
  - Experimental calibration and validation This section describes the experiments and numerical procedures undertaken to calibrate and validate the proposed CPFE-CA model for the F...
  - Results and discussion This section presents and discusses the simulation results obtained from the validated multiscale framework.
- alternative_explanations:
  - Once triggered, however, the excessive stored energy accumulated within the large element volume leads to a non-physically explosive recrystallization process, causing a sharp s...
  - At this stage, the CA module is not activated or participates only to a limited extent, so the model is not sensitive to the limitation on the maximum increment step.
- evidence_anchor:
  - pdf: zotero://select/items/XRMSR8RX page=
  - figure_or_table: image-1 page=3
  - figure_or_table: image-2 page=3
  - figure_or_table: Fig. 2 page=4

### Risk Flags
- reading_depth_locked

### Figure Candidates
- image-1 | page=3 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/69ed58c8b16360c8ecebcf351bdd2173424f3579f0638a9a55c3595e0e024081.jpg
- image-2 | page=3 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/63b7f8426b4505ff712d1cf02dbe5c7176d4735884dbd2c49309316573ae9a28.jpg
- Fig. 2 | page=4 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/f2ca572f2e9b8888120ae90ced6a2397943aa1dc816e55c27689b6e4c7354f34.jpg
- Fig. 3 | page=6 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/a6b7e1f57000db067f1b0de906f59007495a239b12068059de2ae3096325cb5e.jpg
- image-5 | page=8 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/6cd1f23ae9d0ba98a9e5306f1a5886926de14095a51933a4eddcbfc89f324c84.jpg
- image-6 | page=9 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/235ae5c2d324425d17c7fcafe7211441acb01fb719958a391c207b62d3a5c0d1.jpg
- image-7 | page=9 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/e4bfb314afe072702a3058d6a2c944ce1cda700d0146983b2316626d1554698b.jpg
- image-8 | page=9 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/0a4aac7e68bbecf494b99f64c571f262fe148e9132408f7e31c2c6e72b27f00e.jpg
- Fig. 6 | page=9 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/b933bd242628ab5bd5affc40ef60329aea1ac70943e9f765e35389f0436ceb7f.jpg
- image-10 | page=10 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/10441a5ba45576d23d65b493577637c528005f999b45dcc799b9cc601cecf70a.jpg
- image-11 | page=12 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/89dcc8212fe10be9d21844607e54c108caeed28472338738b77f03825a6267ed.jpg
- image-12 | page=12 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/e03a338b15568cd81e3c3d6a4acc0142a87ca842f35f16d9eee5ffdc4e297488.jpg
- image-13 | page=12 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/b840cd6b1b0a537a8a01d721023dfe3c9cadc59d19a6ff4ff52755a0cabc91fa.jpg
- image-14 | page=12 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/520a774fa4d2b3b95cc101da5574fd7600fe63c86693a13bb52a6b8382e146c2.jpg
- image-15 | page=12 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/0a074c59cb5dde5ce333be49eddee6c580b03ce552c396cce0eb786d7c3590c1.jpg
- Fig. 9 | page=12 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/fd6678e15baabf60d0f7936f5155592e28c21d464980014fb715b6c9006f100b.jpg
- Fig. 12 | page=14 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/5d64bac12b3abdb81e1b0766cd5814f442aeeb6fd2f18f6b4e025dba02993feb.jpg
- image-18 | page=15 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/a154ff92999b623577faf4c697590c4dbc443bb5c75337e302e4e5029f4cb897.jpg
- Fig. 14 | page=16 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/213d5c135a0d674d785b5a1bcb0e30d24ad4e8d390e9ff25c5bab5c87d454e10.jpg
- Fig. 15 | page=16 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/5079e6fb3912081b6e58d0e778e548bd0ebe6cbe86f2ff27ec6056ce9d477f83.jpg
- Fig. 17 | page=17 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/3f6a87e05a547a7f1ffb882b78cb158f26b51cc8c894d00e090f1c1f552e5021.jpg
- image-22 | page=19 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/4aa172b547b69e95e9d16ae5ebe2187eb190be569e9c0c6fbea90dd89d2381b8.jpg
- table-1 | page=11 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/77e9062fbffae01a971cca45f9dbec2d3298c03f1170edf9b08b3941341ef8d0.jpg
- table-2 | page=19 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/76c92b087d20fd1cb057a0c5c663bbf80f56ab8d3a665f75f903aeb924f96fc6.jpg
- table-3 | page=19 | path=/Users/Bing/Zotero/storage/K2B2VTBY/LLM-for-Zotero-MinerU-cache-8F8XJXI8.zip::images/fc2e54c8b7e820a2a31077f6d7626961a648969111a26bb8668e367e0e101df9.jpg
