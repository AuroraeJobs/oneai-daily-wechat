# OneAI Daily WeChat

一个用于把 Markdown 日报自动发布到微信公众号的轻量项目。默认流程是：读取 `content/posts` 下最新文章，渲染为微信公众号可接受的 HTML，创建草稿；开启 `--publish` 后会继续提交发布。

> ⚠️ 请不要把 `AppSecret`、`thumb_media_id` 等敏感信息写入仓库。生产环境请使用 GitHub Actions Secrets / Variables。

## 功能

- Markdown + Front Matter 撰写文章
- 自动解析标题、摘要、作者、封面素材 ID
- 微信公众号 `access_token` 获取、草稿创建、发布提交
- GitHub Actions 定时发布与手动触发
- 本地 dry-run 预览，不调用微信 API

## 目录结构

```text
.
├── content/posts/              # 文章 Markdown
├── src/wechat_publisher/       # 发布器源码
├── scripts/new_post.py         # 快速创建每日文章模板
├── .github/workflows/publish.yml
├── .env.example
├── pyproject.toml
└── requirements.txt
```

## 快速开始

### 1. 本地安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

编辑 `.env`：

```bash
WECHAT_APP_ID=你的公众号AppID
WECHAT_APP_SECRET=你的公众号AppSecret
WECHAT_THUMB_MEDIA_ID=封面图片素材media_id
WECHAT_AUTHOR=OneAI
WECHAT_DRY_RUN=true
WECHAT_PUBLISH_AFTER_DRAFT=false
```

### 2. 创建文章

```bash
python scripts/new_post.py "OneAI Daily"
```

文章会生成到 `content/posts/YYYY-MM-DD-oneai-daily.md`。你也可以直接复制 `content/posts/2026-07-01-sample.md` 修改。

### 3. 本地 dry-run

```bash
python -m wechat_publisher.publish --dry-run
```

指定文章：

```bash
python -m wechat_publisher.publish --post content/posts/2026-07-01-sample.md --dry-run
```

### 4. 创建草稿

确认 `.env` 已配置真实参数后：

```bash
WECHAT_DRY_RUN=false python -m wechat_publisher.publish --post content/posts/2026-07-01-sample.md
```

### 5. 创建草稿并提交发布

```bash
WECHAT_DRY_RUN=false python -m wechat_publisher.publish --post content/posts/2026-07-01-sample.md --publish
```

## GitHub Actions 配置

在仓库 `Settings -> Secrets and variables -> Actions` 中配置：

Secrets：

- `WECHAT_APP_ID`
- `WECHAT_APP_SECRET`
- `WECHAT_THUMB_MEDIA_ID`

Variables：

- `WECHAT_AUTHOR`，可选，默认 `OneAI`

工作流位于 `.github/workflows/publish.yml`：

- 定时任务：每天北京时间 07:30 运行，并默认加 `--publish`
- 手动运行：支持选择文章路径、dry-run、是否发布

首次上线建议手动触发一次，选择 `dry_run=true` 验证渲染结果，再选择 `dry_run=false`、`publish=false` 创建草稿，最后再打开发布。

## 文章 Front Matter

微信公众号草稿标题直接取 `title` 字段；正文里的一级标题会被移除，避免草稿标题和正文重复。

```markdown
---
title: "OneAI Daily"
author: "OneAI"
digest: "今天值得关注的 AI 与招聘动态。"
cover_media_id: ""
content_source_url: ""
need_open_comment: 0
only_fans_can_comment: 0
show_cover_pic: 0
---

# OneAI Daily
```

## Markdown 内部备注

以下二级标题开头的章节只保留在 Markdown 源文件里，生成微信公众号草稿时会自动过滤，不进入正文：

- `## 发布备注`
- `## 备注`
- `## 内部备注`
- `## 草稿备注`
- `## Notes`
- `## Publishing Notes`
