#!/usr/bin/env python3
"""Generate simple PNG cards for markdown images that are referenced but missing.

Usage:
  python scripts/generate_article_images.py content/daily/2026-07-03-daily-briefing.md
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+\.png)\)")
H2_RE = re.compile(r"^##\s+(.+)$", re.M)

PALETTES = [
    ((12, 36, 97), (33, 150, 243)),
    ((9, 61, 44), (34, 197, 94)),
    ((72, 36, 10), (249, 168, 37)),
    ((42, 22, 91), (139, 92, 246)),
    ((6, 78, 59), (132, 204, 22)),
]


def safe_rel(path: Path, base: Path = ROOT) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def load_font(size: int, bold: bool = False):
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def wrap_text(text: str, font, max_width: int):
    lines = []
    current = ""
    for char in text:
        test = current + char
        if font.getbbox(test)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines


def resolve(article: Path, ref: str) -> Path:
    """Resolve a markdown image path.

    The image path may point to a file that does not exist yet. In that case we
    still must keep it under the repository instead of falling back to an outside
    path such as ../../assets from ROOT.
    """
    raw = ref.strip()
    if raw.startswith(("http://", "https://")):
        raise ValueError(f"Remote image URL is not supported: {raw}")

    article_candidate = (article.parent / raw).resolve()
    try:
        article_candidate.relative_to(ROOT.resolve())
        return article_candidate
    except ValueError:
        pass

    root_candidate = (ROOT / raw).resolve()
    try:
        root_candidate.relative_to(ROOT.resolve())
        return root_candidate
    except ValueError:
        pass

    # If a bad path tries to escape the repo, put it back under assets/images
    # using only the basename. This avoids accidentally writing outside ROOT.
    fallback = ROOT / "assets" / "images" / article.stem.replace("-daily-briefing", "") / Path(raw).name
    return fallback.resolve()


def make_card(path: Path, title: str, idx: int):
    path.parent.mkdir(parents=True, exist_ok=True)
    w, h = 1200, 675
    c1, c2 = PALETTES[(idx - 1) % len(PALETTES)]
    img = Image.new("RGB", (w, h), c1)
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = (x / w + y / h) / 2
            px[x, y] = tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))

    draw = ImageDraw.Draw(img)
    font_kicker = load_font(36, bold=True)
    font_title = load_font(68, bold=True)
    font_brand = load_font(30, bold=True)

    draw.rounded_rectangle((54, 50, 1146, 625), radius=34, outline=(255, 255, 255), width=3)
    draw.text((86, 92), "ONEAI DAILY", font=font_kicker, fill=(220, 238, 255))
    draw.text((86, 150), f"TOP STORY {idx}", font=font_brand, fill=(220, 238, 255))

    lines = wrap_text(title, font_title, 820)[:3]
    y = 255
    for line in lines:
        draw.text((86, y), line, font=font_title, fill=(255, 255, 255))
        y += 82

    draw.ellipse((875, 195, 1085, 405), outline=(255, 255, 255), width=8)
    draw.text((925, 260), "AI", font=load_font(82, bold=True), fill=(255, 255, 255))
    draw.text((86, 555), "Understand AI. Understand the World.", font=font_brand, fill=(220, 238, 255))
    img.save(path, "PNG", optimize=True)
    print(f"generated: {safe_rel(path)}")


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/generate_article_images.py <article.md>")
    article = Path(sys.argv[1])
    if not article.is_absolute():
        article = ROOT / article
    article = article.resolve()
    text = article.read_text(encoding="utf-8")
    headings = H2_RE.findall(text)
    matches = IMG_RE.findall(text)
    for idx, (_alt, ref) in enumerate(matches, start=1):
        out = resolve(article, ref)
        if out.exists():
            print(f"exists: {safe_rel(out)}")
            continue
        title = headings[idx - 1] if idx - 1 < len(headings) else _alt
        make_card(out, title, idx)


if __name__ == "__main__":
    main()
