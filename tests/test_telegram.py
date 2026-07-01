from dynamic_alert.config import Settings
from dynamic_alert.services.telegram import TelegramNotifier


class _FakeResponse:
    def __init__(self, body: str) -> None:
        self.body = body

    def read(self) -> bytes:
        return self.body.encode("utf-8")

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_telegram_notifier_posts_send_message(monkeypatch) -> None:
    captured: dict[str, str | bytes | float] = {}

    def fake_urlopen(req, timeout: float):
        captured["url"] = req.full_url
        captured["data"] = req.data
        captured["timeout"] = timeout
        return _FakeResponse('{"ok": true}')

    monkeypatch.setattr("dynamic_alert.services.telegram.request.urlopen", fake_urlopen)

    notifier = TelegramNotifier(
        Settings(
            telegram_bot_token="bot-token",
            telegram_chat_id="12345",
            telegram_api_base="https://api.telegram.org",
            telegram_timeout_seconds=3.0,
        )
    )

    delivered = notifier.send("critical temperature")

    assert delivered is True
    assert captured["url"] == "https://api.telegram.org/botbot-token/sendMessage"
    assert b"chat_id=12345" in captured["data"]
    assert b"critical+temperature" in captured["data"]
    assert captured["timeout"] == 3.0
