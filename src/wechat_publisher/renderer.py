from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from pathlib import Path

import markdown

_FRONT_MATTER_RE = re.compile(r"\A---\s*\n(?P<meta>.*?)\n---\s*\n(?P<body>.*)\Z", re.DOTALL)
_HEADING_RE = re.compile(r"^#\s+(?P<title>.+?)\s*$", re.MULTILINE)
_TAG_RE = re.compile(r"<[^>]+>")
_MAX_DIGEST_BYTES = 120


@dataclass(frozen=True)
class RenderedArticle:
    title: str
    author: str
    digest: str
    content: str
    thumb_media_id: str
    content_source_url: str = ""
    need_open_comment: int = 0
    only_fans_can_comment: int = 0
    show_cover_pic: int = 0

    def to_wechat_payload(self) -> dict[str, object]:
        return {
            "title": self.title,
            "author": self.author,
            "digest": self.digest,
            "content": self.content,
            "content_source_url": self.content_source_url,
            "thumb_media_id": self.thumb_media_id,
            "need_open_comment": self.need_open_comment,
            "only_fans_can_comment": self.only_fans_can_comment,
            "show_cover_pic": self.show_cover_pic,
        }


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    match = _FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text

    meta: dict[str, str] = {}
    for raw_line in match.group("meta").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        meta[key.strip()] = _strip_quotes(value.strip())
    return meta, match.group("body")


def render_markdown_article(
    path: Path,
    *,
    default_author: str,
    default_thumb_media_id: str,
    default_need_open_comment: int = 0,
    default_only_fans_can_comment: int = 0,
) -> RenderedArticle:
    text = path.read_text(encoding="utf-8")
    meta, body = parse_front_matter(text)
    html = markdown.markdown(
        body,
        extensions=["extra", "sane_lists", "smarty"],
        output_format="html5",
    )
    content = wrap_for_wechat(html)

    title = meta.get("title") or _extract_title(body) or path.stem
    digest = meta.get("digest") or _build_digest(html)

    return RenderedArticle(
        title=_limit(title, 64),
        author=meta.get("author") or default_author,
        digest=_limit_utf8_bytes(digest, _MAX_DIGEST_BYTES),
        content=content,
        content_source_url=meta.get("content_source_url", ""),
        thumb_media_id=meta.get("cover_media_id") or meta.get("thumb_media_id") or default_thumb_media_id,
        need_open_comment=_int_flag(meta.get("need_open_comment"), default_need_open_comment),
        only_fans_can_comment=_int_flag(meta.get("only_fans_can_comment"), default_only_fans_can_comment),
        show_cover_pic=_int_flag(meta.get("show_cover_pic"), 0),
    )


def wrap_for_wechat(html: str) -> str:
    return (
        '<section style="font-size:16px;line-height:1.75;color:#1f2328;">\n'
        f"{html}\n"
        '<p style="margin-top:24px;color:#8a8f98;font-size:13px;">'
        "由 OneAI Daily 自动发布。</p>\n"
        "</section>"
    )


def _extract_title(body: str) -> str:
    match = _HEADING_RE.search(body)
    return match.group("title").strip() if match else ""


def _build_digest(html: str) -> str:
    text = _TAG_RE.sub(" ", html)
    text = unescape(re.sub(r"\s+", " ", text)).strip()
    return text if text else "OneAI Daily"


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _int_flag(value: str | None, default: int = 0) -> int:
    if value is None or value == "":
        return 1 if int(default) else 0
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return 1
    if normalized in {"0", "false", "no", "off"}:
        return 0
    return 1 if int(value) else 0


def _limit(value: str, max_chars: int) -> str:
    value = value.strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rstrip() + "…"


def _limit_utf8_bytes(value: str, max_bytes: int, suffix: str = "…") -> str:
    value = value.strip()
    if len(value.encode("utf-8")) <= max_bytes:
        return value

    suffix_bytes = suffix.encode("utf-8")
    budget = max_bytes - len(suffix_bytes)
    if budget <= 0:
        return ""

    result: list[str] = []
    used = 0
    for char in value:
        char_bytes = len(char.encode("utf-8"))
        if used + char_bytes > budget:
            break
        result.append(char)
        used += char_bytes

    return "".join(result).rstrip() + suffix
