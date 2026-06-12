# Download

## 何时使用
- 已有 DOI、标题、BibTeX、URL 或参考文献列表，需要直接进入 Step 5
- Step 4 已完成，需要统一路由下载 PDF
- 想检查下载会话、预览路由或补下失败条目

## 最小输入
- DOI / 标题 / BibTeX / JSON 检索结果 / 参考文献列表中的任一种
- 可选：出版社来源、机构访问状态、已知 article URL

## 主要产出
- 规范化后的下载清单
- PDF 文件到 `paper-temp/` 或指定目录
- `unresolved_download_items.md`（如存在未解决项）

## 常见阻塞点
- 标题输入先要归一化成 DOI 或 article URL
- CNKI/万方 / IEEE / 出版商登录属于访问状态问题，不是写作问题
- 顺序执行优先于并发吞吐，尤其是中文库与 CDP 会话
