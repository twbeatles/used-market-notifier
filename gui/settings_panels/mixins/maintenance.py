"""Settings dialog mixin: maintenance."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QLineEdit, QSpinBox, QCheckBox, QLabel,
    QGroupBox, QPushButton, QComboBox, QMessageBox, QFrame,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import os
from db import DatabaseManager
from ..workers import CleanupWorker

class MaintenanceSettingsMixin:
    """Maintenance settings panel behavior."""

    def create_maintenance_tab(self) -> QWidget:
        """Backup/restore + cleanup controls"""
        widget = QWidget()
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Backup group
        backup_group = QGroupBox("💾 백업 / 복원")
        backup_layout = QVBoxLayout(backup_group)
        backup_layout.setSpacing(12)

        self.auto_backup_enabled_check = QCheckBox("자동 백업 사용")
        backup_layout.addWidget(self.auto_backup_enabled_check)

        backup_form = QFormLayout()
        backup_form.setSpacing(12)

        self.auto_backup_interval_spin = QSpinBox()
        self.auto_backup_interval_spin.setRange(1, 365)
        self.auto_backup_interval_spin.setSuffix(" 일")
        self.auto_backup_interval_spin.setMinimumHeight(34)
        backup_form.addRow("백업 주기", self.auto_backup_interval_spin)

        self.backup_keep_count_spin = QSpinBox()
        self.backup_keep_count_spin.setRange(1, 100)
        self.backup_keep_count_spin.setSuffix(" 개")
        self.backup_keep_count_spin.setMinimumHeight(34)
        backup_form.addRow("보관 개수", self.backup_keep_count_spin)

        backup_layout.addLayout(backup_form)

        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(3)
        self.backup_table.setHorizontalHeaderLabels(["파일", "날짜", "크기"])
        backup_h_header = self.backup_table.horizontalHeader()
        if backup_h_header is not None:
            backup_h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.backup_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.backup_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        backup_layout.addWidget(self.backup_table)

        backup_btns = QHBoxLayout()
        backup_btns.addStretch()

        create_btn = QPushButton("지금 백업 생성")
        create_btn.clicked.connect(self.create_backup_now)
        backup_btns.addWidget(create_btn)

        open_btn = QPushButton("백업 폴더 열기")
        open_btn.clicked.connect(self.open_backup_folder)
        backup_btns.addWidget(open_btn)

        restore_btn = QPushButton("선택 백업 복원")
        restore_btn.clicked.connect(self.restore_selected_backup)
        backup_btns.addWidget(restore_btn)

        backup_layout.addLayout(backup_btns)

        # Cleanup group
        cleanup_group = QGroupBox("🧹 자동 클린업")
        cleanup_layout = QVBoxLayout(cleanup_group)
        cleanup_layout.setSpacing(12)

        self.auto_cleanup_enabled_check = QCheckBox("앱 시작 시 1회 오래된 매물 정리 실행")
        cleanup_layout.addWidget(self.auto_cleanup_enabled_check)

        cleanup_form = QFormLayout()
        cleanup_form.setSpacing(12)

        self.cleanup_days_spin = QSpinBox()
        self.cleanup_days_spin.setRange(1, 3650)
        self.cleanup_days_spin.setSuffix(" 일 이전")
        self.cleanup_days_spin.setMinimumHeight(34)
        cleanup_form.addRow("삭제 기준", self.cleanup_days_spin)

        self.cleanup_exclude_favorites_check = QCheckBox("즐겨찾기 제외")
        cleanup_form.addRow("", self.cleanup_exclude_favorites_check)

        self.cleanup_exclude_noted_check = QCheckBox("사용자 메모/상태가 있는 항목 제외")
        cleanup_form.addRow("", self.cleanup_exclude_noted_check)

        cleanup_layout.addLayout(cleanup_form)

        preview_row = QHBoxLayout()
        self.cleanup_preview_label = QLabel("미리보기: -")
        self.cleanup_preview_label.setStyleSheet("color: #a6e3a1;")
        preview_row.addWidget(self.cleanup_preview_label)
        preview_row.addStretch()

        refresh_preview_btn = QPushButton("미리보기 새로고침")
        refresh_preview_btn.clicked.connect(self.refresh_cleanup_preview)
        preview_row.addWidget(refresh_preview_btn)

        cleanup_layout.addLayout(preview_row)

        cleanup_btns = QHBoxLayout()
        cleanup_btns.addStretch()

        self.run_cleanup_btn = QPushButton("지금 정리 실행")
        self.run_cleanup_btn.clicked.connect(self.run_cleanup_now)
        cleanup_btns.addWidget(self.run_cleanup_btn)

        cleanup_layout.addLayout(cleanup_btns)

        layout.addWidget(backup_group)
        layout.addWidget(cleanup_group)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)
        return widget


    def refresh_backup_list(self):
        backups = self.backup_manager.list_backups()
        self.backup_table.setRowCount(len(backups))
        for i, b in enumerate(backups):
            item0 = QTableWidgetItem(b.get("filename", ""))
            item0.setData(Qt.ItemDataRole.UserRole, b.get("path", ""))
            self.backup_table.setItem(i, 0, item0)
            self.backup_table.setItem(i, 1, QTableWidgetItem(b.get("date", "")))
            self.backup_table.setItem(i, 2, QTableWidgetItem(b.get("size_str", "")))


    def create_backup_now(self):
        s = self.settings.settings
        settings_path = str(getattr(self.settings, "settings_path", "settings.json"))
        backup_path = self.backup_manager.create_backup(
            db_path=getattr(s, "db_path", "listings.db"),
            settings_path=settings_path,
        )
        if not backup_path:
            QMessageBox.warning(self, "실패", "백업 생성에 실패했습니다. 로그를 확인하세요.")
            return

        try:
            self.backup_manager.cleanup_old_backups(keep_count=self.backup_keep_count_spin.value())
        except Exception:
            pass

        self.refresh_backup_list()
        QMessageBox.information(self, "완료", f"백업이 생성되었습니다.\n\n{backup_path}")


    def open_backup_folder(self):
        try:
            os.startfile(str(self.backup_manager.backup_dir.resolve()))
        except Exception as e:
            QMessageBox.warning(self, "오류", f"백업 폴더를 열 수 없습니다: {e}")


    def restore_selected_backup(self):
        row = self.backup_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "알림", "복원할 백업을 선택하세요.")
            return

        item = self.backup_table.item(row, 0)
        backup_path = item.data(Qt.ItemDataRole.UserRole) if item else ""
        if not backup_path:
            QMessageBox.warning(self, "오류", "백업 경로를 찾을 수 없습니다.")
            return

        if QMessageBox.question(
            self,
            "주의",
            "선택한 백업으로 DB/설정 파일을 덮어씁니다.\n"
            "복원 후 앱은 종료됩니다.\n\n계속하시겠습니까?",
        ) != QMessageBox.StandardButton.Yes:
            return

        # Stop monitoring if running and close DB connection for safety.
        parent = self.parent()
        try:
            monitor_thread = getattr(parent, "monitor_thread", None) if parent is not None else None
            is_running = getattr(monitor_thread, "isRunning", None)
            if callable(is_running) and is_running():
                stop_monitoring = getattr(parent, "stop_monitoring", None)
                if callable(stop_monitoring):
                    stop_monitoring()
        except Exception:
            pass

        # Do not forcibly close parent.engine.db here: the app is about to quit,
        # and the engine may be using a shared UI DB connection.

        s = self.settings.settings
        settings_path = str(getattr(self.settings, "settings_path", "settings.json"))
        ok = self.backup_manager.restore_backup(
            backup_file=str(backup_path),
            db_path=getattr(s, "db_path", "listings.db"),
            settings_path=settings_path,
        )
        if not ok:
            QMessageBox.warning(self, "실패", "복원에 실패했습니다. 로그를 확인하세요.")
            return

        QMessageBox.information(self, "완료", "복원이 완료되었습니다.\n데이터 일관성을 위해 앱을 종료합니다.")
        QApplication.quit()


    def refresh_cleanup_preview(self):
        try:
            from db import DatabaseManager
            s = self.settings.settings
            db = DatabaseManager(getattr(s, "db_path", "listings.db"))
            try:
                preview = db.get_cleanup_preview(
                    days=self.cleanup_days_spin.value(),
                    exclude_favorites=self.cleanup_exclude_favorites_check.isChecked(),
                    exclude_noted=self.cleanup_exclude_noted_check.isChecked(),
                )
            finally:
                try:
                    db.close()
                except Exception:
                    pass

            self.cleanup_preview_label.setText(
                f"미리보기: {preview.get('delete_count', 0):,} / {preview.get('total_count', 0):,} 삭제 예정"
            )
        except Exception as e:
            self.cleanup_preview_label.setText(f"미리보기 실패: {e}")


    def run_cleanup_now(self):
        parent = self.parent()
        try:
            monitor_thread = getattr(parent, "monitor_thread", None) if parent is not None else None
            is_running = getattr(monitor_thread, "isRunning", None)
            if callable(is_running) and is_running():
                if QMessageBox.question(
                    self,
                    "확인",
                    "모니터링이 실행 중입니다.\n정리 작업을 위해 모니터링을 중지할까요?",
                ) == QMessageBox.StandardButton.Yes:
                    stop_monitoring = getattr(parent, "stop_monitoring", None)
                    if callable(stop_monitoring):
                        stop_monitoring()
                else:
                    return
        except Exception:
            pass

        if QMessageBox.question(
            self,
            "확인",
            "지금 정리를 실행하면 조건에 맞는 오래된 매물이 DB에서 삭제됩니다.\n계속하시겠습니까?",
        ) != QMessageBox.StandardButton.Yes:
            return

        self.run_cleanup_btn.setEnabled(False)
        self.cleanup_preview_label.setText("정리 실행 중...")

        s = self.settings.settings
        self._cleanup_thread = CleanupWorker(
            db_path=getattr(s, "db_path", "listings.db"),
            days=self.cleanup_days_spin.value(),
            exclude_favorites=self.cleanup_exclude_favorites_check.isChecked(),
            exclude_noted=self.cleanup_exclude_noted_check.isChecked(),
        )
        self._cleanup_thread.completed.connect(self._on_cleanup_done)
        self._cleanup_thread.failed.connect(self._on_cleanup_failed)
        self._cleanup_thread.start()


    def _on_cleanup_done(self, deleted_count: int):
        self.run_cleanup_btn.setEnabled(True)
        self.refresh_cleanup_preview()
        QMessageBox.information(self, "완료", f"정리가 완료되었습니다.\n삭제된 항목: {deleted_count:,}개")

        # Best-effort refresh in main UI if available.
        parent = self.parent()
        try:
            stats_widget = getattr(parent, "stats_widget", None) if parent is not None else None
            listings_widget = getattr(parent, "listings_widget", None) if parent is not None else None
            refresh_stats = getattr(stats_widget, "refresh_stats", None)
            refresh_listings = getattr(listings_widget, "refresh_listings", None)
            if callable(refresh_stats):
                refresh_stats()
            if callable(refresh_listings):
                refresh_listings()
        except Exception:
            pass


    def _on_cleanup_failed(self, error: str):
        self.run_cleanup_btn.setEnabled(True)
        self.cleanup_preview_label.setText(f"정리 실패: {error}")
        QMessageBox.warning(self, "실패", f"정리 작업 실패: {error}")
