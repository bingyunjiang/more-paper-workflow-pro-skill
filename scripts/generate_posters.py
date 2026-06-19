#!/usr/bin/env python3
# Copyright (c) 2026 Dr. Jiang Bingyun
# Licensed under CC BY-NC-SA 4.0 — Attribution-NonCommercial-ShareAlike 4.0 International
# https://creativecommons.org/licenses/by-nc-sa/4.0/
#
"""Generate promotional posters in multiple styles for More Paper Workflow Pro Skill.

Usage: python3 scripts/generate_posters.py
Requires: pip install Pillow
"""
try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import os
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = "posters"
W, H = 1400, 2200

# ---- color palettes ----
PALETTES = {
    "dark": {  # current — tech / modern
        "name": "Dark Tech",
        "bg":      (18, 22, 28),
        "card":    (28, 34, 42),
        "accent":  (99, 160, 255),
        "accent2": (255, 153, 51),
        "green":   (80, 200, 130),
        "white":   (230, 235, 245),
        "grey":    (140, 150, 165),
        "dim":     (80, 88, 100),
    },
    "light": {  # clean / minimal
        "name": "Clean Light",
        "bg":      (248, 250, 252),
        "card":    (255, 255, 255),
        "accent":  (30, 100, 200),
        "accent2": (220, 120, 30),
        "green":   (30, 160, 80),
        "white":   (20, 28, 38),
        "grey":    (90, 100, 115),
        "dim":     (180, 188, 200),
    },
    "warm": {  # academic / paper
        "name": "Academic Warm",
        "bg":      (252, 248, 240),
        "card":    (255, 252, 245),
        "accent":  (120, 60, 30),
        "accent2": (180, 100, 40),
        "green":   (60, 130, 80),
        "white":   (40, 30, 20),
        "grey":    (110, 90, 70),
        "dim":     (200, 190, 175),
    },
    "terminal": {  # hacker / CLI vibe
        "name": "Terminal Green",
        "bg":      (10, 14, 10),
        "card":    (18, 26, 18),
        "accent":  (80, 255, 80),
        "accent2": (200, 200, 80),
        "green":   (80, 255, 80),
        "white":   (200, 240, 200),
        "grey":    (120, 160, 120),
        "dim":     (60, 90, 60),
    },
}

# ---- fonts ----
FONT_BASE = "/System/Library/Fonts"
FT = FB = FM = FC = None  # FC = Chinese font
for key, paths in [
    ("FT", [f"{FONT_BASE}/Helvetica.ttc",
            f"{FONT_BASE}/Supplemental/Arial Bold.ttf"]),
    ("FB", [f"{FONT_BASE}/Helvetica.ttc",
            f"{FONT_BASE}/Supplemental/Arial.ttf"]),
    ("FM", [f"{FONT_BASE}/Menlo.ttc",
            f"{FONT_BASE}/SFMono-Regular.otf"]),
    ("FC", [f"{FONT_BASE}/STHeiti Medium.ttc",
            f"{FONT_BASE}/Songti.ttc"]),
]:
    for p in paths:
        if os.path.exists(p):
            if key == "FT": FT = p
            elif key == "FB": FB = p
            elif key == "FM": FM = p
            elif key == "FC": FC = p
            break
if not FT:
    FT = FB = FM = FC = ImageFont.load_default()


def _f(size, w="body"):
    path = FT if w == "title" else FM if w == "mono" else FC if w == "cn" else FB
    try: return ImageFont.truetype(path, size)
    except Exception: return ImageFont.load_default()


def _t(draw, xy, text, font, fill):
    draw.text(xy, text, font=font, fill=fill)


def _c(draw, y, text, font, fill):
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text(((W - (bb[2] - bb[0])) // 2, y), text, font=font, fill=fill)


def _b(draw, x, y, text, font, bg, fg):
    bb = draw.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    px, py = 14, 8
    draw.rounded_rectangle([x, y, x + tw + px * 2, y + th + py * 2], radius=6, fill=bg)
    draw.text((x + px, y + py), text, font=font, fill=fg)


def _hl(draw, y, dim):
    draw.line([(60, y), (W - 60, y)], fill=dim, width=1)


def _wrap(draw, text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = cur + (" " if cur else "") + w
        bb = draw.textbbox((0, 0), test, font=font)
        if bb[2] - bb[0] <= max_width:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines


def _card(draw, x, y, w, h, title, lines, fb, fs, card, accent, grey):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=card)
    _t(draw, (x + 20, y + 16), title, fb, accent)
    for i, line in enumerate(lines):
        _t(draw, (x + 20, y + 50 + i * 30), line, fs, grey)


def make_poster(palette):
    P = palette
    img = Image.new("RGB", (W, H), P["bg"])
    d = ImageDraw.Draw(img)

    ft   = _f(56, "title")
    fh2  = _f(36, "title")
    fb   = _f(24, "body")
    fs   = _f(20, "body")
    fm   = _f(17, "mono")
    fbn  = _f(18, "title")

    # ===== HEADER =====
    _t(d, (60, 50), "More Paper Workflow Pro Skill", ft, P["accent"])
    _b(d, 780, 58, "v1.0.0-20260601", fbn, P["accent"], (255, 255, 255))
    _t(d, (60, 125), "End-to-end academic paper workflow", fb, P["grey"])
    _t(d, (60, 160), "Topic  >  Search  >  Score  >  Download  >  Library  >  Write  >  Polish",
      fs, P["dim"])

    # ===== 8-STEP FLOW (2x4 grid) =====
    steps = [
        ("Define Topic",                P["accent"]),
        ("Outline & Keywords",          P["accent"]),
        ("Search Plan",                 P["accent"]),
        ("Multi-Source Search & Score", P["accent"]),
        ("Batch Download",              P["accent2"]),
        ("Zotero Library",              P["green"]),
        ("Paper Writing",               P["green"]),
        ("Paper Polishing",             P["green"]),
    ]
    cols, cell_w, gap = 4, 320, 10
    total_w = cols * cell_w + (cols - 1) * gap
    sx0 = (W - total_w) // 2
    sy0, row_h = 215, 72

    for i, (label, color) in enumerate(steps):
        col, row = i % cols, i // cols
        sx = sx0 + col * (cell_w + gap)
        sy = sy0 + row * row_h
        cx, cy, r = sx + 14, sy + 36, 10
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        for j, line in enumerate(label.split("\n")):
            _t(d, (sx + 36, sy + 22 + j * 28), line, fb, P["grey"])

    # ===== KEY FEATURES =====
    sec1 = sy0 + 2 * row_h + 20
    _t(d, (60, sec1), "Key Features & Advantages", fh2, P["white"])
    _hl(d, sec1 + 52, P["dim"])

    features = [
        ("Anti-Anti-Scraping",
         "Real browser CDP protocol bypasses Cloudflare/Akamai. "
         "96% download success rate (185 tested, 180 downloaded)."),
        ("Cross-Platform Zero Config",
         "Auto-detects Chrome/Edge paths on macOS / Windows / Linux. "
         "Override with CHROME_PATH / EDGE_PATH env vars."),
        ("Dual-Browser Parallel Download",
         "Chrome + Edge simultaneously -- 2x speed. Auto-detects available "
         "browsers; degrades gracefully to single-browser mode."),
        ("Auto-Resume & Unattended",
         "Session expired -> kill browser -> rebuild profile -> restart -> "
         "continue. Incremental save on PII resolution means no repeated work."),
        ("Zero API Cost",
         "Semantic Scholar / Crossref / OpenAlex / Sci-Hub -- all free. "
         "No API key required for any search source."),
        ("PDF-First Writing (No RAG Hallucination)",
         "Reads full PDF text per chapter with interactive citation confirmation. "
         "Higher precision than vector-chunk RAG approaches."),
        ("4-in-1 Paper Polishing Engine",
         "AI-trace removal (29 patterns) + human-flavor injection + "
         "chapter style guide + before/after comparison table. "
         "Changes confirmed interactively, nothing applied blindly."),
        ("Modular & Layered",
         "Each step runs independently. Jump in at any stage -- "
         "already have DOIs? Start from Step 5."),
    ]

    card_max_w = W - 200
    card_gap = 6
    cy_pos = sec1 + 68

    for title, desc in features:
        desc_lines = _wrap(d, desc, fs, card_max_w)
        line_h = 28
        card_h = 20 + line_h * (1 + len(desc_lines)) + 16
        d.rounded_rectangle([60, cy_pos, W - 60, cy_pos + card_h],
                            radius=8, fill=P["card"])
        _t(d, (80, cy_pos + 14), title, fb, P["accent"])
        for j, line in enumerate(desc_lines):
            _t(d, (80, cy_pos + 44 + j * line_h), line, fs, P["grey"])
        cy_pos += card_h + card_gap

    # ===== DOWNLOAD STRATEGY =====
    sec2 = cy_pos + 30
    _t(d, (60, sec2), "PDF Download Strategy", fh2, P["white"])
    _hl(d, sec2 + 52, P["dim"])

    card_w = (W - 160) // 2
    _card(d, 60, sec2 + 68, card_w, 180,
          "Round 1 -- Sci-Hub  (no login needed)",
          ["- 13 mirrors auto-tested, uses only 9 working ones",
           "- CDP navigate > DOM extract > Fetch capture",
           "- ~6s per paper, covers pre-2021 papers"],
          fb, fs, P["card"], P["accent"], P["grey"])

    _card(d, 80 + card_w, sec2 + 68, card_w, 180,
          "Round 2 -- ScienceDirect  (institutional access)",
          ["- Mode A: IP auth -- fully automatic, zero touch",
           "- Mode B: SSO login -- first time manual, then session reuses",
           "- Auto browser restart + resume on session expiry"],
          fb, fs, P["card"], P["accent"], P["grey"])

    # ===== KEY METRICS =====
    sec3 = sec2 + 280
    _t(d, (60, sec3), "Trusted by Real Research", fh2, P["white"])
    _hl(d, sec3 + 52, P["dim"])

    metrics = [
        ("96%",    "ScienceDirect\nsuccess rate"),
        ("9 / 13", "Sci-Hub mirrors\naccessible via CDP"),
        ("3",      "Free APIs\nSemantic / Crossref\n/ OpenAlex"),
        ("2x",     "Faster with\nChrome + Edge"),
        ("3",      "Platforms\nmacOS / Win / Linux"),
    ]
    mw = (W - 120) // 5
    for i, (num, desc) in enumerate(metrics):
        mx = 60 + i * mw
        _t(d, (mx, sec3 + 70), num, _f(44, "title"), P["accent"])
        _t(d, (mx, sec3 + 125), desc, fs, P["grey"])

    # ===== FOOTER =====
    sec4 = sec3 + 200
    _hl(d, sec4, P["dim"])
    _c(d, sec4 + 45, "github.com/bingyunjiang/More-paper-workflow-pro-skill", fb, P["accent"])
    _c(d, sec4 + 90, "MIT License  -  v1.0.0-20260601", fs, P["dim"])
    new_h = sec4 + 160
    img2 = img.crop((0, 0, W, new_h))

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    name = f"poster-{palette['name'].lower().replace(' ', '-')}.png"
    path = os.path.join(OUTPUT_DIR, name)
    img2.save(path)
    print(f"  {palette['name']:18s} -> {path}  ({W}x{new_h})")


def make_poster_cn(palette):
    """Chinese-localized poster — key text in Chinese, code names kept in English."""
    P = palette
    img = Image.new("RGB", (W, H), P["bg"])
    d = ImageDraw.Draw(img)

    ft   = _f(52, "title")
    fh2  = _f(34, "cn")
    fb   = _f(22, "cn")
    fs   = _f(18, "cn")
    fm   = _f(17, "mono")
    fbn  = _f(18, "title")

    # ===== HEADER =====
    _t(d, (60, 50), "More Paper Workflow Pro Skill", ft, P["accent"])
    _b(d, 780, 58, "v1.0.0-20260601", fbn, P["accent"], (255, 255, 255))
    _t(d, (60, 125), "一站式学术文献工作流：定题 -> 检索 -> 评分 -> 下载 -> 入库 -> 写作 -> 润色", fb, P["grey"])
    _t(d, (60, 160), f"10 个 CLI 脚本 + 1 个共享模块  |  跨平台 macOS / Windows / Linux  |  Python 3.9+", fs, P["dim"])

    # ===== 8-STEP FLOW =====
    steps = [
        ("确定研究主题",       P["accent"]),
        ("生成大纲与关键词",   P["accent"]),
        ("制定检索方案",       P["accent"]),
        ("多渠道检索与评分",   P["accent"]),
        ("批量下载 PDF",       P["accent2"]),
        ("Zotero 文库管理",    P["green"]),
        ("论 文 写 作",        P["green"]),
        ("论 文 润 色",        P["green"]),
    ]
    cols, cell_w, gap = 4, 320, 10
    total_w = cols * cell_w + (cols - 1) * gap
    sx0 = (W - total_w) // 2
    sy0, row_h = 215, 72

    for i, (label, color) in enumerate(steps):
        col, row = i % cols, i // cols
        sx = sx0 + col * (cell_w + gap)
        sy = sy0 + row * row_h
        cx, cy, r = sx + 14, sy + 36, 10
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        for j, line in enumerate(label.split("\n")):
            _t(d, (sx + 36, sy + 22 + j * 28), line, fb, P["grey"])

    # ===== KEY FEATURES =====
    sec1 = sy0 + 2 * row_h + 20
    _t(d, (60, sec1), "核心功能与优势", fh2, P["white"])
    _hl(d, sec1 + 52, P["dim"])

    features = [
        ("反反爬 — CDP 真实浏览器绕过 Cloudflare/Akamai",
         "通过 Chrome DevTools Protocol 操控真实浏览器，绕过出版商反爬系统。"
         "实测 185 篇 ScienceDirect 论文，成功下载 180 篇（96% 成功率）。"),
        ("全平台零配置",
         "自动检测 Chrome / Edge 浏览器路径，macOS / Windows / Linux 即装即用。"
         "也支持 CHROME_PATH / EDGE_PATH 环境变量手动指定。"),
        ("双浏览器并行下载（Chrome + Edge）",
         "同时使用 Chrome 和 Edge 两个浏览器，下载速度翻倍。"
         "自动检测可用浏览器，只有一个浏览器也能正常运行。"),
        ("全自动断点续跑，无需值守",
         "会话过期 -> 自动杀进程 -> 重建 profile -> 重启浏览器 -> 继续下载。"
         "PII 解析每 5 条增量保存，中断恢复不重复工作。"),
        ("零 API 费用",
         "Semantic Scholar / Crossref / OpenAlex / Sci-Hub 全部免费，"
         "无需注册任何 API Key。"),
        ("直接读 PDF 原文，抑制大模型幻觉",
         "逐章读取 PDF 全文，交互确认每处引用。"
         "引用精确性远高于 RAG 向量分块方案。"),
        ("四合一论文润色引擎",
         "去 AI 痕迹（29 种模式替换）+ 注入人味 + 章节风格指南 + before/after 对照表。"
         "逐段交互确认，不盲目替换。"),
        ("模块化分层设计",
         "每个 Step 独立运行，按需组合。"
         "已有 DOI？直接从 Step 5 下载开始。已有 PDF？直接从 Step 6 入库开始。"),
    ]

    card_max_w = W - 200
    card_gap = 6
    cy_pos = sec1 + 68

    for title, desc in features:
        desc_lines = _wrap(d, desc, fs, card_max_w)
        line_h = 28
        card_h = 20 + line_h * (1 + len(desc_lines)) + 16
        d.rounded_rectangle([60, cy_pos, W - 60, cy_pos + card_h],
                            radius=8, fill=P["card"])
        _t(d, (80, cy_pos + 14), title, fb, P["accent"])
        for j, line in enumerate(desc_lines):
            _t(d, (80, cy_pos + 44 + j * line_h), line, fs, P["grey"])
        cy_pos += card_h + card_gap

    # ===== DOWNLOAD STRATEGY =====
    sec2 = cy_pos + 30
    _t(d, (60, sec2), "PDF 下载策略", fh2, P["white"])
    _hl(d, sec2 + 52, P["dim"])

    card_w = (W - 160) // 2
    _card(d, 60, sec2 + 68, card_w, 180,
          "第一轮 — Sci-Hub（免登录）",
          ["- 自动测试 13 个镜像站，仅用 9 个可用站",
           "- CDP 导航 -> DOM 提取 PDF 链接 -> Fetch 拦截捕获",
           "- 约 6 秒/篇，覆盖 2021 年前老论文"],
          fb, fs, P["card"], P["accent"], P["grey"])

    _card(d, 80 + card_w, sec2 + 68, card_w, 180,
          "第二轮 — ScienceDirect（需机构认证）",
          ["- 方式 A：IP 认证全自动，零干预",
           "- 方式 B：SSO 机构登录，首次手动，之后 session 复用",
           "- 会话过期自动重启浏览器 + 断点续跑"],
          fb, fs, P["card"], P["accent"], P["grey"])

    # ===== KEY METRICS =====
    sec3 = sec2 + 280
    _t(d, (60, sec3), "实测数据", fh2, P["white"])
    _hl(d, sec3 + 52, P["dim"])

    metrics = [
        ("96%",    "ScienceDirect\n下载成功率"),
        ("9 / 13", "Sci-Hub 镜像站\nCDP 可用"),
        ("3 源",   "免费检索 API\nSemantic / Crossref\n/ OpenAlex"),
        ("2x",     "双浏览器并行\n速度翻倍"),
        ("3 平台",  "macOS\nWindows / Linux"),
    ]
    mw = (W - 120) // 5
    for i, (num, desc) in enumerate(metrics):
        mx = 60 + i * mw
        _t(d, (mx, sec3 + 70), num, _f(40, "cn"), P["accent"])
        _t(d, (mx, sec3 + 120), desc, fs, P["grey"])

    # ===== FOOTER =====
    sec4 = sec3 + 200
    _hl(d, sec4, P["dim"])
    _c(d, sec4 + 45, "github.com/bingyunjiang/More-paper-workflow-pro-skill", fb, P["accent"])
    _c(d, sec4 + 90, "MIT License  -  v1.0.0-20260601", fs, P["dim"])
    new_h = sec4 + 160
    img2 = img.crop((0, 0, W, new_h))

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, "poster-cn-light.png")
    img2.save(path)
    print(f"  Chinese (Clean Light) -> {path}  ({W}x{new_h})")


def make_social_preview(palette):
    """1280x640 social preview card — compact, readable at small sizes."""
    P = palette
    PW, PH = 1280, 640
    img = Image.new("RGB", (PW, PH), P["bg"])
    d = ImageDraw.Draw(img)

    ft  = _f(46, "title")
    fh2 = _f(28, "title")
    fb  = _f(22, "body")
    fs  = _f(17, "body")
    fm  = _f(15, "mono")

    # ---- left content area ----
    _t(d, (60, 55), "More Paper Workflow Pro Skill", ft, P["accent"])
    _b(d, 630, 62, "v1.0.0-20260601", _f(14, "title"), P["accent"], (255, 255, 255))

    _t(d, (60, 120), "End-to-end academic paper workflow", fh2, P["white"])
    _t(d, (60, 162), "Topic -> Search -> Score -> Download -> Library -> Write -> Polish",
      fs, P["dim"])

    # ---- feature bullets (left side) ----
    bullets = [
        ("CDP",    "Bypasses Cloudflare/Akamai -- 96% download success"),
        ("Dual",   "Chrome + Edge parallel -- 2x speed, auto-detection"),
        ("Free",   "Semantic Scholar / Crossref / OpenAlex / Sci-Hub"),
        ("PDF",    "Direct full-text reading -- no RAG hallucination"),
        ("4-in-1", "AI-trace removal + human flavor + style guide"),
        ("3 OS",   "macOS / Windows / Linux -- zero config"),
    ]
    by = 210
    for label, desc in bullets:
        _b(d, 60, by, label, _f(12, "title"), P["accent"], (255, 255, 255))
        _t(d, (125, by + 1), desc, fs, P["grey"])
        by += 38

    # ---- right side: metrics + download strat ----
    # Metrics block
    rx = 680
    _t(d, (rx, 210), "Key Metrics", fh2, P["white"])

    metrics = [
        ("96%",   "SD success"),
        ("9/13",  "Sci-Hub CDP"),
        ("2x",    "Dual browser"),
        ("3 OS",  "Cross-platform"),
    ]
    mx = rx
    my = 260
    for num, desc in metrics:
        _t(d, (mx, my), num, _f(28, "title"), P["accent"])
        _t(d, (mx + 70, my + 6), desc, fs, P["grey"])
        my += 42

    # Download strategy
    _t(d, (rx, my + 20), "Download Strategy", fh2, P["white"])
    _t(d, (rx, my + 58), "Round 1 -- Sci-Hub: 13 mirrors auto-tested, ~6s/paper", fs, P["grey"])
    _t(d, (rx, my + 82), "Round 2 -- SD: IP auto / SSO manual -- auto resume", fs, P["grey"])

    # ---- footer ----
    _hl(d, PH - 60, P["dim"])
    _t(d, (60, PH - 42), "github.com/bingyunjiang/More-paper-workflow-pro-skill", fs, P["accent"])
    _t(d, (PW - 260, PH - 42), "MIT License  -  v1.0.0-20260601", fs, P["dim"])

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, "social-preview.png")
    img.save(path)
    print(f"  Social Preview       -> {path}  ({PW}x{PH})")


if __name__ == "__main__":
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Please install Pillow: pip install Pillow")
        exit(1)

    print("Generating posters...\n")
    for key, pal in PALETTES.items():
        make_poster(pal)
    # Chinese version based on light theme
    make_poster_cn(PALETTES["light"])
    # Social preview card
    make_social_preview(PALETTES["dark"])
    print(f"\nDone! {len(PALETTES) + 2} images saved to {OUTPUT_DIR}/")
