"""
ui/process_page.py

Live process viewer with sortable table and kill capability.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QAbstractItemView,
    QComboBox, QLineEdit, QMessageBox,
)

from ui.styles import C
from ui.base_page import ScrollablePage
from ui.widgets import Card
from core.system_data import SystemData
from core.snapshot import Snapshot, ProcessInfo


class ProcessPage(ScrollablePage):
    """Live process table with search, sort and kill."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._sort_column = 2   # default: CPU %
        self._sort_order = Qt.DescendingOrder
        self._processes: list[ProcessInfo] = []
        self._build_content()

    def __repr__(self) -> str:
        return f"ProcessPage(processes={len(self._processes)})"

    # ------------------------------------------------------------------ #
    #  UI
    # ------------------------------------------------------------------ #
    def _build_content(self) -> None:
        root = self.content_layout

        # Header row
        header = QHBoxLayout()
        header.setSpacing(12)
        title = QLabel("Running Processes")
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch()

        # Search
        self._search = QLineEdit()
        self._search.setPlaceholderText("  Filter by name…")
        self._search.setFixedWidth(220)
        self._search.setStyleSheet(
            f"background:{C['surface']};border:1px solid {C['border']};"
            f"border-radius:10px;padding:8px 12px;color:{C['text']};"
        )
        self._search.textChanged.connect(self._apply_filter)
        header.addWidget(self._search)

        # Refresh button
        self._refresh_btn = QPushButton("  Refresh")
        self._refresh_btn.setObjectName("SecondaryBtn")
        self._refresh_btn.setCursor(Qt.PointingHandCursor)
        self._refresh_btn.clicked.connect(self._refresh_processes)
        header.addWidget(self._refresh_btn)

        root.addLayout(header)

        # Stats bar
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        self._count_label = QLabel("0 processes")
        self._count_label.setStyleSheet(f"color:{C['text_dim']};font-size:12px;")
        stats_row.addWidget(self._count_label)
        stats_row.addStretch()
        self._kill_btn = QPushButton("  End Process")
        self._kill_btn.setObjectName("PrimaryBtn")
        self._kill_btn.setCursor(Qt.PointingHandCursor)
        self._kill_btn.setEnabled(False)
        self._kill_btn.clicked.connect(self._kill_selected)
        stats_row.addWidget(self._kill_btn)
        root.addLayout(stats_row)

        # Table
        table_card = Card()
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["PID", "Name", "CPU %", "Memory %", "RSS", "Status"]
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().sectionClicked.connect(self._on_sort)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet(
            f"QTableWidget {{ background:{C['surface']}; "
            f"color:{C['text']}; border:none; "
            f"alternate-background-color:{C['surface_alt']}; }}"
            f"QHeaderView::section {{ background:{C['surface']}; "
            f"color:{C['text_dim']}; border:none; "
            f"font-weight:600; padding:8px; }}"
            f"QTableWidget::item:selected {{ background:{C['accent']}; }}"
        )
        header_view = self._table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self._table.itemSelectionChanged.connect(self._on_selection_changed)

        table_card.addWidget(self._table)
        root.addWidget(table_card, stretch=1)

    # ------------------------------------------------------------------ #
    #  Data contract
    # ------------------------------------------------------------------ #
    def update_data(self, snapshot: Snapshot) -> None:
        """Called by Updater on each tick — refreshes process list."""
        self._refresh_processes()

    def _refresh_processes(self) -> None:
        self._processes = SystemData.processes(top_n=80)
        self._populate_table()

    def _populate_table(self) -> None:
        filter_text = self._search.text().lower()
        filtered = [p for p in self._processes
                    if filter_text in p.name.lower()] if filter_text else self._processes

        self._table.setRowCount(len(filtered))
        for row, proc in enumerate(filtered):
            items = [
                str(proc.pid),
                proc.name,
                f"{proc.cpu_percent:.1f}",
                f"{proc.memory_percent:.1f}",
                SystemData.human_bytes(proc.memory_rss),
                proc.status,
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter if col != 1 else Qt.AlignLeft)
                # Right-align numeric columns
                if col in (0, 2, 3, 4):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self._table.setItem(row, col, item)

        self._count_label.setText(f"{len(filtered)} processes")
        self._table.sortItems(self._sort_column, self._sort_order)

    # ------------------------------------------------------------------ #
    #  Sorting
    # ------------------------------------------------------------------ #
    def _on_sort(self, column: int) -> None:
        if column == self._sort_column:
            self._sort_order = (Qt.DescendingOrder
                                if self._sort_order == Qt.AscendingOrder
                                else Qt.AscendingOrder)
        else:
            self._sort_column = column
            self._sort_order = Qt.DescendingOrder
        self._table.sortItems(self._sort_column, self._sort_order)

    # ------------------------------------------------------------------ #
    #  Filtering
    # ------------------------------------------------------------------ #
    def _apply_filter(self, _text: str) -> None:
        self._populate_table()

    # ------------------------------------------------------------------ #
    #  Kill process
    # ------------------------------------------------------------------ #
    def _on_selection_changed(self) -> None:
        has_selection = len(self._table.selectedItems()) > 0
        self._kill_btn.setEnabled(has_selection)

    def _kill_selected(self) -> None:
        rows = set()
        for item in self._table.selectedItems():
            rows.add(item.row())
        if not rows:
            return
        row = rows.pop()
        pid_item = self._table.item(row, 0)
        name_item = self._table.item(row, 1)
        if pid_item is None or name_item is None:
            return
        pid = int(pid_item.text())
        name = name_item.text()

        reply = QMessageBox.question(
            self,
            "End Process",
            f"Are you sure you want to end process?\n\n"
            f"  PID:  {pid}\n  Name: {name}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            success = SystemData.kill_process(pid)
            if success:
                self._refresh_processes()
            else:
                QMessageBox.warning(
                    self, "Failed",
                    f"Could not terminate process {pid} ({name}).\n"
                    f"It may have already exited or you lack permissions.",
                )
