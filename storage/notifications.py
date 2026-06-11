# pyright: reportAttributeAccessIssue=false
"""NotificationLogMixin for DatabaseManager."""

from .common import *


class NotificationLogMixin:
    def log_notification(self, listing_id: int, notification_type: str, message: str):
        """Log a sent notification"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO notification_log (listing_id, notification_type, message_preview)
                VALUES (?, ?, ?)
            ''', (listing_id, notification_type, message[:200]))  # store preview
            self.conn.commit()
            self._invalidate_cache()

    def log_notification_delivery(
        self,
        listing_id: int,
        notification_type: str,
        status: str,
        attempt: int = 1,
        error_message: str | None = None,
        rate_limited: bool = False,
    ) -> None:
        """Log delivery attempt results for operational visibility."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                '''
                INSERT INTO notification_delivery_log
                (listing_id, notification_type, status, attempt, error_message, rate_limited)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (
                    listing_id,
                    notification_type,
                    status,
                    max(1, int(attempt)),
                    (error_message or "")[:500] or None,
                    1 if rate_limited else 0,
                ),
            )
            self.conn.commit()
            self._invalidate_cache()

    def get_notification_logs(self, limit: int = 50, offset: int = 0) -> list:
        """Get notification logs"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT nl.*, l.title, l.platform, l.price, l.url
                FROM notification_log nl
                JOIN listings l ON nl.listing_id = l.id
                ORDER BY nl.sent_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    def get_notification_delivery_summary(self, days: int = 7) -> dict[str, dict[str, Any]]:
        """Summarize delivery success/failure and last events per channel."""
        with self.lock:
            cursor = self.conn.cursor()
            channels = ("telegram", "discord", "slack")
            summary: dict[str, dict[str, Any]] = {
                channel: {
                    "success_count": 0,
                    "failed_count": 0,
                    "success_rate": 0.0,
                    "last_success_at": None,
                    "last_failure_at": None,
                    "last_failure_message": None,
                    "last_rate_limited_at": None,
                }
                for channel in channels
            }

            cursor.execute(
                '''
                SELECT
                    notification_type,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count,
                    MAX(CASE WHEN status = 'success' THEN sent_at END) AS last_success_at,
                    MAX(CASE WHEN status = 'failed' THEN sent_at END) AS last_failure_at,
                    MAX(CASE WHEN rate_limited = 1 THEN sent_at END) AS last_rate_limited_at
                FROM notification_delivery_log
                WHERE sent_at >= datetime('now', ?)
                GROUP BY notification_type
                ''',
                (f'-{days} days',),
            )
            for row in cursor.fetchall():
                channel = str(row["notification_type"] or "")
                if channel not in summary:
                    continue
                success_count = int(row["success_count"] or 0)
                failed_count = int(row["failed_count"] or 0)
                total = success_count + failed_count
                summary[channel].update(
                    {
                        "success_count": success_count,
                        "failed_count": failed_count,
                        "success_rate": round((success_count / total) * 100.0, 1) if total else 0.0,
                        "last_success_at": row["last_success_at"],
                        "last_failure_at": row["last_failure_at"],
                        "last_rate_limited_at": row["last_rate_limited_at"],
                    }
                )

            for channel in channels:
                cursor.execute(
                    '''
                    SELECT error_message
                    FROM notification_delivery_log
                    WHERE notification_type = ?
                      AND status = 'failed'
                      AND sent_at >= datetime('now', ?)
                    ORDER BY sent_at DESC
                    LIMIT 1
                    ''',
                    (channel, f'-{days} days'),
                )
                row = cursor.fetchone()
                summary[channel]["last_failure_message"] = row["error_message"] if row else None

            return summary
