"""
tests/test_updater.py

Tests the periodic update driver with typed Snapshot objects.
"""
from __future__ import annotations

import pytest
from PySide6.QtCore import QTimer
from controller.updater import Updater
from core.snapshot import Snapshot


class FakePage:
    """Records every snapshot it receives for assertions."""
    def __init__(self):
        self.snapshots: list[Snapshot] = []

    def update_data(self, snapshot: Snapshot) -> None:
        self.snapshots.append(snapshot)


class TestSnapshot:
    def test_snapshot_returns_typed_object(self):
        snap = Updater._snapshot()
        assert isinstance(snap, Snapshot)
        assert hasattr(snap, "cpu_percent")
        assert hasattr(snap, "memory")
        assert hasattr(snap, "disks")
        assert hasattr(snap, "network")

    def test_snapshot_is_fresh_each_call(self):
        a = Updater._snapshot()
        b = Updater._snapshot()
        assert a is not b


class TestSubscription:
    def test_subscribe_calls_update_data(qapp):
        updater = Updater(interval_ms=10000)
        page = FakePage()
        updater.subscribe(page)
        updater._dispatch(Updater._snapshot())
        assert len(page.snapshots) == 1
        assert isinstance(page.snapshots[0], Snapshot)

    def test_unsubscribe_removes_page(qapp):
        updater = Updater(interval_ms=10000)
        page = FakePage()
        updater.subscribe(page)
        assert updater.subscriber_count == 1
        updater.unsubscribe(page)
        assert updater.subscriber_count == 0

    def test_subscriber_without_update_data_raises(qapp):
        updater = Updater(interval_ms=10000)
        class Bare:
            pass
        with pytest.raises(TypeError, match="does not implement"):
            updater.subscribe(Bare())


class TestTimerLifecycle:
    def test_start_primes_subscribers(qapp):
        updater = Updater(interval_ms=10000)
        page = FakePage()
        updater.subscribe(page)
        updater.start()
        assert len(page.snapshots) == 1
        updater.stop()

    def test_stop_halts_delivery(qapp, qtbot):
        updater = Updater(interval_ms=50)
        page = FakePage()
        updater.subscribe(page)
        updater.start()
        updater.stop()
        before = len(page.snapshots)
        qtbot.wait(200)
        assert len(page.snapshots) == before

    def test_set_interval_changes_timing(qapp):
        updater = Updater(interval_ms=1000)
        updater.set_interval(5000)
        assert updater._timer.interval() == 5000


class TestRefreshNow:
    def test_refresh_now_dispatches(qapp):
        updater = Updater(interval_ms=10000)
        page = FakePage()
        updater.subscribe(page)
        updater.refresh_now()
        assert len(page.snapshots) == 1


class TestTickedSignal:
    def test_signal_emits_with_snapshot(qapp, qtbot):
        updater = Updater(interval_ms=50)
        received: list[Snapshot] = []
        updater.ticked.connect(lambda s: received.append(s))
        updater.start()
        qtbot.waitUntil(lambda: len(received) >= 2, timeout=2000)
        updater.stop()
        assert len(received) >= 2
        assert isinstance(received[0], Snapshot)


class TestRepr:
    def test_updater_repr(qapp):
        updater = Updater(interval_ms=2000)
        assert "Updater" in repr(updater)
        assert "2000" in repr(updater)
