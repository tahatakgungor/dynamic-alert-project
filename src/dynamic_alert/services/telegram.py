from dynamic_alert.config import Settings


class TelegramNotifier:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send(self, message: str) -> bool:
        # Ilk surumde dry-run davranisi kullaniliyor.
        # Token tanimlandiginda burasi gercek HTTP istegi ile genisletilecek.
        if not self.settings.telegram_bot_token or not self.settings.telegram_chat_id:
            print(f"[telegram-dry-run] {message}")
            return False
        print(f"[telegram] {message}")
        return True
