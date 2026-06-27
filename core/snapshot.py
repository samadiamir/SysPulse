"""
core/snapshot.py

Typed data structures that replace raw dicts flowing through the system.
Using dataclasses gives us:
  - Named fields (no string-key dict access)
  - Type hints (IDE autocomplete, static checking)
  - __repr__ for free (debugging)
  - Immutability via frozen=True where appropriate
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MemoryInfo:
    total: int
    available: int
    used: int
    percent: float

    def __repr__(self) -> str:
        from core.system_data import SystemData as _SD
        return (f"MemoryInfo(used={_SD.human_bytes(self.used)}/"
                f"{_SD.human_bytes(self.total)}, {self.percent:.1f}%)")


@dataclass(frozen=True)
class DiskInfo:
    device: str
    mountpoint: str
    fstype: str
    total: int
    used: int
    free: int
    percent: float

    def __repr__(self) -> str:
        return (f"DiskInfo({self.device} {self.mountpoint} "
                f"{self.percent:.1f}%)")


@dataclass(frozen=True)
class NetworkInfo:
    bytes_sent: int
    bytes_recv: int

    def __repr__(self) -> str:
        from core.system_data import SystemData as _SD
        return (f"NetworkInfo(↓{_SD.human_bytes(self.bytes_recv)} "
                f"↑{_SD.human_bytes(self.bytes_sent)})")


@dataclass(frozen=True)
class BatteryInfo:
    percent: float
    plugged: bool
    secs_left: int

    def __repr__(self) -> str:
        state = "plugged" if self.plugged else "on-battery"
        return f"BatteryInfo({self.percent:.0f}%, {state})"


@dataclass
class Snapshot:
    """Immutable-ish snapshot of all system metrics at one point in time."""
    cpu_percent: float
    cpu_per_core: list[float]
    memory: MemoryInfo
    disks: list[DiskInfo]
    network: NetworkInfo
    battery: BatteryInfo | None

    def __repr__(self) -> str:
        return (f"Snapshot(cpu={self.cpu_percent:.1f}%, "
                f"mem={self.memory.percent:.1f}%, "
                f"disks={len(self.disks)})")


@dataclass(frozen=True)
class ProcessInfo:
    """A single running process."""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_rss: int          # resident set size in bytes
    status: str
    username: str

    def __repr__(self) -> str:
        return (f"ProcessInfo(pid={self.pid}, {self.name!r}, "
                f"cpu={self.cpu_percent:.1f}%, mem={self.memory_percent:.1f}%)")


@dataclass(frozen=True)
class HealthResult:
    """Result of a single health check — replaces bare (status, message) tuple."""
    status: str      # "good" | "warning" | "critical"
    message: str
    detail: str = ""

    def __repr__(self) -> str:
        return f"HealthResult({self.status}: {self.message})"

    @property
    def is_critical(self) -> bool:
        return self.status == "critical"

    @property
    def is_warning(self) -> bool:
        return self.status == "warning"

    @property
    def is_good(self) -> bool:
        return self.status == "good"
