"""Regression tests for the SOLID package-split refactor.

Each split keeps its previous public surface intact:
``models``, ``message_templates``, ``auto_tagger`` (file -> package),
``backup.manager`` / ``storage.stats`` / ``engine.notification_runtime`` /
``gui.main.window`` / ``gui.theme.dark`` (module -> section subpackage).
"""

import unittest


class TestModelsPackage(unittest.TestCase):
    def test_public_surface_preserved(self):
        import models

        expected = [
            "AppSettings", "FavoriteItem", "Item", "KeywordPreset",
            "MessageTemplate", "NotificationLog", "NotificationSchedule",
            "NotificationType", "NotifierConfig", "Platform", "SaleStatus",
            "SearchKeyword", "SellerFilter", "TagRule", "ThemeMode",
        ]
        for name in expected:
            self.assertTrue(hasattr(models, name), f"models.{name} missing")
            self.assertIn(name, models.__all__)

    def test_behavior_preserved(self):
        from models import Item, SearchKeyword

        item = Item(platform="danggeun", article_id="1", title="아이폰",
                    price="100,000원", link="http://x", keyword="아이폰",
                    location="강남")
        kw = SearchKeyword(keyword="아이폰", location="강남")
        self.assertTrue(kw.matches(item))
        self.assertEqual(item.parse_price(), 100000)

        strict = SearchKeyword(keyword="아이폰", location="강남")
        no_loc = Item(platform="danggeun", article_id="2", title="아이폰",
                      price="100,000원", link="http://y", keyword="아이폰")
        self.assertFalse(strict.matches_location(no_loc))


class TestMessageTemplatesPackage(unittest.TestCase):
    def test_defaults_and_render(self):
        from message_templates import MessageTemplateManager

        mgr = MessageTemplateManager()
        self.assertEqual(len(mgr.get_templates()), 7)
        rendered = mgr.render_template("기본 문의", {"title": "아이폰"})
        self.assertIsNotNone(rendered)
        self.assertIn("아이폰", rendered or "")

    def test_normalize_models_and_dicts(self):
        from models import MessageTemplate as ModelTemplate
        from message_templates import MessageTemplate, MessageTemplateManager

        mgr = MessageTemplateManager(custom_templates=[
            ModelTemplate(name="m", content="hi {title}", platform="all"),
            {"name": "d", "content": "hello {title}", "platform": "bunjang"},
            MessageTemplate(name="n", content="yo {title}", platform="all"),
        ])
        self.assertEqual(len(mgr.get_templates()), 3)
        self.assertEqual(
            mgr.render_template("m", {"title": "T"}), "hi T")
        self.assertEqual(len(mgr.get_templates(platform="danggeun")), 2)

    def test_clipboard_and_context_helpers(self):
        from message_templates import MessageTemplateManager

        self.assertTrue(callable(MessageTemplateManager.copy_to_clipboard))
        ctx = MessageTemplateManager().create_context_from_listing(
            {"title": "T", "price": "P", "seller": "S",
             "location": "L", "platform": "danggeun"},
            target_price=1000,
        )
        self.assertEqual(ctx["platform"], "당근마켓")
        self.assertEqual(ctx["target_price"], "1,000원")


class TestAutoTaggerPackage(unittest.TestCase):
    def test_rules_and_analysis(self):
        from auto_tagger import AutoTagger, TagResult, auto_tag

        self.assertEqual(len(AutoTagger.DEFAULT_RULES), 8)
        tagger = AutoTagger()
        self.assertEqual(
            tagger.analyze("맥북 프로 M2 A급 풀박스 정품"),
            ["A급", "풀박스", "정품"],
        )
        detailed = tagger.analyze_detailed("아이폰 급처")
        self.assertTrue(all(isinstance(t, TagResult) for t in detailed))
        self.assertEqual(auto_tag("아이폰 급처"), ["급처"])

    def test_store_and_display(self):
        from auto_tagger import AutoTagger

        tagger = AutoTagger()
        tagger.add_rule("테스트", ["테스트키워드"])
        self.assertIn("테스트", tagger.analyze("테스트키워드 매물"))
        html = tagger.format_tags_html(["A급"])
        self.assertIn("A급", html)
        tagger.remove_rule("테스트")
        self.assertNotIn("테스트", tagger.analyze("테스트키워드 매물"))


class TestBackupSplit(unittest.TestCase):
    def test_surface_preserved(self):
        from backup_manager import BackupManager

        for name in ("create_backup", "restore_backup", "list_backups",
                     "auto_backup_if_needed", "cleanup_old_backups"):
            self.assertTrue(hasattr(BackupManager, name), name)
        self.assertEqual(BackupManager._safe_member_basename("a.zip"), "a.zip")
        self.assertIsNone(BackupManager._safe_member_basename("../x"))

    def test_helpers_match_manager(self):
        from backup import path_safety, size_format
        from backup_manager import BackupManager

        self.assertEqual(
            BackupManager._safe_member_basename("ok.zip"),
            path_safety.safe_member_basename("ok.zip"),
        )
        mgr = BackupManager.__new__(BackupManager)
        self.assertEqual(mgr._format_size(2048), size_format.format_size(2048))


class TestThemeSplit(unittest.TestCase):
    def test_dark_style_reassembled(self):
        from gui.styles import DARK_STYLE, LIGHT_STYLE
        from gui.theme import dark_sections

        parts = [getattr(dark_sections, name) for name in dark_sections.__all__]
        self.assertEqual("".join(parts), DARK_STYLE)
        for selector in ("QPushButton", "QTabBar::tab", "QScrollBar",
                         "QMenu", "QSlider", "QSpinBox", "glassCard"):
            self.assertIn(selector, DARK_STYLE)
        self.assertTrue(LIGHT_STYLE)


class TestMainWindowSplit(unittest.TestCase):
    def test_method_surface_preserved(self):
        from gui.main.window import MainWindow

        expected = [
            "setup_ui", "create_header", "setup_tray", "setup_shortcuts",
            "open_add_keyword", "focus_listings_search", "show_shortcuts_help",
            "_run_startup_maintenance", "_on_startup_cleanup_done",
            "_on_startup_cleanup_failed", "_check_auto_backup",
            "_show_settings_recovery_notice", "_mark_live_data_dirty",
            "_flush_live_data_refresh", "_on_tab_changed",
            "refresh_current_tab", "toggle_monitoring", "start_monitoring",
            "on_monitor_finished", "stop_monitoring", "update_ui_state",
            "on_status_update", "on_new_item", "on_price_change",
            "on_error", "open_settings", "apply_theme",
            "_detect_system_dark_mode", "show_window", "quit_app",
            "closeEvent",
        ]
        missing = [name for name in expected if not hasattr(MainWindow, name)]
        self.assertEqual(missing, [])


class TestEngineStorageSplit(unittest.TestCase):
    def test_engine_surface_preserved(self):
        from monitor_engine import MonitorEngine

        for name in ("initialize_notifiers", "send_notifications",
                     "_notification_worker", "_deliver_notification_channels",
                     "_send_system_message", "_notification_policy",
                     "search_keyword", "run_cycle", "start", "stop"):
            self.assertTrue(hasattr(MonitorEngine, name), name)

    def test_storage_surface_preserved(self):
        from db import DatabaseManager

        for name in ("record_search_stats", "get_dashboard_snapshot",
                     "get_daily_stats", "get_price_changes",
                     "get_recent_listings", "get_status_counts",
                     "get_status_history", "add_listing",
                     "get_total_listings", "get_listings_by_keyword"):
            self.assertTrue(hasattr(DatabaseManager, name), name)


if __name__ == "__main__":
    unittest.main()
