"""
main.py

Application entry point for SysPulse.
"""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from controller.settings_manager import SettingsManager
from ui.main_window import MainWindow, apply_theme

def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("SysPulse")
    app.setOrganizationName("SysPulse")

    sm = SettingsManager.instance()
    apply_theme(app, theme_name=sm.theme,
                font_family=sm.font_family,
                font_size=sm.font_size,
                density=sm.density)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
