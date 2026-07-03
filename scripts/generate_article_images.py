#!/usr/bin/env python3
"""Generate PNG news cards for markdown images that are referenced by an article.

Usage:
  python scripts/generate_article_images.py content/daily/2026-07-03-daily-briefing.md

Environment:
  FORCE_REGENERATE_IMAGES=1   regenerate images even if they already exist
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

WIDTH = 1200
HEIGHT = 675

PALETTES = [
    ((10, 36, 93), (34, 132, 235)),
    ((7, 77, 54), (32, 172, 109)),
    ((73, 42, 14), (238, 157, 42)),
    ((37, 28, 92), (110, 90, 230)),
    ((6, 86, 64), (120, 190, 42)),
]


def env_truthy(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "y", "on"}


def safe_rel(path: Path, base: Path = ROOT) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def load_font(size: int, bold: bool = False):
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def text_width(text: str, font) -> int:
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]


def wrap_text(text: str, font, max_width: int, max_lines: int = 3):
    text = text.strip()
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if text_width(candidate, font) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = char
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)

    if len(lines) == max_lines and len("".join(lines)) < len(text):
        last = lines[-1]
        while last and text_width(last + "…", font) > max_width:
            last = last[:-1]
        lines[-1] = last + "…"
    return lines


def clean_title(title: str, idx: int) -> str:
    title = re.sub(r"^\s*\d+[\.、]\s*", "", title.strip())
    # Keep the topic prefix, but remove excessive spaces around separators.
    title = title.replace(" | ", "｜").replace("｜", "｜")
    return title


def resolve(article: Path, ref: str) -> Path:
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

    fallback = ROOT / "assets" / "images" / article.stem.replace("-daily-briefing", "") / Path(raw).name
    return fallback.resolve()


def draw_gradient(draw_img: Image.Image, c1: tuple[int, int, int], c2: tuple[int, int, int]) -> None:
    px = draw_img.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            t = (x / WIDTH * 0.72) + (y / HEIGHT * 0.28)
            px[x, y] = tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))


def make_card(path: Path, title: str, idx: int):
    path.parent.mkdir(parents=True, exist_ok=True)
    c1, c2 = PALETTES[(idx - 1) % len(PALETTES)]
    img = Image.new("RGB", (WIDTH, HEIGHT), c1)
    draw_gradient(img, c1, c2)
    draw = ImageDraw.Draw(img)

    title = clean_title(title, idx)
    font_kicker = load_font(34, bold=True)
    font_story = load_font(28, bold=True)
    font_brand = load_font(28, bold=True)

    # Choose a title font that fits a 3-line left text block.
    for size in (56, 52, 48, 44):
        font_title = load_font(size, bold=True)
        title_lines = wrap_text(title, font_title, max_width=700, max_lines=3)
        if len(title_lines) <= 3:
            break

    # Main border and subtle panels.
    draw.rounded_rectangle((54, 50, 1146, 625), radius=34, outline=(255, 255, 255), width=3)
    draw.rounded_rectangle((780, 130, 1105, 545), radius=36, fill=(255, 255, 255), outline=None)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle((780, 130, 1105, 545), radius=36, fill=(255, 255, 255, 32))
    od.ellipse((850, 210, 1065, 425), outline=(255, 255, 255, 220), width=7)
    od.ellipse((920, 280, 995, 355), fill=(255, 255, 255, 30))
    img.alpha_composite(overlay) if img.mode == "RGBA" else None

    # Re-create draw after possible alpha operation.
    draw = ImageDraw.Draw(img)
    draw.text((86, 92), "ONEAI DAILY", font=font_kicker, fill=(220, 238, 255))
    draw.text((86, 145), f"TOP STORY {idx}", font=font_story, fill=(220, 238, 255))

    # Title block: constrained to the left so it never overlaps the AI badge.
    y = 252
    for line in title_lines:
        draw.text((86, y), line, font=font_title, fill=(255, 255, 255))
        y += int(font_title.size * 1.25)

    # Right visual badge.
    badge_font = load_font(86, bold=True)
    draw.ellipse((860, 220, 1060, 420), outline=(255, 255, 255), width=7)
    draw.text((910, 278), "AI", font=badge_font, fill=(255, 255, 255))

    # Footer.
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
    force = env_truthy("FORCE_REGENERATE_IMAGES", "0")

    for idx, (_alt, ref) in enumerate(matches, start=1):
        out = resolve(article, ref)
        if out.exists() and not force:
            print(f"exists: {safe_rel(out)}")
            continue
        title = headings[idx - 1] if idx - 1 < len(headings) else _alt
        make_card(out, title, idx)


if __name__ == "__main__":
    main()
