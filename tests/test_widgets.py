"""
tests/test_widgets.py

Tests the reusable UI widgets with proper encapsulation checks.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from ui.styles import C, hex_to_rgb, hex_to_qt_color, hex_to_rgba
from ui.widgets import Card, StatCard, InfoRow, Badge, CircularGauge


class TestStyleHelpers:
    def test_hex_to_rgb(self):
        assert hex_to_rgb("#4f8cff") == (79, 140, 255)

    def test_hex_to_rgb_without_hash(self):
        assert hex_to_rgb("4f8cff") == (79, 140, 255)

    def test_hex_to_rgba_format(self):
        assert hex_to_rgba("#000000", 0.5) == "rgba(0, 0, 0, 0.5)"

    def test_hex_to_qt_color_alpha_clamped_and_scaled(self):
        assert hex_to_qt_color("#ffffff", 1.0) == (255, 255, 255, 255)
        assert hex_to_qt_color("#ffffff", 0.0) == (255, 255, 255, 0)
        assert hex_to_qt_color("#ffffff", 5.0)[-1] == 255
        assert hex_to_qt_color("#ffffff", -1.0)[-1] == 0


class TestCard:
    def test_card_with_title(qapp):
        card = Card("Live Resources")
        assert card._title_label is not None
        assert "LIVE RESOURCES" in card._title_label.text()

    def test_card_without_title_has_no_label(qapp):
        card = Card()
        assert card._title_label is None

    def test_card_repr(qapp):
        card = Card("Test")
        assert "Card" in repr(card)
        assert "TEST" in repr(card)


class TestStatCard:
    def test_set_value_updates_labels(qapp):
        card = StatCard("CPU", icon_name=None)
        card.set_value("42%", "load average")
        assert card._value_label.text() == "42%"
        assert card._sub_label.text() == "load average"

    def test_statcard_repr(qapp):
        card = StatCard("CPU", icon_name=None)
        card.set_value("50%", "test")
        assert "50%" in repr(card)


class TestInfoRow:
    def test_initial_values(qapp):
        row = InfoRow("Brand", "Intel i7")
        assert row._label.text() == "Brand"
        assert row._value.text() == "Intel i7"

    def test_coerces_non_string_value(qapp):
        row = InfoRow("L2 Cache", 262144)
        assert row._value.text() == "262144"

    def test_set_value_coerces(qapp):
        row = InfoRow("Cores")
        row.set_value(8)
        assert row._value.text() == "8"

    def test_value_property(qapp):
        row = InfoRow("Test", "hello")
        assert row.value == "hello"

    def test_info_row_repr(qapp):
        row = InfoRow("Key", "Val")
        assert "Key" in repr(row)
        assert "Val" in repr(row)


class TestBadge:
    def test_status_sets_text(qapp):
        badge = Badge("—", status="good")
        badge.set_status("warning", "WARN")
        assert badge.text() == "WARN"
        assert badge.current_status == "warning"

    def test_each_status_is_valid(qapp):
        badge = Badge()
        for status in ("good", "warning", "critical"):
            badge.set_status(status, status.upper())
            assert badge.text() == status.upper()

    def test_badge_repr(qapp):
        badge = Badge("HEALTHY", status="good")
        assert "HEALTHY" in repr(badge)
        assert "good" in repr(badge)


class TestCircularGauge:
    def test_set_value_clamps_high(qapp):
        gauge = CircularGauge(label="CPU")
        gauge.set_value(150.0)
        assert gauge.value == 100.0

    def test_set_value_clamps_low(qapp):
        gauge = CircularGauge(label="CPU")
        gauge.set_value(-20.0)
        assert gauge.value == 0.0

    def test_value_property_is_readonly(qapp):
        gauge = CircularGauge(label="CPU")
        gauge.set_value(42.0)
        assert gauge.value == 42.0

    def test_set_color_updates(qapp):
        gauge = CircularGauge(label="CPU", color="#000000")
        gauge.set_color(C["cpu"])
        assert gauge._color == C["cpu"]

    def test_height_for_width(qapp):
        gauge = CircularGauge(label="CPU")
        assert gauge.hasHeightForWidth()
        assert gauge.heightForWidth(120) == 120

    def test_paint_does_not_raise(qapp):
        gauge = CircularGauge(label="CPU")
        gauge.set_value(45.0)
        gauge.resize(200, 200)
        from PySide6.QtGui import QPixmap
        gauge.render(QPixmap(200, 200))

    def test_gauge_repr(qapp):
        gauge = CircularGauge(label="CPU")
        gauge.set_value(42.0)
        assert "CPU" in repr(gauge)
        assert "42%" in repr(gauge)
