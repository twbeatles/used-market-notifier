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


if __name__ == "__main__":
    unittest.main()
