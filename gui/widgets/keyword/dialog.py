"""Keyword edit dialog."""

from .common import *


class KeywordEditDialog(QDialog):
    """Modern dialog for editing keyword configuration"""

    def __init__(self, keyword: SearchKeyword | None = None, settings_manager=None, parent=None):
        super().__init__(parent)
        self.keyword = keyword or SearchKeyword(keyword="")
        self.settings_manager = settings_manager
        self.setup_ui()
        self.load_keyword()

    def setup_ui(self):
        self.setWindowTitle("키워드 설정")
        self.setMinimumWidth(500)
        self.setStyleSheet("QDialog { background-color: #1a1b26; }")

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("🔍 키워드 설정")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #7aa2f7;")
        layout.addWidget(title)

        # Keyword input group
        keyword_group = QGroupBox("기본 정보")
        keyword_layout = QFormLayout(keyword_group)
        keyword_layout.setSpacing(12)

        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("예: 맥북 에어 M2")
        self.keyword_edit.setMinimumHeight(40)
        keyword_layout.addRow("검색어", self.keyword_edit)

        # Preset dropdown
        preset_row = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("📁 프리셋 선택...")
        self._load_presets()
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        self.preset_combo.setMinimumHeight(36)
        preset_row.addWidget(self.preset_combo)

        save_preset_btn = QPushButton("💾 프리셋 저장")
        save_preset_btn.setMinimumHeight(36)
        save_preset_btn.clicked.connect(self._save_as_preset)
        preset_row.addWidget(save_preset_btn)
        keyword_layout.addRow("프리셋", preset_row)

        self.enabled_check = QCheckBox("🔍 키워드 모니터링 활성화")
        self.enabled_check.setChecked(True)
        keyword_layout.addRow("", self.enabled_check)

        self.notify_check = QCheckBox("🔔 이 키워드 알림 받기")
        self.notify_check.setChecked(True)
        keyword_layout.addRow("", self.notify_check)

        layout.addWidget(keyword_group)

        # Price filter group
        price_group = QGroupBox("💰 가격 필터")
        price_layout = QHBoxLayout(price_group)
        price_layout.setSpacing(12)

        self.min_price_spin = QSpinBox()
        self.min_price_spin.setRange(0, 100000000)
        self.min_price_spin.setSingleStep(10000)
        self.min_price_spin.setSpecialValueText("최소")
        self.min_price_spin.setSuffix(" 원")
        self.min_price_spin.setMinimumHeight(40)
        price_layout.addWidget(QLabel("최소"))
        price_layout.addWidget(self.min_price_spin)

        price_layout.addWidget(QLabel("~"))

        self.max_price_spin = QSpinBox()
        self.max_price_spin.setRange(0, 100000000)
        self.max_price_spin.setSingleStep(10000)
        self.max_price_spin.setSpecialValueText("최대")
        self.max_price_spin.setSuffix(" 원")
        self.max_price_spin.setMinimumHeight(40)
        price_layout.addWidget(QLabel("최대"))
        price_layout.addWidget(self.max_price_spin)

        layout.addWidget(price_group)

        # Location and exclude in a row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(16)

        # Location
        location_group = QGroupBox("📍 지역 (당근)")
        location_layout = QVBoxLayout(location_group)
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("예: 강남구")
        self.location_edit.setMinimumHeight(40)
        self.location_edit.setToolTip(
            "당근 지역 필터는 현재 세션 지역 기준의 best-effort 검색 후 후처리 필터로 동작합니다."
        )
        location_layout.addWidget(self.location_edit)
        location_note = QLabel(
            "현재 당근 지역 필터는 세션 지역 기준의 best-effort 검색 후 후처리로 적용됩니다."
        )
        location_note.setWordWrap(True)
        location_note.setStyleSheet(
            """
            color: #f9e2af;
            font-size: 9pt;
            background: transparent;
            """
        )
        location_layout.addWidget(location_note)
        filter_row.addWidget(location_group)

        # Exclude keywords
        exclude_group = QGroupBox("🚫 제외 키워드")
        exclude_layout = QVBoxLayout(exclude_group)
        self.exclude_edit = QTextEdit()
        self.exclude_edit.setMaximumHeight(80)
        self.exclude_edit.setPlaceholderText("케이스\n부품\n택포X")
        exclude_layout.addWidget(self.exclude_edit)
        filter_row.addWidget(exclude_group)

        layout.addLayout(filter_row)

        # Platform selection
        platform_group = QGroupBox("📦 검색 플랫폼")
        platform_layout = QHBoxLayout(platform_group)
        platform_layout.setSpacing(16)

        self.danggeun_check = QCheckBox("🥕 당근마켓")
        self.danggeun_check.setChecked(True)
        self.danggeun_check.setStyleSheet("font-size: 11pt;")
        platform_layout.addWidget(self.danggeun_check)

        self.bunjang_check = QCheckBox("⚡ 번개장터")
        self.bunjang_check.setChecked(True)
        self.bunjang_check.setStyleSheet("font-size: 11pt;")
        platform_layout.addWidget(self.bunjang_check)

        self.joonggonara_check = QCheckBox("🛒 중고나라")
        self.joonggonara_check.setChecked(True)
        self.joonggonara_check.setStyleSheet("font-size: 11pt;")
        platform_layout.addWidget(self.joonggonara_check)

        platform_layout.addStretch()
        layout.addWidget(platform_group)

        # Buttons
        layout.addStretch()
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()

        cancel_btn = QPushButton("취소")
        cancel_btn.setObjectName("secondary")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 저장")
        save_btn.setObjectName("success")
        save_btn.setMinimumWidth(100)
        save_btn.clicked.connect(self._validate_and_accept)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _validate_and_accept(self):
        """Validate input before accepting dialog"""
        # Check keyword is not empty
        keyword = self.keyword_edit.text().strip()
        if not keyword:
            QMessageBox.warning(self, "입력 오류", "검색어를 입력해주세요.")
            self.keyword_edit.setFocus()
            return

        if len(keyword) < 2:
            QMessageBox.warning(self, "입력 오류", "검색어는 최소 2자 이상이어야 합니다.")
            self.keyword_edit.setFocus()
            return

        # Check at least one platform is selected
        has_platform = (
            self.danggeun_check.isChecked() or
            self.bunjang_check.isChecked() or
            self.joonggonara_check.isChecked()
        )
        if not has_platform:
            QMessageBox.warning(self, "입력 오류", "최소 1개 이상의 플랫폼을 선택해주세요.")
            return

        min_price = self.min_price_spin.value()
        max_price = self.max_price_spin.value()
        if min_price > 0 and max_price > 0 and min_price > max_price:
            QMessageBox.warning(self, "입력 오류", "최소 가격은 최대 가격보다 클 수 없습니다.")
            self.min_price_spin.setFocus()
            return

        self.accept()

    def load_keyword(self):
        self.keyword_edit.setText(self.keyword.keyword)
        self.enabled_check.setChecked(self.keyword.enabled)
        self.notify_check.setChecked(getattr(self.keyword, 'notify_enabled', True))

        if self.keyword.min_price:
            self.min_price_spin.setValue(self.keyword.min_price)
        if self.keyword.max_price:
            self.max_price_spin.setValue(self.keyword.max_price)

        self.location_edit.setText(self.keyword.location or "")
        self.exclude_edit.setPlainText("\n".join(self.keyword.exclude_keywords))

        self.danggeun_check.setChecked("danggeun" in self.keyword.platforms)
        self.bunjang_check.setChecked("bunjang" in self.keyword.platforms)
        self.joonggonara_check.setChecked("joonggonara" in self.keyword.platforms)

    def _load_presets(self):
        """Load presets into combo box"""
        if self.settings_manager:
            for preset in self.settings_manager.get_presets():
                self.preset_combo.addItem(f"📋 {preset.name}", preset)

    def _on_preset_selected(self, index: int):
        """Apply selected preset"""
        if index <= 0:
            return
        preset = self.preset_combo.itemData(index)
        if preset:
            if preset.min_price:
                self.min_price_spin.setValue(preset.min_price)
            else:
                self.min_price_spin.setValue(0)
            if preset.max_price:
                self.max_price_spin.setValue(preset.max_price)
            else:
                self.max_price_spin.setValue(0)
            self.location_edit.setText(preset.location or "")
            self.exclude_edit.setPlainText("\n".join(preset.exclude_keywords))
            self.danggeun_check.setChecked("danggeun" in preset.platforms)
            self.bunjang_check.setChecked("bunjang" in preset.platforms)
            self.joonggonara_check.setChecked("joonggonara" in preset.platforms)

    def _save_as_preset(self):
        """Save current settings as preset"""
        if not self.settings_manager:
            QMessageBox.warning(self, "오류", "설정 관리자 없음")
            return

        name, ok = QInputDialog.getText(self, "프리셋 저장", "프리셋 이름:")
        if not ok or not name.strip():
            return

        min_price = self.min_price_spin.value()
        max_price = self.max_price_spin.value()
        if min_price > 0 and max_price > 0 and min_price > max_price:
            QMessageBox.warning(self, "입력 오류", "최소 가격은 최대 가격보다 클 수 없습니다.")
            self.min_price_spin.setFocus()
            return

        platforms = []
        if self.danggeun_check.isChecked():
            platforms.append("danggeun")
        if self.bunjang_check.isChecked():
            platforms.append("bunjang")
        if self.joonggonara_check.isChecked():
            platforms.append("joonggonara")

        exclude_text = self.exclude_edit.toPlainText().strip()
        exclude_keywords = [k.strip() for k in exclude_text.split("\n") if k.strip()]

        preset = KeywordPreset(
            name=name.strip(),
            min_price=self.min_price_spin.value() if self.min_price_spin.value() > 0 else None,
            max_price=self.max_price_spin.value() if self.max_price_spin.value() > 0 else None,
            location=self.location_edit.text().strip() or None,
            exclude_keywords=exclude_keywords,
            platforms=platforms,
        )
        self.settings_manager.add_preset(preset)

        # Refresh combo
        self.preset_combo.addItem(f"📋 {name}", preset)
        QMessageBox.information(self, "성공", f"프리셋 '{name}'이(가) 저장되었습니다!")

    def get_keyword(self) -> SearchKeyword:
        platforms = []
        if self.danggeun_check.isChecked():
            platforms.append("danggeun")
        if self.bunjang_check.isChecked():
            platforms.append("bunjang")
        if self.joonggonara_check.isChecked():
            platforms.append("joonggonara")

        exclude_text = self.exclude_edit.toPlainText().strip()
        exclude_keywords = [k.strip() for k in exclude_text.split("\n") if k.strip()]

        return SearchKeyword(
            keyword=self.keyword_edit.text().strip(),
            min_price=self.min_price_spin.value() if self.min_price_spin.value() > 0 else None,
            max_price=self.max_price_spin.value() if self.max_price_spin.value() > 0 else None,
            location=self.location_edit.text().strip() or None,
            exclude_keywords=exclude_keywords,
            platforms=platforms,
            enabled=self.enabled_check.isChecked(),
            notify_enabled=self.notify_check.isChecked(),
        )
