"""
ui/settings_page.py

Modern settings panel with theme toggle, accent picker,
font, language and update interval controls.
Uses debounced slider and typed Snapshot.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QComboBox, QSlider, QPushButton, QFrame,
)

from ui.styles import C
from ui.widgets import Card, ToggleSwitch, AccentButton
from controller.settings_manager import SettingsManager
from core.snapshot import Snapshot


LANGUAGES = [
    ("en", "English"), ("ar", "العربية"), ("fr", "Français"),
    ("de", "Deutsch"), ("zh", "中文"), ("es", "Español"),
    ("ja", "日本語"),
]

ACCENT_SWATCHES = [
    "#4f8cff", "#0969da", "#8250df", "#3fb950",
    "#39d2c0", "#d29922", "#f85149", "#e16f24",
]

FONT_FAMILIES = [
    "Segoe UI", "Inter", "Noto Sans",
    "SF Pro Display", "Roboto", "Ubuntu",
]


class SettingsPage(QWidget):
    """Full settings UI. Signals back to MainWindow for live hot-apply."""

    theme_changed    = Signal(str)
    accent_changed   = Signal(str)
    font_changed     = Signal(str, int)
    language_changed = Signal(str)
    interval_changed = Signal(int)
    density_changed  = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._sm = SettingsManager.instance()
        self._interval_debounce = QTimer(self)
        self._interval_debounce.setSingleShot(True)
        self._interval_debounce.setInterval(250)
        self._interval_debounce.timeout.connect(self._emit_interval)
        self._pending_interval: int = self._sm.update_ms
        self._build_ui()
        self._load_values()
        self._connect_signals()

    def __repr__(self) -> str:
        return f"SettingsPage(theme={self._sm.theme!r})"

    # ------------------------------------------------------------------ #
    #  UI construction
    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        host = QWidget()
        root = QVBoxLayout(host)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        title = QLabel("Settings")
        title.setObjectName("SectionTitle")
        subtitle = QLabel("Customise the look and feel of SysPulse")
        subtitle.setStyleSheet(
            f"color:{C['text_dim']};font-size:13px;margin-bottom:8px;"
        )
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addSpacing(8)

        root.addWidget(self._build_appearance_section())
        root.addWidget(self._build_system_section())
        root.addLayout(self._build_reset_row())
        root.addStretch()

        scroll.setWidget(host)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _build_appearance_section(self) -> Card:
        card = Card("Appearance")

        # Theme
        row = self._label_row("Theme", "Switch between dark and light mode")
        self._theme_toggle = ToggleSwitch(checked=(self._sm.theme == "dark"))
        row.addWidget(self._theme_toggle, alignment=Qt.AlignRight)
        card.addLayout(row)
        card.addWidget(self._separator())

        # Accent
        row = self._label_row("Accent Colour", "Highlight colour across the app")
        swatch_row = QHBoxLayout()
        swatch_row.setSpacing(8)
        for col in ACCENT_SWATCHES:
            btn = AccentButton(col)
            btn.setToolTip(col)
            btn.clicked.connect(lambda c=col: self._on_accent_clicked(c))
            swatch_row.addWidget(btn)
        swatch_row.addStretch()
        row.addLayout(swatch_row)
        card.addLayout(row)
        card.addWidget(self._separator())

        # Font
        row = self._label_row("Font", "Choose a typeface")
        self._font_combo = QComboBox()
        self._font_combo.addItems(FONT_FAMILIES)
        self._font_combo.setMinimumWidth(180)
        row.addWidget(self._font_combo, alignment=Qt.AlignRight)
        card.addLayout(row)
        card.addWidget(self._separator())

        # Font size
        row = self._label_row("Font Size", "Adjust text size (pt)")
        size_col = QHBoxLayout()
        size_col.setSpacing(12)
        self._size_slider = QSlider(Qt.Horizontal)
        self._size_slider.setRange(10, 20)
        self._size_slider.setFixedWidth(180)
        self._size_label = QLabel("13 pt")
        self._size_label.setFixedWidth(48)
        self._size_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        size_col.addWidget(self._size_slider)
        size_col.addWidget(self._size_label)
        row.addLayout(size_col)
        card.addLayout(row)
        card.addWidget(self._separator())

        # Density
        row = self._label_row("UI Density", "Compact, normal or large spacing")
        self._density_combo = QComboBox()
        self._density_combo.addItems(["Compact", "Normal", "Large"])
        self._density_combo.setMinimumWidth(180)
        row.addWidget(self._density_combo, alignment=Qt.AlignRight)
        card.addLayout(row)
        return card

    def _build_system_section(self) -> Card:
        card = Card("System")

        row = self._label_row("Language", "Display language (requires restart)")
        self._lang_combo = QComboBox()
        for code, name in LANGUAGES:
            self._lang_combo.addItem(name, code)
        self._lang_combo.setMinimumWidth(180)
        row.addWidget(self._lang_combo, alignment=Qt.AlignRight)
        card.addLayout(row)
        card.addWidget(self._separator())

        row = self._label_row("Update Interval",
                              "How often metrics refresh (ms)")
        int_col = QHBoxLayout()
        int_col.setSpacing(12)
        self._interval_slider = QSlider(Qt.Horizontal)
        self._interval_slider.setRange(500, 5000)
        self._interval_slider.setSingleStep(100)
        self._interval_slider.setFixedWidth(180)
        self._interval_label = QLabel("1500 ms")
        self._interval_label.setFixedWidth(72)
        self._interval_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        int_col.addWidget(self._interval_slider)
        int_col.addWidget(self._interval_label)
        row.addLayout(int_col)
        card.addLayout(row)
        return card

    def _build_reset_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addStretch()
        self._reset_btn = QPushButton("  Reset to Defaults")
        self._reset_btn.setObjectName("SecondaryBtn")
        self._reset_btn.setCursor(Qt.PointingHandCursor)
        self._reset_btn.clicked.connect(self._reset_defaults)
        row.addWidget(self._reset_btn)
        return row

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _label_row(title: str, desc: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 6, 0, 6)
        left = QVBoxLayout()
        left.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet(f"color:{C['text']};font-size:14px;font-weight:600;")
        d = QLabel(desc)
        d.setStyleSheet(f"color:{C['text_dim']};font-size:12px;")
        left.addWidget(t)
        left.addWidget(d)
        row.addLayout(left)
        row.addStretch()
        return row

    @staticmethod
    def _separator() -> QFrame:
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{C['border']};")
        return sep

    # ------------------------------------------------------------------ #
    #  Load / connect
    # ------------------------------------------------------------------ #
    def _load_values(self) -> None:
        sm = self._sm
        self._theme_toggle.setChecked(sm.theme == "dark")
        self._font_combo.setCurrentText(sm.font_family)
        self._size_slider.setValue(sm.font_size)
        self._size_label.setText(f"{sm.font_size} pt")
        for i, (code, _) in enumerate(LANGUAGES):
            if code == sm.language:
                self._lang_combo.setCurrentIndex(i)
                break
        self._interval_slider.setValue(sm.update_ms)
        self._interval_label.setText(f"{sm.update_ms} ms")
        # Density
        density_map = {"compact": 0, "normal": 1, "large": 2}
        self._density_combo.setCurrentIndex(density_map.get(sm.density, 1))

    def _connect_signals(self) -> None:
        self._theme_toggle.toggled.connect(self._on_theme)
        self._font_combo.currentTextChanged.connect(self._on_font)
        self._size_slider.valueChanged.connect(self._on_size)
        self._lang_combo.currentIndexChanged.connect(self._on_lang)
        self._interval_slider.valueChanged.connect(self._on_interval)
        self._density_combo.currentIndexChanged.connect(self._on_density)

    # ------------------------------------------------------------------ #
    #  Slots
    # ------------------------------------------------------------------ #
    def _on_theme(self, checked: bool) -> None:
        theme = "dark" if checked else "light"
        self._sm.theme = theme
        self.theme_changed.emit(theme)

    def _on_accent_clicked(self, color: str) -> None:
        self._sm.accent = color
        self.accent_changed.emit(color)

    def _on_font(self, family: str) -> None:
        if not family:
            return
        self._sm.font_family = family
        self.font_changed.emit(family, self._sm.font_size)

    def _on_size(self, v: int) -> None:
        self._size_label.setText(f"{v} pt")
        self._sm.font_size = v
        self.font_changed.emit(self._sm.font_family, v)

    def _on_lang(self, idx: int) -> None:
        code = self._lang_combo.itemData(idx)
        if code:
            self._sm.language = code
            self.language_changed.emit(code)

    def _on_interval(self, v: int) -> None:
        self._interval_label.setText(f"{v} ms")
        self._pending_interval = v
        self._interval_debounce.start()

    def _emit_interval(self) -> None:
        v = self._pending_interval
        self._sm.update_ms = v
        self.interval_changed.emit(v)

    def _on_density(self, idx: int) -> None:
        density_map = {0: "compact", 1: "normal", 2: "large"}
        density = density_map.get(idx, "normal")
        self._sm.density = density
        self.density_changed.emit(density)

    def _reset_defaults(self) -> None:
        sm = self._sm
        for key, val in SettingsManager.DEFAULTS.items():
            sm.set(key, val)
        self._load_values()
        self.theme_changed.emit(sm.theme)
        self.accent_changed.emit(sm.accent)
        self.font_changed.emit(sm.font_family, sm.font_size)
        self.interval_changed.emit(sm.update_ms)
        self.density_changed.emit(sm.density)

    def update_data(self, _snapshot: Snapshot) -> None:
        """Required by PageSubscriber protocol — no-op for settings."""
        pass
