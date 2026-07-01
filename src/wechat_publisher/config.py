from __future__ import annotations

import os
from dataclasses import dataclass, replace

from dotenv import load_dotenv

TRUTHY = {"1", "true", "t", "yes", "y", "on"}
FALSY = {"0", "false", "f", "no", "n", "off"}


def as_bool(value: str | None, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    normalized = value.strip().lower()
    if normalized in TRUTHY:
        return True
    if normalized in FALSY:
        return False
    raise ValueError(f"Invalid boolean value: {value!r}")


@dataclass(frozen=True)
class Settings:
    app_id: str = ""
    app_secret: str = ""
    thumb_media_id: str = ""
    author: str = "OneAI"
    dry_run: bool = False
    publish_after_draft: bool = False
    need_open_comment: int = 0
    only_fans_can_comment: int = 0
    api_base: str = "https://api.weixin.qq.com"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            app_id=os.getenv("WECHAT_APP_ID", "").strip(),
            app_secret=os.getenv("WECHAT_APP_SECRET", "").strip(),
            thumb_media_id=os.getenv("WECHAT_THUMB_MEDIA_ID", "").strip(),
            author=os.getenv("WECHAT_AUTHOR", "OneAI").strip() or "OneAI",
            dry_run=as_bool(os.getenv("WECHAT_DRY_RUN"), default=False),
            publish_after_draft=as_bool(os.getenv("WECHAT_PUBLISH_AFTER_DRAFT"), default=False),
            need_open_comment=int(os.getenv("WECHAT_NEED_OPEN_COMMENT", "0") or 0),
            only_fans_can_comment=int(os.getenv("WECHAT_ONLY_FANS_CAN_COMMENT", "0") or 0),
            api_base=os.getenv("WECHAT_API_BASE", "https://api.weixin.qq.com").rstrip("/"),
        )

    def with_overrides(
        self,
        *,
        dry_run: bool | None = None,
        publish_after_draft: bool | None = None,
    ) -> "Settings":
        changes: dict[str, bool] = {}
        if dry_run is not None:
            changes["dry_run"] = dry_run
        if publish_after_draft is not None:
            changes["publish_after_draft"] = publish_after_draft
        return replace(self, **changes)

    def validate_for_api(self) -> None:
        missing = []
        if not self.app_id:
            missing.append("WECHAT_APP_ID")
        if not self.app_secret:
            missing.append("WECHAT_APP_SECRET")
        if missing:
            raise RuntimeError("Missing required environment variables: " + ", ".join(missing))
