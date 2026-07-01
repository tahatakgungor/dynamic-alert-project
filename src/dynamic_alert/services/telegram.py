from __future__ import annotations

import json
from urllib import error, parse, request

from dynamic_alert.config import Settings


class TelegramNotifier:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send(self, message: str) -> bool:
        if not self.settings.telegram_bot_token or not self.settings.telegram_chat_id:
            print(f"[telegram-dry-run] {message}")
            return False

        endpoint = (
            f"{self.settings.telegram_api_base.rstrip('/')}"
            f"/bot{self.settings.telegram_bot_token}/sendMessage"
        )
        payload = parse.urlencode(
            {
                "chat_id": self.settings.telegram_chat_id,
                "text": message,
                "disable_web_page_preview": "true",
            }
        ).encode("utf-8")
        http_request = request.Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=self.settings.telegram_timeout_seconds) as response:
                body = response.read().decode("utf-8", errors="ignore")
        except error.URLError as exc:
            print(f"[telegram-error] {exc}")
            return False

        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {}

        if parsed.get("ok") is True:
            return True

        print(f"[telegram-error] unexpected response: {body}")
        return False
