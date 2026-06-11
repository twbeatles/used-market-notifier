"""Shared imports for monitor engine mixins."""

import asyncio
import concurrent.futures
import inspect
import logging
from datetime import datetime
from time import perf_counter
from typing import Awaitable, Callable, Optional, cast

from auto_tagger import AutoTagger
from db import DatabaseManager
from models import NotificationType, SearchKeyword
from notifiers import DiscordNotifier, SlackNotifier, TelegramNotifier
from scrapers import (
    BunjangScraper,
    DanggeunScraper,
    Item,
    JoonggonaraScraper,
    PlaywrightBunjangScraper,
    PlaywrightDanggeunScraper,
    PlaywrightJoonggonaraScraper,
    ScraperDependencyUnavailable,
)
from scrapers.marketplace_parsers import evaluate_scrape_quality
from settings_manager import SettingsManager

from .notifications import (
    NotificationDeliveryResult,
    NotificationJob,
    NotificationPolicy,
    NotificationPolicyDecision,
)
from .types import NotifierProtocol, ScraperProtocol, SettingsProvider
