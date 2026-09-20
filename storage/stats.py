# pyright: reportAttributeAccessIssue=false
"""StatisticsMixin for DatabaseManager.

Canonical query implementations live in :mod:`storage.stats_sections`
(one concern per module: recording, read queries, price history, daily
volumes, dashboard snapshot). This module only composes them so the
``DatabaseManager`` MRO and every existing call site stay intact.
"""

from .common import *
from .stats_sections import (
    StatsDailyMixin,
    StatsDashboardMixin,
    StatsPriceMixin,
    StatsQueryMixin,
    StatsRecordMixin,
)


class StatisticsMixin(
    StatsRecordMixin,
    StatsQueryMixin,
    StatsPriceMixin,
    StatsDailyMixin,
    StatsDashboardMixin,
):
    """Statistics queries composed from focused section mixins."""
