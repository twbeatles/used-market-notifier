"""Mixin module: normalization."""

from typing import Any
from models import (
    AppSettings, SearchKeyword, NotifierConfig,
    NotificationSchedule, NotificationType, ThemeMode, SellerFilter,
    KeywordPreset, TagRule, MessageTemplate
)


class SettingsNormalizationMixin:
    """Normalization behavior."""

    def _mark_normalized(self, field: str, raw_value: Any, default_value: Any) -> None:
        normalized = self.load_recovery_state.setdefault("normalized_fields", [])
        if isinstance(normalized, list):
            normalized.append(field)
        self.logger.warning(
            "Invalid settings field normalized: %s=%r -> %r",
            field,
            raw_value,
            default_value,
        )


    def _as_bool(self, data: dict, key: str, default: bool) -> bool:
        raw = data.get(key, default)
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, str):
            lowered = raw.strip().lower()
            if lowered in ("true", "1", "yes", "y", "on"):
                self._mark_normalized(key, raw, True)
                return True
            if lowered in ("false", "0", "no", "n", "off"):
                self._mark_normalized(key, raw, False)
                return False
        self._mark_normalized(key, raw, default)
        return default


    def _as_int(self, data: dict, key: str, default: int, *, min_value: int, max_value: int | None = None) -> int:
        raw = data.get(key, default)
        try:
            value = int(raw)
        except Exception:
            self._mark_normalized(key, raw, default)
            return default
        if value < min_value or (max_value is not None and value > max_value):
            self._mark_normalized(key, raw, default)
            return default
        if raw != value:
            self._mark_normalized(key, raw, value)
        return value


    def _as_optional_int(self, value: Any, field: str) -> int | None:
        if value in (None, ""):
            return None
        try:
            parsed = int(value)
        except Exception:
            self._mark_normalized(field, value, None)
            return None
        if parsed < 0:
            self._mark_normalized(field, value, None)
            return None
        return parsed


    def _as_str_list(self, value: Any, field: str) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            self._mark_normalized(field, value, [value])
            return [value]
        if not isinstance(value, list):
            self._mark_normalized(field, value, [])
            return []
        result = [str(item).strip() for item in value if str(item).strip()]
        if len(result) != len(value):
            self._mark_normalized(field, value, result)
        return result


    def _as_platforms(self, value: Any, field: str) -> list[str]:
        raw_values = self._as_str_list(value, field)
        result = [platform for platform in raw_values if platform in self.VALID_PLATFORMS]
        if not result:
            result = [str(platform) for platform in self.VALID_PLATFORMS]
            if value != result:
                self._mark_normalized(field, value, result)
        elif result != raw_values:
            self._mark_normalized(field, value, result)
        return result


    def _as_theme(self, value: Any) -> ThemeMode:
        try:
            return ThemeMode(str(value or ThemeMode.DARK.value))
        except Exception:
            self._mark_normalized("theme_mode", value, ThemeMode.DARK.value)
            return ThemeMode.DARK


    def _as_scraper_mode(self, value: Any) -> str:
        mode = str(value or "playwright_primary").strip().lower()
        if mode not in self.VALID_SCRAPER_MODES:
            self._mark_normalized("scraper_mode", value, "playwright_primary")
            return "playwright_primary"
        return mode


    def _normalize_schedule(self, data: Any) -> NotificationSchedule:
        schedule_data = data if isinstance(data, dict) else {}
        if not isinstance(data, dict):
            self._mark_normalized("notification_schedule", data, {})
        days_raw = schedule_data.get("days", [0, 1, 2, 3, 4, 5, 6])
        days: list[int] = []
        if isinstance(days_raw, list):
            for day in days_raw:
                try:
                    parsed = int(day)
                except Exception:
                    continue
                if 0 <= parsed <= 6 and parsed not in days:
                    days.append(parsed)
        if not days:
            days = [0, 1, 2, 3, 4, 5, 6]
            self._mark_normalized("notification_schedule.days", days_raw, days)
        return NotificationSchedule(
            enabled=self._as_bool(schedule_data, "enabled", True),
            start_hour=self._as_int(schedule_data, "start_hour", 0, min_value=0, max_value=23),
            end_hour=self._as_int(schedule_data, "end_hour", 24, min_value=0, max_value=24),
            days=days,
        )
