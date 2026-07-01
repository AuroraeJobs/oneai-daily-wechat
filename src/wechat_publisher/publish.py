from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import Settings
from .renderer import render_markdown_article
from .wechat_client import WeChatClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POSTS_DIR = PROJECT_ROOT / "content" / "posts"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publish OneAI Daily Markdown posts to WeChat.")
    parser.add_argument("--post", help="Path to the Markdown post. Defaults to the latest file in content/posts.")
    parser.add_argument("--dry-run", action="store_true", help="Render and print payload without calling WeChat API.")
    parser.add_argument("--publish", action="store_true", help="Temporarily disabled: draft will be created, but publish API will not be called.")
    args = parser.parse_args(argv)

    settings = Settings.from_env().with_overrides(
        dry_run=True if args.dry_run else None,
        publish_after_draft=True if args.publish else None,
    )

    post_path = _resolve_post_path(args.post)
    article = render_markdown_article(
        post_path,
        default_author=settings.author,
        default_thumb_media_id=settings.thumb_media_id,
        default_need_open_comment=settings.need_open_comment,
        default_only_fans_can_comment=settings.only_fans_can_comment,
    )
    payload = article.to_wechat_payload()

    if settings.dry_run:
        print("[dry-run] Rendered WeChat article payload:")
        print(json.dumps({"post": str(post_path), "article": payload}, ensure_ascii=False, indent=2))
        return 0

    settings.validate_for_api()
    client = WeChatClient(settings)
    token = client.get_access_token()
    media_id = client.add_draft(token, payload)
    print(f"Draft created successfully. media_id={media_id}")

    if settings.publish_after_draft:
        # Temporarily disabled because the account currently returns 48001 api unauthorized
        # for /cgi-bin/freepublish/submit. Keep drafts auto-created, then publish manually
        # from the WeChat Official Account backend.
        #
        # result = client.submit_publish(token, media_id)
        # print("Publish submitted successfully:")
        # print(json.dumps(result, ensure_ascii=False, indent=2))
        print("Publish requested, but the WeChat publish API call is currently disabled.")
        print("Draft was created only. Please publish it manually in the WeChat backend.")
    else:
        print("Publish skipped. Draft was created only.")
    return 0


def _resolve_post_path(post: str | None) -> Path:
    if post:
        path = Path(post)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
    else:
        path = _latest_post(DEFAULT_POSTS_DIR)

    if not path.exists():
        raise FileNotFoundError(f"Post file not found: {path}")
    if path.suffix.lower() != ".md":
        raise ValueError(f"Post must be a Markdown file: {path}")
    return path


def _latest_post(posts_dir: Path) -> Path:
    posts = sorted(posts_dir.glob("*.md"), key=lambda path: (path.stat().st_mtime, path.name), reverse=True)
    if not posts:
        raise FileNotFoundError(f"No Markdown posts found in {posts_dir}")
    return posts[0]


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - keep CLI failure readable in Actions logs.
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
