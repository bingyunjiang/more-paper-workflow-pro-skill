# Windows BibTeX Smoke Test Pack

用于在 Windows 环境下实测 `more-paper-workflow-pro-skill` 的 Step 5 下载链路与基础兼容性。

## 包内容

- `windows_smoketest_publishers.bib`
  - 一批来自 Zotero 的中英文 BibTeX 条目
  - 已尽量覆盖多个出版社，重点补强 `Elsevier / ScienceDirect`
- `windows_smoketest_manifest.csv`
  - 条目清单，便于按出版社、语言、DOI 前缀分批测试
- `中文论文元数据.json`
  - 给 CNKI / 万方下载脚本直接使用的中文输入文件
  - 采用 `title + source + article_url` 最小契约，并补齐推荐字段
- `中文下载清单.md`
  - 中文源下载所需字段说明
  - 标出 `ready` 与 `unresolved` 条目
- `windows_smoketest_notes.md`
  - 建议测试顺序和注意事项

## 设计原则

- 不追求“大而全”，而是追求“小而全”
- 优先选择：
  - 有 DOI
  - 出版社明确
  - 与充电桩 / 储能 / 电池热管理 / 快充 / V2G 相关
  - 对下载路由有代表性
- 中文条目主要用于验证：
  - BibTeX 编码兼容性
  - Windows 路径与控制台兼容性
  - 非英文元数据在流程中的稳健性
- 中文下载真正建议使用 `中文论文元数据.json`，不要只喂 BibTeX

## 建议测试顺序

1. 先测 `Elsevier / ScienceDirect`
2. 再测 `IEEE`
3. 再测 `MDPI / Wiley / Springer / RSC / Nature`
4. 最后测中文条目，观察编码、文件名、日志输出是否稳定

## 备注

- `Elsevier / ScienceDirect` 已放入 5 条，方便压主链路
- `Springer` 这条在 Zotero 中元数据不完整，但 DOI 合法，适合测“弱元数据 BibTeX”的兼容性
- 中文条目不保证都能走同一英文出版社下载路由；它们主要用于系统兼容性与编码回归
