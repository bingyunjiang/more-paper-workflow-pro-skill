# Zotero Missing PDF Attachments — Find & Download

如何在 Zotero 文库中定位无 PDF 附件的条目，并通过多出版商 CDP 方式补下。

## 问题定义

Zotero 条目有元数据（标题、作者、DOI、集合归属）但无 PDF 附件（child items 为空）。这些条目在批量检索和导入后常见，需要补下 PDF。

## 检出流程

### 方式 A：集合级别批量扫描（推荐）

用 `zotero_get_collection_items(collection_key, detail='summary')` 逐集合扫描，summary 模式含 `**Attachments:**` 字段：

```
## N. Title
**Attachments:** PDF, 1 attachment  ← 有附件
...
## M. Title
**Tags:** `P0-B1`                    ← 无Attachments行 = 无PDF
```

**无附件的特征：** 条目块中**没有** `**Attachments:**` 这一行。

### 方式 B：确认 children 为空

```python
zotero_get_items_children(item_keys=[...])
# 返回 "No child items." = 确认无PDF
```

### 扫描建议

| 目标 | 方法 | 耗时 |
|------|------|------|
| 全库扫描 | 对所有集合执行 detail='summary'（每次限100条，需翻页） | 依赖库大小 |
| 定向检查 | 用 `zotero_semantic_search(topic)` → 筛选无附件条目 | 快速 |

## 出版商分类下载策略

检出无附件条目后，按照 DOI 的前缀决定下载策略：

### A 类：OA 期刊（直连 HTTP）

| 出版商 | DOI 前缀 | PDF URL 模式 | 已验证 |
|--------|----------|-------------|--------|
| Nature Comms | `10.1038/s41467-` | `https://www.nature.com/articles/{id}.pdf` | ✅ 3.1MB |

直接 `urllib.request` + User-Agent 即可下载，无需浏览器。

### B 类：CDP + 机构登录（推荐）

参见 `publisher-access-matrix.md` 的完整矩阵和 CDP 通用方案。

**前置条件：**
1. CDP Chrome 已启动（`--remote-debugging-port=9223`）
2. 通过 `Network.getCookies` 确认有出版商 Cookie
3. 若无 Cookie → 在 CDP Chrome 窗口中完成机构登录

**已验证成功的出版商：**\n| 出版商 | 成功率 | 方法 |\n|--------|--------|------|\n| **IEEE** | 5/5 (100%) | 两步走：[Step A] 文章页→点PDF按钮→stamp新标签页→Fetch＋Page.reload。[Step B，A失败时回退] 直接导航到 `stamp/stamp.jsp?tp=&arnumber=XXXXX` 或 `stampPDF/getPDF.jsp?tp=&arnumber=XXXXX` → Fetch＋Page.reload。**注意：** 若stamp页面重定向到 `?denied=` 表示该论文当前机构订阅未覆盖，跳过。 |\n| **Wiley** | 有限 | epdf URL + Fetch → 需要处理云阅读器问题 |

### C 类：Sci-Hub CDP（仅限 2021 年前论文）

用 `download_via_scihub.py`，自动测试镜像站后批量下载。详见 `publisher-access-matrix.md`。

## Cookie 诊断（关键前置步骤）

见 `publisher-access-matrix.md` → 「先决条件：CDP 浏览器与会话管理」→「CDP Cookie 诊断」。

**特别注意：** CDP Chrome 使用隔离的临时 Profile（如 `/tmp/chrome_scidownload`），用户在日常 Chrome 完成的登录不共享。需要：
- **方案 A：** 在 CDP Chrome 窗口中手动登录
- **方案 B：** 关闭日常 Chrome → 用真实 Profile 启动 CDP Chrome（需清理残留锁文件）

## 附件挂回 Zotero

Zotero MCP 无"为已有条目添加 PDF 附件"的接口。两种方式：

| 方式 | 操作 | 适用场景 |
|------|------|----------|
| **手动拖拽** | 在 Zotero 桌面端将 PDF 拖到对应条目上 | 少量（<20篇） |
| **zotero_add_from_file** | 创建新条目（PDF中有DOI时自动匹配元数据，需手动合并/删除重复） | 批量，但会产生重复 |

推荐手动拖拽——零配置，最可靠。
