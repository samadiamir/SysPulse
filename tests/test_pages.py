"""
tests/test_pages.py

Page tests using typed Snapshot objects.
"""
from __future__ import annotations

import pytest
from PySide6.QtGui import QShowEvent

from ui.main_window import MainWindow, apply_theme
from ui.dashboard_page import DashboardPage
from ui.performance_page import PerformancePage
from ui.hardware_page import HardwarePage
from ui.health_page import HealthPage
from ui.settings_page import SettingsPage
from ui.customize_page import CustomizePage
from core.snapshot import Snapshot, MemoryInfo, DiskInfo, NetworkInfo, BatteryInfo


@pytest.fixture
def sample_snapshot() -> Snapshot:
    return Snapshot(
        cpu_percent=42.0,
        cpu_per_core=[10.0, 55.0, 30.0, 80.0],
        memory=MemoryInfo(
            total=16 * 1024**3, available=8 * 1024**3,
            used=8 * 1024**3, percent=50.0,
        ),
        disks=[DiskInfo(
            device="C:", mountpoint="C:\\", fstype="NTFS",
            total=500 * 1024**3, used=250 * 1024**3,
            free=250 * 1024**3, percent=50.0,
        )],
        network=NetworkInfo(bytes_sent=1024, bytes_recv=2048),
        battery=BatteryInfo(percent=80.0, plugged=True, secs_left=-1),
    )


# --------------------------------------------------------------------------- #
#  Dashboard
# --------------------------------------------------------------------------- #
class TestDashboardPage:
    def test_construction(qapp):
        DashboardPage()

    def test_update_data_sets_gauges(qapp, sample_snapshot):
        page = DashboardPage()
        page.update_data(sample_snapshot)
        assert page._cpu_col._gauge.value == pytest.approx(42.0)
        assert page._mem_col._gauge.value == pytest.approx(50.0)

    def test_update_data_disk_card(qapp, sample_snapshot):
        page = DashboardPage()
        page.update_data(sample_snapshot)
        assert "50%" in page._disk_card._value_label.text()

    def test_update_data_battery_plugged(qapp, sample_snapshot):
        page = DashboardPage()
        page.update_data(sample_snapshot)
        assert "80%" in page._battery_card._value_label.text()
        assert "Plugged" in page._battery_card._sub_label.text()

    def test_update_data_no_battery(qapp, sample_snapshot):
        page = DashboardPage()
        sample_snapshot.battery = None
        page.update_data(sample_snapshot)
        assert "N/A" in page._battery_card._value_label.text()

    def test_gauge_column_encapsulation(qapp):
        """_GaugeColumn exposes set_value(), not gauge directly."""
        from ui.dashboard_page import _GaugeColumn
        col = _GaugeColumn("TEST", "#4f8cff")
        col.set_value(55.0, "detail text")
        assert col._gauge.value == pytest.approx(55.0)
        assert col._detail_label.text() == "detail text"

    def test_repr(qapp):
        page = DashboardPage()
        assert "DashboardPage" in repr(page)


# --------------------------------------------------------------------------- #
#  Performance
# --------------------------------------------------------------------------- #
class TestPerformancePage:
    def test_construction(qapp):
        PerformancePage()

    def test_update_data_sets_kpis(qapp, sample_snapshot):
        page = PerformancePage()
        page.update_data(sample_snapshot)
        assert "42.0" in page._cpu_kpi._value_label.text()
        assert "50.0" in page._mem_kpi._value_label.text()
        assert page._cores_kpi._value_label.text() == "4"

    def test_push_appends_history(qapp, sample_snapshot):
        page = PerformancePage()
        page.update_data(sample_snapshot)
        page.update_data(sample_snapshot)
        assert len(page._cpu_plot._data) == 2
        assert len(page._mem_plot._data) == 2

    def test_core_bars_match_core_count(qapp, sample_snapshot):
        page = PerformancePage()
        page.update_data(sample_snapshot)
        assert len(page._core_bars) == len(sample_snapshot.cpu_per_core)

    def test_core_count_change_rebuilds_bars(qapp, sample_snapshot):
        page = PerformancePage()
        sample_snapshot.cpu_per_core = [10.0, 20.0, 30.0]
        page.update_data(sample_snapshot)
        assert len(page._core_bars) == 3
        sample_snapshot.cpu_per_core = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        page.update_data(sample_snapshot)
        assert len(page._core_bars) == 6

    def test_repr(qapp):
        page = PerformancePage()
        assert "PerformancePage" in repr(page)


# --------------------------------------------------------------------------- #
#  Hardware
# --------------------------------------------------------------------------- #
class TestHardwarePage:
    def test_construction(qapp):
        HardwarePage()

    def test_populate_on_show(qapp):
        page = HardwarePage()
        assert page._populated is False
        page.showEvent(QShowEvent())
        assert page._populated is True
        assert page._processor_card._value_label.text().strip() != ""

    def test_update_data_refreshes_memory(qapp, sample_snapshot):
        page = HardwarePage()
        page.update_data(sample_snapshot)
        assert "Used" in page._mem_rows._rows
        page._mem_rows.update_value("Used", "8.0 GB")
        assert page._mem_rows._rows["Used"].value == "8.0 GB"

    def test_repr(qapp):
        page = HardwarePage()
        assert "HardwarePage" in repr(page)


# --------------------------------------------------------------------------- #
#  Health
# --------------------------------------------------------------------------- #
class TestHealthPage:
    def test_construction(qapp):
        HealthPage()

    def test_update_data_sets_badge(qapp, sample_snapshot):
        page = HealthPage()
        page.update_data(sample_snapshot)
        text = page._overall_badge.text().upper()
        assert text in ("HEALTHY", "WARNING", "CRITICAL")

    def test_tips_rendered(qapp, sample_snapshot):
        page = HealthPage()
        page.update_data(sample_snapshot)
        assert len(page._tips_label.text()) > 0

    def test_repr(qapp):
        page = HealthPage()
        assert "HealthPage" in repr(page)


# --------------------------------------------------------------------------- #
#  Main window integration
# --------------------------------------------------------------------------- #
class TestMainWindow:
    def test_construction_builds_pages(qapp):
        win = MainWindow()
        assert len(win._pages) == 7
        assert win._pages[0] is not None   # Dashboard
        assert win._pages[6] is not None   # Settings
        assert win._pages[5] is not None   # Customise
        assert win._pages[1] is None       # Performance (lazy)
        win._updater.stop()

    def test_switch_page_changes_stack(qapp):
        win = MainWindow()
        for i in range(7):
            win._switch_page(i)
            assert win._stack.currentIndex() == i
            assert win._pages[i] is not None
        win._updater.stop()


def test_apply_theme_runs(qapp):
    apply_theme(qapp, "dark")
