# Direct API Search Fallback

> 当 `scripts/search_by_topic.py` 无法使用（bug、限流、结果噪声大）时的直接 API 检索替代方案。
> 适用于 Step 4 的紧急回退。

## 何时使用

- `search_by_topic.py` 抛出未预期错误
- Semantic Scholar 持续 429
- OpenAlex 检索结果噪声 > 80%（大量无关论文混入）
- 需要精确控制查询参数或过滤逻辑

## 核心原则

对于传统工科方向（机械/电气/热工），**title-focused 查询** 远优于全文 search：

1. 至少使用 2 组 title 关键词做 AND（如 `title.search:"EV charger"` 结合全文 search thermal）
2. 或：用全文 search 然后 Python 层做 title 关键词二次过滤
3. 或：逐条 API 调用+本地评分，不做多源 federate

## OpenAlex 直接 API 调用

```python
import requests

url = "https://api.openalex.org/works"
params = {
    "search": "EV charger thermal management cooling",
    "filter": "type:article",
    "sort": "relevance_score:desc",
    "per-page": 100,
}
resp = requests.get(url, params=params, timeout=30)
data = resp.json()

for p in data.get("results", []):
    doi = (p.get("doi") or "").replace("https://doi.org/", "")
    title = p.get("title") or ""
    year = p.get("publication_year")
    cited = p.get("cited_by_count", 0) or 0
    
    # SAFE venue extraction (避坑: source 可能为 None)
    venue = ""
    primary_loc = p.get("primary_location")
    if primary_loc and isinstance(primary_loc, dict):
        src = primary_loc.get("source")
        if src and isinstance(src, dict):
            venue = src.get("display_name", "") or ""
    
    authors = []
    for a in p.get("authorships", []):
        if a and isinstance(a, dict):
            author_obj = a.get("author")
            if author_obj and isinstance(author_obj, dict):
                name = author_obj.get("display_name", "") or ""
                if name:
                    authors.append(name)
```

## 重试策略

```python
def search_s2(query, limit=100, retries=3):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": query, "limit": min(limit, 100),
              "fields": "title,authors,year,externalIds,citationCount,venue"}
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 429:
                wait = 5 * (attempt + 1)
                print(f"  429, waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json().get("data", [])
        except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as e:
            print(f"  SSL/Connection error: {e}, waiting 3s...")
            time.sleep(3)
    return []
```

**关键：** 每调用之间必须 `time.sleep(1.1)`。SSL 错误后不要立即重试同一 query — 先等待 5s。连续 2 次 429 → 跳过 S2，仅用 OpenAlex。

## 传统工科检索参数（推荐）

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| 源 | OpenAlex 优先 | S2 仅作为补充（受限于 429） |
| limit | 50-100 | Deep 用 100，Quick 用 30 |
| 策略 | relevance + cited + recent | 3 条线并行，去重 |
| title 过滤 | `title.search:(term1 OR term2)` | 大幅降低噪声 |
| 年份 | ≥2020 或 ≥2018 | 视需求调整 |
| 排除 | `NOT "battery"` 等 | 工科方向常见干扰源 |

## 本地评分方案

直接 API + 本地 Python 评分（基于 title 关键词 + year + citations + venue）比 `search_by_topic.py` 的管线式流程更可控：

1. 先用 API 拉取原始结果（~300-600 篇去重后）
2. Python 层做 title 关键词评分（定义 domain-specific 关键词分组）
3. 输出 T1/T2/T3 分级 + 统计报告
4. 绕过 federated_kg_resolver / rcs_parser 等脚本

适用于 Step 4.6 引文扩展后的评分闭环。
