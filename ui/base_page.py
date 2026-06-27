"""
ui/base_page.py

Shared base class and layout utilities used by every page.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLayout,
)


class ScrollablePage(QWidget):
    """Base for every page that needs a scrollable content area.

    Subclasses call ``self._content_layout`` to add widgets to the
    scrollable body — the outer frame / scroll plumbing is handled here.
    """

    _DEFAULT_MARGINS = (28, 24, 28, 24)
    _DEFAULT_SPACING = 18

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.NoFrame)

        self._host = QWidget()
        self._root = QVBoxLayout(self._host)
        m = self._DEFAULT_MARGINS
        self._root.setContentsMargins(m[0], m[1], m[2], m[3])
        self._root.setSpacing(self._DEFAULT_SPACING)

        self._scroll.setWidget(self._host)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._scroll)

    @property
    def content_layout(self) -> QVBoxLayout:
        """Add widgets to this layout — they appear inside the scroll area."""
        return self._root


def clear_layout(layout: QLayout) -> None:
    """Remove and destroy every child widget inside *layout*."""
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w is not None:
            w.setParent(None)
            w.deleteLater()
