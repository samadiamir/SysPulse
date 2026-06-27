"""
ui/styles.py

Dual-theme (dark / light) style system with glassmorphism.
"""
from __future__ import annotations


# --------------------------------------------------------------------------- #
#  Colour palettes
# --------------------------------------------------------------------------- #
DARK = {
    "bg":             "#0b0e14",
    "surface":        "#141821",
    "surface_alt":    "#1b2030",
    "glass":          "rgba(24, 32, 48, 0.55)",
    "glass_hover":    "rgba(30, 40, 62, 0.65)",
    "border":         "rgba(255, 255, 255, 0.06)",
    "border_focus":   "rgba(79, 140, 255, 0.45)",
    "text":           "#e6edf3",
    "text_dim":       "#7d8590",
    "text_muted":     "#484f58",
    "accent":         "#4f8cff",
    "accent_hover":   "#6da0ff",
    "good":           "#3fb950",
    "warning":        "#d29922",
    "critical":       "#f85149",
    "cpu":            "#58a6ff",
    "mem":            "#bc8cff",
    "disk":           "#3fb950",
    "net":            "#d29922",
    "battery":        "#39d2c0",
    "scrollbar":      "rgba(255,255,255,0.08)",
    "scrollbar_hover":"rgba(255,255,255,0.14)",
}

LIGHT = {
    "bg":             "#f0f2f5",
    "surface":        "#ffffff",
    "surface_alt":    "#f6f8fa",
    "glass":          "rgba(255, 255, 255, 0.72)",
    "glass_hover":    "rgba(255, 255, 255, 0.85)",
    "border":         "rgba(0, 0, 0, 0.08)",
    "border_focus":   "rgba(79, 140, 255, 0.5)",
    "text":           "#1f2328",
    "text_dim":       "#656d76",
    "text_muted":     "#afb8c1",
    "accent":         "#0969da",
    "accent_hover":   "#218bff",
    "good":           "#1a7f37",
    "warning":        "#bf8700",
    "critical":       "#cf222e",
    "cpu":            "#0969da",
    "mem":            "#8250df",
    "disk":           "#1a7f37",
    "net":            "#bf8700",
    "battery":        "#0e8a7e",
    "scrollbar":      "rgba(0,0,0,0.1)",
    "scrollbar_hover":"rgba(0,0,0,0.2)",
}

THEMES: dict[str, dict] = {"dark": DARK, "light": LIGHT}

# Active palette — mutated by set_active_theme()
C: dict[str, str] = dict(DARK)


def set_active_theme(name: str) -> dict:
    global C
    C = dict(THEMES.get(name, DARK))
    return C


# --------------------------------------------------------------------------- #
#  Density presets (compact / normal / large)
# --------------------------------------------------------------------------- #
DENSITY_PRESETS: dict[str, dict[str, int]] = {
    "compact": {
        "font_delta":    -1,
        "card_padding":  12,
        "card_spacing":  6,
        "page_margin":   18,
        "page_spacing":  10,
        "sidebar_pad_v": 18,
        "nav_padding":   9,
        "border_radius": 12,
        "gauge_min":     140,
    },
    "normal": {
        "font_delta":    0,
        "card_padding":  18,
        "card_spacing":  10,
        "page_margin":   28,
        "page_spacing":  18,
        "sidebar_pad_v": 28,
        "nav_padding":   13,
        "border_radius": 18,
        "gauge_min":     180,
    },
    "large": {
        "font_delta":    2,
        "card_padding":  24,
        "card_spacing":  14,
        "page_margin":   36,
        "page_spacing":  24,
        "sidebar_pad_v": 34,
        "nav_padding":   16,
        "border_radius": 22,
        "gauge_min":     220,
    },
}


def get_density(density: str = "normal") -> dict[str, int]:
    """Return the density preset for *density*, falling back to normal."""
    return DENSITY_PRESETS.get(density, DENSITY_PRESETS["normal"])


# --------------------------------------------------------------------------- #
#  Colour helpers
# --------------------------------------------------------------------------- #
def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    r, g, b = hex_to_rgb(hex_color)
    return f"rgba({r}, {g}, {b}, {alpha})"


def hex_to_qt_color(hex_color: str, alpha: float = 1.0) -> tuple[int, int, int, int]:
    r, g, b = hex_to_rgb(hex_color)
    a = int(round(max(0.0, min(1.0, alpha)) * 255))
    return (r, g, b, a)


# --------------------------------------------------------------------------- #
#  QSS section builders
# --------------------------------------------------------------------------- #
def _qss_global(c: dict, font_family: str, font_size: int) -> str:
    return f"""
* {{
    font-family: '{font_family}', 'Inter', 'Noto Sans', sans-serif;
    font-size: {font_size}px;
    color: {c['text']};
}}
QMainWindow, QWidget {{
    background: {c['bg']};
}}
"""

def _qss_sidebar(c: dict, d: dict) -> str:
    np = d["nav_padding"]
    br = d["border_radius"]
    return f"""
QFrame#Sidebar {{
    background: {c['surface']};
    border-right: 1px solid {c['border']};
}}
QLabel#AppTitle {{
    color: {c['text']};
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.5px;
}}
QLabel#AppSubtitle {{
    color: {c['text_dim']};
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 2px;
}}
QPushButton#NavButton {{
    text-align: left;
    padding: {np}px 18px;
    border: none;
    border-radius: {br}px;
    font-size: 14px;
    font-weight: 500;
    color: {c['text_dim']};
    background: transparent;
}}
QPushButton#NavButton:hover {{
    background: {c['glass_hover']};
    color: {c['text']};
}}
QPushButton#NavButton:checked {{
    background: {c['glass']};
    color: {c['accent']};
    font-weight: 600;
    border: 1px solid {c['border']};
}}
"""

def _qss_cards(c: dict, cp: int = 18, br: int = 18) -> str:
    return f"""
QFrame#GlassCard {{
    background: {c['glass']};
    border: 1px solid {c['border']};
    border-radius: {br}px;
}}
QLabel#CardTitle {{
    color: {c['text_dim']};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QLabel#CardValue {{
    color: {c['text']};
    font-size: 30px;
    font-weight: 800;
    letter-spacing: -0.5px;
}}
QLabel#CardSub {{
    color: {c['text_dim']};
    font-size: 12px;
}}
QLabel#SectionTitle {{
    color: {c['text']};
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.3px;
}}
QLabel#FieldLabel {{
    color: {c['text_dim']};
    font-size: 12px;
}}
QLabel#FieldValue {{
    color: {c['text']};
    font-size: 13px;
    font-weight: 600;
}}
"""

def _qss_controls(c: dict, br: int = 18, _np: int = 13) -> str:
    cr = max(br - 4, 6)  # control radius is slightly smaller than card radius
    return f"""
QFrame#ToggleTrack {{
    border-radius: {cr}px;
    border: 1px solid {c['border']};
}}
QFrame#ToggleTrack[checked="true"] {{
    background: {c['accent']};
    border-color: {c['accent']};
}}
QFrame#ToggleTrack[checked="false"] {{
    background: {c['surface_alt']};
}}
QFrame#ToggleThumb {{
    background: {c['text']};
    border-radius: {max(cr - 2, 4)}px;
}}
QComboBox {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: {cr}px;
    padding: 8px 14px;
    color: {c['text']};
}}
QComboBox:hover {{
    border-color: {c['accent']};
}}
QComboBox::drop-down {{
    border: none;
    width: 28px;
}}
QComboBox QAbstractItemView {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: {cr}px;
    selection-background-color: {c['accent']};
    selection-color: #ffffff;
    color: {c['text']};
    outline: none;
    padding: 4px;
}}
QSpinBox {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: {cr}px;
    padding: 8px 12px;
    color: {c['text']};
}}
QSpinBox:hover {{ border-color: {c['accent']}; }}
QSpinBox::up-button, QSpinBox::down-button {{
    width: 24px;
    border: none;
    background: transparent;
}}
QSlider::groove:horizontal {{
    height: 6px;
    background: {c['surface_alt']};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {c['accent']};
    width: 18px; height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}}
QSlider::sub-page:horizontal {{
    background: {c['accent']};
    border-radius: 3px;
}}
QPushButton#PrimaryBtn {{
    background: {c['accent']};
    color: #ffffff;
    border: none;
    border-radius: {cr}px;
    padding: 10px 22px;
    font-weight: 600;
}}
QPushButton#PrimaryBtn:hover {{ background: {c['accent_hover']}; }}
QPushButton#SecondaryBtn {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: {cr}px;
    padding: 10px 22px;
    font-weight: 500;
    color: {c['text']};
}}
QPushButton#SecondaryBtn:hover {{
    background: {c['glass_hover']};
    border-color: {c['accent']};
}}
"""

def _qss_scroll_and_bars(c: dict) -> str:
    return f"""
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {c['scrollbar']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {c['scrollbar_hover']};
}}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
QStatusBar {{
    background: {c['surface']};
    border-top: 1px solid {c['border']};
    color: {c['text_dim']};
}}
QStatusBar::item {{ border: none; }}
QMenuBar {{
    background: {c['surface']};
    color: {c['text']};
    border-bottom: 1px solid {c['border']};
}}
QMenuBar::item:selected {{ background: {c['glass_hover']}; }}
QMenu {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 10px;
    padding: 6px;
}}
QMenu::item {{ padding: 8px 28px 8px 16px; border-radius: 6px; }}
QMenu::item:selected {{ background: {c['glass_hover']}; }}
QToolTip {{
    background: {c['surface']};
    color: {c['text']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
}}
"""


def build_qss(theme: dict, font_family: str = "Segoe UI",
              font_size: int = 13, density: str = "normal") -> str:
    """Return a complete QSS string for the given palette + font + density."""
    d = get_density(density)
    fs = font_size + d["font_delta"]
    cp = d["card_padding"]
    br = d["border_radius"]
    np = d["nav_padding"]

    return (
        _qss_global(theme, font_family, fs)
        + _qss_sidebar(theme, d)
        + _qss_cards(theme, cp, br)
        + _qss_controls(theme, br, np)
        + _qss_scroll_and_bars(theme)
    )


# --------------------------------------------------------------------------- #
#  Status helpers
# --------------------------------------------------------------------------- #
def status_qss_class(status: str) -> str:
    return {"good": "StatusGood", "warning": "StatusWarning",
            "critical": "StatusCritical"}.get(status, "StatusGood")


def status_color(status: str) -> str:
    return {"good": C["good"], "warning": C["warning"],
            "critical": C["critical"]}.get(status, C["good"])
