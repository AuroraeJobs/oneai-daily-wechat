# OneAI Daily WeChat Project Context

This file is the first place future assistants should read before generating or publishing OneAI Daily content.

## Repository

- GitHub repo: `AuroraeJobs/oneai-daily-wechat`
- Main content directory: `content/daily/`
- Per-issue asset directory pattern: `content/daily/assets/YYYY-MM-DD/`
- Primary local publish command:

```bash
git pull
FORCE_REGENERATE_IMAGES=1 python scripts/generate_article_images.py content/daily/YYYY-MM-DD-daily-briefing.md
./scripts/local_publish.sh content/daily/YYYY-MM-DD-daily-briefing.md
```

`local_publish.sh` also runs image generation, commits generated image changes, pushes them, uploads WeChat materials, and creates a draft.

## Content goals

OneAI Daily is a concise Chinese daily briefing focused on:

- AI & technology
- Business & markets
- Science
- Politics & policy
- Startups
- World news
- Engineering

Prioritize: breaking developments, deep analysis, industry trends, product launches, research papers, and investment or market moves.

Each daily issue should contain 5 concise stories from the past 24 hours. For each story include:

- A short section title
- One concise summary paragraph
- `为什么重要：` explaining why the story matters
- `来源：` with source name, article title, date, and URL
- One image immediately after the section heading

## Markdown frontmatter standard

Every daily issue should include this frontmatter shape:

```yaml
---
title: "OneAI Daily｜今日AI要闻"
wechat_title: "每期总结式公众号标题"
cover: "assets/YYYY-MM-DD/cover.png"
date: "YYYY-MM-DD"
digest: "今日AI要闻"
source: "manual-curated"
topics:
  - AI & technology
  - business & markets
  - science
  - politics & policy
  - startups
  - world news
  - engineering
image_mode: "png-publish-svg-source"
hero_images:
  - content/daily/assets/YYYY-MM-DD/01-topic-slug.svg
  - content/daily/assets/YYYY-MM-DD/02-topic-slug.svg
  - content/daily/assets/YYYY-MM-DD/03-topic-slug.svg
  - content/daily/assets/YYYY-MM-DD/04-topic-slug.svg
  - content/daily/assets/YYYY-MM-DD/05-topic-slug.svg
---
```

Rules:

- `wechat_title` is the actual WeChat article title. It must summarize the issue, not be a generic date title.
- `title` is an internal/archive title and can remain stable.
- `digest` must stay short. Keep it within 10 Chinese characters when possible.
- `cover` must point to a per-issue PNG cover. Do not use the global default cover when an issue cover exists.
- The body must not include an opening quote/intro like `> 5 条过去 24 小时内...`. Start directly from story 1.
- Keep `## 发布备注` only for source control notes. Publishing scripts strip it from WeChat drafts.

## WeChat title rules

Use `wechat_title` for the public title. It should summarize the 5-story issue in one line.

Good example:

```yaml
wechat_title: "AI 公司法、视频融资与无人机热潮"
```

Avoid:

```yaml
wechat_title: "OneAI Daily｜今日AI要闻"
wechat_title: "OneAI Daily Briefing｜2026-07-04"
```

## Body structure

Use this structure:

```markdown
# OneAI Daily｜今日AI要闻

## 1. AI 政策｜阿根廷提出 AI 运营公司法案

![Argentina AI policy](assets/YYYY-MM-DD/01-ai-policy-argentina.svg)

摘要段落。

**为什么重要：** 重要性分析。

**来源：** Source, “Article title”, YYYY-MM-DD.  
https://example.com/article

---
```

Important:

- The publishing script removes the first H1 from the WeChat body, so the WeChat page will only show the official WeChat title once.
- Do not add a generic introductory blockquote after the H1.
- Use clean, compact Chinese prose.
- Do not include `发布备注` in the published body; scripts strip it.

## Image generation rules

There are two asset types per issue:

1. `cover.png`: WeChat cover image.
2. `01...png` to `05...png`: published body cards.

SVG files may remain as editable source files, but publishing must prefer same-name PNG files.

Current rules implemented in `scripts/generate_article_images.py`:

- Generates `cover.png` from `wechat_title`.
- Generates same-name PNG body cards for Markdown images that reference `.svg` or `.png`.
- Uses 1200 x 675 images.
- No white border frame.
- No right-side icons.
- No subtitle on cover.
- Cover contains only the main title plus small `ONEAI DAILY` brand text.
- Body card titles are generated from each story H2.
- Background is gradient plus light line/dot accents only.

To regenerate images:

```bash
FORCE_REGENERATE_IMAGES=1 python scripts/generate_article_images.py content/daily/YYYY-MM-DD-daily-briefing.md
```

Expected output includes:

```text
generated cover: content/daily/assets/YYYY-MM-DD/cover.png
generated: content/daily/assets/YYYY-MM-DD/01-xxx.png
```

## Publishing rules

Use:

```bash
./scripts/local_publish.sh content/daily/YYYY-MM-DD-daily-briefing.md
```

Expected behavior:

- Pull latest code.
- Create or reuse `.venv`.
- Install dependencies.
- Generate or refresh PNG article images.
- Commit generated image and Markdown changes if any.
- Push changes.
- Upload WeChat cover material.
- Upload body images through WeChat article image API.
- Create a WeChat draft.

Publishing script expectations:

- `scripts/push_wechat_draft.py` should prioritize `wechat_title` over `title`.
- `scripts/push_wechat_draft.py` should prioritize `cover` over `DEFAULT_COVER`.
- Body image upload should prefer a same-name PNG when Markdown references an SVG.
- Old drafts are not edited. Every fix requires creating a new draft.

Successful logs should include lines like:

```text
generated cover: content/daily/assets/YYYY-MM-DD/cover.png
uploaded cover material: assets/YYYY-MM-DD/cover.png -> <media_id>
using generated PNG for SVG body image: content/daily/assets/YYYY-MM-DD/01-xxx.png
uploaded generated PNG for SVG body image: assets/YYYY-MM-DD/01-xxx.svg -> https://mmbiz.qpic.cn/...
draft created successfully
```

## Common pitfalls and fixes

### Draft still shows old content

Cause: WeChat drafts are immutable from this script once created.

Fix: create a new draft by rerunning `local_publish.sh` after `git pull`.

### `发布备注` appears in draft

Cause: old script or old draft.

Fix: pull latest code and create a new draft. Publishing scripts strip internal note headings:

- `## 发布备注`
- `## 备注`
- `## 内部备注`
- `## 草稿备注`
- `## Notes`
- `## Publishing Notes`

### Body images missing

Cause: SVG body images were skipped by an older script.

Fix: current script converts/generates PNG and uploads it. Rerun after `git pull`.

### Chinese text missing in images

Cause: SVG-to-PNG conversion on local machine may lack Chinese fonts.

Fix: body cards should be generated directly as PNG by `generate_article_images.py`; publishing should upload same-name PNG instead of direct SVG conversion.

### Duplicate title inside article body

Cause: template used to render `{{ title }}` inside the article body.

Fix: `templates/wechat.html` should not add a title header. WeChat itself displays the title.

### Generic intro blockquote appears under title

Cause: Markdown body includes a line like `> 5 条过去 24 小时内...`.

Fix: remove it. Body should begin directly with `## 1...` after the H1.

### White border on images

Cause: image generation script drew a rounded white rectangle.

Fix: current image generation script should not draw white border frames.

## Current issue example: 2026-07-04

Important paths:

- Markdown: `content/daily/2026-07-04-daily-briefing.md`
- Cover: `content/daily/assets/2026-07-04/cover.png`
- Body image sources: `content/daily/assets/2026-07-04/*.svg`
- Published body images: `content/daily/assets/2026-07-04/*.png`

Current public title:

```text
AI 公司法、视频融资与无人机热潮
```

Current resolved issue-level decisions:

- No subtitle on cover.
- No white border on cover or body cards.
- No intro blockquote in WeChat body.
- Use per-issue cover.
- Use summary-style `wechat_title`.
- Use PNG for WeChat publishing, SVG only as source.

## Checklist before creating a draft

1. Markdown frontmatter has `wechat_title` and `cover`.
2. Body starts directly from story 1 after the H1.
3. No generic intro blockquote.
4. Run image generation with `FORCE_REGENERATE_IMAGES=1`.
5. Confirm `cover.png` and 5 body PNGs exist.
6. Run `./scripts/local_publish.sh <article>`.
7. Review the newly created WeChat draft, not an older draft.
