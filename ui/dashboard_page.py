"""
ui/dashboard_page.py

Glass-morphed dashboard with large circular gauges and stat cards.
Respects widget visibility settings from SettingsManager.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy, QWidget

from ui.styles import C
from ui.base_page import ScrollablePage, clear_layout
from ui.widgets import Card, StatCard, CircularGauge, InfoRow, build_info_grid
from core.system_data import SystemData
from core.snapshot import Snapshot
from controller.settings_manager import SettingsManager


class DashboardPage(ScrollablePage):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._sm = SettingsManager.instance()
        root = self.content_layout
        root.setSpacing(22)

        # Live Resources
        self._gauge_card = Card("Live Resources")
        gauges_row = QHBoxLayout()
        gauges_row.setSpacing(0)
        gauges_row.setContentsMargins(8, 12, 8, 0)

        self._cpu_col = _GaugeColumn("CPU", C["cpu"])
        self._mem_col = _GaugeColumn("MEMORY", C["mem"])

        gauges_row.addStretch(1)
        gauges_row.addWidget(self._cpu_col, stretch=2)
        gauges_row.addStretch(1)
        gauges_row.addWidget(self._mem_col, stretch=2)
        gauges_row.addStretch(1)
        self._gauge_card.addLayout(gauges_row)
        root.addWidget(self._gauge_card)

        # Stat cards
        self._stats_widget = QWidget()
        cards_row = QHBoxLayout(self._stats_widget)
        cards_row.setSpacing(14)
        cards_row.setContentsMargins(0, 0, 0, 0)
        self._disk_card = StatCard("Disk Usage", icon_name="fa5s.hdd",
                                   icon_color=C["disk"])
        self._battery_card = StatCard("Battery", icon_name="fa5s.battery-half",
                                      icon_color=C["battery"])
        self._network_card = StatCard("Network", icon_name="fa5s.network-wired",
                                      icon_color=C["net"])
        for card in (self._disk_card, self._battery_card, self._network_card):
            cards_row.addWidget(card)
        root.addWidget(self._stats_widget)

        # Partitions
        self._partitions_card = Card("Storage Partitions")
        self._disk_grid = build_info_grid([])
        self._partitions_card.addLayout(self._disk_grid)
        root.addWidget(self._partitions_card)

        root.addStretch()

        # Apply initial visibility
        self._apply_visibility()

    def __repr__(self) -> str:
        return "DashboardPage()"

    def refresh_visibility(self) -> None:
        """Re-read settings and show/hide dashboard sections."""
        self._apply_visibility()

    def _apply_visibility(self) -> None:
        self._gauge_card.setVisible(self._sm.dash_show_gauges)
        self._stats_widget.setVisible(self._sm.dash_show_stats)
        self._partitions_card.setVisible(self._sm.dash_show_partitions)

    def update_data(self, snapshot: Snapshot) -> None:
        cpu_pct = snapshot.cpu_percent
        mem_pct = snapshot.memory.percent

        if self._sm.dash_show_gauges:
            self._cpu_col.set_value(cpu_pct, f"{cpu_pct:.1f}%")
            self._mem_col.set_value(
                mem_pct,
                f"{SystemData.human_bytes(snapshot.memory.used)} / "
                f"{SystemData.human_bytes(snapshot.memory.total)}",
            )

        if self._sm.dash_show_stats:
            if snapshot.disks:
                worst = max(snapshot.disks, key=lambda d: d.percent)
                self._disk_card.set_value(
                    f"{worst.percent:.0f}%",
                    f"{worst.device} · "
                    f"{SystemData.human_bytes(worst.used)} / "
                    f"{SystemData.human_bytes(worst.total)}",
                )

            bat = snapshot.battery
            if bat is None:
                self._battery_card.set_value("N/A", "No battery detected")
            else:
                state = "Plugged in" if bat.plugged else "On battery"
                self._battery_card.set_value(f"{bat.percent:.0f}%", state)

            net = snapshot.network
            self._network_card.set_value(
                "Active",
                f"↓ {SystemData.human_bytes(net.bytes_recv)}  "
                f"↑ {SystemData.human_bytes(net.bytes_sent)}",
            )

        if self._sm.dash_show_partitions:
            self._refresh_partitions(snapshot.disks)

    def _refresh_partitions(self, disks) -> None:
        clear_layout(self._disk_grid)
        if not disks:
            lbl = QLabel("No partitions detected.")
            lbl.setObjectName("CardSub")
            lbl.setAlignment(Qt.AlignCenter)
            self._disk_grid.addWidget(lbl, 0, 0)
            return
        for i, d in enumerate(disks):
            self._disk_grid.addWidget(
                InfoRow(
                    f"{d.device}  ({d.mountpoint})",
                    f"{d.percent:.1f}% · "
                    f"{SystemData.human_bytes(d.used)} of "
                    f"{SystemData.human_bytes(d.total)} · {d.fstype}",
                ), i, 0, 1, 2,
            )


class _GaugeColumn(QWidget):
    """A vertically-stacked gauge with title + live value underneath."""

    def __init__(self, title: str, color: str,
                 parent: QWidget | None = None):
        super().__init__(parent)
        self._title = title
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)

        self._gauge = CircularGauge(label=title, color=color)
        self._gauge.setMinimumSize(200, 200)
        self._gauge.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self._gauge, alignment=Qt.AlignCenter)

        self._detail_label = QLabel("—")
        self._detail_label.setAlignment(Qt.AlignCenter)
        self._detail_label.setStyleSheet(
            f"color: {C['text_dim']}; font-size: 13px; font-weight: 500;"
        )
        layout.addWidget(self._detail_label, alignment=Qt.AlignCenter)

    def __repr__(self) -> str:
        return f"_GaugeColumn({self._title!r}={self._gauge.value:.0f}%)"

    def set_value(self, percent: float, detail: str = "") -> None:
        self._gauge.set_value(percent)
        if detail:
            self._detail_label.setText(detail)
