"""
tests/test_system_data.py

Tests for SystemData — now with typed return objects.
"""
from __future__ import annotations

import pytest
from core.system_data import SystemData
from core.snapshot import MemoryInfo, DiskInfo, NetworkInfo, BatteryInfo, Snapshot


class TestCpuInfo:
    def test_cpu_brand_is_nonempty_string(self):
        assert isinstance(SystemData.cpu_brand(), str)
        assert SystemData.cpu_brand().strip() != ""

    def test_cpu_brand_is_cached(self):
        assert SystemData.cpu_brand() is SystemData.cpu_brand()

    def test_physical_and_logical_cores_positive(self):
        assert SystemData.cpu_cores_physical() >= 1
        assert SystemData.cpu_cores_logical() >= SystemData.cpu_cores_physical()


class TestRealtimeMetrics:
    def test_cpu_percent_in_range(self):
        pct = SystemData.cpu_percent()
        assert isinstance(pct, float)
        assert 0.0 <= pct <= 100.0

    def test_cpu_per_core_count_matches_logical(self):
        per_core = SystemData.cpu_per_core_percent()
        assert len(per_core) == SystemData.cpu_cores_logical()

    def test_memory_returns_memoryinfo(self):
        mem = SystemData.memory()
        assert isinstance(mem, MemoryInfo)
        assert mem.total > 0
        assert mem.used <= mem.total
        assert 0.0 <= mem.percent <= 100.0


class TestDisks:
    def test_disks_returns_list_of_diskinfo(self):
        disks = SystemData.disks()
        assert isinstance(disks, list)
        if disks:
            assert isinstance(disks[0], DiskInfo)
            assert disks[0].total >= disks[0].used
            assert 0.0 <= disks[0].percent <= 100.0


class TestNetwork:
    def test_network_returns_networkinfo(self):
        net = SystemData.network()
        assert isinstance(net, NetworkInfo)
        assert net.bytes_sent >= 0
        assert net.bytes_recv >= 0


class TestBattery:
    def test_battery_returns_info_or_none(self):
        bat = SystemData.battery()
        if bat is not None:
            assert isinstance(bat, BatteryInfo)
            assert 0.0 <= bat.percent <= 100.0


class TestSnapshot:
    def test_snapshot_returns_typed_snapshot(self):
        snap = SystemData.snapshot()
        assert isinstance(snap, Snapshot)
        assert isinstance(snap.memory, MemoryInfo)
        assert isinstance(snap.network, NetworkInfo)
        assert all(isinstance(d, DiskInfo) for d in snap.disks)

    def test_snapshot_repr(self):
        snap = SystemData.snapshot()
        r = repr(snap)
        assert "Snapshot" in r
        assert "cpu=" in r


class TestOsInfo:
    def test_os_info_has_keys(self):
        info = SystemData.os_info()
        assert {"system", "release", "version", "machine",
                "processor", "hostname"} <= set(info)


class TestHumanBytes:
    @pytest.mark.parametrize("value, suffix, expected_prefix", [
        (0, "B", "0.0 B"),
        (1024, "B", "K"),
        (1024 ** 2, "B", "M"),
        (1024 ** 3, "B", "G"),
        (1024 ** 4, "B", "T"),
    ])
    def test_unit_progression(self, value, suffix, expected_prefix):
        result = SystemData.human_bytes(value, suffix)
        assert expected_prefix in result

    def test_custom_suffix(self):
        assert "bit" in SystemData.human_bytes(2048, suffix="bit")
