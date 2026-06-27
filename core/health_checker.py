"""
core/health_checker.py

Aggregates high-level "health" verdicts from the raw system metrics.
Returns typed HealthResult objects instead of bare (status, message) tuples.
"""
from __future__ import annotations

from core.system_data import SystemData
from core.snapshot import HealthResult, Snapshot


class HealthChecker:
    """Stateless evaluator that turns metrics into human health signals."""

    GOOD = "good"
    WARN = "warning"
    CRIT = "critical"

    # Resource thresholds (percent)
    CPU_WARN = 75.0
    CPU_CRIT = 90.0
    MEM_WARN = 75.0
    MEM_CRIT = 90.0
    DISK_WARN = 80.0
    DISK_CRIT = 95.0
    BAT_WARN = 30.0
    BAT_CRIT = 15.0

    def __repr__(self) -> str:
        return "HealthChecker()"

    # ------------------------------------------------------------------ #
    @classmethod
    def _classify(cls, value: float, warn: float, crit: float) -> str:
        if value >= crit:
            return cls.CRIT
        if value >= warn:
            return cls.WARN
        return cls.GOOD

    # ------------------------------------------------------------------ #
    @classmethod
    def cpu_health(cls, snapshot: Snapshot | None = None) -> HealthResult:
        pct = snapshot.cpu_percent if snapshot else SystemData.cpu_percent()
        status = cls._classify(pct, cls.CPU_WARN, cls.CPU_CRIT)
        return HealthResult(status=status, message=f"CPU usage at {pct:.1f}%")

    @classmethod
    def memory_health(cls, snapshot: Snapshot | None = None) -> HealthResult:
        if snapshot:
            pct = snapshot.memory.percent
        else:
            pct = SystemData.memory().percent
        status = cls._classify(pct, cls.MEM_WARN, cls.MEM_CRIT)
        return HealthResult(status=status, message=f"Memory usage at {pct:.1f}%")

    @classmethod
    def disk_health(cls, snapshot: Snapshot | None = None) -> HealthResult:
        if snapshot:
            disks = snapshot.disks
        else:
            disks = SystemData.disks()
        if not disks:
            return HealthResult(status=cls.GOOD, message="No disks detected")
        worst = max(disks, key=lambda d: d.percent)
        status = cls._classify(worst.percent, cls.DISK_WARN, cls.DISK_CRIT)
        return HealthResult(
            status=status,
            message=f"{worst.device} at {worst.percent:.1f}%",
        )

    @classmethod
    def battery_health(cls, snapshot: Snapshot | None = None) -> HealthResult:
        bat = snapshot.battery if snapshot else SystemData.battery()
        if bat is None:
            return HealthResult(status=cls.GOOD, message="No battery present")
        if bat.plugged:
            return HealthResult(
                status=cls.GOOD,
                message=f"Charging ({bat.percent:.0f}%)",
            )
        status = cls._classify(100 - bat.percent, cls.BAT_WARN, cls.BAT_CRIT)
        if status == cls.CRIT:
            msg = f"Battery low: {bat.percent:.0f}%"
        elif status == cls.WARN:
            msg = f"Battery draining: {bat.percent:.0f}%"
        else:
            msg = f"Battery healthy: {bat.percent:.0f}%"
        return HealthResult(status=status, message=msg)

    @classmethod
    def overall(cls, snapshot: Snapshot | None = None) -> HealthResult:
        """Roll up every subsystem into a single verdict."""
        checks = [
            cls.cpu_health(snapshot),
            cls.memory_health(snapshot),
            cls.disk_health(snapshot),
            cls.battery_health(snapshot),
        ]
        statuses = [c.status for c in checks]
        if cls.CRIT in statuses:
            return HealthResult(status=cls.CRIT, message="Critical: action required")
        if cls.WARN in statuses:
            return HealthResult(status=cls.WARN, message="Some resources under pressure")
        return HealthResult(status=cls.GOOD, message="All systems nominal")
