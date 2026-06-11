"""Settings dialog worker threads."""

import asyncio

from PyQt6.QtCore import QThread, pyqtSignal

from models import NotificationType
from notifiers import DiscordNotifier, SlackNotifier, TelegramNotifier


class CleanupWorker(QThread):
    """Run DB cleanup in a background thread."""

    completed = pyqtSignal(int)
    failed = pyqtSignal(str)

    def __init__(self, db_path: str, days: int, exclude_favorites: bool, exclude_noted: bool):
        super().__init__()
        self.db_path = db_path
        self.days = days
        self.exclude_favorites = exclude_favorites
        self.exclude_noted = exclude_noted

    def run(self):
        try:
            from db import DatabaseManager
            db = DatabaseManager(self.db_path)
            try:
                deleted = db.cleanup_old_listings(
                    days=self.days,
                    exclude_favorites=self.exclude_favorites,
                    exclude_noted=self.exclude_noted,
                )
            finally:
                try:
                    db.close()
                except Exception:
                    pass
            self.completed.emit(int(deleted))
        except Exception as e:
            self.failed.emit(str(e))


class NotificationTestThread(QThread):
    """Thread for testing notifications asynchronously"""
    finished = pyqtSignal(bool, str)

    def __init__(self, notifier_type, **kwargs):
        super().__init__()
        self.notifier_type = notifier_type
        self.kwargs = kwargs

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            if self.notifier_type == NotificationType.TELEGRAM:
                token = str(self.kwargs.get('token') or "")
                chat_id = str(self.kwargs.get('chat_id') or "")
                notifier = TelegramNotifier(
                    token,
                    chat_id
                )
                success = loop.run_until_complete(
                    notifier.send_message("🔔 [테스트] 중고거래 알리미 알림 테스트입니다.")
                )
                if success:
                    self.finished.emit(True, "텔레그램 알림 전송 성공!")
                else:
                    self.finished.emit(False, "알림 전송 실패. 설정(토큰/ID)을 확인하세요.")

            elif self.notifier_type == NotificationType.DISCORD:
                url = str(self.kwargs.get('url') or "")
                notifier = DiscordNotifier(url)
                success = loop.run_until_complete(
                    notifier.send_message("🔔 [테스트] 중고거래 알리미 알림 테스트입니다.")
                )
                if success:
                    self.finished.emit(True, "디스코드 알림 전송 성공!")
                else:
                    self.finished.emit(False, "알림 전송 실패. Webhook URL을 확인하세요.")

            elif self.notifier_type == NotificationType.SLACK:
                url = str(self.kwargs.get('url') or "")
                notifier = SlackNotifier(url)
                success = loop.run_until_complete(
                    notifier.send_message("🔔 [테스트] 중고거래 알리미 알림 테스트입니다.")
                )
                if success:
                    self.finished.emit(True, "슬랙 알림 전송 성공!")
                else:
                    self.finished.emit(False, "알림 전송 실패. Webhook URL을 확인하세요.")

            loop.close()

        except Exception as e:
            self.finished.emit(False, f"오류 발생: {str(e)}")
