"""
controller/alert_manager.py

Monitors snapshots and fires desktop notifications when thresholds
are crossed. Uses a cooldown so the same alert doesn't spam.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Callable

from PySide6.QtCore import QObject, Signal

from core.snapshot import Snapshot, HealthResult
from core.health_checker import HealthChecker

_log = logging.getLogger(__name__)


class AlertManager(QObject):
    """Fires alerts when resource thresholds are breached.

    Uses a per-alert cooldown (default 60s) so the same condition
    doesn't trigger repeated notifications.
    """

    alert_fired = Signal(str, str, str)  # (severity, title, message)

    def __init__(self, cooldown_seconds: int = 60,
                 parent: QObject | None = None):
        super().__init__(parent)
        self._cooldown = timedelta(seconds=cooldown_seconds)
        self._last_fired: dict[str, datetime] = {}
        self._enabled = True
        # Severity -> (title, emoji)
        self._sev_config: dict[str, tuple[str, str]] = {
            "critical": ("Critical Alert", "🔴"),
            "warning":  ("Warning", "🟡"),
        }

    def __repr__(self) -> str:
        return (f"AlertManager(enabled={self._enabled}, "
                f"cooldown={self._cooldown.total_seconds():.0f}s, "
                f"fired={len(self._last_fired)})")

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #
    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def check(self, snapshot: Snapshot) -> None:
        """Evaluate the snapshot and fire alerts for any breaches."""
        if not self._enabled:
            return

        checks: list[tuple[str, HealthResult]] = [
            ("cpu",    HealthChecker.cpu_health(snapshot)),
            ("memory", HealthChecker.memory_health(snapshot)),
            ("disk",   HealthChecker.disk_health(snapshot)),
            ("battery", HealthChecker.battery_health(snapshot)),
        ]

        for key, result in checks:
            if result.is_critical or result.is_warning:
                self._maybe_fire(key, result)

    # ------------------------------------------------------------------ #
    #  Internals
    # ------------------------------------------------------------------ #
    def _maybe_fire(self, key: str, result: HealthResult) -> None:
        """Fire the alert only if the cooldown for *key* has elapsed."""
        now = datetime.now()
        last = self._last_fired.get(key)
        if last and (now - last) < self._cooldown:
            return

        self._last_fired[key] = now
        sev = result.status
        title_prefix, emoji = self._sev_config.get(sev, ("Alert", "⚠️"))
        title = f"{emoji} {title_prefix}: {key.capitalize()}"
        message = result.message

        _log.info("Alert fired: %s — %s", title, message)
        self.alert_fired.emit(sev, title, message)

    def dismiss(self, key: str) -> None:
        """Clear the cooldown for a specific alert key."""
        self._last_fired.pop(key, None)

    def dismiss_all(self) -> None:
        """Clear all cooldowns."""
        self._last_fired.clear()
