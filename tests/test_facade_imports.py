import unittest


class TestFacadeImports(unittest.TestCase):
    def test_legacy_core_imports_still_work(self):
        from db import DatabaseManager
        from monitor_engine import (
            MonitorEngine,
            NotificationDeliveryResult,
            NotificationJob,
            NotificationPolicy,
            NotificationPolicyDecision,
            NotifierProtocol,
            ScraperProtocol,
            SettingsProvider,
        )
        from settings_manager import SettingsManager
        from app_settings import SETTINGS_FILE
        from app_settings.serialization import SettingsSerializationMixin
        from app_settings.recovery import SettingsRecoveryMixin
        from app_settings.presets import PresetSettingsMixin

        self.assertTrue(DatabaseManager)
        self.assertTrue(MonitorEngine)
        self.assertTrue(NotificationJob)
        self.assertTrue(NotificationDeliveryResult)
        self.assertTrue(NotificationPolicy)
        self.assertTrue(NotificationPolicyDecision)
        self.assertTrue(SettingsProvider)
        self.assertTrue(ScraperProtocol)
        self.assertTrue(NotifierProtocol)
        self.assertTrue(SettingsManager)
        self.assertEqual(SETTINGS_FILE, "settings.json")
        self.assertTrue(SettingsSerializationMixin)
        self.assertTrue(SettingsRecoveryMixin)
        self.assertTrue(PresetSettingsMixin)

    def test_legacy_parser_imports_still_work(self):
        from scrapers import marketplace_parsers as parsers

        expected = [
            "HtmlAnchorSnapshot",
            "HtmlDocumentSnapshot",
            "BunjangCardParseResult",
            "parse_html_snapshot",
            "normalize_whitespace",
            "normalize_multiline_text",
            "normalize_price_text",
            "looks_like_time_line",
            "is_strict_price_line",
            "is_count_or_metric_line",
            "is_malformed_listing_title",
            "normalize_location_value",
            "extract_label_value",
            "extract_location_from_text",
            "extract_profile_name_from_aria_label",
            "pick_seller_candidate",
            "merge_item_metadata",
            "normalize_sale_status",
            "parse_bunjang_detail_payload",
            "normalize_url_for_match",
            "validate_platform_url",
            "extract_bunjang_product_id",
            "parse_bunjang_card_text",
            "parse_bunjang_search_items",
            "extract_numeric_article_id",
            "is_valid_joonggonara_title",
            "classify_joonggonara_candidate",
            "evaluate_scrape_quality",
            "parse_joonggonara_search_items",
            "parse_joonggonara_detail_text",
        ]

        missing = [name for name in expected if not hasattr(parsers, name)]
        self.assertEqual(missing, [])

    def test_legacy_gui_imports_still_work(self):
        from gui.keyword_manager import KeywordCard, KeywordEditDialog, KeywordManagerWidget
        from gui.listings_widget import ListingsWidget
        from gui.settings_dialog import (
            CleanupWorker,
            MessageTemplateEditDialog,
            NotificationTestThread,
            SettingsDialog,
            TagRuleEditDialog,
        )
        from gui.stats_widget import StatsWidget
        from gui.main_window import MainWindow, MaintenanceCleanupThread, MonitorThread
        from gui.styles import CATPPUCCIN_MOCHA, DARK_STYLE, LIGHT_STYLE, PLATFORM_INFO
        from gui.components import GlassCard, PulsingDot, StatCard
        from backup_manager import BackupManager
        from gui.export_dialog import ExportDialog
        from gui.compare_dialog import CompareDialog
        from gui.favorites_widget import FavoritesEditDialog, FavoritesWidget
        from scrapers.playwright_base import PlaywrightScraper, async_retry

        self.assertTrue(KeywordCard)
        self.assertTrue(KeywordEditDialog)
        self.assertTrue(KeywordManagerWidget)
        self.assertTrue(ListingsWidget)
        self.assertTrue(SettingsDialog)
        self.assertTrue(CleanupWorker)
        self.assertTrue(TagRuleEditDialog)
        self.assertTrue(MessageTemplateEditDialog)
        self.assertTrue(NotificationTestThread)
        self.assertTrue(StatsWidget)
        self.assertTrue(MainWindow)
        self.assertTrue(MonitorThread)
        self.assertTrue(MaintenanceCleanupThread)
        self.assertTrue(DARK_STYLE)
        self.assertTrue(LIGHT_STYLE)
        self.assertTrue(CATPPUCCIN_MOCHA)
        self.assertTrue(PLATFORM_INFO)
        self.assertTrue(GlassCard)
        self.assertTrue(PulsingDot)
        self.assertTrue(StatCard)
        self.assertTrue(BackupManager)
        self.assertTrue(ExportDialog)
        self.assertTrue(CompareDialog)
        self.assertTrue(FavoritesEditDialog)
        self.assertTrue(FavoritesWidget)
        self.assertTrue(PlaywrightScraper)
        self.assertTrue(async_retry)


if __name__ == "__main__":
    unittest.main()
