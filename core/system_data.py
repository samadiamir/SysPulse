"""
core/system_data.py

Centralized provider for real-time and static system information.
Includes a lightweight TTL cache so expensive OS calls (disk I/O)
don't repeat every single refresh cycle.

Returns typed dataclass objects instead of raw dicts.
"""
from __future__ import annotations

import time
import psutil
import cpuinfo
import platform
import socket
from typing import Any

from core.snapshot import (
    Snapshot, MemoryInfo, DiskInfo, NetworkInfo, BatteryInfo, ProcessInfo,
)


class _TTLCache:
    """Simple key→value cache that expires after *ttl* seconds."""

    def __init__(self, ttl: float = 4.0):
        self._ttl = ttl
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str, factory) -> Any:
        now = time.monotonic()
        if key in self._store:
            ts, val = self._store[key]
            if now - ts < self._ttl:
                return val
        val = factory()
        self._store[key] = (now, val)
        return val

    def invalidate(self, key: str | None = None) -> None:
        if key is None:
            self._store.clear()
        else:
            self._store.pop(key, None)

    def __repr__(self) -> str:
        return f"_TTLCache(ttl={self._ttl}s, entries={len(self._store)})"


# Module-level cache instance
_cache = _TTLCache(ttl=4.0)


class SystemData:
    """Read-only accessor for system metrics and hardware specs.

    All methods are classmethods/staticmethods — no instance needed.
    """

    _cpu_info_cache: dict | None = None

    def __repr__(self) -> str:
        return f"SystemData(brand={self.cpu_brand()})"

    # ------------------------------------------------------------------ #
    #  Static hardware / OS info
    # ------------------------------------------------------------------ #
    @classmethod
    def cpu_info(cls) -> dict:
        if cls._cpu_info_cache is None:
            cls._cpu_info_cache = cpuinfo.get_cpu_info()
        return cls._cpu_info_cache

    @classmethod
    def cpu_brand(cls) -> str:
        return cls.cpu_info().get("brand_raw", "Unknown CPU")

    @classmethod
    def cpu_cores_physical(cls) -> int:
        return psutil.cpu_count(logical=False) or 0

    @classmethod
    def cpu_cores_logical(cls) -> int:
        return psutil.cpu_count(logical=True) or 0

    # ------------------------------------------------------------------ #
    #  Real-time metrics (fast — no I/O)
    # ------------------------------------------------------------------ #
    @staticmethod
    def cpu_percent() -> float:
        return psutil.cpu_percent(interval=None)

    @staticmethod
    def cpu_per_core_percent() -> list[float]:
        return psutil.cpu_percent(interval=None, percpu=True)

    @staticmethod
    def memory() -> MemoryInfo:
        v = psutil.virtual_memory()
        return MemoryInfo(
            total=v.total,
            available=v.available,
            used=v.used,
            percent=v.percent,
        )

    # ------------------------------------------------------------------ #
    #  Slower metrics — TTL-cached
    # ------------------------------------------------------------------ #
    @staticmethod
    def _query_disks() -> list[DiskInfo]:
        out = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except (PermissionError, OSError):
                continue
            out.append(DiskInfo(
                device=part.device,
                mountpoint=part.mountpoint,
                fstype=part.fstype,
                total=usage.total,
                used=usage.used,
                free=usage.free,
                percent=usage.percent,
            ))
        return out

    @staticmethod
    def disks() -> list[DiskInfo]:
        return _cache.get("disks", SystemData._query_disks)

    @staticmethod
    def network() -> NetworkInfo:
        n = psutil.net_io_counters()
        return NetworkInfo(bytes_sent=n.bytes_sent, bytes_recv=n.bytes_recv)

    @staticmethod
    def battery() -> BatteryInfo | None:
        try:
            b = psutil.sensors_battery()
        except AttributeError:
            return None
        if b is None:
            return None
        return BatteryInfo(
            percent=b.percent,
            plugged=b.power_plugged,
            secs_left=b.secsleft,
        )

    @staticmethod
    def processes(top_n: int = 50) -> list[ProcessInfo]:
        """Return the top *top_n* processes sorted by CPU usage."""
        procs: list[ProcessInfo] = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent",
                                       "memory_percent", "memory_info",
                                       "status", "username"]):
            try:
                info = p.info
                rss = info.get("memory_info")
                rss_bytes = rss.rss if rss else 0
                procs.append(ProcessInfo(
                    pid=info["pid"],
                    name=info.get("name", "—"),
                    cpu_percent=info.get("cpu_percent", 0.0) or 0.0,
                    memory_percent=info.get("memory_percent", 0.0) or 0.0,
                    memory_rss=rss_bytes,
                    status=info.get("status", "—"),
                    username=info.get("username", "—") or "—",
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied,
                    psutil.ZombieProcess):
                continue
        procs.sort(key=lambda p: p.cpu_percent, reverse=True)
        return procs[:top_n]

    @staticmethod
    def kill_process(pid: int) -> bool:
        """Attempt to terminate a process by PID. Returns True on success."""
        try:
            p = psutil.Process(pid)
            p.terminate()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    # ------------------------------------------------------------------ #
    #  OS / platform
    # ------------------------------------------------------------------ #
    @staticmethod
    def os_info() -> dict:
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "hostname": socket.gethostname(),
        }

    # ------------------------------------------------------------------ #
    #  Snapshot builder
    # ------------------------------------------------------------------ #
    @classmethod
    def snapshot(cls) -> Snapshot:
        """Collect a single typed snapshot of all metrics."""
        return Snapshot(
            cpu_percent=cls.cpu_percent(),
            cpu_per_core=cls.cpu_per_core_percent(),
            memory=cls.memory(),
            disks=cls.disks(),
            network=cls.network(),
            battery=cls.battery(),
        )

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def human_bytes(num: int | float, suffix: str = "B") -> str:
        for unit in ("", "K", "M", "G", "T", "P"):
            if abs(num) < 1024.0:
                return f"{num:3.1f} {unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f} E{suffix}"
