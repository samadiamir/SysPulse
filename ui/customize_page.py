"""
ui/customize_page.py

Dashboard customization panel — toggle visibility of dashboard widgets.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
)

from ui.styles import C
from ui.widgets import Card, ToggleSwitch
from controller.settings_manager import SettingsManager
from core.snapshot import Snapshot


class CustomizePage(QWidget):
    """Dashboard widget toggle panel."""

    dashboard_changed = Signal()  # fires when any toggle changes

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._sm = SettingsManager.instance()
        self._build_ui()
        self._load_values()
        self._connect_signals()

    def __repr__(self) -> str:
        return "CustomizePage()"

    def _build_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        host = QWidget()
        root = QVBoxLayout(host)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        title = QLabel("Customise Dashboard")
        title.setObjectName("SectionTitle")
        subtitle = QLabel("Choose which sections appear on the Dashboard page")
        subtitle.setStyleSheet(f"color:{C['text_dim']};font-size:13px;margin-bottom:8px;")
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addSpacing(8)

        # Dashboard widgets card
        card = Card("Dashboard Widgets")

        # Live Resources (gauges)
        row = self._label_row(
            "Live Resources",
            "CPU and Memory circular gauges with live percentage"
        )
        self._gauges_toggle = ToggleSwitch()
        row.addWidget(self._gauges_toggle, alignment=Qt.AlignRight)
        card.addLayout(row)
        card.addWidget(self._separator())

        # Stat cards
        row = self._label_row(
            "Quick Stats",
            "Disk usage, Battery status and Network activity cards"
        )
        self._stats_toggle = ToggleSwitch()
        row.addWidget(self._stats_toggle, alignment=Qt.AlignRight)
        card.addLayout(row)
        card.addWidget(self._separator())

        # Partitions table
        row = self._label_row(
            "Storage Partitions",
            "Detailed table of all mounted disk partitions"
        )
        self._partitions_toggle = ToggleSwitch()
        row.addWidget(self._partitions_toggle, alignment=Qt.AlignRight)
        card.addLayout(row)

        root.addWidget(card)
        root.addStretch()

        scroll.setWidget(host)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _label_row(self, title: str, desc: str) -> QHBoxLayout:
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

    def _separator(self):
        from PySide6.QtWidgets import QFrame
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{C['border']};")
        return sep

    def _load_values(self) -> None:
        self._gauges_toggle.setChecked(self._sm.dash_show_gauges)
        self._stats_toggle.setChecked(self._sm.dash_show_stats)
        self._partitions_toggle.setChecked(self._sm.dash_show_partitions)

    def _connect_signals(self) -> None:
        self._gauges_toggle.toggled.connect(self._on_gauges)
        self._stats_toggle.toggled.connect(self._on_stats)
        self._partitions_toggle.toggled.connect(self._on_partitions)

    def _on_gauges(self, v: bool) -> None:
        self._sm.dash_show_gauges = v
        self.dashboard_changed.emit()

    def _on_stats(self, v: bool) -> None:
        self._sm.dash_show_stats = v
        self.dashboard_changed.emit()

    def _on_partitions(self, v: bool) -> None:
        self._sm.dash_show_partitions = v
        self.dashboard_changed.emit()

    def update_data(self, _snapshot: Snapshot) -> None:
        pass
