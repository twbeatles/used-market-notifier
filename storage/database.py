# db.py
"""Database manager composed from storage mixins."""

from .common import *
from .favorites import FavoritesNotesMixin
from .filters import SellerFilterMixin
from .listings import ListingPersistenceMixin
from .maintenance import MaintenanceMixin
from .notifications import NotificationLogMixin
from .schema import SchemaMixin
from .stats import StatisticsMixin


class DatabaseManager(
    SchemaMixin,
    ListingPersistenceMixin,
    StatisticsMixin,
    FavoritesNotesMixin,
    NotificationLogMixin,
    SellerFilterMixin,
    MaintenanceMixin,
):
    """SQLite database manager with price history tracking - Thread Safe."""

    PRICE_PARSE_VERSION = 2
    SCHEMA_VERSION = 3

    def __init__(self, db_path: str = "listings.db"):
        self.db_path = db_path
        # check_same_thread=False allowed but we handle locking manually
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        self.logger = logging.getLogger("DatabaseManager")

        # Stats cache with TTL (reduce redundant queries)
        self._stats_cache = {}
        self._cache_ttl = 30  # 30 seconds cache
        self._cache_time = None

        # Enable WAL mode and other optimizations for better concurrency
        self.conn.execute('PRAGMA foreign_keys=ON')
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.execute('PRAGMA synchronous=NORMAL')  # Faster writes
        self.conn.execute('PRAGMA cache_size=-64000')  # 64MB cache
        self.create_tables()

    def _invalidate_cache(self):
        """Invalidate stats cache on write operations"""
        self._cache_time = None
        self._stats_cache = {}

    def close(self):
        """Close database connection"""
        self.conn.close()
