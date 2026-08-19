CATPPUCCIN_MOCHA = {
    "base": "#1e1e2e",
    "mantle": "#181825",
    "crust": "#11111b",
    "surface0": "#313244",
    "surface1": "#45475a",
    "surface2": "#585b70",
    "text": "#cdd6f4",
    "subtext1": "#bac2de",
    "subtext0": "#a6adc8",
    "green": "#a6e3a1",
    "red": "#f38ba8",
    "yellow": "#f9e2af",
    "blue": "#89b4fa",
    "mauve": "#cba6f7",
    "peach": "#fab387",
    "teal": "#94e2d5",
}

DARK_THEME_QSS = f"""
QMainWindow, QDialog {{
    background-color: {CATPPUCCIN_MOCHA['base']};
    color: {CATPPUCCIN_MOCHA['text']};
}}

QWidget {{
    background-color: {CATPPUCCIN_MOCHA['base']};
    color: {CATPPUCCIN_MOCHA['text']};
}}

QTreeWidget, QTableWidget, QTableView {{
    background-color: {CATPPUCCIN_MOCHA['mantle']};
    color: {CATPPUCCIN_MOCHA['text']};
    gridline-color: {CATPPUCCIN_MOCHA['surface0']};
    alternate-background-color: {CATPPUCCIN_MOCHA['base']};
    border: 1px solid {CATPPUCCIN_MOCHA['surface0']};
    border-radius: 4px;
    selection-background-color: {CATPPUCCIN_MOCHA['surface1']};
    selection-color: {CATPPUCCIN_MOCHA['text']};
}}

QTreeWidget::item, QTableWidget::item, QTableView::item {{
    padding: 4px 8px;
}}

QTreeWidget::item:selected, QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {CATPPUCCIN_MOCHA['surface1']};
}}

QHeaderView::section {{
    background-color: {CATPPUCCIN_MOCHA['surface0']};
    color: {CATPPUCCIN_MOCHA['text']};
    border: 1px solid {CATPPUCCIN_MOCHA['surface1']};
    padding: 4px 8px;
    font-weight: bold;
}}

QPushButton {{
    background-color: {CATPPUCCIN_MOCHA['surface0']};
    color: {CATPPUCCIN_MOCHA['text']};
    border: 1px solid {CATPPUCCIN_MOCHA['surface1']};
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {CATPPUCCIN_MOCHA['surface1']};
}}

QPushButton:pressed {{
    background-color: {CATPPUCCIN_MOCHA['surface2']};
}}

QLineEdit {{
    background-color: {CATPPUCCIN_MOCHA['mantle']};
    color: {CATPPUCCIN_MOCHA['text']};
    border: 1px solid {CATPPUCCIN_MOCHA['surface0']};
    border-radius: 4px;
    padding: 4px 8px;
}}

QLineEdit:focus {{
    border: 1px solid {CATPPUCCIN_MOCHA['blue']};
}}

QCheckBox {{
    color: {CATPPUCCIN_MOCHA['text']};
    spacing: 6px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {CATPPUCCIN_MOCHA['surface1']};
    border-radius: 3px;
    background-color: {CATPPUCCIN_MOCHA['mantle']};
}}

QCheckBox::indicator:checked {{
    background-color: {CATPPUCCIN_MOCHA['blue']};
    border-color: {CATPPUCCIN_MOCHA['blue']};
}}

QScrollArea {{
    border: none;
    background-color: {CATPPUCCIN_MOCHA['base']};
}}

QScrollBar:vertical {{
    background-color: {CATPPUCCIN_MOCHA['mantle']};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {CATPPUCCIN_MOCHA['surface1']};
    border-radius: 5px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {CATPPUCCIN_MOCHA['surface2']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {CATPPUCCIN_MOCHA['mantle']};
    height: 10px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {CATPPUCCIN_MOCHA['surface1']};
    border-radius: 5px;
    min-width: 20px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

QLabel {{
    color: {CATPPUCCIN_MOCHA['text']};
}}

QMenu {{
    background-color: {CATPPUCCIN_MOCHA['mantle']};
    color: {CATPPUCCIN_MOCHA['text']};
    border: 1px solid {CATPPUCCIN_MOCHA['surface0']};
    border-radius: 4px;
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 24px;
    border-radius: 3px;
}}

QMenu::item:selected {{
    background-color: {CATPPUCCIN_MOCHA['surface1']};
}}

QMenu::separator {{
    height: 1px;
    background-color: {CATPPUCCIN_MOCHA['surface0']};
    margin: 4px 8px;
}}

QSplitter::handle {{
    background-color: {CATPPUCCIN_MOCHA['surface0']};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

QPlainTextEdit {{
    background-color: {CATPPUCCIN_MOCHA['mantle']};
    color: {CATPPUCCIN_MOCHA['text']};
    border: 1px solid {CATPPUCCIN_MOCHA['surface0']};
    border-radius: 4px;
    font-family: monospace;
    padding: 4px;
}}

QStatusBar {{
    background-color: {CATPPUCCIN_MOCHA['crust']};
    color: {CATPPUCCIN_MOCHA['subtext0']};
}}

QGroupBox {{
    color: {CATPPUCCIN_MOCHA['text']};
    border: 1px solid {CATPPUCCIN_MOCHA['surface0']};
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 12px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    padding: 0 4px;
}}

QProgressBar {{
    background-color: {CATPPUCCIN_MOCHA['mantle']};
    border: 1px solid {CATPPUCCIN_MOCHA['surface0']};
    border-radius: 4px;
    text-align: center;
    color: {CATPPUCCIN_MOCHA['text']};
    height: 16px;
}}

QProgressBar::chunk {{
    background-color: {CATPPUCCIN_MOCHA['blue']};
    border-radius: 3px;
}}
"""
