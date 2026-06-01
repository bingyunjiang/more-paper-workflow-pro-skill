#!/usr/bin/env python3
"""
生成 Zotero 文库组织架构（Step 6）。
读取论文大纲和关键词文件，生成 Zotero 集合结构。
输出为 Markdown 文件，供用户参考或在 Zotero 桌面端创建。

Usage:
  python3 scripts/organize_zotero.py 大纲关键词.md --output zotero-架构.md
"""
import sys, os, re

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
    """从大纲关键词文件生成 Zotero 集合结构"""
    chapters = []
    current_chapter = None

    for line in keywords_text.split("\n"):
        # 识别章节标题
        m = re.match(r"\|?\s*(\d+)\.?\s+(.+?)\s*\|?", line)
        if m:
            current_chapter = m.group(2).strip()
            chapters.append((current_chapter, []))
            continue

        # 识别子章节或标签
        m = re.match(r"\|?\s*(\S+)\s*\|\s*(.+?)\s*\|", line)
        if m and current_chapter:
            tag = m.group(1).strip()
            desc = m.group(2).strip()
            chapters[-1][1].append((tag, desc))

    # 生成结构文本
    lines = []
    for i, (ch, tags) in enumerate(chapters, 1):
        lines.append(f"    📁 {i}-{ch[:20]}")
        for j, (tag, desc) in enumerate(tags[:5]):
            lines.append(f"        ├── {tag}  {desc[:30]}")
    
    return "\n".join(lines)

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

    structure = generate_structure(keywords) if keywords else "    📁 1-基础\n    📁 2-散热\n    📁 3-预测\n    📁 4-控制"

    tags_table = "| P0-A1 | 基础理论 | 领域基础理论 |\n| P0-A3 | 方法综述 | 方法综述 |\n| P1-D5 | 子方向 | 子方向描述 |\n| P0-B2 | 方法 | 方法描述 |\n| P0-C2 | 控制策略 | 控制策略描述 |"

    content = TEMPLATE.format(
        time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        source=source,
        structure=structure,
        tags=tags_table
    )

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Zotero 架构已保存至: {args.output}", flush=True)
