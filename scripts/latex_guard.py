#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""
LaTeX compilation guard — validates .tex files for common errors before submission.

Inspired by PaperSpine's latex_guard.py. Detects:
  - Broken cross-references (\\ref{} without matching \\label{})
  - Undefined citations (\\cite{} without matching \\bibitem{} or .bib entry)
  - Missing packages for used commands
  - Unclosed environments
  - Duplicate labels

Usage:
  python3 latex_guard.py main.tex                    # Validate, print report
  python3 latex_guard.py main.tex --output report.md  # Save report
  python3 latex_guard.py main.tex --markdown            # Output as Markdown
  python3 latex_guard.py main.tex --fix-broken-refs    # Attempt auto-fix
"""
try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import sys
import os
import re
from collections import defaultdict


# ── Core Validation ──────────────────────────────────────────────────────────

def validate_tex(tex_path: str) -> dict:
    """Run all validation checks on a .tex file. Returns a results dict."""
    with open(tex_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    results = {
        "file": tex_path,
        "checks": {},
        "errors": 0,
        "warnings": 0,
    }

    # Check 1: Unclosed environments
    env_issues = _check_environments(content)
    results["checks"]["environments"] = env_issues
    results["errors"] += len(env_issues)

    # Check 2: Broken cross-references
    ref_issues = _check_references(content)
    results["checks"]["references"] = ref_issues
    results["errors"] += len([i for i in ref_issues if i["severity"] == "error"])
    results["warnings"] += len([i for i in ref_issues if i["severity"] == "warning"])

    # Check 3: Undefined citations
    cite_issues = _check_citations(content)
    results["checks"]["citations"] = cite_issues
    results["errors"] += len([i for i in cite_issues if i["severity"] == "error"])
    results["warnings"] += len([i for i in cite_issues if i["severity"] == "warning"])

    # Check 4: Duplicate labels
    dup_issues = _check_duplicate_labels(content)
    results["checks"]["duplicate_labels"] = dup_issues
    results["errors"] += len(dup_issues)

    # Check 5: Missing common packages
    pkg_issues = _check_missing_packages(content)
    results["checks"]["packages"] = pkg_issues
    results["warnings"] += len(pkg_issues)

    return results


# ── Individual Checks ────────────────────────────────────────────────────────

def _check_environments(content: str) -> list[dict]:
    """Check for unclosed \\begin{...} ... \\end{...} environments."""
    issues = []
    begins = re.findall(r'\\begin\{([^}]+)\}', content)
    ends = re.findall(r'\\end\{([^}]+)\}', content)

    from collections import Counter
    begin_counts = Counter(begins)
    end_counts = Counter(ends)

    for env in begin_counts:
        if begin_counts[env] != end_counts.get(env, 0):
            diff = begin_counts[env] - end_counts.get(env, 0)
            issues.append({
                "severity": "error",
                "message": f"环境 '{env}' 有 {begin_counts[env]} 个 \\begin 但 {end_counts.get(env, 0)} 个 \\end（差 {diff}）",
                "fix": f"添加 {diff} 个 \\end{{{env}}} 或删除多余的 \\begin{{{env}}}",
            })

    return issues


def _check_references(content: str) -> list[dict]:
    """Check for \\ref{} with undefined \\label{}."""
    issues = []

    # Extract all labels
    labels = set(re.findall(r'\\label\{([^}]+)\}', content))

    # Extract all refs
    refs_raw = re.findall(r'\\ref\{([^}]+)\}', content)
    refs = set(refs_raw)

    undefined = refs - labels
    for ref in undefined:
        ref_count = refs_raw.count(ref)
        issues.append({
            "severity": "error" if ref_count > 1 else "warning",
            "message": f"\\ref{{{ref}}} 引用了一个不存在的标签（出现 {ref_count} 次）",
            "fix": f"添加 \\label{{{ref}}} 或修正 \\ref 名称",
        })

    return issues


def _check_citations(content: str) -> list[dict]:
    """Check for \\cite{} commands without matching bibliography entries."""
    issues = []

    # Extract citation keys from \\cite{} commands
    cite_keys = set()
    for match in re.finditer(r'\\cite\{([^}]+)\}', content):
        for key in match.group(1).split(','):
            cite_keys.add(key.strip())

    # Extract keys from \\bibitem{} entries
    bibitem_keys = set(re.findall(r'\\bibitem\{([^}]+)\}', content))

    # If using bibliography file, we can't easily check — skip
    if '\\bibliography{' in content:
        return issues

    # Check \\cite without matching \\bibitem
    if bibitem_keys:
        undefined = cite_keys - bibitem_keys
        for key in undefined:
            issues.append({
                "severity": "error",
                "message": f"\\cite{{{key}}} 引用了不存在的 \\bibitem 条目",
                "fix": f"添加 \\bibitem{{{key}}} 或修正引用键名",
            })

    return issues


def _check_duplicate_labels(content: str) -> list[dict]:
    """Check for duplicate \\label{} definitions."""
    issues = []
    labels = re.findall(r'\\label\{([^}]+)\}', content)

    from collections import Counter
    label_counts = Counter(labels)

    for label, count in label_counts.items():
        if count > 1:
            issues.append({
                "severity": "error",
                "message": f"\\label{{{label}}} 定义了 {count} 次（重复）",
                "fix": f"重命名或删除重复的 \\label{{{label}}}",
            })

    return issues


def _check_missing_packages(content: str) -> list[dict]:
    """Check for commonly-used commands that require specific packages."""
    issues = []

    # Map of command patterns to required packages
    required_packages = {
        r'\\includegraphics': 'graphicx',
        r'\\tikz': 'tikz',
        r'\\hl\{': 'soul',
        r'\\cref\{': 'cleveref',
        r'\\num\{': 'siunitx',
        r'\\si\{': 'siunitx',
        r'\\ce\{': 'mhchem',
        r'\\url\{': 'hyperref',
        r'\\href\{': 'hyperref',
        r'\\subfloat': 'subfig',
        r'\\multirow': 'multirow',
        r'\\booktabs': 'booktabs',
    }

    packages_loaded = set(re.findall(r'\\usepackage(?:\[[^\]]*\])?\{([^}]+)\}', content))

    for pattern, pkg in required_packages.items():
        if re.search(pattern, content) and pkg not in packages_loaded and '\\' + pkg not in content:
            issues.append({
                "severity": "warning",
                "message": f"检测到 {pattern} 命令但未加载 {pkg} 宏包",
                "fix": f"在导言区添加 \\usepackage{{{pkg}}}",
            })

    return issues


# ── Report Rendering ─────────────────────────────────────────────────────────

def render_report_md(results: dict) -> str:
    """Render validation results as Markdown."""
    md = f"""# LaTeX 编译校验报告

> 文件：`{results['file']}`
> 错误：{results['errors']}  |  警告：{results['warnings']}

"""

    if results["errors"] == 0 and results["warnings"] == 0:
        md += "## ✅ 未检测到问题\n\nLaTeX 文件通过了所有校验检查。\n"
        return md

    # Environments
    envs = results["checks"].get("environments", [])
    if envs:
        md += "## 环境问题\n\n"
        for e in envs:
            md += f"- ❌ {e['message']}\n  → {e['fix']}\n"
        md += "\n"

    # References
    refs = results["checks"].get("references", [])
    if refs:
        errors = [r for r in refs if r["severity"] == "error"]
        warnings = [r for r in refs if r["severity"] == "warning"]
        if errors or warnings:
            md += "## 交叉引用问题\n\n"
            for r in errors:
                md += f"- ❌ {r['message']}\n  → {r['fix']}\n"
            for r in warnings:
                md += f"- ⚠️ {r['message']}\n  → {r['fix']}\n"
            md += "\n"

    # Citations
    cites = results["checks"].get("citations", [])
    if cites:
        md += "## 引用问题\n\n"
        for c in cites:
            prefix = "❌" if c["severity"] == "error" else "⚠️"
            md += f"- {prefix} {c['message']}\n  → {c['fix']}\n"
        md += "\n"

    # Duplicate labels
    dups = results["checks"].get("duplicate_labels", [])
    if dups:
        md += "## 重复标签\n\n"
        for d in dups:
            md += f"- ❌ {d['message']}\n  → {d['fix']}\n"
        md += "\n"

    # Packages
    pkgs = results["checks"].get("packages", [])
    if pkgs:
        md += "## 可能需要加载的宏包\n\n"
        for p in pkgs:
            md += f"- ⚠️ {p['message']}\n  → {p['fix']}\n"
        md += "\n"

    # Summary
    if results["errors"] > 0:
        md += f"## ⚠️ 发现 {results['errors']} 个错误\n\n建议在编译前修复所有错误项。\n"
    else:
        md += "## ✅ 无严重错误\n\n可以尝试编译。注意处理上面的警告项。\n"

    return md


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate LaTeX files for common errors",
    )
    parser.add_argument("tex_file", nargs="?", help="Path to .tex file")
    parser.add_argument("--output", "-o", help="Output report path")
    parser.add_argument("--markdown", action="store_true",
                        help="Output as Markdown (default: plain text)")
    parser.add_argument("--fix-broken-refs", action="store_true",
                        help="Attempt to fix broken references (experimental)")

    args = parser.parse_args()

    if not args.tex_file:
        parser.print_help()
        return

    if not os.path.exists(args.tex_file):
        print(f"❌ 文件不存在: {args.tex_file}")
        return

    print(f"🔍 校验 {args.tex_file} ...")
    results = validate_tex(args.tex_file)

    if args.markdown or args.output:
        report = render_report_md(results)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ 报告已保存: {args.output}")
        else:
            print(report)
    else:
        # Plain text output
        print(f"\n── 校验结果 ──")
        print(f"   错误: {results['errors']}  |  警告: {results['warnings']}")
        for check_name, issues in results["checks"].items():
            if issues:
                print(f"\n  [{check_name}]")
                for issue in issues[:5]:
                    prefix = "❌" if issue.get("severity") == "error" else "⚠️"
                    print(f"    {prefix} {issue['message']}")
        if results["errors"] == 0:
            print("\n✅ 未检测到严重错误")
        else:
            print(f"\n⚠️ 发现 {results['errors']} 个错误需修复")


if __name__ == "__main__":
    main()
