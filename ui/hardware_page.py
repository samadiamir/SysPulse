"""
ui/hardware_page.py

Modern hardware specs viewer with glass cards.
Uses typed Snapshot objects and proper encapsulation.
"""
from __future__ import annotations

import platform
from typing import Any

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget

from ui.styles import C
from ui.base_page import ScrollablePage, clear_layout
from ui.widgets import Card, StatCard, InfoRow
from core.system_data import SystemData
from core.snapshot import Snapshot


class HardwarePage(ScrollablePage):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._populated = False
        self._build_content()

    def __repr__(self) -> str:
        return f"HardwarePage(populated={self._populated})"

    def _build_content(self) -> None:
        root = self.content_layout

        head = QHBoxLayout()
        head.setSpacing(14)
        self._processor_card = StatCard("Processor", icon_name="fa5s.microchip",
                                        icon_color=C["cpu"])
        self._memory_card = StatCard("Total Memory", icon_name="fa5s.memory",
                                     icon_color=C["mem"])
        self._os_card = StatCard("Operating System", icon_name="fa5s.desktop",
                                 icon_color=C["accent"])
        for c in (self._processor_card, self._memory_card, self._os_card):
            head.addWidget(c)
        root.addLayout(head)

        cols = QHBoxLayout()
        cols.setSpacing(14)
        left = QVBoxLayout()
        right = QVBoxLayout()

        self._cpu_card = Card("CPU Details")
        self._cpu_rows = _RowContainer()
        self._cpu_card.addWidget(self._cpu_rows)
        left.addWidget(self._cpu_card)

        self._mem_card = Card("Memory Details")
        self._mem_rows = _RowContainer()
        self._mem_card.addWidget(self._mem_rows)
        left.addWidget(self._mem_card)

        self._os_card_details = Card("System & OS")
        self._os_rows = _RowContainer()
        self._os_card_details.addWidget(self._os_rows)
        right.addWidget(self._os_card_details)

        left.addStretch()
        right.addStretch()
        cols.addLayout(left, stretch=1)
        cols.addLayout(right, stretch=1)
        root.addLayout(cols)
        root.addStretch()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._populated:
            self._populate()
            self._populated = True

    def _populate(self) -> None:
        info = SystemData.cpu_info()
        os_info = SystemData.os_info()
        mem = SystemData.memory()

        self._processor_card.set_value(
            SystemData.cpu_brand(), f"{SystemData.cpu_cores_physical()} cores"
        )
        self._memory_card.set_value(
            SystemData.human_bytes(mem.total),
            f"{SystemData.human_bytes(mem.available)} available",
        )
        self._os_card.set_value(
            os_info["system"],
            f"{os_info['release']} · {os_info['machine']}",
        )

        self._cpu_rows.set_rows([
            ("Brand", SystemData.cpu_brand()),
            ("Physical Cores", str(SystemData.cpu_cores_physical())),
            ("Logical Cores", str(SystemData.cpu_cores_logical())),
            ("Architecture", info.get("arch", platform.machine())),
            ("Bits", str(info.get("bits", "—"))),
            ("Frequency",
             f"{info.get('hz_advertised_friendly', '—')} "
             f"(actual {info.get('hz_actual_friendly', '—')})"),
            ("L2 Cache", str(info.get("l2_cache_size", "—") or "—")),
            ("L3 Cache", str(info.get("l3_cache_size", "—") or "—")),
            ("Vendor", info.get("vendor_id_raw", "—")),
        ])
        self._mem_rows.set_rows([
            ("Total", SystemData.human_bytes(mem.total)),
            ("Available", SystemData.human_bytes(mem.available)),
            ("Used", SystemData.human_bytes(mem.used)),
            ("Usage", f"{mem.percent:.1f} %"),
        ])
        self._os_rows.set_rows([
            ("Operating System", os_info["system"]),
            ("Release", os_info["release"]),
            ("Version", os_info["version"]),
            ("Machine", os_info["machine"]),
            ("Hostname", os_info["hostname"]),
            ("Processor", os_info["processor"] or SystemData.cpu_brand()),
        ])

    def update_data(self, snapshot: Snapshot) -> None:
        if not self._populated:
            self._populate()
            self._populated = True
        mem = snapshot.memory
        self._memory_card.set_value(
            SystemData.human_bytes(mem.total),
            f"{SystemData.human_bytes(mem.available)} available",
        )
        self._mem_rows.update_value("Used",
                                    SystemData.human_bytes(mem.used))
        self._mem_rows.update_value("Available",
                                    SystemData.human_bytes(mem.available))
        self._mem_rows.update_value("Usage", f"{mem.percent:.1f} %")


class _RowContainer(QWidget):
    """Vertical stack of InfoRows that can be (re)populated."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 4, 0, 4)
        self._layout.setSpacing(0)
        self._rows: dict[str, InfoRow] = {}

    def __repr__(self) -> str:
        return f"_RowContainer(rows={len(self._rows)})"

    def set_rows(self, rows: list[tuple[str, str]]) -> None:
        self._clear()
        for label, value in rows:
            row = InfoRow(label, value)
            self._rows[label] = row
            self._layout.addWidget(row)
        self._layout.addStretch()

    def update_value(self, label: str, value: str) -> None:
        if label in self._rows:
            self._rows[label].set_value(value)

    def _clear(self) -> None:
        clear_layout(self._layout)
        self._rows.clear()
