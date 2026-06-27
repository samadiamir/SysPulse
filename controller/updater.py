"""
controller/updater.py

Drives periodic refresh of the UI with fresh system data.
Uses typed Snapshot objects and the PageSubscriber Protocol.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal

from core.system_data import SystemData
from core.snapshot import Snapshot
from ui.page_protocol import PageSubscriber


class Updater(QObject):
    """Periodic data pump.

    Pages register via :meth:`subscribe` and must implement the
    :class:`PageSubscriber` protocol. The :attr:`ticked` signal is
    also available for ad-hoc consumers.
    """

    ticked = Signal(object)  # emits Snapshot

    def __init__(self, interval_ms: int = 1500, parent: QObject | None = None):
        super().__init__(parent)
        self._interval = interval_ms
        self._timer = QTimer(self)
        self._timer.setInterval(self._interval)
        self._timer.timeout.connect(self._on_timeout)
        self._subscribers: list[PageSubscriber] = []

    def __repr__(self) -> str:
        return (f"Updater(interval={self._interval}ms, "
                f"subscribers={len(self._subscribers)})")

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #
    def subscribe(self, page: PageSubscriber) -> None:
        """Register a page that implements the PageSubscriber protocol.
        Raises TypeError if *page* does not implement update_data().
        """
        if not hasattr(page, "update_data") or not callable(page.update_data):
            raise TypeError(
                f"{type(page).__name__} does not implement PageSubscriber "
                f"(missing update_data method)"
            )
        self._subscribers.append(page)

    def unsubscribe(self, page: PageSubscriber) -> None:
        """Remove a previously registered page."""
        self._subscribers = [s for s in self._subscribers if s is not page]

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)

    def start(self) -> None:
        """Start the periodic update loop. Dispatches one tick immediately."""
        self._dispatch(self._snapshot())
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def refresh_now(self) -> None:
        """Public trigger for a manual one-off refresh."""
        self._dispatch(self._snapshot())

    def set_interval(self, interval_ms: int) -> None:
        self._interval = interval_ms
        self._timer.setInterval(interval_ms)

    # ------------------------------------------------------------------ #
    #  Internals
    # ------------------------------------------------------------------ #
    def _on_timeout(self) -> None:
        snapshot = self._snapshot()
        self.ticked.emit(snapshot)
        self._dispatch(snapshot)

    def _dispatch(self, snapshot: Snapshot) -> None:
        for page in self._subscribers:
            page.update_data(snapshot)

    @staticmethod
    def _snapshot() -> Snapshot:
        return SystemData.snapshot()
