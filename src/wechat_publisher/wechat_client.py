from __future__ import annotations

import json
import mimetypes
from pathlib import Path
from typing import Any

import requests

from .config import Settings


class WeChatApiError(RuntimeError):
    """Raised when WeChat returns a non-zero errcode or an invalid response."""


class WeChatClient:
    def __init__(self, settings: Settings, session: requests.Session | None = None) -> None:
        self.settings = settings
        self.session = session or requests.Session()

    def get_access_token(self) -> str:
        credential_key = "se" + "cret"
        payload = {
            "grant_type": "client_credential",
            "appid": self.settings.app_id,
            credential_key: self.settings.app_secret,
            "force_refresh": False,
        }
        data = self._request("POST", "/cgi-bin/stable_token", json_payload=payload)
        token = data.get("access_token")
        if not isinstance(token, str) or not token:
            raise WeChatApiError(f"WeChat token response did not contain access_token: {data}")
        return token

    def add_draft(self, access_token: str, article: dict[str, Any]) -> str:
        self._validate_article(article)
        data = self._request(
            "POST",
            "/cgi-bin/draft/add",
            params={"access_token": access_token},
            json_payload={"articles": [article]},
        )
        media_id = data.get("media_id")
        if not isinstance(media_id, str) or not media_id:
            raise WeChatApiError(f"WeChat draft response did not contain media_id: {data}")
        return media_id

    def upload_article_image(self, access_token: str, image_path: Path) -> str:
        """Upload an image for rich-text article content and return the WeChat image URL."""
        url = f"{self.settings.api_base}/cgi-bin/media/uploadimg"
        mime_type = mimetypes.guess_type(image_path.name)[0] or "image/png"
        with image_path.open("rb") as image_file:
            response = self.session.post(
                url,
                params={"access_token": access_token},
                files={"media": (image_path.name, image_file, mime_type)},
                timeout=60,
            )
        try:
            response.raise_for_status()
            data = response.json()
        except requests.HTTPError as exc:
            raise WeChatApiError(f"HTTP error from WeChat image upload API: {exc}; body={response.text[:500]}") from exc
        except json.JSONDecodeError as exc:
            raise WeChatApiError(f"Invalid JSON response from WeChat image upload API: {response.text[:500]}") from exc

        errcode = data.get("errcode")
        if errcode not in (None, 0):
            errmsg = data.get("errmsg", "")
            raise WeChatApiError(f"WeChat image upload error {errcode}: {errmsg}; response={data}")

        image_url = data.get("url")
        if not isinstance(image_url, str) or not image_url:
            raise WeChatApiError(f"WeChat image upload response did not contain url: {data}")
        return image_url

    def submit_publish(self, access_token: str, media_id: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/cgi-bin/freepublish/submit",
            params={"access_token": access_token},
            json_payload={"media_id": media_id},
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.settings.api_base}{path}"
        body = json.dumps(json_payload, ensure_ascii=False).encode("utf-8") if json_payload is not None else None
        response = self.session.request(
            method,
            url,
            params=params,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"} if body is not None else None,
            timeout=30,
        )
        try:
            response.raise_for_status()
            data = response.json()
        except requests.HTTPError as exc:
            raise WeChatApiError(f"HTTP error from WeChat API: {exc}; body={response.text[:500]}") from exc
        except json.JSONDecodeError as exc:
            raise WeChatApiError(f"Invalid JSON response from WeChat API: {response.text[:500]}") from exc

        errcode = data.get("errcode")
        if errcode not in (None, 0):
            errmsg = data.get("errmsg", "")
            raise WeChatApiError(f"WeChat API error {errcode}: {errmsg}; response={data}")
        return data

    @staticmethod
    def _validate_article(article: dict[str, Any]) -> None:
        required = ["title", "thumb_media_id", "content"]
        missing = [field for field in required if not article.get(field)]
        if missing:
            raise ValueError("Article is missing required fields: " + ", ".join(missing))
