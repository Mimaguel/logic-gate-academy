"""
gui/theme.py
=================
Visual theme for Sirkitry: a bold red/black/white palette with
condensed display type, inspired by the general conventions of stylish,
high-contrast "action game" UI design (thick color-blocking, sharp
rectangular panels, bold uppercase type, neon-red glow accents) - this is
an ORIGINAL design, not a reproduction of any specific copyrighted game's
assets or artwork.

Nothing here is game logic - it's purely: colors, fonts, and the QSS
stylesheet string. `gui/main_window.py` calls `load_fonts()` once at
startup and applies `build_stylesheet()` to the main window.
"""

from __future__ import annotations
from pathlib import Path

from PySide6.QtGui import QFontDatabase

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
IMAGES_DIR = ASSETS_DIR / "images"
SOUNDS_DIR = ASSETS_DIR / "sounds"

# -- palette -------------------------------------------------------------
RED = "#E60E2D"
RED_DARK = "#A60A20"
RED_GLOW = "#FF3B57"
BLACK = "#0B0B0D"
BLACK_SOFT = "#17171B"
PANEL = "#1D1D22"
PANEL_LIGHT = "#2A2A31"
WHITE = "#F2F2F0"
GRAY = "#9A9AA4"
GREEN = "#33D17A"
YELLOW = "#F2C744"

FONT_FILES = [
    "BebasNeue-Regular",
    "Rajdhani-Light",
    "Rajdhani-Regular",
    "Rajdhani-Medium",
    "Rajdhani-SemiBold",
    "Rajdhani-Bold",
]


def load_fonts() -> None:
    """Register the bundled .ttf files with Qt. Safe to call more than
    once (Qt just re-registers the same families)."""
    for name in FONT_FILES:
        path = FONTS_DIR / f"{name}.ttf"
        if path.exists():
            QFontDatabase.addApplicationFont(str(path))


def build_stylesheet() -> str:
    return f"""
    * {{
        font-family: "Rajdhani";
        font-size: 14px;
        color: {WHITE};
    }}

    QMainWindow, #centralwidget, QStackedWidget {{
        background-color: {BLACK};
    }}

    /* ---- persistent top banner ---- */
    QFrame[role="topBanner"] {{
        background-color: {BLACK_SOFT};
    }}
    QLabel[role="brandTitle"] {{
        font-family: "Bebas Neue";
        font-size: 22px;
        letter-spacing: 3px;
        color: {WHITE};
    }}
    QLabel[role="brandStatus"] {{
        font-family: "Rajdhani SemiBold";
        font-size: 12px;
        letter-spacing: 1px;
        color: {RED_GLOW};
    }}
    QFrame[role="accentStrip"] {{
        background-color: {RED};
    }}

    /* ---- page / section titles ---- */
    QLabel[role="pageTitle"], QLabel[role="heroTitle"] {{
        font-family: "Bebas Neue";
        letter-spacing: 3px;
        color: {WHITE};
        padding-bottom: 10px;
        border-bottom: 3px solid {RED};
        margin-bottom: 6px;
    }}
    QLabel[role="subtitle"] {{
        color: {GRAY};
        font-size: 14px;
        letter-spacing: 1px;
    }}
    QLabel[role="fieldLabel"] {{
        color: {RED_GLOW};
        font-family: "Rajdhani SemiBold";
        font-size: 12px;
        letter-spacing: 2px;
        text-transform: uppercase;
    }}
    QLabel[role="liveStat"] {{
        color: {RED_GLOW};
        font-family: "Rajdhani SemiBold";
        font-size: 15px;
        letter-spacing: 1px;
    }}
    QLabel[role="questionText"] {{
        font-size: 17px;
        color: {WHITE};
    }}
    QLabel[role="statusError"] {{
        color: {RED_GLOW};
        font-family: "Rajdhani SemiBold";
    }}
    QLabel[role="warningText"] {{
        color: {YELLOW};
        font-family: "Rajdhani SemiBold";
        font-size: 15px;
    }}
    QLabel[role="feedback"] {{
        font-family: "Rajdhani SemiBold";
        font-size: 16px;
        min-height: 24px;
    }}

    /* ---- buttons ---- */
    QPushButton {{
        font-family: "Rajdhani SemiBold";
        font-size: 15px;
        letter-spacing: 1px;
        text-transform: uppercase;
        border-radius: 3px;
        padding: 9px 20px;
    }}
    QPushButton[role="primary"] {{
        background-color: {RED};
        color: {WHITE};
        border: 2px solid {RED};
    }}
    QPushButton[role="primary"]:hover {{
        background-color: {RED_GLOW};
        border-color: {RED_GLOW};
    }}
    QPushButton[role="primary"]:pressed {{
        background-color: {RED_DARK};
        border-color: {RED_DARK};
    }}
    QPushButton[role="secondary"] {{
        background-color: {PANEL};
        color: {WHITE};
        border: 2px solid {PANEL_LIGHT};
    }}
    QPushButton[role="secondary"]:hover {{
        border-color: {RED};
        color: {RED_GLOW};
    }}
    QPushButton[role="secondary"]:pressed {{
        background-color: {PANEL_LIGHT};
    }}
    QPushButton[role="ghost"] {{
        background-color: transparent;
        color: {GRAY};
        border: none;
    }}
    QPushButton[role="ghost"]:hover {{
        color: {WHITE};
    }}
    QPushButton[role="danger"] {{
        background-color: transparent;
        color: {RED_GLOW};
        border: 2px solid {RED};
    }}
    QPushButton[role="danger"]:hover {{
        background-color: {RED};
        color: {WHITE};
    }}
    QPushButton[role="answerButton"] {{
        font-family: "Bebas Neue";
        font-size: 30px;
        letter-spacing: 2px;
        background-color: {PANEL};
        border: 2px solid {PANEL_LIGHT};
        border-radius: 4px;
    }}
    QPushButton[role="answerButton"]:hover {{
        border-color: {RED};
        color: {RED_GLOW};
        background-color: {PANEL_LIGHT};
    }}
    QPushButton[role="difficultyEasy"],
    QPushButton[role="difficultyMedium"],
    QPushButton[role="difficultyHard"] {{
        background-color: {PANEL};
        border: 2px solid {PANEL_LIGHT};
        text-align: left;
        padding-left: 22px;
    }}
    QPushButton[role="difficultyEasy"]:hover {{ border-color: {GREEN}; color: {GREEN}; }}
    QPushButton[role="difficultyMedium"]:hover {{ border-color: {YELLOW}; color: {YELLOW}; }}
    QPushButton[role="difficultyHard"]:hover {{ border-color: {RED}; color: {RED_GLOW}; }}

    /* ---- inputs ---- */
    QLineEdit {{
        background-color: {PANEL};
        border: 2px solid {PANEL_LIGHT};
        border-radius: 3px;
        padding: 6px 10px;
        color: {WHITE};
        selection-background-color: {RED};
    }}
    QLineEdit:focus {{
        border-color: {RED};
    }}

    /* ---- text panels ---- */
    QTextBrowser {{
        background-color: {PANEL};
        border: 2px solid {PANEL_LIGHT};
        border-radius: 3px;
        padding: 14px;
        font-size: 15px;
    }}

    /* ---- tables ---- */
    QTableWidget {{
        background-color: {PANEL};
        border: 2px solid {PANEL_LIGHT};
        gridline-color: {PANEL_LIGHT};
        border-radius: 3px;
    }}
    QHeaderView {{
        background-color: {BLACK_SOFT};
        border: none;
    }}
    QHeaderView::section {{
        background-color: {BLACK_SOFT};
        color: {RED_GLOW};
        font-family: "Rajdhani SemiBold";
        letter-spacing: 1px;
        padding: 8px;
        border: none;
        border-bottom: 2px solid {RED};
    }}
    QTableWidget::item {{
        padding: 5px;
    }}
    QTableCornerButton::section {{
        background-color: {BLACK_SOFT};
        border: none;
    }}

    /* ---- scrollbars ---- */
    QScrollBar:vertical {{
        background: {BLACK_SOFT};
        width: 12px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {RED};
        min-height: 24px;
        border-radius: 5px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QToolTip {{
        background-color: {BLACK_SOFT};
        color: {WHITE};
        border: 1px solid {RED};
        padding: 4px;
    }}
    """
