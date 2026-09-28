"""Regression: Fluent SettingsPage resolves MainWindow as its host (ISSUE-003)."""

import os
import shutil
import tempfile
import unittest
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _pyside_fluent_available() -> bool:
    try:
        import qfluentwidgets  # noqa: F401
        from PySide6.QtWidgets import QApplication  # noqa: F401
    except Exception:
        return False
    return True


@unittest.skipUnless(_pyside_fluent_available(), "requires PySide6 + qfluentwidgets")
class SettingsHostTest(unittest.TestCase):
    def setUp(self):
        from PySide6.QtWidgets import QApplication

        from backup_manager import BackupManager
        from gui.main_window import MainWindow
        from settings_manager import SettingsManager

        self._app = QApplication.instance() or QApplication([])
        self._old_cwd = os.getcwd()
        self.tmp = tempfile.mkdtemp(prefix="umn_host_test_")
        os.chdir(self.tmp)  # MainWindow's BackupManager uses a relative backup dir
        self.manager = SettingsManager(settings_path=os.path.join(self.tmp, "settings.json"))
        self.manager.settings.db_path = os.path.join(self.tmp, "listings.db")
        self.manager.settings.auto_backup_enabled = False
        self.manager.settings.auto_start_monitoring = False
        self.manager.save()
        self.window = MainWindow(settings_manager=self.manager)
        self.page = self.window.settings_page
        self.page.backup_manager = BackupManager(os.path.join(self.tmp, "backup"))

    def tearDown(self):
        try:
            self.window.db.close()
        except Exception:
            pass
        self.window.hide()
        self.window.deleteLater()
        os.chdir(self._old_cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_host_resolves_to_main_window(self):
        from gui.settings_panels.host import resolve_host_db, resolve_settings_host

        self.assertIsNot(self.page.parent(), self.window)  # re-parented into the Fluent stack
        self.assertIs(resolve_settings_host(self.page), self.window)
        self.assertIs(resolve_host_db(self.window), self.window.db)
        self.assertIs(self.page._get_parent_db(), self.window.db)

    def test_blocked_sellers_list_and_unblock(self):
        self.window.db.add_seller_filter("nasty_seller", "bunjang", is_blocked=True)
        self.page.load_blocked_sellers()
        self.assertEqual(self.page.seller_table.rowCount(), 1)

        self.page.seller_table.setCurrentCell(0, 0)
        with mock.patch("gui.settings_panels.mixins.seller.QMessageBox") as box:
            box.StandardButton.Yes = object()
            box.question.return_value = box.StandardButton.Yes
            self.page.unblock_seller()
            box.warning.assert_not_called()
        self.assertEqual(self.window.db.get_blocked_sellers(), [])
        self.assertEqual(self.page.seller_table.rowCount(), 0)

    def _prepare_backup_selection(self):
        backup = self.page.backup_manager.create_backup(
            self.manager.settings.db_path, str(self.manager.settings_path)
        )
        self.assertIsNotNone(backup)
        self.page.refresh_backup_list()
        self.page.backup_table.setCurrentCell(0, 0)

    def test_restore_stops_monitoring_first_and_quits_through_host(self):
        self._prepare_backup_selection()
        state = {"active": True, "calls": []}

        def fake_stop(wait=False, timeout_ms=0):
            state["calls"].append(wait)
            state["active"] = False
            return True

        with mock.patch.object(self.window, "is_monitoring_active", lambda: state["active"]), \
                mock.patch.object(self.window, "stop_monitoring", fake_stop), \
                mock.patch.object(self.window, "quit_app") as quit_app, \
                mock.patch("gui.settings_panels.mixins.maintenance.QMessageBox") as box:
            box.StandardButton.Yes = object()
            box.question.return_value = box.StandardButton.Yes
            self.page.restore_selected_backup()

        self.assertEqual(state["calls"], [True])
        quit_app.assert_called_once()
        box.warning.assert_not_called()

    def test_restore_is_refused_when_monitoring_cannot_stop(self):
        self._prepare_backup_selection()
        with mock.patch.object(self.window, "is_monitoring_active", lambda: True), \
                mock.patch.object(self.window, "stop_monitoring", lambda wait=False, timeout_ms=0: False), \
                mock.patch.object(self.page.backup_manager, "restore_backup") as restore, \
                mock.patch("gui.settings_panels.mixins.maintenance.QMessageBox") as box:
            box.StandardButton.Yes = object()
            box.question.return_value = box.StandardButton.Yes
            self.page.restore_selected_backup()

        restore.assert_not_called()
        box.warning.assert_called_once()

    def test_cleanup_asks_and_stops_monitoring(self):
        state = {"active": True, "calls": []}

        def fake_stop(wait=False, timeout_ms=0):
            state["calls"].append(wait)
            state["active"] = False
            return True

        with mock.patch.object(self.window, "is_monitoring_active", lambda: state["active"]), \
                mock.patch.object(self.window, "stop_monitoring", fake_stop), \
                mock.patch("gui.settings_panels.mixins.maintenance.CleanupWorker") as worker, \
                mock.patch("gui.settings_panels.mixins.maintenance.QMessageBox") as box:
            box.StandardButton.Yes = object()
            box.question.return_value = box.StandardButton.Yes
            self.page.run_cleanup_now()

        self.assertEqual(box.question.call_count, 2)  # stop-monitoring prompt + delete confirmation
        self.assertEqual(state["calls"], [True])
        worker.return_value.start.assert_called_once()


if __name__ == "__main__":
    unittest.main()
