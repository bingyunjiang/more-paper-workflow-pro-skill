# Search Source Capability Evidence

本文件记录 Step 3 来源编译器在 2026-07-11 的官方文档查证结果。能力真相的机器源是 `config/search_source_capabilities.json`。文档或接口变化后必须重新查证，不得依靠旧经验延续 `exact` 状态。

## 已查证结论

- OpenAlex Works Search：官方文档明确支持大写 `AND / OR / NOT`、双引号短语、`~N` 邻近、通配和模糊检索；通配需使用 `search.exact`。长布尔查询受约 4 KB URL 上限约束，应拆分后按 work ID 求并集。旧的 `filter=title.search:` 已标为 deprecated。
- Crossref REST：官方文档提供 `/works`、query 参数、filter、rows/cursor 等能力，但没有把 `query.title` 或 `query.bibliographic` 定义为可依赖的集合布尔语言。2026-07-11 对 `query.title` 的探针中，`cold plate`、引号版本以及带 `AND/OR/NOT` 的版本返回相同 total，不能据此声称布尔或精确短语成立。因此 Crossref 只做降级候选召回，概念块约束由客户端复核。
- Semantic Scholar `/paper/search`：官方 Swagger 明确写明 `No special query syntax is supported`，且连字符词需要改为空格。该 endpoint 只接受 plain-text relevance query。
- Semantic Scholar `/paper/search/bulk`：官方 Swagger 单独说明支持 `+`、`|`、`-`、双引号短语、前缀 `*`、模糊和邻近。两种 endpoint 不得混用语法。
- PubMed：官方帮助页支持大写 `AND / OR / NOT`、括号、字段标签、双引号短语、通配和 `[Title/Abstract:~N]` 邻近；短语索引、Automatic Term Mapping、字段标签和通配之间存在明确交互，编译结果必须保留警告。
- arXiv API：官方手册支持 `ti / abs / au / cat / all` 等字段前缀，布尔操作符为 `AND / OR / ANDNOT`，支持括号和双引号短语。
- CNKI / 万方：当前工作流通过登录后的 CDP 网页适配器执行，不存在本 skill 已查证的稳定公开 API 合同。编译状态只能是 `manual_required` 或 `observed_ui`，UI 变化后需要重新探针。

## 2026-07-11 在线探针

- OpenAlex：`search=(battery AND "thermal management") NOT building` 返回成功，并在响应 `meta.x_query` 中展开为正向与否定的 fulltext search 条件，验证当前布尔解析器实际生效。
- Crossref：`query.title=cold plate`、引号、`AND`、`OR`、`NOT` 五种形式返回相同 total；该观察不能证明严格集合等价，但足以否定“仅凭操作符字符串就已保真编译”的假设。
- Semantic Scholar：普通和 bulk endpoint 在匿名探针中均返回 HTTP 429；语法能力因此保持 `documented`，不升级为 `probe_verified`。运行时必须保留限流降级。
- PubMed E-utilities：带 `[tiab]`、括号和布尔操作符的最小查询成功返回结果计数。
- arXiv API：带字段前缀、括号、`AND/OR` 和短语的最小查询成功返回 Atom feed 与 totalResults。

## 官方来源

- OpenAlex Search: https://developers.openalex.org/guides/searching
- OpenAlex Filters: https://developers.openalex.org/guides/filtering
- Crossref REST API: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- Crossref tips: https://www.crossref.org/documentation/retrieve-metadata/rest-api/tips-for-using-the-crossref-rest-api/
- Semantic Scholar Graph API / Swagger: https://api.semanticscholar.org/api-docs/graph
- PubMed Help: https://pubmed.ncbi.nlm.nih.gov/help/
- arXiv API User's Manual: https://info.arxiv.org/help/api/user-manual.html

## 编译状态规则

- `exact`：所用语义均有 endpoint 对应的官方文档支持。
- `degraded`：来源可以召回候选，但无法在服务端保真表达全部概念块；必须声明 `post_filter_required=true`。
- `manual_required`：网页/CDP adapter 尚无稳定公开合同，执行前需按当前 UI 探针。
- `invalid`：请求依赖来源明确不支持的语义，且没有安全降级路径。
