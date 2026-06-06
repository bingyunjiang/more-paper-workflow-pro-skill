#!/usr/bin/env python3
"""Generate a version update poster for WeChat朋友圈.

Usage:
    python3 posters/generate_update_poster.py

Customize the UPDATE_DATA dict below for each new version.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1400, 2400

# ---- color palette ----
PALETTE = {
    "bg":      (240, 242, 246),
    "card":    (255, 255, 255),
    "accent":  (99, 107, 255),   # indigo
    "accent2": (245, 158, 11),   # amber
    "accent3": (16, 185, 129),   # emerald
    "white":   (17, 24, 39),
    "grey":    (107, 114, 128),
    "dim":     (209, 213, 219),
}

# ---- fonts ----
FONT_BASE = "/System/Library/Fonts"
FT = FB = FC = None
for key, paths in [
    ("FT", [f"{FONT_BASE}/Helvetica.ttc", f"{FONT_BASE}/Supplemental/Arial Bold.ttf"]),
    ("FB", [f"{FONT_BASE}/Helvetica.ttc", f"{FONT_BASE}/Supplemental/Arial.ttf"]),
    ("FC", [f"{FONT_BASE}/STHeiti Medium.ttc", f"{FONT_BASE}/Songti.ttc",
            f"{FONT_BASE}/PingFang.ttc"]),
]:
    for p in paths:
        if os.path.exists(p):
            if key == "FT": FT = p
            elif key == "FB": FB = p
            elif key == "FC": FC = p
            break
if not FT:
    FT = FB = FC = ImageFont.load_default()

def _f(size, w="body"):
    path = FT if w == "title" else FC if w == "cn" else FB
    try: return ImageFont.truetype(path, size)
    except: return ImageFont.load_default()

def _t(draw, xy, text, font, fill):
    draw.text(xy, text, font=font, fill=fill)

def _c(draw, y, text, font, fill):
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text(((W - (bb[2]-bb[0]))//2, y), text, font=font, fill=fill)

def _rbox(draw, x, y, w, h, r=10, fill=None, outline=None, width=1):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill, outline=outline, width=width)

def _tag(draw, x, y, text, font, bg, fg, r=4):
    bb = draw.textbbox((0, 0), text, font=font)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]
    px, py = 8, 4
    _rbox(draw, x, y, tw+px*2, th+py*2, r=r, fill=bg)
    _t(draw, (x+px, y+py), text, font, fg)


def generate_poster(data):
    """Render a poster from structured data.

    `data` dict keys:
        - version (str): e.g. "v1.0.5-20260605"
        - title (str): main title, e.g. "More Paper Workflow Pro"
        - subtitle (str): below title, e.g. "8 步学术文献工作流 · 一站式从定题到润色"
        - slogan (str): highlighted band text, e.g. "搜的更全  ·  下得更快"
        - output (str): output filename, e.g. "v105-update-poster.png"
        - sections (list of dict): each has:
            - num (str): ① ② ③ ④ ...
            - color_key (str): key into PALETTE ("accent", "accent2", "accent3")
            - title (str): section title
            - subtitle (str): section subtitle tag
            - items (list of str): bullet items
    """
    P = PALETTE
    img = Image.new("RGB", (W, H), P["bg"])
    d = ImageDraw.Draw(img)

    ft     = _f(48, "title")
    fh2    = _f(32, "cn")
    fh3    = _f(24, "cn")
    fb     = _f(20, "cn")
    fs     = _f(18, "cn")
    fstitle = _f(24, "cn")
    fsub   = _f(36, "cn")

    y = 0

    # ===== HEADER =====
    y += 50
    _t(d, (60, y), data["title"], ft, P["accent"])
    _t(d, (W - 400, y + 12), data["version"], fh2, P["accent"])
    _t(d, (W - 280, y + 64), "#更新简报", fh3, P["accent"])
    _t(d, (60, y + 85), data["subtitle"], fsub, P["white"])
    y += 170

    # ===== SLOGAN =====
    slogan_h = 52
    _rbox(d, 60, y, W - 120, slogan_h, r=8, fill=P["accent"])
    _c(d, y + 10, data["slogan"], fh2, (255, 255, 255))
    y += slogan_h + 30

    # divider
    d.line([(60, y), (W-60, y)], fill=P["dim"], width=1)
    y += 36

    # ===== SECTIONS (2x2 GRID) =====
    secs = data["sections"]
    gap_x, gap_y = 20, 30
    card_w = (W - 120 - gap_x) // 2
    item_h = 42

    for row_idx in range(2):
        left = secs[row_idx * 2]
        right = secs[row_idx * 2 + 1]
        row_secs = [left, right]

        card_heights = []
        for s in row_secs:
            card_heights.append(170 + len(s["items"]) * item_h + 20)
        row_h = max(card_heights)

        for col_idx, s in enumerate(row_secs):
            x = 60 + col_idx * (card_w + gap_x)
            ch = card_heights[col_idx]
            color = P[s["color_key"]]

            _rbox(d, x, y, card_w, ch, r=12, fill=P["card"])

            # Number circle
            cx, cy, r = x + 30, y + 34, 20
            d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=color)
            _t(d, (cx-9, cy-11), s["num"] + " ", _f(24, "title"), (255, 255, 255))

            # Title
            _t(d, (x + 60, y + 20), s["title"], fh2, color)

            # Subtitle tag
            light_bg = tuple(min(c+130, 255) for c in color)
            _tag(d, x + 60, y + 77, s["subtitle"], fstitle, light_bg, P["white"])

            # Items
            yy = y + 165
            for item in s["items"]:
                d.ellipse([(x + 16, yy + 8), (x + 22, yy + 14)], fill=P["grey"])
                _t(d, (x + 32, yy + 1), item, fb, P["grey"])
                yy += item_h

        y += row_h + gap_y

    # ===== FOOTER =====
    y += 30
    d.line([(60, y), (W-60, y)], fill=P["dim"], width=1)
    y += 36
    _c(d, y, "github.com/bingyunjiang/More-paper-workflow-pro-skill", _f(40, "title"), P["accent"])
    y += 50
    _c(d, y, "MIT License  ·  " + data["version"], fs, P["grey"])

    new_h = y + 50
    img2 = img.crop((0, 0, W, new_h))

    os.makedirs("posters", exist_ok=True)
    path = os.path.join("posters", data["output"])
    img2.save(path)
    print(f"  Poster -> {path}  ({W}x{new_h})")


# =====================================================================
# Customize this data dict for each version update
# =====================================================================
UPDATE_DATA = {
    "version":  "v1.0.5-20260605",
    "title":    "More Paper Workflow Pro",
    "subtitle": "8 步学术文献工作流 · 一站式从定题到润色",
    "slogan":   "搜的更全  ·  下得更快",

    "sections": [
        {
            "num": "①", "color_key": "accent",
            "title": "检索能力大升级",
            "subtitle": "搜得更全 · 筛得更准",
            "items": [
                "Step 3/4 重构为 4a→4h 八道工序",
                "T1→T2→T3 三级回退路由，T1 不足 30 条自动降级",
                "新增引文验证、DOI 去重、饱和度分析",
                "6 领域路由规则：医学/工程/CS/综述/中文",
                "search_by_topic.py v3.0：布尔查询 + Pre-flight + 多格式导出",
            ]
        },
        {
            "num": "②", "color_key": "accent2",
            "title": "统一下载路由",
            "subtitle": "一个入口 · 覆盖 23 家出版社",
            "items": [
                "unified_download_router.py 全自动路由",
                "三轮顺序执行：Sci-Hub → SD CDP → Generic CDP",
                "Generic CDP 引擎：直连 PDF → 文章页 CSS 选择器回退",
                "15 个反检测 Chrome flag + warmup_profile 预热",
                "9 篇实测全过，MDPI (Akamai) 暂无解",
            ]
        },
        {
            "num": "③", "color_key": "accent3",
            "title": "综述矩阵 + 综述写作",
            "subtitle": "结构化证据 · 专属写作模式",
            "items": [
                "Step 6e 新增 13 列文献综述矩阵",
                "证据优先级：笔记 → 标注 → 元数据 → 全文",
                "Step 7 新增 review 写作模式（8 节骨架 + 7 条纪律）",
                "GB/T 7714-2015 完整规范补全",
                "新增期刊风格学习、科研图表生成、引用审计",
            ]
        },
        {
            "num": "④", "color_key": "accent",
            "title": "SKILL.md 模块化拆分",
            "subtitle": "3284 行 → 9 个独立 Agent",
            "items": [
                "SKILL.md 从 3284 行精简为 377 行",
                "agents/ 目录 9 个独立 Agent（每 Step 一个）",
                "新增 error_log / decision_log / term_aliases",
                "术语别名表贯穿 Step 2→3→7→8",
                "触发词 164 → 184 条",
            ]
        },
    ],

    "output": "v105-update-poster.png",
}

if __name__ == "__main__":
    generate_poster(UPDATE_DATA)
