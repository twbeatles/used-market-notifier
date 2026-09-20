# pyright: reportAttributeAccessIssue=false
"""NotificationRuntimeMixin for MonitorEngine.

Canonical implementations live in :mod:`engine.notification_sections`
(one concern per module: channel setup, policy helpers, delivery,
worker/retry, system fan-out, public queue API). This module only
composes them so the ``MonitorEngine`` MRO stays intact.
"""

from .common import *
from .notification_sections import (
    NotificationChannelsMixin,
    NotificationDeliveryMixin,
    NotificationPolicyMixin,
    NotificationQueueMixin,
    NotificationSystemMixin,
    NotificationWorkerMixin,
)


class NotificationRuntimeMixin(
    NotificationChannelsMixin,
    NotificationPolicyMixin,
    NotificationDeliveryMixin,
    NotificationWorkerMixin,
    NotificationSystemMixin,
    NotificationQueueMixin,
):
    """Notification queue/delivery behavior composed from section mixins."""
