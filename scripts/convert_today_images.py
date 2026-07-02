#!/usr/bin/env python3
from pathlib import Path
import cairosvg

ROOT = Path(__file__).resolve().parents[1]
DAY = ROOT / "assets" / "images" / "2026-07-02"
NAMES = [
    "01-ai-governance",
    "02-together-ai-funding",
    "03-semiconductor-rally",
    "04-claude-science",
    "05-wimbledon",
]

for name in NAMES:
    svg = DAY / f"{name}.svg"
    png = DAY / f"{name}.png"
    if not svg.exists():
        print(f"missing: {svg}")
        continue
    cairosvg.svg2png(url=str(svg), write_to=str(png), output_width=1200, output_height=675)
    print(f"converted: {png}")

article = ROOT / "content" / "daily" / "2026-07-02-daily-briefing.md"
text = article.read_text(encoding="utf-8")
text = text.replace(".svg)", ".png)")
article.write_text(text, encoding="utf-8")
print(f"updated: {article}")
