"""
ui/health_page.py

Health verdicts with glass cards and colour-coded badges.
Uses typed Snapshot and HealthResult objects.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget

from ui.styles import C
from ui.base_page import ScrollablePage
from ui.widgets import Card, Badge
from core.health_checker import HealthChecker
from core.system_data import SystemData
from core.snapshot import Snapshot, HealthResult


class HealthPage(ScrollablePage):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._build_content()

    def __repr__(self) -> str:
        return "HealthPage()"

    def _build_content(self) -> None:
        root = self.content_layout

        # Banner
        banner_card = Card()
        banner_row = QHBoxLayout()
        banner_row.setSpacing(16)
        left = QVBoxLayout()
        left.setSpacing(4)
        self._overall_title = QLabel("System Health")
        self._overall_title.setStyleSheet(
            f"color:{C['text']};font-size:22px;font-weight:800;"
            "letter-spacing:-0.3px;"
        )
        self._overall_msg = QLabel("Initialising…")
        self._overall_msg.setStyleSheet(f"color:{C['text_dim']};font-size:13px;")
        left.addWidget(self._overall_title)
        left.addWidget(self._overall_msg)
        banner_row.addLayout(left)
        banner_row.addStretch()
        self._overall_badge = Badge("—", status="good")
        banner_row.addWidget(self._overall_badge, alignment=Qt.AlignVCenter)
        banner_card.addLayout(banner_row)
        root.addWidget(banner_card)

        # Subsystem cards
        grid = QHBoxLayout()
        grid.setSpacing(14)
        self._cpu_card = _HealthSubsystemCard("CPU", "cpu")
        self._mem_card = _HealthSubsystemCard("Memory", "mem")
        self._disk_card = _HealthSubsystemCard("Storage", "disk")
        self._bat_card = _HealthSubsystemCard("Battery", "battery")
        for c in (self._cpu_card, self._mem_card, self._disk_card, self._bat_card):
            grid.addWidget(c)
        root.addLayout(grid)

        # Tips
        tips_card = Card("Recommendations")
        self._tips_label = QLabel("")
        self._tips_label.setWordWrap(True)
        self._tips_label.setStyleSheet(
            f"color:{C['text']};font-size:13px;line-height:160%;"
        )
        tips_card.addWidget(self._tips_label)
        root.addWidget(tips_card)
        root.addStretch()

    def update_data(self, snapshot: Snapshot) -> None:
        overall = HealthChecker.overall(snapshot)
        self._apply_overall(overall)

        cpu_r = HealthChecker.cpu_health(snapshot)
        self._cpu_card.set_status(
            cpu_r.status, cpu_r.message,
            f"{snapshot.cpu_percent:.1f}% load",
        )

        mem_r = HealthChecker.memory_health(snapshot)
        self._mem_card.set_status(
            mem_r.status, mem_r.message,
            f"{SystemData.human_bytes(snapshot.memory.used)} used",
        )

        disk_r = HealthChecker.disk_health(snapshot)
        self._disk_card.set_status(disk_r.status, disk_r.message,
                                   "Live monitoring active")

        bat_r = HealthChecker.battery_health(snapshot)
        bat = snapshot.battery
        sub = "No battery" if bat is None else f"{bat.percent:.0f}% remaining"
        self._bat_card.set_status(bat_r.status, bat_r.message, sub)

        self._tips_label.setText(_build_tips(
            cpu_r, mem_r, disk_r, bat_r, snapshot
        ))

    def _apply_overall(self, result: HealthResult) -> None:
        self._overall_msg.setText(result.message)
        label = {"good": "HEALTHY", "warning": "WARNING",
                 "critical": "CRITICAL"}[result.status]
        self._overall_badge.set_status(result.status, label)


def _build_tips(cpu_r: HealthResult, mem_r: HealthResult,
                disk_r: HealthResult, bat_r: HealthResult,
                snap: Snapshot) -> str:
    tips: list[str] = []
    if cpu_r.is_critical:
        tips.append("• CPU is saturated — close heavy applications.")
    elif cpu_r.is_warning:
        tips.append("• CPU load elevated — monitor for runaway tasks.")
    if mem_r.is_warning or mem_r.is_critical:
        tips.append("• Memory pressure — close unused programs.")
    if disk_r.is_warning or disk_r.is_critical:
        tips.append("• A disk is nearly full — free up space.")
    bat = snap.battery
    if bat_r.is_critical and bat and not bat.plugged:
        tips.append("• Battery critically low — connect power.")
    elif bat_r.is_warning and bat and not bat.plugged:
        tips.append("• Battery running low — consider plugging in.")
    if not tips:
        tips.append("• All systems nominal — no action needed.")
    return "\n".join(tips)


class _HealthSubsystemCard(Card):
    def __init__(self, title: str, color_key: str):
        super().__init__(title=title)
        self._color_key = color_key
        col = QVBoxLayout()
        col.setSpacing(8)
        self._badge = Badge("—", status="good")
        col.addWidget(self._badge)
        self._msg = QLabel("—")
        self._msg.setWordWrap(True)
        self._msg.setStyleSheet(f"color:{C['text']};font-size:13px;")
        col.addWidget(self._msg)
        self._sub = QLabel("")
        self._sub.setStyleSheet(f"color:{C['text_dim']};font-size:11px;")
        col.addWidget(self._sub)
        col.addStretch()
        self.addLayout(col)

    def __repr__(self) -> str:
        return f"_HealthSubsystemCard({self._badge!r})"

    def set_status(self, status: str, message: str, sub: str = "") -> None:
        """Set the card's health status, message, and optional subtitle."""
        self._badge.set_status(status, status.upper())
        self._msg.setText(message)
        self._sub.setText(sub)
