#!/usr/bin/env python3
"""Generate PNG cover and news cards for a daily briefing Markdown article.

Usage:
  python scripts/generate_article_images.py content/daily/2026-07-04-daily-briefing.md

Environment:
  FORCE_REGENERATE_IMAGES=1   regenerate images even if they already exist
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(?P<meta>.*?)\n---\s*\n(?P<body>.*)\Z", re.S)
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
COVER_PALETTE = ((8, 24, 72), (28, 110, 215))


def env_truthy(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "y", "on"}


def safe_rel(path: Path, base: Path = ROOT) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def parse_article(text: str) -> tuple[dict, str]:
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text
    return yaml.safe_load(match.group("meta")) or {}, match.group("body")


def load_font(size: int, bold: bool = False):
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if path and Path(path).exists():
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


def clean_title(title: str, idx: int | None = None) -> str:
    title = re.sub(r"^\s*\d+[\.、]\s*", "", title.strip())
    return title.replace(" | ", "｜")


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


def draw_background_accents(draw: ImageDraw.ImageDraw) -> None:
    draw.ellipse((760, 110, 1240, 590), fill=(255, 255, 255, 10))
    draw.ellipse((940, 20, 1240, 320), fill=(255, 255, 255, 8))
    draw.line((86, 500, 1080, 500), fill=(255, 255, 255, 55), width=3)


def make_cover(path: Path, title: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    c1, c2 = COVER_PALETTE
    img = Image.new("RGB", (WIDTH, HEIGHT), c1)
    draw_gradient(img, c1, c2)
    draw = ImageDraw.Draw(img)
    draw_background_accents(draw)
    draw.rounded_rectangle((54, 50, 1146, 625), radius=34, outline=(255, 255, 255), width=3)

    font_brand = load_font(34, bold=True)
    draw.text((86, 106), "ONEAI DAILY", font=font_brand, fill=(220, 238, 255))

    title = clean_title(title)
    for size in (82, 76, 70, 64, 58):
        font_title = load_font(size, bold=True)
        title_lines = wrap_text(title, font_title, max_width=930, max_lines=2)
        if len(title_lines) <= 2:
            break

    total_h = len(title_lines) * int(font_title.size * 1.22)
    y = 338 - total_h // 2
    for line in title_lines:
        draw.text((86, y), line, font=font_title, fill=(255, 255, 255))
        y += int(font_title.size * 1.22)

    img.save(path, "PNG", optimize=True)
    print(f"generated cover: {safe_rel(path)}")


def make_card(path: Path, title: str, idx: int):
    path.parent.mkdir(parents=True, exist_ok=True)
    c1, c2 = PALETTES[(idx - 1) % len(PALETTES)]
    img = Image.new("RGB", (WIDTH, HEIGHT), c1)
    draw_gradient(img, c1, c2)
    draw = ImageDraw.Draw(img)
    draw_background_accents(draw)

    title = clean_title(title, idx)
    font_kicker = load_font(34, bold=True)
    font_story = load_font(28, bold=True)
    font_brand = load_font(28, bold=True)

    for size in (60, 56, 52, 48):
        font_title = load_font(size, bold=True)
        title_lines = wrap_text(title, font_title, max_width=950, max_lines=2)
        if len(title_lines) <= 2:
            break

    draw.rounded_rectangle((54, 50, 1146, 625), radius=34, outline=(255, 255, 255), width=3)

    draw.text((86, 92), "ONEAI DAILY", font=font_kicker, fill=(220, 238, 255))
    draw.text((86, 145), f"TOP STORY {idx}", font=font_story, fill=(220, 238, 255))

    y = 286
    for line in title_lines:
        draw.text((86, y), line, font=font_title, fill=(255, 255, 255))
        y += int(font_title.size * 1.25)

    draw.text((86, 555), "Understand AI. Understand the World.", font=font_brand, fill=(220, 238, 255))
    img.save(path, "PNG", optimize=True)
    print(f"generated: {safe_rel(path)}")


def maybe_generate_cover(article: Path, metadata: dict, force: bool) -> None:
    cover_ref = str(metadata.get("cover") or "").strip()
    if not cover_ref:
        print("no article cover configured")
        return
    cover_path = resolve(article, cover_ref)
    if cover_path.exists() and not force:
        print(f"exists cover: {safe_rel(cover_path)}")
        return
    title = str(metadata.get("wechat_title") or metadata.get("title") or "OneAI Daily")
    make_cover(cover_path, title)


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/generate_article_images.py <article.md>")
    article = Path(sys.argv[1])
    if not article.is_absolute():
        article = ROOT / article
    article = article.resolve()
    text = article.read_text(encoding="utf-8")
    metadata, body = parse_article(text)
    headings = H2_RE.findall(body)
    matches = IMG_RE.findall(body)
    force = env_truthy("FORCE_REGENERATE_IMAGES", "0")

    maybe_generate_cover(article, metadata, force)

    for idx, (_alt, ref) in enumerate(matches, start=1):
        out = resolve(article, ref)
        if out.exists() and not force:
            print(f"exists: {safe_rel(out)}")
            continue
        title = headings[idx - 1] if idx - 1 < len(headings) else _alt
        make_card(out, title, idx)


if __name__ == "__main__":
    main()
