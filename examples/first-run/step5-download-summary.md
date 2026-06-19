# Step 5 Sample

## 输入

3 个 DOI：

- `10.1016/j.est.2024.113105`
- `10.1109/ACCESS.2024.3399912`
- `10.1016/j.energy.2022.125097`

## 触发结果

- 直接进入 Step 5：统一下载路由
- 不要求回跑 Step 1-4

## 最小产物片段

```markdown
# 下载路由预览

| DOI | Publisher Guess | Route | Status |
|---|---|---|---|
| 10.1016/j.est.2024.113105 | Elsevier | Sci-Hub -> SD CDP | ready |
| 10.1109/ACCESS.2024.3399912 | IEEE | Sci-Hub -> Generic CDP / IEEE fallback | ready |
| 10.1016/j.energy.2022.125097 | Elsevier | Sci-Hub -> SD CDP | ready |

输出：
- `download_manifest.json`
- `unresolved_download_items.md`（若有失败）
```

## 你会立刻得到什么

- 下载路由是否可走通
- 哪些条目已经 `ready`
- 哪些条目需要人工登录或后续修复
