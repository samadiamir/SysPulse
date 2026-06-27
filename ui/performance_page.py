"""
ui/performance_page.py

Modern live charts with glass KPI cards.
Uses typed Snapshot objects and proper encapsulation.
"""
from __future__ import annotations

from collections import deque

import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QWidget

from ui.styles import C, hex_to_qt_color
from ui.base_page import ScrollablePage, clear_layout
from ui.widgets import Card
from core.snapshot import Snapshot

pg.setConfigOptions(antialias=True, background=None, foreground="#7d8590")


def _pg_color(key: str) -> tuple[int, int, int, int]:
    val = C[key]
    if val.startswith("#"):
        return hex_to_qt_color(val)
    parts = val.replace("rgba(", "").replace(")", "").split(",")
    r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
    a = int(float(parts[3]) * 255)
    return (r, g, b, a)


def _pg_pen(key: str) -> str:
    val = C[key]
    return val if val.startswith("#") else "#2c313c"


class _TimeSeriesPlot(pg.PlotWidget):
    """Rolling line chart with fill-under."""

    def __init__(self, title: str, color_key: str, window: int = 120,
                 y_max: float = 100.0, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self._color_key = color_key
        self._color_hex = C[color_key]
        self.showGrid(x=False, y=True, alpha=0.08)
        self.setMouseEnabled(False, False)
        self.hideButtons()
        self.setYRange(0, y_max, padding=0.04)
        self.getPlotItem().setTitle(
            f"<span style='color:{C['text_dim']};font-size:11px;"
            f"font-weight:600;'>{title.upper()}</span>"
        )
        for side in ("left", "bottom"):
            ax = self.getAxis(side)
            ax.setPen(_pg_pen("border"))
            ax.setTextPen(_pg_pen("text_dim"))
        self.setLabel("left", "%", color=_pg_pen("text_dim"))

        self._curve = self.plot(pen=pg.mkPen(color=_pg_color(color_key), width=2))
        self._baseline = self.plot(pen=None)
        self._fill: pg.FillBetweenItem | None = None
        self._data: deque[float] = deque(maxlen=window)

    def __repr__(self) -> str:
        return f"_TimeSeriesPlot({self._color_key!r}, points={len(self._data)})"

    def push(self, value: float) -> None:
        self._data.append(value)
        data = list(self._data)
        self._curve.setData(data)
        self._baseline.setData([0.0] * len(data))
        if self._fill is None and len(data) > 1:
            self._fill = pg.FillBetweenItem(
                self._curve, self._baseline,
                brush=pg.mkBrush(hex_to_qt_color(self._color_hex, 0.18)),
            )
            self.getPlotItem().addItem(self._fill)


class PerformancePage(ScrollablePage):
    HISTORY = 120

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        root = self.content_layout

        # KPIs
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)
        self._cpu_kpi = _KpiCard("CPU Load", "cpu")
        self._mem_kpi = _KpiCard("Memory Load", "mem")
        self._cores_kpi = _KpiCard("Active Cores", "accent")
        for k in (self._cpu_kpi, self._mem_kpi, self._cores_kpi):
            kpi_row.addWidget(k)
        root.addLayout(kpi_row)

        # Charts
        self._cpu_plot = _TimeSeriesPlot("Overall CPU Usage", "cpu")
        self._mem_plot = _TimeSeriesPlot("Memory Usage", "mem")

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(4)
        splitter.addWidget(self._wrap("CPU Performance", self._cpu_plot))
        splitter.addWidget(self._wrap("Memory Performance", self._mem_plot))
        splitter.setSizes([280, 280])
        root.addWidget(splitter, stretch=1)

        # Per-core
        self._core_card = Card("Per-Core Usage")
        self._core_layout = QHBoxLayout()
        self._core_layout.setSpacing(8)
        self._core_card.addLayout(self._core_layout)
        root.addWidget(self._core_card)
        self._core_bars: list[pg.BarGraphItem] = []

    def __repr__(self) -> str:
        return f"PerformancePage(cpu_pts={len(self._cpu_plot._data)})"

    def _wrap(self, title: str, widget: pg.PlotWidget) -> Card:
        card = Card(title)
        card.addWidget(widget)
        return card

    def update_data(self, snapshot: Snapshot) -> None:
        cpu = snapshot.cpu_percent
        mem = snapshot.memory.percent
        per_core = snapshot.cpu_per_core
        self._cpu_plot.push(cpu)
        self._mem_plot.push(mem)
        self._cpu_kpi.set_text(f"{cpu:.1f} %")
        self._mem_kpi.set_text(f"{mem:.1f} %")
        self._cores_kpi.set_text(str(len(per_core)))
        self._update_core_bars(per_core)

    def _update_core_bars(self, per_core: list[float]) -> None:
        if len(self._core_bars) != len(per_core):
            clear_layout(self._core_layout)
            self._core_bars.clear()
            for i in range(len(per_core)):
                bar = pg.BarGraphItem(
                    x=[0], height=[0], width=0.55,
                    brush=pg.mkBrush(_pg_color("cpu")),
                    pen=pg.mkPen(None),
                )
                pw = pg.PlotWidget()
                pw.setBackground(C["surface"])
                pw.setMouseEnabled(False, False)
                pw.hideButtons()
                pw.getPlotItem().hideAxis("left")
                pw.getPlotItem().hideAxis("bottom")
                pw.addItem(bar)
                pw.getPlotItem().setTitle(
                    f"<div style='color:{C['text_dim']};"
                    f"font-size:10px;font-weight:600;'>C{i}</div>"
                )
                self._core_layout.addWidget(pw)
                self._core_bars.append(bar)
        for bar, val in zip(self._core_bars, per_core):
            bar.setOpts(height=[val])


class _KpiCard(Card):
    """Small headline KPI card. Uses set_text() to avoid shadowing QWidget.set()."""

    def __init__(self, title: str, color_key: str):
        super().__init__(title=title)
        self._color_key = color_key
        self._value_label = QLabel("--")
        self._value_label.setStyleSheet(
            f"color:{C[color_key]};font-size:28px;font-weight:800;"
            "letter-spacing:-0.5px;"
        )
        self.addWidget(self._value_label)
        self.addStretch()

    def __repr__(self) -> str:
        return f"_KpiCard({self._value_label.text()!r})"

    def set_text(self, text: str) -> None:
        self._value_label.setText(text)
