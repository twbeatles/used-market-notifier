"""Settings dialog editor classes."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QCheckBox, QLabel,
    QPushButton, QComboBox, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt

from models import MessageTemplate, TagRule


class TagRuleEditDialog(QDialog):
    """Add/edit TagRule."""

    def __init__(self, rule: TagRule | None = None, parent=None):
        super().__init__(parent)
        self._rule = rule
        self._build_ui()
        if rule:
            self._load(rule)

    def _build_ui(self):
        self.setWindowTitle("태그 규칙 편집")
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(12)

        self.enabled_check = QCheckBox("사용")
        form.addRow("", self.enabled_check)

        self.tag_name_edit = QLineEdit()
        form.addRow("태그 이름*", self.tag_name_edit)

        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText("예: 🏷️")
        form.addRow("아이콘", self.icon_edit)

        self.color_edit = QLineEdit()
        self.color_edit.setPlaceholderText("예: #89b4fa")
        form.addRow("색상", self.color_edit)

        self.keywords_edit = QTextEdit()
        self.keywords_edit.setPlaceholderText("키워드들을 줄바꿈 또는 콤마로 구분해서 입력하세요")
        self.keywords_edit.setMinimumHeight(140)
        form.addRow("키워드*", self.keywords_edit)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()

        cancel = QPushButton("취소")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)

        ok = QPushButton("확인")
        ok.clicked.connect(self._on_ok)
        btns.addWidget(ok)

        layout.addLayout(btns)

    def _load(self, rule: TagRule):
        self.enabled_check.setChecked(getattr(rule, "enabled", True))
        self.tag_name_edit.setText(getattr(rule, "tag_name", ""))
        self.icon_edit.setText(getattr(rule, "icon", ""))
        self.color_edit.setText(getattr(rule, "color", ""))
        self.keywords_edit.setPlainText("\n".join(getattr(rule, "keywords", []) or []))

    def _on_ok(self):
        tag_name = self.tag_name_edit.text().strip()
        if not tag_name:
            QMessageBox.warning(self, "오류", "태그 이름은 필수입니다.")
            return

        raw = self.keywords_edit.toPlainText().strip()
        keywords: list[str] = []
        if raw:
            parts = []
            for line in raw.splitlines():
                parts.extend([p.strip() for p in line.split(",")])
            keywords = [p for p in parts if p]

        if not keywords:
            QMessageBox.warning(self, "오류", "키워드는 최소 1개 이상 필요합니다.")
            return

        self._result = TagRule(
            tag_name=tag_name,
            keywords=keywords,
            color=(self.color_edit.text().strip() or "#89b4fa"),
            icon=(self.icon_edit.text().strip() or "🏷️"),
            enabled=self.enabled_check.isChecked(),
        )
        self.accept()

    def get_rule(self) -> TagRule:
        return getattr(self, "_result", self._rule)  # type: ignore[return-value]


class MessageTemplateEditDialog(QDialog):
    """Add/edit MessageTemplate."""

    def __init__(self, template: MessageTemplate | None = None, parent=None):
        super().__init__(parent)
        self._template = template
        self._build_ui()
        if template:
            self._load(template)

    def _build_ui(self):
        self.setWindowTitle("메시지 템플릿 편집")
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.name_edit = QLineEdit()
        form.addRow("이름*", self.name_edit)

        self.platform_combo = QComboBox()
        self.platform_combo.addItem("all", "all")
        self.platform_combo.addItem("danggeun", "danggeun")
        self.platform_combo.addItem("bunjang", "bunjang")
        self.platform_combo.addItem("joonggonara", "joonggonara")
        form.addRow("플랫폼", self.platform_combo)

        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("변수: {title}, {price}, {seller}, {location}, {target_price}")
        self.content_edit.setMinimumHeight(180)
        form.addRow("내용*", self.content_edit)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()

        cancel = QPushButton("취소")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)

        ok = QPushButton("확인")
        ok.clicked.connect(self._on_ok)
        btns.addWidget(ok)

        layout.addLayout(btns)

    def _load(self, t: MessageTemplate):
        self.name_edit.setText(getattr(t, "name", ""))
        content = getattr(t, "content", "") or ""
        self.content_edit.setPlainText(content)
        platform = getattr(t, "platform", "all") or "all"
        idx = self.platform_combo.findData(platform)
        if idx >= 0:
            self.platform_combo.setCurrentIndex(idx)

    def _on_ok(self):
        name = self.name_edit.text().strip()
        content = self.content_edit.toPlainText().strip()
        if not name:
            QMessageBox.warning(self, "오류", "이름은 필수입니다.")
            return
        if not content:
            QMessageBox.warning(self, "오류", "내용은 필수입니다.")
            return
        self._result = MessageTemplate(
            name=name,
            content=content,
            platform=self.platform_combo.currentData(),
        )
        self.accept()

    def get_template(self) -> MessageTemplate:
        return getattr(self, "_result", self._template)  # type: ignore[return-value]
