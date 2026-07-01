#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "content" / "posts"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value)
    value = value.strip("-")
    return value or "daily"


def main() -> int:
    title = " ".join(sys.argv[1:]).strip() or "OneAI Daily"
    today = date.today().isoformat()
    path = POSTS_DIR / f"{today}-{slugify(title)}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        print(f"Post already exists: {path}")
        return 1

    path.write_text(
        f'''---
title: "{title}"
author: "OneAI"
digest: "今天值得关注的 AI 与招聘动态。"
cover_media_id: ""
content_source_url: ""
need_open_comment: 0
only_fans_can_comment: 0
show_cover_pic: 0
---

# {title}

## 今日摘要

- 要点一
- 要点二
- 要点三

## 深度解读

在这里写正文。

## 行动建议

在这里写给读者的建议。
''',
        encoding="utf-8",
    )
    print(f"Created {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
