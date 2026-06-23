"""Settings dialog mixin: auto_tagging."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QLineEdit, QSpinBox, QCheckBox, QLabel,
    QGroupBox, QPushButton, QComboBox, QMessageBox, QFrame,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from models import TagRule
from auto_tagger import AutoTagger
from ..editors import TagRuleEditDialog

class AutoTaggingSettingsMixin:
    """Auto Tagging settings panel behavior."""

    def create_auto_tagging_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        self.auto_tagging_enabled_check = QCheckBox("자동 태깅 사용")
        self.auto_tagging_enabled_check.setToolTip("끄면 자동 태그 생성/저장이 동작하지 않습니다.")
        self.auto_tagging_enabled_check.toggled.connect(self._on_auto_tagging_toggled)
        layout.addWidget(self.auto_tagging_enabled_check)

        desc = QLabel("🏷️ 제목 키워드에 따라 자동으로 태그를 부여합니다. (모니터링 재시작 시 적용)")
        desc.setStyleSheet("color: #89b4fa;")
        layout.addWidget(desc)

        self.tag_rules_table = QTableWidget()
        self.tag_rules_table.setColumnCount(5)
        self.tag_rules_table.setHorizontalHeaderLabels(["사용", "태그", "아이콘", "색상", "키워드"])
        tag_h_header = self.tag_rules_table.horizontalHeader()
        if tag_h_header is not None:
            tag_h_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tag_rules_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tag_rules_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tag_rules_table)

        btns = QHBoxLayout()
        btns.addStretch()

        self.tag_add_btn = QPushButton("추가")
        self.tag_add_btn.clicked.connect(self.add_tag_rule)
        btns.addWidget(self.tag_add_btn)

        self.tag_edit_btn = QPushButton("편집")
        self.tag_edit_btn.clicked.connect(self.edit_tag_rule)
        btns.addWidget(self.tag_edit_btn)

        self.tag_del_btn = QPushButton("삭제")
        self.tag_del_btn.clicked.connect(self.delete_tag_rule)
        btns.addWidget(self.tag_del_btn)

        self.tag_reset_btn = QPushButton("기본값으로 초기화")
        self.tag_reset_btn.clicked.connect(self.reset_tag_rules_default)
        btns.addWidget(self.tag_reset_btn)

        layout.addLayout(btns)
        return widget


    def _on_auto_tagging_toggled(self, enabled: bool):
        # Disable editing UI when feature is off (rules are still kept/saved).
        try:
            self.tag_rules_table.setEnabled(enabled)
            self.tag_add_btn.setEnabled(enabled)
            self.tag_edit_btn.setEnabled(enabled)
            self.tag_del_btn.setEnabled(enabled)
            self.tag_reset_btn.setEnabled(enabled)
        except Exception:
            pass


    def _refresh_tag_rules_table(self):
        if not hasattr(self, "tag_rules_table"):
            return
        rules = self._tag_rules or []
        self.tag_rules_table.setRowCount(len(rules))
        for i, r in enumerate(rules):
            enabled_item = QTableWidgetItem("")
            enabled_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable
            )
            enabled_item.setCheckState(Qt.CheckState.Checked if getattr(r, "enabled", True) else Qt.CheckState.Unchecked)
            self.tag_rules_table.setItem(i, 0, enabled_item)

            self.tag_rules_table.setItem(i, 1, QTableWidgetItem(getattr(r, "tag_name", "")))
            self.tag_rules_table.setItem(i, 2, QTableWidgetItem(getattr(r, "icon", "")))
            self.tag_rules_table.setItem(i, 3, QTableWidgetItem(getattr(r, "color", "")))

            keywords = getattr(r, "keywords", []) or []
            self.tag_rules_table.setItem(i, 4, QTableWidgetItem(", ".join(keywords)))


    def _selected_tag_rule_index(self) -> int:
        row = self.tag_rules_table.currentRow()
        return row if row >= 0 else -1


    def add_tag_rule(self):
        dlg = TagRuleEditDialog(parent=self)
        if dlg.exec():
            self._tag_rules.append(dlg.get_rule())
            self._refresh_tag_rules_table()


    def edit_tag_rule(self):
        idx = self._selected_tag_rule_index()
        if idx < 0 or idx >= len(self._tag_rules):
            QMessageBox.information(self, "알림", "편집할 규칙을 선택하세요.")
            return
        dlg = TagRuleEditDialog(rule=self._tag_rules[idx], parent=self)
        if dlg.exec():
            self._tag_rules[idx] = dlg.get_rule()
            self._refresh_tag_rules_table()


    def delete_tag_rule(self):
        idx = self._selected_tag_rule_index()
        if idx < 0 or idx >= len(self._tag_rules):
            QMessageBox.information(self, "알림", "삭제할 규칙을 선택하세요.")
            return
        if QMessageBox.question(self, "확인", "선택한 규칙을 삭제하시겠습니까?") != QMessageBox.StandardButton.Yes:
            return
        self._tag_rules.pop(idx)
        self._refresh_tag_rules_table()


    def reset_tag_rules_default(self):
        if QMessageBox.question(self, "확인", "기본 태그 규칙으로 초기화하시겠습니까?") != QMessageBox.StandardButton.Yes:
            return
        self._tag_rules = [
            TagRule(
                tag_name=r.get("tag_name", ""),
                keywords=list(r.get("keywords", [])),
                color=r.get("color", "#89b4fa"),
                icon=r.get("icon", "🏷️"),
                enabled=True,
            )
            for r in AutoTagger.DEFAULT_RULES
        ]
        self._refresh_tag_rules_table()
