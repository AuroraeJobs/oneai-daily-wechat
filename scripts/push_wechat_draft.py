#!/usr/bin/env python3
"""Upload a OneAI Daily markdown article and its local images to WeChat, then create a draft.

Required env vars, usually loaded from .env:
  WECHAT_APP_ID
  WECHAT_APP_SECRET

Optional env vars:
  ARTICLE_PATH=content/daily/2026-07-02-daily-briefing.md
  AUTHOR=OneAI Daily
  NEED_OPEN_COMMENT=0
  ONLY_FANS_CAN_COMMENT=0

Usage:
  python scripts/push_wechat_draft.py
  python scripts/push_wechat_draft.py content/daily/2026-07-02-daily-briefing.md

Notes:
  - The script automatically loads .env from the project root when present.
  - If no CLI path or ARTICLE_PATH is provided, it uses the newest markdown file in content/daily.
  - WeChat draft/add requires thumb_media_id, so the cover image is uploaded as a permanent image material.
  - Article body images are uploaded through media/uploadimg and local markdown image paths are replaced with WeChat image URLs.
  - SVG images are converted to PNG before upload because WeChat image APIs are more reliable with PNG/JPG.
"""

from __future__ import annotations

import os
import re
import sys
import json
import mimetypes
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import markdown
import requests
import yaml
from bs4 import BeautifulSoup
from dotenv import load_dotenv

try:
    import cairosvg
except Exception:  # pragma: no cover
    cairosvg = None


REPO_ROOT = Path(__file__).resolve().parents[1]
DAILY_DIR = REPO_ROOT / "content" / "daily"

# Load local secrets/config first; existing shell env still takes precedence.
load_dotenv(REPO_ROOT / ".env", override=False)


@dataclass
class Article:
    metadata: dict
    body: str
    path: Path


class WeChatError(RuntimeError):
    pass


def find_latest_article() -> Path:
    if not DAILY_DIR.exists():
        raise FileNotFoundError(f"Daily content directory not found: {DAILY_DIR}")
    candidates = sorted(
        DAILY_DIR.glob("*.md"),
        key=lambda p: (p.stat().st_mtime, p.name),
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"No markdown articles found in {DAILY_DIR}")
    return candidates[0]


def resolve_article_path() -> Path:
    if len(sys.argv) > 1 and sys.argv[1].strip():
        raw = sys.argv[1].strip()
    else:
        raw = os.getenv("ARTICLE_PATH", "").strip()

    if raw:
        path = Path(raw)
        if not path.is_absolute():
            path = REPO_ROOT / path
        return path.resolve()

    return find_latest_article().resolve()


def load_article(path: Path) -> Article:
    if not path.exists():
        raise FileNotFoundError(f"Article not found: {path}")
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            metadata = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()
            return Article(metadata=metadata, body=body, path=path)
    return Article(metadata={}, body=text, path=path)


def request_json(method: str, url: str, **kwargs) -> dict:
    response = requests.request(method, url, timeout=60, **kwargs)
    try:
        payload = response.json()
    except Exception as exc:
        raise WeChatError(f"Non-JSON response from WeChat: HTTP {response.status_code} {response.text[:300]}") from exc
    if payload.get("errcode") not in (None, 0):
        raise WeChatError(f"WeChat API error {payload.get('errcode')}: {payload.get('errmsg')} response={payload}")
    return payload


def get_access_token(app_id: str, app_secret: str) -> str:
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {
        "grant_type": "client_credential",
        "appid": app_id,
        "secret": app_secret,
    }
    payload = request_json("GET", url, params=params)
    token = payload.get("access_token")
    if not token:
        raise WeChatError(f"No access_token returned: {payload}")
    return token


def as_uploadable_image(path: Path) -> Tuple[Path, str, tempfile.TemporaryDirectory | None]:
    suffix = path.suffix.lower()
    if suffix == ".svg":
        if cairosvg is None:
            raise WeChatError("SVG image found but cairosvg is not installed")
        tmpdir = tempfile.TemporaryDirectory()
        out_path = Path(tmpdir.name) / f"{path.stem}.png"
        cairosvg.svg2png(url=str(path), write_to=str(out_path), output_width=1200, output_height=675)
        return out_path, "image/png", tmpdir

    mime, _ = mimetypes.guess_type(path.name)
    if mime not in {"image/jpeg", "image/png", "image/gif", "image/bmp"}:
        mime = "image/png"
    return path, mime, None


def upload_body_image(access_token: str, image_path: Path) -> str:
    upload_path, mime, tmpdir = as_uploadable_image(image_path)
    try:
        url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}"
        with upload_path.open("rb") as fh:
            payload = request_json("POST", url, files={"media": (upload_path.name, fh, mime)})
        img_url = payload.get("url")
        if not img_url:
            raise WeChatError(f"No image url returned for {image_path}: {payload}")
        return img_url
    finally:
        if tmpdir:
            tmpdir.cleanup()


def upload_thumb_material(access_token: str, image_path: Path) -> str:
    upload_path, mime, tmpdir = as_uploadable_image(image_path)
    try:
        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
        with upload_path.open("rb") as fh:
            payload = request_json("POST", url, files={"media": (upload_path.name, fh, mime)})
        media_id = payload.get("media_id")
        if not media_id:
            raise WeChatError(f"No media_id returned for cover {image_path}: {payload}")
        return media_id
    finally:
        if tmpdir:
            tmpdir.cleanup()


def resolve_image_path(article_path: Path, image_ref: str) -> Path:
    raw = image_ref.strip()
    if raw.startswith(("http://", "https://")):
        raise WeChatError(f"Remote image URLs are not supported in this script yet: {raw}")
    candidate = (article_path.parent / raw).resolve()
    if not candidate.exists():
        candidate = (REPO_ROOT / raw).resolve()
    if not candidate.exists():
        raise FileNotFoundError(f"Image not found: {image_ref} resolved from {article_path}")
    return candidate


def replace_markdown_images(article: Article, access_token: str) -> str:
    image_cache: Dict[str, str] = {}

    def repl(match: re.Match) -> str:
        alt = match.group(1)
        ref = match.group(2)
        if ref not in image_cache:
            local_path = resolve_image_path(article.path, ref)
            image_cache[ref] = upload_body_image(access_token, local_path)
            print(f"uploaded body image: {ref} -> {image_cache[ref]}")
        return f"![{alt}]({image_cache[ref]})"

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", repl, article.body)


def markdown_to_wechat_html(md_text: str) -> str:
    html = markdown.markdown(md_text, extensions=["extra", "sane_lists"])
    soup = BeautifulSoup(html, "html.parser")

    for img in soup.find_all("img"):
        img["style"] = "width:100%;height:auto;border-radius:12px;margin:18px 0;display:block;"

    for h1 in soup.find_all("h1"):
        h1["style"] = "font-size:24px;line-height:1.35;margin:20px 0 14px;font-weight:700;"
    for h2 in soup.find_all("h2"):
        h2["style"] = "font-size:20px;line-height:1.45;margin:22px 0 12px;font-weight:700;"
    for p in soup.find_all("p"):
        p["style"] = "font-size:16px;line-height:1.85;margin:12px 0;color:#222;"
    for blockquote in soup.find_all("blockquote"):
        blockquote["style"] = "border-left:4px solid #999;padding-left:12px;color:#666;margin:16px 0;"
    for hr in soup.find_all("hr"):
        hr["style"] = "border:none;border-top:1px solid #eee;margin:24px 0;"

    return str(soup)


def create_draft(access_token: str, article: Article, content_html: str, thumb_media_id: str) -> dict:
    metadata = article.metadata
    title = metadata.get("title") or "OneAI Daily"
    digest = metadata.get("digest") or "今日5条"
    author = metadata.get("author") or os.getenv("AUTHOR", "OneAI Daily")

    payload = {
        "articles": [
            {
                "title": title,
                "author": author,
                "digest": digest[:54],
                "content": content_html,
                "content_source_url": "",
                "thumb_media_id": thumb_media_id,
                "need_open_comment": int(os.getenv("NEED_OPEN_COMMENT", "0")),
                "only_fans_can_comment": int(os.getenv("ONLY_FANS_CAN_COMMENT", "0")),
            }
        ]
    }
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    return request_json(
        "POST",
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )


def main() -> int:
    app_id = os.getenv("WECHAT_APP_ID")
    app_secret = os.getenv("WECHAT_APP_SECRET")
    if not app_id or not app_secret:
        raise SystemExit("Missing WECHAT_APP_ID or WECHAT_APP_SECRET. Add them to .env or export them in your shell.")

    article_path = resolve_article_path()
    print(f"using article: {article_path.relative_to(REPO_ROOT)}")
    article = load_article(article_path)

    access_token = get_access_token(app_id, app_secret)
    print("got WeChat access_token")

    cover_ref = article.metadata.get("cover")
    if not cover_ref:
        match = re.search(r"!\[[^\]]*\]\(([^)]+)\)", article.body)
        if not match:
            raise WeChatError("No cover in front matter and no markdown image found")
        cover_ref = match.group(1)

    cover_path = resolve_image_path(article.path, cover_ref)
    thumb_media_id = upload_thumb_material(access_token, cover_path)
    print(f"uploaded cover material: {cover_ref} -> {thumb_media_id}")

    body_with_wechat_images = replace_markdown_images(article, access_token)
    html = markdown_to_wechat_html(body_with_wechat_images)
    result = create_draft(access_token, article, html, thumb_media_id)
    print("draft created successfully")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise
