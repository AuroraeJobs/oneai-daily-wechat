from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import cairosvg

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

    if settings.dry_run:
        article = render_markdown_article(
            post_path,
            default_author=settings.author,
            default_thumb_media_id=settings.thumb_media_id,
            default_need_open_comment=settings.need_open_comment,
            default_only_fans_can_comment=settings.only_fans_can_comment,
        )
        payload = article.to_wechat_payload()
        print("[dry-run] Rendered WeChat article payload:")
        print(json.dumps({"post": str(post_path), "article": payload}, ensure_ascii=False, indent=2))
        return 0

    settings.validate_for_api()
    client = WeChatClient(settings)
    token = client.get_access_token()

    with tempfile.TemporaryDirectory(prefix="oneai-wechat-images-") as temp_dir:
        temp_path = Path(temp_dir)
        image_cache: dict[str, str] = {}

        def image_url_resolver(src: str) -> str:
            return _upload_local_article_image(
                src,
                post_path=post_path,
                temp_dir=temp_path,
                client=client,
                access_token=token,
                image_cache=image_cache,
            )

        article = render_markdown_article(
            post_path,
            default_author=settings.author,
            default_thumb_media_id=settings.thumb_media_id,
            default_need_open_comment=settings.need_open_comment,
            default_only_fans_can_comment=settings.only_fans_can_comment,
            image_url_resolver=image_url_resolver,
        )
        payload = article.to_wechat_payload()

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


def _upload_local_article_image(
    src: str,
    *,
    post_path: Path,
    temp_dir: Path,
    client: WeChatClient,
    access_token: str,
    image_cache: dict[str, str],
) -> str:
    parsed = urlparse(src)
    if parsed.scheme in {"http", "https", "data"}:
        return src

    cache_key = src
    if cache_key in image_cache:
        return image_cache[cache_key]

    image_path = Path(parsed.path)
    if not image_path.is_absolute():
        image_path = post_path.parent / image_path
    image_path = image_path.resolve()
    if not image_path.exists():
        raise FileNotFoundError(f"Article image not found: {image_path}")

    upload_path = _prepare_upload_image(image_path, temp_dir)
    image_url = client.upload_article_image(access_token, upload_path)
    image_cache[cache_key] = image_url
    print(f"Uploaded article image: {image_path.name} -> {image_url}")
    return image_url


def _prepare_upload_image(image_path: Path, temp_dir: Path) -> Path:
    suffix = image_path.suffix.lower()
    if suffix == ".svg":
        png_path = temp_dir / f"{image_path.stem}.png"
        cairosvg.svg2png(url=str(image_path), write_to=str(png_path), output_width=1200, output_height=675)
        return png_path

    if suffix == ".png":
        return image_path

    if suffix in {".jpg", ".jpeg"}:
        upload_path = temp_dir / f"{image_path.stem}.jpg"
        shutil.copyfile(image_path, upload_path)
        return upload_path

    raise ValueError(f"Unsupported article image type for WeChat upload: {image_path}")


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
