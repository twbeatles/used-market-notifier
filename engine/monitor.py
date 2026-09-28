# monitor_engine.py
"""Core monitoring engine assembled from focused mixins."""

from .common import *
from .metadata import MetadataEnrichmentMixin
from .notification_runtime import NotificationRuntimeMixin
from .runtime import RuntimeMixin
from .scrapers import ScraperLifecycleMixin
from .search_flow import SearchFlowMixin


class MonitorEngine(
    MetadataEnrichmentMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    ScraperLifecycleMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    NotificationRuntimeMixin,
    SearchFlowMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
    RuntimeMixin,  # pyright: ignore[reportGeneralTypeIssues]  # static-only cycle; runtime base is object
):
    """Core engine for monitoring used marketplaces."""

    SCRAPER_CONCURRENCY = 2
    NOTIFICATION_MAX_RETRIES = 3
    NOTIFICATION_DRAIN_TIMEOUT = 20.0
    METADATA_ENRICHMENT_LIMIT = 10
    # 키워드·플랫폼·사이클당 개별 알림 상한. 초과분은 요약 알림 1건으로 보낸다.
    NOTIFICATION_BURST_LIMIT = 15
    # 폴백 스크래퍼 생성 실패 시 재시도를 멈추는 시간(초)
    FALLBACK_RETRY_COOLDOWN_SECONDS = 600.0
    DANGGEUN_LOCATION_WARNING = (
        "당근 검색 지역을 적용합니다. 같은 지명은 서울 동을 우선하고, "
        "지역 확인에 실패하면 접속 지역으로 검색합니다. "
        "키워드에 적은 지역은 매물 지역명 필터로도 사용됩니다"
    )

    def __init__(
        self,
        settings_manager: SettingsProvider,
        db: Optional[DatabaseManager] = None,
        suppress_initial_notifications: bool = True,
    ):
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
        # 프로세스 첫 엔진의 첫 사이클은 알림을 건너뛴다(앱 실행 중 재시작은 False로 생성).
        self.is_first_run = bool(suppress_initial_notifications)

        # Thread pool for synchronous scraping (created lazily on start()).
        self._executor: Optional[concurrent.futures.ThreadPoolExecutor] = None

        # Stop/close state for idempotent teardown
        self._resources_closed = False
        self._close_called = False
        self._start_task: Optional[asyncio.Task] = None
        self._stop_event: Optional[asyncio.Event] = None
        self._stop_pending = False

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
        # 폴백 지연 생성: 플랫폼별 남은 엔진 후보와 생성 실패 쿨다운
        self._fallback_candidates: dict[str, list[str]] = {}
        self._fallback_retry_after: dict[str, float] = {}
        # 사용자 지정 검색 간격 판정용 (키워드 설정 서명 -> monotonic 시각)
        self._keyword_last_run: dict[str, float] = {}

        # Callbacks for UI updates
        self.on_new_item: Optional[Callable[[Item], None]] = None
        self.on_price_change: Optional[Callable[[Item, str, str], None]] = None
        self.on_status_update: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
