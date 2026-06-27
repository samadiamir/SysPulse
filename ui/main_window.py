"""
ui/main_window.py

Application shell: modern sidebar + stacked pages + settings integration.
Features: lazy pages, notification alerts, export to CSV/JSON.
"""
from __future__ import annotations

import logging

try:
    import qtawesome as qta
except ImportError:
    qta = None

try:
    import qdarktheme
except ImportError:
    qdarktheme = None

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QPushButton,
    QStackedWidget, QLabel, QButtonGroup, QStatusBar, QMessageBox,
    QFileDialog,
)

from ui.styles import C, set_active_theme, build_qss, THEMES
from ui.settings_page import SettingsPage
from controller.updater import Updater
from controller.settings_manager import SettingsManager
from controller.alert_manager import AlertManager
from controller import exporter

_log = logging.getLogger(__name__)

# Page specs: (display name, fa-icon, import path, class name)
NAV_ITEMS = [
    ("Dashboard",   "fa5s.tachometer-alt",
     "ui.dashboard_page",   "DashboardPage"),
    ("Performance", "fa5s.chart-line",
     "ui.performance_page", "PerformancePage"),
    ("Processes",   "fa5s.tasks",
     "ui.process_page",     "ProcessPage"),
    ("Hardware",    "fa5s.microchip",
     "ui.hardware_page",    "HardwarePage"),
    ("Health",      "fa5s.heartbeat",
     "ui.health_page",      "HealthPage"),
    ("Customise",   "fa5s.sliders-h",
     "ui.customize_page",   "CustomizePage"),
    ("Settings",    "fa5s.cog",
     "ui.settings_page",    "SettingsPage"),
]

# Index constants for readability
_IDX_SETTINGS = 6


def _lazy_import(module_path: str, class_name: str):
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SysPulse — System Monitor")
        self.resize(1220, 780)
        self.setMinimumSize(1000, 660)

        self._sm = SettingsManager.instance()
        self._updater = Updater(interval_ms=self._sm.update_ms, parent=self)
        self._alert_mgr = AlertManager(cooldown_seconds=60, parent=self)
        self._pages: list[QWidget | None] = [None] * len(NAV_ITEMS)
        self._build_ui()
        self._wire_updater()
        self._wire_settings()
        self._wire_alerts()
        self._wire_customize()

    # ------------------------------------------------------------------ #
    #  UI construction
    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content(), stretch=1)
        self.setCentralWidget(central)
        self._build_statusbar()
        self._build_menubar()

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame(objectName="Sidebar")
        sidebar.setFixedWidth(240)
        v = QVBoxLayout(sidebar)
        v.setContentsMargins(20, 28, 20, 20)
        v.setSpacing(6)

        title = QLabel("SysPulse")
        title.setObjectName("AppTitle")
        subtitle = QLabel("SYSTEM MONITOR")
        subtitle.setObjectName("AppSubtitle")
        v.addWidget(title)
        v.addWidget(subtitle)
        v.addSpacing(24)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_buttons: list[QPushButton] = []

        for idx, (name, icon, _, _) in enumerate(NAV_ITEMS):
            btn = QPushButton(f"  {name}")
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            if icon and qta is not None:
                try:
                    btn.setIcon(qta.icon(icon, color=C["text_dim"]))
                except (ValueError, AttributeError) as exc:
                    _log.debug("Icon load failed for %s: %s", icon, exc)
            btn.clicked.connect(lambda _chk, i=idx: self._switch_page(i))
            self._nav_group.addButton(btn, idx)
            self._nav_buttons.append(btn)
            v.addWidget(btn)

        v.addStretch()
        hint = QLabel("v1.4  ·  Real-time")
        hint.setStyleSheet(f"color:{C['text_dim']};font-size:11px;")
        hint.setAlignment(Qt.AlignCenter)
        v.addWidget(hint)
        return sidebar

    def _build_content(self) -> QWidget:
        self._stack = QStackedWidget()
        for _ in NAV_ITEMS:
            self._stack.addWidget(QWidget())
        return self._stack

    def _ensure_page(self, idx: int) -> QWidget:
        page = self._pages[idx]
        if page is None:
            _, _, mod_path, cls_name = NAV_ITEMS[idx]
            cls = _lazy_import(mod_path, cls_name)
            page = cls()
            self._pages[idx] = page
            old = self._stack.widget(idx)
            self._stack.removeWidget(old)
            old.deleteLater()
            self._stack.insertWidget(idx, page)
            self._updater.subscribe(page)
        return page

    def _build_statusbar(self) -> None:
        bar = QStatusBar(self)
        bar.setSizeGripEnabled(False)
        self._status_label = QLabel("Ready")
        bar.addWidget(self._status_label, stretch=1)
        self._rate_label = QLabel(f"Refresh: {self._sm.update_ms / 1000:.1f} s")
        bar.addPermanentWidget(self._rate_label)
        self._alert_status = QLabel("🔔 Alerts: ON")
        self._alert_status.setStyleSheet(f"color:{C['text_dim']};font-size:11px;")
        bar.addPermanentWidget(self._alert_status)
        self.setStatusBar(bar)

    def _build_menubar(self) -> None:
        mb = self.menuBar()

        # File menu
        file_menu = mb.addMenu("&File")

        export_json_action = QAction("Export Snapshot as &JSON…", self)
        export_json_action.setShortcut("Ctrl+Shift+J")
        export_json_action.triggered.connect(self._export_json)
        file_menu.addAction(export_json_action)

        export_csv_action = QAction("Export Snapshot as &CSV…", self)
        export_csv_action.setShortcut("Ctrl+Shift+C")
        export_csv_action.triggered.connect(self._export_csv)
        file_menu.addAction(export_csv_action)

        file_menu.addSeparator()

        quit_action = QAction("E&xit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # View menu
        view_menu = mb.addMenu("&View")
        refresh_now = QAction("&Refresh now", self)
        refresh_now.setShortcut("F5")
        refresh_now.triggered.connect(self._manual_refresh)
        view_menu.addAction(refresh_now)

        view_menu.addSeparator()

        self._toggle_alerts_action = QAction("Disable &Notifications", self)
        self._toggle_alerts_action.triggered.connect(self._toggle_alerts)
        view_menu.addAction(self._toggle_alerts_action)

        # Help menu
        help_menu = mb.addMenu("&Help")
        about_action = QAction("&About SysPulse", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    # ------------------------------------------------------------------ #
    #  Navigation
    # ------------------------------------------------------------------ #
    def _switch_page(self, idx: int) -> None:
        self._ensure_page(idx)
        self._stack.setCurrentIndex(idx)
        self._status_label.setText(f"Viewing {NAV_ITEMS[idx][0]}")

    # ------------------------------------------------------------------ #
    #  Updater wiring
    # ------------------------------------------------------------------ #
    def _wire_updater(self) -> None:
        self._ensure_page(0)
        self._nav_buttons[0].setChecked(True)
        self._stack.setCurrentIndex(0)
        self._updater.start()
        self._status_label.setText("Monitoring…")

    def _manual_refresh(self) -> None:
        self._updater.refresh_now()
        self._status_label.setText("Refreshed manually")

    # ------------------------------------------------------------------ #
    #  Alerts wiring
    # ------------------------------------------------------------------ #
    def _wire_alerts(self) -> None:
        self._alert_mgr.alert_fired.connect(self._on_alert)

    def _on_alert(self, severity: str, title: str, message: str) -> None:
        """Show a desktop notification for a threshold breach."""
        _log.info("Alert [%s]: %s — %s", severity, title, message)
        # Use QMessageBox for now — on Windows could use win10toast
        if severity == "critical":
            QMessageBox.warning(self, title, message)
        else:
            self._status_label.setText(f"⚠ {title}: {message}")

    def _toggle_alerts(self) -> None:
        self._alert_mgr.enabled = not self._alert_mgr.enabled
        if self._alert_mgr.enabled:
            self._toggle_alerts_action.setText("Disable &Notifications")
            self._alert_status.setText("🔔 Alerts: ON")
        else:
            self._toggle_alerts_action.setText("Enable &Notifications")
            self._alert_status.setText("🔕 Alerts: OFF")

    # ------------------------------------------------------------------ #
    #  Export
    # ------------------------------------------------------------------ #
    def _export_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Snapshot as JSON",
            str(exporter.get_export_dir() / f"syspulse_{exporter._timestamp()}.json"),
            "JSON Files (*.json);;All Files (*)",
        )
        if not path:
            return
        from pathlib import Path
        snap = Updater._snapshot()
        out = exporter.export_json(snap, Path(path))
        self._status_label.setText(f"Exported JSON → {out.name}")

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Snapshot as CSV",
            str(exporter.get_export_dir() / f"syspulse_{exporter._timestamp()}.csv"),
            "CSV Files (*.csv);;All Files (*)",
        )
        if not path:
            return
        from pathlib import Path
        snap = Updater._snapshot()
        out = exporter.export_csv(snap, Path(path))
        self._status_label.setText(f"Exported CSV → {out.name}")

    # ------------------------------------------------------------------ #
    #  Settings wiring
    # ------------------------------------------------------------------ #
    def _wire_settings(self) -> None:
        settings_page = self._ensure_page(_IDX_SETTINGS)
        settings_page.theme_changed.connect(self._apply_theme)
        settings_page.accent_changed.connect(self._apply_accent)
        settings_page.font_changed.connect(self._apply_font)
        settings_page.interval_changed.connect(self._apply_interval)
        settings_page.density_changed.connect(self._apply_density)

    def _wire_customize(self) -> None:
        from ui.customize_page import CustomizePage
        customize_page = self._ensure_page(5)  # Customise is index 5
        customize_page.dashboard_changed.connect(self._on_dashboard_changed)

    def _on_dashboard_changed(self) -> None:
        """Refresh dashboard visibility when customize toggles change."""
        if self._pages[0] is not None:
            self._pages[0].refresh_visibility()

    def _rebuild_style(self) -> None:
        qss = build_qss(C, self._sm.font_family, self._sm.font_size,
                        self._sm.density)
        self.setStyleSheet(qss)

    def _apply_theme(self, theme_name: str) -> None:
        set_active_theme(theme_name)
        self._rebuild_style()

    def _apply_accent(self, color: str) -> None:
        C["accent"] = color
        self._rebuild_style()

    def _apply_font(self, _family: str, _size: int) -> None:
        self._rebuild_style()

    def _apply_density(self, _density: str) -> None:
        self._rebuild_style()

    def _apply_interval(self, ms: int) -> None:
        self._updater.set_interval(ms)
        self._rate_label.setText(f"Refresh: {ms / 1000:.1f} s")

    # ------------------------------------------------------------------ #
    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About SysPulse",
            "<h3>SysPulse</h3>"
            "<p>Real-time desktop system monitoring and hardware "
            "diagnostics.</p>"
            "<p>Built with Python, PySide6, psutil, PyQtGraph, "
            "QtAwesome and PyQtDarkTheme.</p>",
        )

    def closeEvent(self, event) -> None:
        self._updater.stop()
        super().closeEvent(event)


def apply_theme(app: QApplication, theme_name: str = "dark",
                font_family: str = "Segoe UI",
                font_size: int = 13, density: str = "normal") -> None:
    set_active_theme(theme_name)
    if qdarktheme is not None:
        try:
            qdarktheme.setup_theme(theme_name)
        except Exception as exc:
            _log.debug("qdarktheme setup failed: %s", exc)
    qss = build_qss(THEMES.get(theme_name, THEMES["dark"]),
                    font_family, font_size, density)
    app.setStyleSheet(qss)


from PySide6.QtWidgets import QApplication  # noqa: E402
