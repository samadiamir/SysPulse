"""
ui/widgets.py

Modern glassmorphism reusable widgets with proper encapsulation.
"""
from __future__ import annotations

from PySide6.QtCore import (
    Qt, QRectF, QSize, QPropertyAnimation, QEasingCurve, Property, Signal,
)
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PySide6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout,
    QSizePolicy, QWidget,
)

try:
    import qtawesome as qta
except ImportError:
    qta = None

from ui.styles import C, hex_to_rgba


# --------------------------------------------------------------------------- #
#  Glass Card
# --------------------------------------------------------------------------- #
class Card(QFrame):
    """Glassmorphism card container."""

    def __init__(self, title: str | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(22, 18, 22, 18)
        self._layout.setSpacing(10)

        self._title_label: QLabel | None = None
        if title:
            self._title_label = QLabel(title.upper())
            self._title_label.setObjectName("CardTitle")
            self._layout.addWidget(self._title_label)

    def __repr__(self) -> str:
        title = self._title_label.text() if self._title_label else "untitled"
        return f"Card({title!r})"

    def addWidget(self, w: QWidget) -> None:
        self._layout.addWidget(w)

    def addLayout(self, layout: QVBoxLayout | QHBoxLayout) -> None:
        self._layout.addLayout(layout)

    def addStretch(self) -> None:
        self._layout.addStretch()

    @property
    def body(self) -> QVBoxLayout:
        return self._layout


# --------------------------------------------------------------------------- #
#  Stat card (icon + big value + subtitle)
# --------------------------------------------------------------------------- #
class StatCard(Card):
    def __init__(self, title: str, icon_name: str | None = None,
                 icon_color: str | None = None,
                 parent: QWidget | None = None):
        super().__init__(title=title, parent=parent)
        row = QHBoxLayout()
        row.setSpacing(14)
        self._layout.addLayout(row)

        self._icon_label = QLabel()
        self._icon_label.setFixedSize(44, 44)
        self._icon_label.setAlignment(Qt.AlignCenter)
        self._icon_color = icon_color or C["accent"]
        self._set_icon(icon_name)
        row.addWidget(self._icon_label, alignment=Qt.AlignTop)

        col = QVBoxLayout()
        col.setSpacing(2)
        self._value_label = QLabel("--")
        self._value_label.setObjectName("CardValue")
        self._sub_label = QLabel("")
        self._sub_label.setObjectName("CardSub")
        col.addWidget(self._value_label)
        col.addWidget(self._sub_label)
        row.addLayout(col)
        row.addStretch()

    def __repr__(self) -> str:
        return f"StatCard({self._value_label.text()!r})"

    def _set_icon(self, icon_name: str | None) -> None:
        if icon_name and qta is not None:
            try:
                self._icon_label.setPixmap(
                    qta.icon(icon_name, color=self._icon_color).pixmap(QSize(32, 32))
                )
                return
            except (ValueError, AttributeError):
                pass
        self._icon_label.setText("●")
        self._icon_label.setStyleSheet(f"color:{self._icon_color};font-size:28px;")

    def set_value(self, value: str, subtitle: str = "") -> None:
        self._value_label.setText(value)
        self._sub_label.setText(subtitle)


# --------------------------------------------------------------------------- #
#  Info row
# --------------------------------------------------------------------------- #
class InfoRow(QWidget):
    def __init__(self, label: str, value: str | int | float = "—",
                 parent: QWidget | None = None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 7, 0, 7)

        self._label = QLabel(str(label))
        self._label.setObjectName("FieldLabel")
        self._label.setMinimumWidth(170)

        self._value = QLabel(str(value))
        self._value.setObjectName("FieldValue")
        self._value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._value.setWordWrap(True)

        lay.addWidget(self._label)
        lay.addStretch()
        lay.addWidget(self._value, stretch=1)

    def __repr__(self) -> str:
        return f"InfoRow({self._label.text()!r}={self._value.text()!r})"

    def set_value(self, value: str | int | float) -> None:
        self._value.setText(str(value))

    @property
    def value(self) -> str:
        return self._value.text()


def build_info_grid(rows: list[tuple[str, str]]) -> QGridLayout:
    grid = QGridLayout()
    grid.setHorizontalSpacing(24)
    grid.setVerticalSpacing(0)
    for i, (label, value) in enumerate(rows):
        grid.addWidget(InfoRow(label, value), i, 0, 1, 2)
    return grid


# --------------------------------------------------------------------------- #
#  Badge
# --------------------------------------------------------------------------- #
class Badge(QLabel):
    def __init__(self, text: str = "", status: str = "good",
                 parent: QWidget | None = None):
        super().__init__(text, parent)
        self._current_status = status
        self._apply_style(status)

    def __repr__(self) -> str:
        return f"Badge({self.text()!r}, status={self._current_status!r})"

    def set_status(self, status: str, text: str | None = None) -> None:
        self._current_status = status
        self._apply_style(status)
        if text is not None:
            self.setText(text)

    @property
    def current_status(self) -> str:
        return self._current_status

    def _apply_style(self, status: str) -> None:
        from ui.styles import status_color
        c = status_color(status)
        self.setStyleSheet(
            f"background:{hex_to_rgba(c, 0.14)};color:{c};"
            f"font-size:11px;font-weight:700;padding:5px 12px;border-radius:8px;"
        )


# --------------------------------------------------------------------------- #
#  Circular gauge
# --------------------------------------------------------------------------- #
class CircularGauge(QWidget):
    """A sleek circular ring gauge (0–100%)."""

    def __init__(self, label: str = "", color: str | None = None,
                 parent: QWidget | None = None):
        super().__init__(parent)
        self._value: float = 0.0
        self._label = label
        self._color = color or C["accent"]
        self._track = C["surface_alt"]
        self.setMinimumSize(180, 180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def __repr__(self) -> str:
        return f"CircularGauge({self._label!r}={self._value:.0f}%)"

    @property
    def value(self) -> float:
        """Read-only access to the current gauge value."""
        return self._value

    def set_value(self, v: float) -> None:
        self._value = max(0.0, min(100.0, float(v)))
        self.update()

    def set_color(self, c: str) -> None:
        self._color = c
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(200, 200)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, w: int) -> int:
        return w

    def paintEvent(self, _ev: object) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        sz = min(self.width(), self.height()) - 24
        mx = (self.width() - sz) / 2
        my = (self.height() - sz) / 2
        rect = QRectF(mx, my, sz, sz)
        pw = max(12, sz * 0.11)

        # Inner glow
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(self._color).lighter(160)))
        inner = QRectF(mx + pw + 4, my + pw + 4,
                       sz - 2 * pw - 8, sz - 2 * pw - 8)
        p.setOpacity(0.06)
        p.drawEllipse(inner)
        p.setOpacity(1.0)

        # Track
        pen = QPen(QColor(self._track), pw)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, 0, 360 * 16)

        # Value arc
        span = int(-self._value / 100.0 * 360 * 16)
        vp = QPen(QColor(self._color), pw)
        vp.setCapStyle(Qt.RoundCap)
        p.setPen(vp)
        p.drawArc(rect, 90 * 16, span)

        # Percentage
        p.setPen(QColor(C["text"]))
        f = QFont("Segoe UI", int(sz * 0.19))
        f.setBold(True)
        p.setFont(f)
        text_rect = QRectF(rect.x(), rect.y() - sz * 0.04,
                           rect.width(), rect.height())
        p.drawText(text_rect, Qt.AlignCenter, f"{self._value:.0f}%")

        # Label
        if self._label:
            p.setPen(QColor(C["text_dim"]))
            p.setFont(QFont("Segoe UI", int(sz * 0.075), QFont.Weight.DemiBold))
            lr = QRectF(rect.x(), rect.y() + sz * 0.19,
                        rect.width(), rect.height())
            p.drawText(lr, Qt.AlignCenter, self._label.upper())
        p.end()


# --------------------------------------------------------------------------- #
#  Toggle Switch
# --------------------------------------------------------------------------- #
class ToggleSwitch(QWidget):
    """A modern iOS-style toggle switch with smooth animation."""
    toggled = Signal(bool)

    def __init__(self, checked: bool = False, parent: QWidget | None = None):
        super().__init__(parent)
        self._checked = checked
        self._thumb_pos: float = 26.0 if checked else 4.0
        self.setFixedSize(52, 28)
        self.setCursor(Qt.PointingHandCursor)

        self._anim = QPropertyAnimation(self, b"thumbPos")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)

    def __repr__(self) -> str:
        return f"ToggleSwitch(checked={self._checked})"

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, v: bool) -> None:
        if self._checked == v:
            return
        self._checked = v
        self._animate()
        self.toggled.emit(v)

    def _get_thumb_pos(self) -> float:
        return self._thumb_pos

    def _set_thumb_pos(self, v: float) -> None:
        self._thumb_pos = v
        self.update()

    thumbPos = Property(float, _get_thumb_pos, _set_thumb_pos)

    def _animate(self) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._thumb_pos)
        self._anim.setEndValue(26.0 if self._checked else 4.0)
        self._anim.start()

    def mousePressEvent(self, _ev: object) -> None:
        self.setChecked(not self._checked)

    def paintEvent(self, _ev: object) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        track_color = QColor(C["accent"]) if self._checked else QColor(C["surface_alt"])
        p.setBrush(QBrush(track_color))
        p.setPen(QPen(QColor(C["border"]), 1))
        p.drawRoundedRect(0, 0, 52, 28, 14, 14)
        p.setBrush(QBrush(QColor("#ffffff")))
        p.setPen(Qt.NoPen)
        p.drawEllipse(int(self._thumb_pos), 3, 22, 22)
        p.end()


# --------------------------------------------------------------------------- #
#  Accent colour selector
# --------------------------------------------------------------------------- #
class AccentButton(QWidget):
    """A circular accent colour swatch that emits clicked."""
    clicked = Signal()

    def __init__(self, color: str, size: int = 28,
                 parent: QWidget | None = None):
        super().__init__(parent)
        self._color = color
        self._size = size
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)

    def __repr__(self) -> str:
        return f"AccentButton({self._color!r})"

    def mousePressEvent(self, _ev: object) -> None:
        self.clicked.emit()

    def paintEvent(self, _ev: object) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(QColor(self._color)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(1, 1, self._size - 2, self._size - 2)
        p.end()
