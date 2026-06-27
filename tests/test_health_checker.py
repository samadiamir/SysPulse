"""
tests/test_health_checker.py

Tests HealthChecker with typed HealthResult returns.
"""
from __future__ import annotations

import pytest
from core import health_checker
from core.health_checker import HealthChecker
from core.snapshot import Snapshot, MemoryInfo, DiskInfo, NetworkInfo, BatteryInfo


def _make_snapshot(**overrides) -> Snapshot:
    """Build a Snapshot with sensible defaults, overridden as needed."""
    defaults = dict(
        cpu_percent=10.0,
        cpu_per_core=[10.0, 10.0, 10.0, 10.0],
        memory=MemoryInfo(total=16 * 1024**3, available=12 * 1024**3,
                          used=4 * 1024**3, percent=25.0),
        disks=[DiskInfo(device="C:", mountpoint="C:\\", fstype="NTFS",
                        total=500 * 1024**3, used=200 * 1024**3,
                        free=300 * 1024**3, percent=40.0)],
        network=NetworkInfo(bytes_sent=1024, bytes_recv=2048),
        battery=BatteryInfo(percent=90.0, plugged=True, secs_left=-1),
    )
    defaults.update(overrides)
    return Snapshot(**defaults)


class TestClassification:
    def test_below_warn_is_good(self):
        snap = _make_snapshot(cpu_percent=10.0)
        r = HealthChecker.cpu_health(snap)
        assert r.is_good

    def test_at_warn_is_warning(self):
        snap = _make_snapshot(cpu_percent=HealthChecker.CPU_WARN)
        r = HealthChecker.cpu_health(snap)
        assert r.is_warning

    def test_at_crit_is_critical(self):
        snap = _make_snapshot(cpu_percent=HealthChecker.CPU_CRIT)
        r = HealthChecker.cpu_health(snap)
        assert r.is_critical


class TestMemoryAndDisk:
    def test_memory_warning(self):
        snap = _make_snapshot(
            memory=MemoryInfo(total=16 * 1024**3, available=2 * 1024**3,
                              used=14 * 1024**3, percent=HealthChecker.MEM_WARN)
        )
        r = HealthChecker.memory_health(snap)
        assert r.is_warning

    def test_disk_uses_worst_partition(self):
        snap = _make_snapshot(disks=[
            DiskInfo(device="C:", mountpoint="C:\\", fstype="NTFS",
                     total=100, used=10, free=90, percent=10.0),
            DiskInfo(device="D:", mountpoint="D:\\", fstype="NTFS",
                     total=100, used=85, free=15, percent=85.0),
        ])
        r = HealthChecker.disk_health(snap)
        assert r.is_warning
        assert "D:" in r.message

    def test_disk_empty_is_good(self):
        snap = _make_snapshot(disks=[])
        r = HealthChecker.disk_health(snap)
        assert r.is_good


class TestBattery:
    def test_no_battery(self):
        snap = _make_snapshot(battery=None)
        r = HealthChecker.battery_health(snap)
        assert r.is_good
        assert "No battery" in r.message

    def test_plugged_is_good(self):
        snap = _make_snapshot(
            battery=BatteryInfo(percent=5.0, plugged=True, secs_left=-1)
        )
        r = HealthChecker.battery_health(snap)
        assert r.is_good

    def test_low_battery_critical(self):
        snap = _make_snapshot(
            battery=BatteryInfo(percent=10.0, plugged=False, secs_left=600)
        )
        r = HealthChecker.battery_health(snap)
        assert r.is_critical
        assert "10" in r.message


class TestOverall:
    def test_all_good(self):
        snap = _make_snapshot()
        r = HealthChecker.overall(snap)
        assert r.is_good

    def test_one_critical_propagates(self):
        snap = _make_snapshot(cpu_percent=99.0)
        r = HealthChecker.overall(snap)
        assert r.is_critical

    def test_one_warning_propagates_when_no_critical(self):
        snap = _make_snapshot(
            memory=MemoryInfo(total=16 * 1024**3, available=2 * 1024**3,
                              used=14 * 1024**3, percent=80.0)
        )
        r = HealthChecker.overall(snap)
        assert r.is_warning


class TestRepr:
    def test_health_result_repr(self):
        r = HealthChecker.cpu_health(_make_snapshot())
        assert "HealthResult" in repr(r)
        assert r.status in repr(r)
