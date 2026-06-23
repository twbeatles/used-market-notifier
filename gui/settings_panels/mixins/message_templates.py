"""Settings dialog mixin: message_templates."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QLineEdit, QSpinBox, QCheckBox, QLabel,
    QGroupBox, QPushButton, QComboBox, QMessageBox, QFrame,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from models import MessageTemplate
from message_templates import MessageTemplateManager
from ..editors import MessageTemplateEditDialog

class MessageTemplatesSettingsMixin:
    """Message Templates settings panel behavior."""

    def create_message_templates_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        desc = QLabel("💬 판매자에게 보낼 메시지 템플릿을 관리합니다.")
        desc.setStyleSheet("color: #89b4fa;")
        layout.addWidget(desc)

        self.templates_table = QTableWidget()
        self.templates_table.setColumnCount(3)
        self.templates_table.setHorizontalHeaderLabels(["이름", "플랫폼", "내용"])
        template_h_header = self.templates_table.horizontalHeader()
        if template_h_header is not None:
            template_h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.templates_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.templates_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.templates_table)

        btns = QHBoxLayout()
        btns.addStretch()

        add_btn = QPushButton("추가")
        add_btn.clicked.connect(self.add_template)
        btns.addWidget(add_btn)

        edit_btn = QPushButton("편집")
        edit_btn.clicked.connect(self.edit_template)
        btns.addWidget(edit_btn)

        del_btn = QPushButton("삭제")
        del_btn.clicked.connect(self.delete_template)
        btns.addWidget(del_btn)

        reset_btn = QPushButton("기본값으로 초기화")
        reset_btn.clicked.connect(self.reset_templates_default)
        btns.addWidget(reset_btn)

        layout.addLayout(btns)
        return widget


    def _refresh_message_templates_table(self):
        if not hasattr(self, "templates_table"):
            return
        templates = self._message_templates or []
        self.templates_table.setRowCount(len(templates))
        for i, t in enumerate(templates):
            name = getattr(t, "name", "")
            platform = getattr(t, "platform", "all") or "all"
            content = getattr(t, "content", "")
            preview = content.replace("\n", " ")
            if len(preview) > 80:
                preview = preview[:77] + "..."

            self.templates_table.setItem(i, 0, QTableWidgetItem(name))
            self.templates_table.setItem(i, 1, QTableWidgetItem(platform))
            self.templates_table.setItem(i, 2, QTableWidgetItem(preview))


    def _selected_template_index(self) -> int:
        row = self.templates_table.currentRow()
        return row if row >= 0 else -1


    def add_template(self):
        dlg = MessageTemplateEditDialog(parent=self)
        if dlg.exec():
            self._message_templates.append(dlg.get_template())
            self._refresh_message_templates_table()


    def edit_template(self):
        idx = self._selected_template_index()
        if idx < 0 or idx >= len(self._message_templates):
            QMessageBox.information(self, "알림", "편집할 템플릿을 선택하세요.")
            return
        dlg = MessageTemplateEditDialog(template=self._message_templates[idx], parent=self)
        if dlg.exec():
            self._message_templates[idx] = dlg.get_template()
            self._refresh_message_templates_table()


    def delete_template(self):
        idx = self._selected_template_index()
        if idx < 0 or idx >= len(self._message_templates):
            QMessageBox.information(self, "알림", "삭제할 템플릿을 선택하세요.")
            return
        if QMessageBox.question(self, "확인", "선택한 템플릿을 삭제하시겠습니까?") != QMessageBox.StandardButton.Yes:
            return
        self._message_templates.pop(idx)
        self._refresh_message_templates_table()


    def reset_templates_default(self):
        if QMessageBox.question(self, "확인", "기본 템플릿으로 초기화하시겠습니까?") != QMessageBox.StandardButton.Yes:
            return
        self._message_templates = [
            MessageTemplate(name=t.name, content=t.content, platform=t.platform)
            for t in MessageTemplateManager.DEFAULT_TEMPLATES
        ]
        self._refresh_message_templates_table()
