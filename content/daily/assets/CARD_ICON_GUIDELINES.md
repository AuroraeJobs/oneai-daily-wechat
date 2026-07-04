# Daily briefing card icon guidelines

For OneAI Daily briefing SVG cards, keep the right-side icon slot fixed across all cards to avoid layout drift.

## Fixed icon slot

Use this container for every card:

```svg
<g transform="translate(860 178)" opacity="0.92">
  <rect x="0" y="0" width="220" height="220" rx="28" fill="#ffffff" opacity="0.14"/>
  <!-- fixed icon body goes here -->
</g>
```

Rules:

- Do not move the container. Keep `translate(860 178)`.
- Do not resize the backing plate. Keep `220 x 220`, `rx=28`.
- Use only white strokes/fills inside the icon slot.
- Keep icon geometry inside the `220 x 220` plate.
- Reuse one of the five fixed icon bodies below.

## Fixed icon types

### 1. AI policy

```svg
<rect x="42" y="58" width="110" height="124" rx="14" fill="none" stroke="#ffffff" stroke-width="8"/>
<path d="M62 92h70M62 122h70M62 152h48" stroke="#ffffff" stroke-width="8" stroke-linecap="round"/>
<circle cx="162" cy="74" r="34" fill="none" stroke="#ffffff" stroke-width="8"/>
<text x="142" y="84" font-family="Arial, sans-serif" font-size="30" font-weight="800" fill="#ffffff">AI</text>
```

### 2. Market / funding flow

```svg
<path d="M46 160 L88 126 L126 138 L162 96 L190 70" fill="none" stroke="#ffffff" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M168 70h22v22" fill="none" stroke="#ffffff" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="88" cy="126" r="8" fill="#ffffff"/>
<circle cx="126" cy="138" r="8" fill="#ffffff"/>
<circle cx="162" cy="96" r="8" fill="#ffffff"/>
```

### 3. Startup / AI video

```svg
<rect x="42" y="56" width="136" height="92" rx="14" fill="none" stroke="#ffffff" stroke-width="8"/>
<path d="M92 78 L92 126 L132 102 Z" fill="#ffffff"/>
<path d="M54 176h112" stroke="#ffffff" stroke-width="8" stroke-linecap="round"/>
<path d="M52 44v120M72 44v120M148 44v120M168 44v120" stroke="#ffffff" stroke-width="5" opacity="0.55"/>
```

### 4. Engineering / drones

```svg
<path d="M52 110h116M110 52v116" stroke="#ffffff" stroke-width="10" stroke-linecap="round"/>
<circle cx="52" cy="110" r="28" fill="none" stroke="#ffffff" stroke-width="8"/>
<circle cx="168" cy="110" r="28" fill="none" stroke="#ffffff" stroke-width="8"/>
<circle cx="110" cy="52" r="24" fill="none" stroke="#ffffff" stroke-width="8"/>
<circle cx="110" cy="168" r="24" fill="none" stroke="#ffffff" stroke-width="8"/>
<circle cx="110" cy="110" r="16" fill="#ffffff"/>
```

### 5. AI infrastructure / chip

```svg
<rect x="58" y="58" width="104" height="104" rx="14" fill="none" stroke="#ffffff" stroke-width="8"/>
<path d="M78 88h64M78 112h64M78 136h44" stroke="#ffffff" stroke-width="7" stroke-linecap="round"/>
<path d="M40 88H20M40 112H20M40 136H20M180 88h20M180 112h20M180 136h20" stroke="#ffffff" stroke-width="7" stroke-linecap="round" opacity="0.82"/>
<path d="M82 40V20M110 40V20M138 40V20M82 180v20M110 180v20M138 180v20" stroke="#ffffff" stroke-width="7" stroke-linecap="round" opacity="0.82"/>
```
