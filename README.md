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

正文内容……
```

字段说明：

- `title`：公众号标题；缺省时使用正文第一个一级标题
- `author`：作者；缺省时使用环境变量 `WECHAT_AUTHOR`
- `digest`：摘要；缺省时从正文首段截取
- `cover_media_id`：单篇文章封面素材 ID；缺省时使用 `WECHAT_THUMB_MEDIA_ID`
- `content_source_url`：原文链接，可留空
- `need_open_comment`：是否打开评论，`0` 或 `1`
- `only_fans_can_comment`：是否仅粉丝可评论，`0` 或 `1`
- `show_cover_pic`：正文是否展示封面，`0` 或 `1`

## 注意事项

- 公众号发布接口要求公众号已开通对应能力，并且服务器 IP / 调用环境符合微信后台配置。
- `WECHAT_THUMB_MEDIA_ID` 需要是已上传到公众号素材库的图片素材 ID。
- 定时任务使用 UTC cron，当前配置 `30 23 * * *` 对应北京时间第二天 07:30。
- 本项目不会生成封面图；封面素材上传流程可后续扩展。
