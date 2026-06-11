# monitor_engine.py
"""Core monitoring engine assembled from focused mixins."""

from .common import *
from .metadata import MetadataEnrichmentMixin
from .notification_runtime import NotificationRuntimeMixin
from .runtime import RuntimeMixin
from .scrapers import ScraperLifecycleMixin
from .search_flow import SearchFlowMixin


class MonitorEngine(
    MetadataEnrichmentMixin,
    ScraperLifecycleMixin,
    NotificationRuntimeMixin,
    SearchFlowMixin,
    RuntimeMixin,
):
    """Core engine for monitoring used marketplaces."""

    SCRAPER_CONCURRENCY = 2
    NOTIFICATION_MAX_RETRIES = 3
    NOTIFICATION_DRAIN_TIMEOUT = 20.0
    METADATA_ENRICHMENT_LIMIT = 10
    DANGGEUN_LOCATION_WARNING = (
        "당근 지역 필터는 현재 best-effort 검색 후 후처리로 동작하며, 요청 지역 정확도는 보장되지 않습니다"
    )

    def __init__(self, settings_manager: SettingsProvider, db: Optional[DatabaseManager] = None):
        self.settings = settings_manager
        self.logger = logging.getLogger("MonitorEngine")
        self.db = db or DatabaseManager(self.settings.settings.db_path)
        self._owns_db = db is None

        self.primary_scrapers: dict[str, ScraperProtocol] = {}
        self.fallback_scrapers: dict[str, ScraperProtocol] = {}
        self.primary_scraper_kind: dict[str, str] = {}
        self.fallback_scraper_kind: dict[str, str] = {}
        # Backward-compatible alias used by some UI paths.
        self.scrapers = self.primary_scrapers
        self.notifiers: list[NotifierProtocol] = []
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self.is_first_run = True  # Skip notifications on initial crawl

        # Thread pool for synchronous scraping (created lazily on start()).
        self._executor: Optional[concurrent.futures.ThreadPoolExecutor] = None

        # Stop/close state for idempotent teardown
        self._resources_closed = False
        self._close_called = False
        self._start_task: Optional[asyncio.Task] = None
        self._stop_event: Optional[asyncio.Event] = None

        # Notification queue worker
        self._notification_queue: Optional[asyncio.Queue] = None
        self._notification_worker_task: Optional[asyncio.Task] = None

        # Auto-tagger for automatic tag detection (optionally from settings.tag_rules)
        self.auto_tagger = self._create_auto_tagger_from_settings()

        # Consecutive empty result tracking per platform
        self._empty_result_counter: dict[str, int] = {}
        self._playwright_runtime_checked = False
        self._playwright_runtime_available = False

        # Per-cycle aggregates (set by run_cycle)
        self._cycle_platform_raw_counts: Optional[dict[str, int]] = None
        self._cycle_platform_attempts: Optional[dict[str, int]] = None
        self._cycle_fallback_counts: Optional[dict[str, int]] = None
        self._cycle_blocked_set: set[tuple[str, Optional[str]]] = set()
        self._cycle_danggeun_location_warning_keys: set[tuple[str, str]] = set()
        self._platform_backoff_until: dict[str, float] = {}
        self._enrichment_cache: dict[tuple[str, str], Item] = {}

        # Callbacks for UI updates
        self.on_new_item: Optional[Callable[[Item], None]] = None
        self.on_price_change: Optional[Callable[[Item, str, str], None]] = None
        self.on_status_update: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
