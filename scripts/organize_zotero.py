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
try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import sys, os, re, json
from collections import defaultdict

TEMPLATE = """# Zotero 文库架构

> 生成时间: {time}
> 依据: {source}

## 文库结构

```
📁 {root_name} （根集合）
{structure}
```

## 标签方案

| 标签 | 章节/方向 | 说明 |
|------|-----------|------|
{tags}

## 创建方式

### 方式一：手动创建
在 Zotero 桌面端 → 新建集合 → 按上述结构逐级创建。

### 方式二：MCP 自动创建（推荐）
由 AI agent 通过 `zotero_create_collection` 工具递归创建，
详见 `agents/step_6_zotero.md` → 6a-MCP 节。
"""

DEFAULT_ROOT_NAME = "论文文献库"
TEMPLATE_TITLES = {"论文大纲与关键词", "论文大纲", "大纲关键词"}
HEADER_TAGS = {
    "关键词", "关键字", "标签", "术语", "说明", "章节",
    "keyword", "keywords", "tag", "tags", "term", "terms", "section",
}
META_SECTION_TITLES = {
    "论文标题", "检索语言", "关键词清单", "章节证据需求表",
    "Step 3/6/7 交接", "Step 3/6/7 Handoff",
}
OUTLINE_SECTION_TITLES = {"章节大纲", "论文大纲", "大纲"}


def _clean_title(value):
    """Normalize a candidate paper title extracted from the outline."""
    if not value:
        return ""
    value = value.strip().strip("#").strip()
    value = re.sub(r"^[：:\-\s]+", "", value).strip()
    value = re.sub(r"\s+", " ", value)
    return value


def extract_paper_title(keywords_text):
    """Extract the paper title from 大纲关键词.md using Step 2's format."""
    lines = keywords_text.splitlines()

    # Preferred Step 2 format:
    # ## 论文标题
    # Actual title
    for i, line in enumerate(lines):
        if re.match(r"^##+\s*论文标题\s*$", line.strip()):
            for nxt in lines[i + 1:]:
                if nxt.strip().startswith("#"):
                    break
                candidate = _clean_title(nxt)
                if not candidate:
                    continue
                return candidate

    # Inline title lines.
    inline_patterns = [
        r"^\s*(论文题目|题目|标题|研究主题)\s*[：:]\s*(.+?)\s*$",
    ]
    for line in lines:
        for pat in inline_patterns:
            m = re.match(pat, line)
            if m:
                candidate = _clean_title(m.group(2))
                if candidate:
                    return candidate

    # YAML/frontmatter title.
    if lines and lines[0].strip() == "---":
        for line in lines[1:]:
            if line.strip() == "---":
                break
            m = re.match(r"^\s*title\s*:\s*[\"']?(.+?)[\"']?\s*$", line)
            if m:
                candidate = _clean_title(m.group(1))
                if candidate:
                    return candidate

    # Last resort: a first-level heading that is not the template title.
    for line in lines:
        m = re.match(r"^#\s+(.+?)\s*$", line.strip())
        if m:
            candidate = _clean_title(m.group(1))
            if candidate and candidate not in TEMPLATE_TITLES:
                return candidate

    return DEFAULT_ROOT_NAME


def generate_structure(keywords_text):
    """从大纲关键词文件生成 Zotero 集合结构（支持多级嵌套）。"""
    chapters = []
    table_rows = []        # (tag, desc) for last chapter
    current_path = []
    current_level = 0
    in_table = False
    section = ""

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
            section = title
            if title in META_SECTION_TITLES or title in OUTLINE_SECTION_TITLES:
                in_table = False
                continue

            # 按 level 裁剪 / 追加路径
            current_path = current_path[:level - 1]
            current_path.append(title)
            current_level = level

            chapters.append({
                "level": level,
                "path": list(current_path),
                "rows": [],
            })
            in_table = False
            continue

        # ── Step 2 标准格式：## 章节大纲 下的编号列表 ──
        if section in OUTLINE_SECTION_TITLES:
            om = re.match(r"^(\d+(?:\.\d+)*)[\.、]\s*(.+)$", stripped)
            if om:
                number = om.group(1)
                title = om.group(2).strip()
                depth = number.count(".") + 1
                current_path = current_path[:depth - 1]
                current_path.append(title)
                chapters.append({
                    "level": depth,
                    "path": list(current_path),
                    "rows": [],
                    "number": number,
                })
                continue
            if stripped.startswith("|") and stripped.endswith("|"):
                continue

        # ── Step 2 扩展元信息表：供 Step 3/7 使用，不进入 Zotero 架构 ──
        if (
            section in META_SECTION_TITLES
            and section != "关键词清单"
            and stripped.startswith("|")
            and stripped.endswith("|")
        ):
            continue

        # ── Step 2 标准格式：## 关键词清单 表格 ──
        if section == "关键词清单" and stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if cells and (cells[0].lower() in HEADER_TAGS or set(cells[0]) <= {"-", ":"}):
                continue
            if len(cells) >= 2 and chapters:
                chapter_ref = cells[0]
                tag = cells[1]
                desc = cells[2] if len(cells) >= 3 else ""
                if tag and tag.lower() not in HEADER_TAGS and not tag.startswith("-"):
                    target = None
                    for ch in chapters:
                        if str(ch.get("number", "")) == chapter_ref:
                            target = ch
                            break
                    if target is None:
                        target = chapters[-1]
                    rows = list(target.get("rows", []))
                    rows.append((tag, desc))
                    target["rows"] = rows
                continue

        # ── 识别表格行: | tag | desc | ──
        # 要求以 | 开头且结尾，中间不含分隔线 (----)
        tm = re.match(r'^\|\s*(\S[\S ]*?\S)\s*\|\s*(.+?)\s*\|$', stripped)
        if tm and chapters:
            tag = tm.group(1).strip()
            desc = tm.group(2).strip()
            if tag and tag.lower() not in HEADER_TAGS and not tag.startswith("-"):
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

    return "\n".join(lines), tag_map, chapters


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


def build_tree(chapters, root_name=DEFAULT_ROOT_NAME):
    """将扁平的章节列表转换为嵌套树结构，供 JSON 输出和 MCP 递归创建。

    每个 chapter 有 level (1-based, 1=一级标题) 和 path (从根到当前节点的标题列表)。
    返回: {"name": root_name, "children": [...]}
    """
    root = {"name": root_name, "children": []}

    # path_stack[i] = 当前 depth i 对应的树节点引用
    # depth 0 = root, depth 1 = 一级标题, ...
    path_stack = [root]

    for ch in chapters:
        depth = ch["level"]         # 1=一级, 2=二级, ...
        label = ch["path"][-1]      # 当前节点自己的标题

        # 裁剪栈到当前深度（回溯到父级）
        path_stack = path_stack[:depth]

        tags = []
        for tag, desc in ch["rows"]:
            tags.append({"tag": tag, "desc": desc})

        node = {"name": label, "tags": tags, "children": []}
        path_stack[-1]["children"].append(node)
        path_stack.append(node)

    return root


def tree_to_json(root):
    """将树结构序列化为 JSON 字符串。"""
    return json.dumps(root, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import argparse, datetime
    parser = argparse.ArgumentParser(description="生成 Zotero 文库架构")
    parser.add_argument("input", nargs="?", help="大纲关键词.md 文件")
    parser.add_argument("--output", "-o", default="zotero-架构.md")
    parser.add_argument("--json", "-j", dest="json_output", default=None,
                        help="额外输出 JSON 树结构（供 MCP 自动创建集合使用）")
    parser.add_argument("--template", "-t", help="标签方案示例文件")
    parser.add_argument("--root-name", default=None,
                        help="Zotero 根集合名；不传时从大纲中的论文标题自动解析")
    args = parser.parse_args()

    keywords = ""
    source = "手动输入"
    tree = None  # 嵌套树结构，供 JSON 输出
    if args.input and os.path.exists(args.input):
        with open(args.input, encoding="utf-8") as f:
            keywords = f.read()
        source = args.input

    root_name = _clean_title(args.root_name) if args.root_name else (
        extract_paper_title(keywords) if keywords else DEFAULT_ROOT_NAME
    )

    if keywords:
        structure, tag_map, chapters = generate_structure(keywords)
        tags_table = generate_tags(tag_map)
        tree = build_tree(chapters, root_name=root_name)
    else:
        structure = "    📁 1-基础\n    📁 2-散热\n    📁 3-预测\n    📁 4-控制"
        tags_table = "| P0-A1 | 基础理论 | 领域基础理论 |"
        tree = None

    content = TEMPLATE.format(
        time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        source=source,
        root_name=root_name,
        structure=structure,
        tags=tags_table,
    )

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Zotero 架构已保存至: {args.output}", flush=True)

    # JSON 输出（供 MCP 自动创建集合使用）
    if args.json_output and tree:
        with open(args.json_output, "w", encoding="utf-8") as f:
            f.write(tree_to_json(tree))
        print(f"Zotero 架构 JSON 已保存至: {args.json_output}", flush=True)
    elif args.json_output:
        print("⚠ --json 需要有效的输入文件来生成树结构", flush=True)
