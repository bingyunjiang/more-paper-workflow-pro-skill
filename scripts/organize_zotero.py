#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""
生成 Zotero 文库组织架构（Step 6）。
读取论文大纲和关键词文件，生成 Zotero 集合结构。
输出为 Markdown 文件，供用户参考或在 Zotero 桌面端创建。

支持格式：
  - ## / ### / #### 级别的 markdown heading 作为章节标题
  - | 关键字 | 说明 | 表格行作为该章节下的子节点

Usage:
  python3 scripts/organize_zotero.py 大纲关键词.md --output zotero-架构.md
"""
import sys, os, re
from collections import defaultdict

TEMPLATE = """# Zotero 文库架构

> 生成时间: {time}
> 依据: {source}

## 文库结构

```
📁 研究主题论文文献库 （根集合）
{structure}
```

## 标签方案

| 标签 | 章节/方向 | 说明 |
|------|-----------|------|
{tags}

## 创建方式

### 方式一：手动创建
在 Zotero 桌面端 → 新建集合 → 按上述结构逐级创建。

### 方式二：API 自动创建（待实现）
通过 Zotero Web API 自动创建集合树。
"""


def generate_structure(keywords_text):
    """从大纲关键词文件生成 Zotero 集合结构（支持多级嵌套）。"""
    chapters = []
    table_rows = []        # (tag, desc) for last chapter
    current_path = []
    current_level = 0
    in_table = False

    for line in keywords_text.split("\n"):
        stripped = line.strip()

        # ── 识别 markdown heading: ## / ### / #### ──
        hm = re.match(r'^(#{2,4})\s+(.+)$', stripped)
        if hm:
            # 先把前一个章节积累的表格行归档
            if table_rows and chapters:
                chapters[-1]["rows"] = list(table_rows)
            table_rows = []

            level = len(hm.group(1)) - 1   # ##→1, ###→2, ####→3
            title = hm.group(2).strip()
            # 按 level 裁剪 / 追加路径
            current_path = current_path[:level]
            current_path.append(title)
            current_level = level

            chapters.append({
                "level": level,
                "path": list(current_path),
                "rows": [],
            })
            in_table = False
            continue

        # ── 识别表格行: | tag | desc | ──
        # 要求以 | 开头且结尾，中间不含分隔线 (----)
        tm = re.match(r'^\|\s*(\S[\S ]*?\S)\s*\|\s*(.+?)\s*\|$', stripped)
        if tm and chapters:
            tag = tm.group(1).strip()
            desc = tm.group(2).strip()
            if tag and tag != "关键词" and not tag.startswith("-"):
                table_rows.append((tag, desc))
                in_table = True
            continue

        # 遇到非空、非表格行 → 关闭表格积累
        if stripped and not stripped.startswith("|"):
            if table_rows and chapters:
                chapters[-1]["rows"] = list(table_rows)
                table_rows = []
            in_table = False

    # 收尾：最后的表格行
    if table_rows and chapters:
        chapters[-1]["rows"] = list(table_rows)

    # ── 渲染结构文本 ──
    lines = []
    tag_map = defaultdict(list)  # chapter_label -> [(tag, desc)]
    for ch in chapters:
        indent = "    " * ch["level"]
        label = ch["path"][-1]
        lines.append(f"{indent}📁 {label}")

        for tag, desc in ch["rows"][:8]:    # 最多 8 个关键字
            lines.append(f"{indent}    ├── {tag}  {desc[:50]}")
            tag_map[label].append((tag, desc))

    return "\n".join(lines), tag_map


def generate_tags(tag_map):
    """从解析到的标签生成标签方案表格。"""
    rows = []
    order = 1
    for chapter, tags in tag_map.items():
        for tag, desc in tags:
            label = f"P{order}"
            rows.append(f"| {label:6s} | {chapter[:20]:20s} | {desc[:40]} |")
            order += 1
    if not rows:
        rows.append("| P0-A1 | 基础理论 | 领域基础理论 |")
    return "\n".join(rows)


if __name__ == "__main__":
    import argparse, datetime
    parser = argparse.ArgumentParser(description="生成 Zotero 文库架构")
    parser.add_argument("input", nargs="?", help="大纲关键词.md 文件")
    parser.add_argument("--output", "-o", default="zotero-架构.md")
    parser.add_argument("--template", "-t", help="标签方案示例文件")
    args = parser.parse_args()

    keywords = ""
    source = "手动输入"
    if args.input and os.path.exists(args.input):
        with open(args.input, encoding="utf-8") as f:
            keywords = f.read()
        source = args.input

    if keywords:
        structure, tag_map = generate_structure(keywords)
        tags_table = generate_tags(tag_map)
    else:
        structure = "    📁 1-基础\n    📁 2-散热\n    📁 3-预测\n    📁 4-控制"
        tags_table = "| P0-A1 | 基础理论 | 领域基础理论 |"

    content = TEMPLATE.format(
        time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        source=source,
        structure=structure,
        tags=tags_table,
    )

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Zotero 架构已保存至: {args.output}", flush=True)
