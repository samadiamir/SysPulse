"""
controller/settings_manager.py

Persistent user preferences backed by QSettings.
Stores theme, font family, font size, language, update interval,
and sidebar collapse state.
"""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, QSettings, Signal


class SettingsManager(QObject):
    """Singleton-style preferences store.

    Signals fire after ``setValue`` so the UI can react to any change
    without polling. The ``changed`` signal carries the key name.
    """

    changed = Signal(str)  # emits the key that was updated

    DEFAULTS: dict[str, Any] = {
        "theme":             "dark",
        "accent":            "#4f8cff",
        "font_family":       "Segoe UI",
        "font_size":         13,
        "language":          "en",
        "update_ms":         1500,
        "density":           "normal",  # "compact" | "normal" | "large"
        "sidebar_collapsed": False,
        "chart_line_width":  2,
        "chart_antialias":   True,
        # Dashboard widget visibility
        "dash_show_gauges":     True,
        "dash_show_stats":      True,
        "dash_show_partitions": True,
    }

    _instance: SettingsManager | None = None

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._settings = QSettings("SysPulse", "SysPulse")

    def __repr__(self) -> str:
        return (f"SettingsManager(theme={self.theme!r}, "
                f"font={self.font_family!r} {self.font_size}pt)")

    @classmethod
    def instance(cls) -> SettingsManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------ #
    #  Read / Write
    # ------------------------------------------------------------------ #
    def get(self, key: str) -> Any:
        """Return the stored value for *key*, falling back to DEFAULTS."""
        default = self.DEFAULTS.get(key)
        val = self._settings.value(key, default)
        # QSettings round-trips bools as strings on some platforms.
        if isinstance(default, bool):
            if isinstance(val, str):
                return val.lower() in ("true", "1")
            return bool(val)
        if isinstance(default, int):
            try:
                return int(val)
            except (TypeError, ValueError):
                return default
        return val

    def set(self, key: str, value: Any) -> None:
        old = self.get(key)
        if old == value:
            return
        self._settings.setValue(key, value)
        self.changed.emit(key)

    # ------------------------------------------------------------------ #
    #  Typed convenience properties
    # ------------------------------------------------------------------ #
    @property
    def theme(self) -> str:
        return self.get("theme")

    @theme.setter
    def theme(self, value: str) -> None:
        self.set("theme", value)

    @property
    def accent(self) -> str:
        return self.get("accent")

    @accent.setter
    def accent(self, value: str) -> None:
        self.set("accent", value)

    @property
    def font_family(self) -> str:
        return self.get("font_family")

    @font_family.setter
    def font_family(self, value: str) -> None:
        self.set("font_family", value)

    @property
    def font_size(self) -> int:
        return self.get("font_size")

    @font_size.setter
    def font_size(self, value: int) -> None:
        self.set("font_size", value)

    @property
    def language(self) -> str:
        return self.get("language")

    @language.setter
    def language(self, value: str) -> None:
        self.set("language", value)

    @property
    def update_ms(self) -> int:
        return self.get("update_ms")

    @update_ms.setter
    def update_ms(self, value: int) -> None:
        self.set("update_ms", value)

    @property
    def density(self) -> str:
        return self.get("density")

    @density.setter
    def density(self, value: str) -> None:
        self.set("density", value)

    # Dashboard widget visibility
    @property
    def dash_show_gauges(self) -> bool:
        return self.get("dash_show_gauges")

    @dash_show_gauges.setter
    def dash_show_gauges(self, value: bool) -> None:
        self.set("dash_show_gauges", value)

    @property
    def dash_show_stats(self) -> bool:
        return self.get("dash_show_stats")

    @dash_show_stats.setter
    def dash_show_stats(self, value: bool) -> None:
        self.set("dash_show_stats", value)

    @property
    def dash_show_partitions(self) -> bool:
        return self.get("dash_show_partitions")

    @dash_show_partitions.setter
    def dash_show_partitions(self, value: bool) -> None:
        self.set("dash_show_partitions", value)
