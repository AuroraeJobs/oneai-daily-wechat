# Daily briefing card visual guidelines

For OneAI Daily briefing SVG cards, use a no-icon layout. The main headline should span horizontally across the card so the right side does not look empty.

## Fixed layout rules

- Do not use right-side icons or icon slots.
- Keep the card size at `1200 x 675`.
- Keep the outer border at `x=54 y=50 width=1092 height=575 rx=34`.
- Keep the brand line at `x=86 y=126`, `font-size=36`.
- Keep the category line at `x=86 y=177`, `font-size=30`.
- Use a single-line headline at approximately `x=86 y=348`.
- Adjust headline font size per length, usually between `52` and `64`, so the title stays on one line.
- Use the subtitle at approximately `x=88 y=426`, `font-size=34`.
- Keep the footer at `x=86 y=582`, `font-size=28`.

## Right-side balance

To avoid an empty right side without adding icons, use subtle abstract background shapes only:

```svg
<circle cx="970" cy="330" r="260" fill="#ffffff" opacity="0.045"/>
<circle cx="1060" cy="250" r="150" fill="#ffffff" opacity="0.035"/>
<path d="M86 478 H1068" stroke="#ffffff" stroke-width="3" opacity="0.22"/>
```

These shapes are decorative background accents, not icons. Keep them behind text and below the main background rectangle.

## Example headline block

```svg
<text x="86" y="348" font-family="Arial, 'Noto Sans CJK SC', sans-serif" font-size="60" font-weight="800" fill="#ffffff">Kling raises $2.8B for AI video</text>
<text x="88" y="426" font-family="Arial, 'Noto Sans CJK SC', sans-serif" font-size="34" fill="#eee4ff">China’s generative-video race accelerates</text>
```

## Font sizing guide

- Short headline, 20–28 characters: `64`
- Medium headline, 29–35 characters: `58–60`
- Long headline, 36–42 characters: `52–56`
- If a headline still does not fit at `52`, shorten the headline rather than wrapping to two lines.
