"""
controller/exporter.py

Export system snapshots to CSV or JSON files.
"""
from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from core.snapshot import Snapshot
from core.system_data import SystemData


# Default export directory — user's Documents/SysPulse/Exports
_EXPORT_DIR = Path.home() / "Documents" / "SysPulse" / "Exports"


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _snapshot_to_dict(snap: Snapshot) -> dict[str, Any]:
    """Convert a Snapshot to a JSON-serialisable dict."""
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": snap.cpu_percent,
        "cpu_per_core": snap.cpu_per_core,
        "memory": {
            "total": snap.memory.total,
            "available": snap.memory.available,
            "used": snap.memory.used,
            "percent": snap.memory.percent,
        },
        "disks": [
            {
                "device": d.device,
                "mountpoint": d.mountpoint,
                "fstype": d.fstype,
                "total": d.total,
                "used": d.used,
                "free": d.free,
                "percent": d.percent,
            }
            for d in snap.disks
        ],
        "network": {
            "bytes_sent": snap.network.bytes_sent,
            "bytes_recv": snap.network.bytes_recv,
        },
        "battery": None if snap.battery is None else {
            "percent": snap.battery.percent,
            "plugged": snap.battery.plugged,
            "secs_left": snap.battery.secs_left,
        },
    }


# --------------------------------------------------------------------------- #
#  Public API
# --------------------------------------------------------------------------- #
def export_json(snap: Snapshot, path: Path | None = None) -> Path:
    """Export a snapshot to a JSON file. Returns the file path."""
    if path is None:
        _ensure_dir(_EXPORT_DIR)
        path = _EXPORT_DIR / f"syspulse_{_timestamp()}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _snapshot_to_dict(snap)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def export_csv(snap: Snapshot, path: Path | None = None) -> Path:
    """Export a snapshot to a CSV file. Returns the file path."""
    if path is None:
        _ensure_dir(_EXPORT_DIR)
        path = _EXPORT_DIR / f"syspulse_{_timestamp()}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []

    # CPU
    rows.append({"category": "cpu", "metric": "overall", "value": snap.cpu_percent})
    for i, val in enumerate(snap.cpu_per_core):
        rows.append({"category": "cpu", "metric": f"core_{i}", "value": val})

    # Memory
    for field in ("total", "available", "used", "percent"):
        rows.append({"category": "memory", "metric": field,
                     "value": getattr(snap.memory, field)})

    # Disks
    for d in snap.disks:
        for field in ("total", "used", "free", "percent"):
            rows.append({"category": f"disk:{d.device}", "metric": field,
                         "value": getattr(d, field)})

    # Network
    rows.append({"category": "network", "metric": "bytes_sent",
                 "value": snap.network.bytes_sent})
    rows.append({"category": "network", "metric": "bytes_recv",
                 "value": snap.network.bytes_recv})

    # Battery
    if snap.battery:
        rows.append({"category": "battery", "metric": "percent",
                     "value": snap.battery.percent})
        rows.append({"category": "battery", "metric": "plugged",
                     "value": int(snap.battery.plugged)})

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["category", "metric", "value"])
        writer.writeheader()
        writer.writerows(rows)
    return path


def get_export_dir() -> Path:
    return _ensure_dir(_EXPORT_DIR)
