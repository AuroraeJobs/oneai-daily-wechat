from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from pathlib import Path

import markdown

_FRONT_MATTER_RE = re.compile(r"\A---\s*\n(?P<meta>.*?)\n---\s*\n(?P<body>.*)\Z", re.DOTALL)
_HEADING_RE = re.compile(r"^#\s+(?P<title>.+?)\s*$", re.MULTILINE)
_TAG_RE = re.compile(r"<[^>]+>")
_UNICODE_ESCAPE_RE = re.compile(r"\\([uU])([0-9a-fA-F]{4,8})")
_MAX_DIGEST_BYTES = 120
_FOOTER_TEXT = "由 OneAI Daily 自动发布。"


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
    text = _decode_unicode_escape_literals(path.read_text(encoding="utf-8"))
    meta, body = parse_front_matter(text)

    title = meta.get("title") or _extract_title(body) or path.stem
    body = _strip_leading_h1(body)

    html = markdown.markdown(
        body,
        extensions=["extra", "sane_lists", "smarty"],
        output_format="html5",
    )
    content = wrap_for_wechat(html)
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
    html = _style_wechat_blocks(html)

    footer = ""
    if _FOOTER_TEXT not in html:
        footer = (
            '<p style="margin:30px 0 0;color:#8a8f98;font-size:13px;line-height:1.7;">'
            f"{_FOOTER_TEXT}</p>\n"
        )

    return (
        '<section style="font-size:17px;line-height:1.9;color:#1f2328;">\n'
        f"{html}\n"
        f"{footer}"
        "</section>"
    )


def _style_wechat_blocks(html: str) -> str:
    replacements = [
        (
            r"<h1>",
            '<h1 style="margin:0 0 24px;font-size:28px;line-height:1.35;font-weight:700;color:#111827;">',
        ),
        (
            r"<h2>",
            '<h2 style="margin:38px 0 18px;padding-top:4px;font-size:22px;line-height:1.45;font-weight:700;color:#111827;">',
        ),
        (
            r"<h3>",
            '<h3 style="margin:30px 0 14px;font-size:19px;line-height:1.5;font-weight:700;color:#111827;">',
        ),
        (
            r"<p>",
            '<p style="margin:16px 0;line-height:1.95;color:#1f2328;">',
        ),
        (
            r"<blockquote>",
            '<blockquote style="margin:24px 0;padding:10px 0 10px 16px;border-left:4px solid #d1d5db;color:#4b5563;background:#f9fafb;">',
        ),
        (
            r"<hr\s*/?>",
            '<hr style="border:none;border-top:1px solid #e5e7eb;margin:34px 0;">',
        ),
    ]

    for pattern, replacement in replacements:
        html = re.sub(pattern, replacement, html)
    return html


def _strip_leading_h1(body: str) -> str:
    return re.sub(r"\A\s*#\s+.+?(?:\n+|\Z)", "", body, count=1)


def _extract_title(body: str) -> str:
    match = _HEADING_RE.search(body)
    return match.group("title").strip() if match else ""


def _build_digest(html: str) -> str:
    text = _TAG_RE.sub(" ", html)
    text = unescape(re.sub(r"\s+", " ", text)).strip()
    return text if text else "OneAI Daily"


def _decode_unicode_escape_literals(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        marker = match.group(1)
        digits = match.group(2)
        if marker == "u" and len(digits) != 4:
            return match.group(0)
        if marker == "U" and len(digits) != 8:
            return match.group(0)
        try:
            return chr(int(digits, 16))
        except ValueError:
            return match.group(0)

    return _UNICODE_ESCAPE_RE.sub(replace, value)


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
