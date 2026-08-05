import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import QSettings, Qt

class ThemeManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            cls._instance._init_manager()
        return cls._instance

    def _init_manager(self):
        self.current_theme = "Definido por el sistema"
        self._palettes = {
            "Oscuro": {
                "is_dark": True,
                "window_bg": "#2D2D2D",
                "panel_bg": "#383838",
                "canvas_area_bg": "#525252",
                "text_color": "#EDEDED",
                "subtext_color": "#AAAAAA",
                "border_color": "#686868",
                "accent_color": "#0078D7",
                "tab_bg": "#7A7A7A",
                "tab_selected_bg": "#525252",
                "dock_title_bg": "#282828",
                "group_title_color": "#64B4FF",
                "button_bg": "#444444",
                "button_hover": "#555555",
                "input_bg": "#2B2B2B",
            },
            "Claro": {
                "is_dark": False,
                "window_bg": "#EAEAEA",
                "panel_bg": "#DFDFDF",
                "canvas_area_bg": "#C8C8C8",
                "text_color": "#262626",
                "subtext_color": "#484848",
                "border_color": "#B0B0B0",
                "accent_color": "#0066CC",
                "tab_bg": "#D0D0D0",
                "tab_selected_bg": "#C8C8C8",
                "dock_title_bg": "#D0D0D0",
                "group_title_color": "#222222",
                "button_bg": "#E2E2E2",
                "button_hover": "#D4D4D4",
                "input_bg": "#FFFFFF",
            }
        }
        self.cargar_tema_configurado()

    def registrar_paleta(self, nombre: str, paleta: dict):
        """Permite agregar nuevos temas personalizados fácilmente (ej. 'Rosa', 'Azul', 'Alto Contraste')."""
        self._palettes[nombre] = paleta

    def obtener_temas_disponibles(self) -> list[str]:
        return ["Definido por el sistema", "Oscuro", "Claro"] + [t for t in self._palettes.keys() if t not in ("Oscuro", "Claro")]

    def obtener_color_area_canvas(self) -> QColor:
        res_nombre = self.resolver_nombre_tema(self.current_theme)
        pal = self._palettes.get(res_nombre, self._palettes["Claro"])
        hex_col = pal.get("canvas_area_bg", "#C8C8C8")
        return QColor(hex_col)

    def es_sistema_oscuro(self) -> bool:
        app = QApplication.instance()
        if app:
            hints = app.styleHints()
            if hasattr(hints, 'colorScheme'):
                if hints.colorScheme() == Qt.ColorScheme.Dark:
                    return True
                if hints.colorScheme() == Qt.ColorScheme.Light:
                    return False
            bg = app.palette().color(QPalette.ColorRole.Window)
            return bg.lightness() < 128
        return True

    def resolver_nombre_tema(self, nombre: str) -> str:
        if nombre == "Definido por el sistema" or "sistema" in nombre.lower() or "system" in nombre.lower():
            return "Oscuro" if self.es_sistema_oscuro() else "Claro"
        if nombre in self._palettes:
            return nombre
        if "claro" in nombre.lower() or "light" in nombre.lower():
            return "Claro"
        return "Oscuro"

    def cargar_tema_configurado(self):
        settings = QSettings("PaintNotNet", "PaintNotNet")
        tema = settings.value("theme", "Definido por el sistema")
        self.current_theme = str(tema)

    def establecer_tema(self, nombre_tema: str, main_window=None):
        self.current_theme = nombre_tema
        res_nombre = self.resolver_nombre_tema(nombre_tema)

        app = QApplication.instance()
        if not app:
            return

        if main_window and hasattr(main_window, 'tab_widget') and main_window.tab_widget:
            main_window.tab_widget.setStyleSheet("")

        is_dark = (res_nombre == "Oscuro")
        pal = self._palettes.get(res_nombre, self._palettes["Oscuro" if is_dark else "Claro"])
        w_bg   = pal.get("window_bg", "#2D2D2D" if is_dark else "#EAEAEA")
        p_bg   = pal.get("panel_bg", "#383838" if is_dark else "#DFDFDF")
        c_bg   = pal.get("canvas_area_bg", "#525252" if is_dark else "#C8C8C8")
        txt    = pal.get("text_color", "#EDEDED" if is_dark else "#222222")
        brd    = pal.get("border_color", "#686868" if is_dark else "#B0B0B0")
        acc    = pal.get("accent_color", "#0078D7" if is_dark else "#0066CC")
        dt_bg  = pal.get("dock_title_bg", "#282828" if is_dark else "#D0D0D0")
        gt_col = pal.get("group_title_color", "#64B4FF" if is_dark else "#222222")
        btn_bg = pal.get("button_bg", "#444444" if is_dark else "#E2E2E2")
        btn_hv = pal.get("button_hover", "#555555" if is_dark else "#D4D4D4")
        inp_bg = pal.get("input_bg", "#2B2B2B" if is_dark else "#FFFFFF")

        # Set App Palette
        app_pal = QPalette()
        app_pal.setColor(QPalette.ColorRole.Window, QColor(p_bg))
        app_pal.setColor(QPalette.ColorRole.WindowText, QColor(txt))
        app_pal.setColor(QPalette.ColorRole.Base, QColor(inp_bg))
        app_pal.setColor(QPalette.ColorRole.AlternateBase, QColor(c_bg))
        app_pal.setColor(QPalette.ColorRole.Text, QColor(txt))
        app_pal.setColor(QPalette.ColorRole.Button, QColor(btn_bg))
        app_pal.setColor(QPalette.ColorRole.ButtonText, QColor(txt))
        app_pal.setColor(QPalette.ColorRole.Highlight, QColor(acc))
        app_pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
        app.setPalette(app_pal)

        chk_img = "url(gui/iconos/check.png)"
        radio_border = f"3px solid {inp_bg}"

        qss = f"""
        QMainWindow, QDialog, QDockWidget > QWidget {{
            background-color: {p_bg};
            color: {txt};
        }}
        QLabel {{
            color: {txt};
        }}
        QCheckBox, QRadioButton {{
            color: {txt} !important;
            spacing: 5px;
        }}
        QCheckBox::indicator {{
            width: 14px;
            height: 14px;
            border: 1px solid {brd};
            border-radius: 3px;
            background-color: {inp_bg};
        }}
        QCheckBox::indicator:hover {{
            border-color: {acc};
        }}
        QCheckBox::indicator:checked {{
            background-color: {acc};
            border-color: {acc};
            image: {chk_img};
        }}
        QRadioButton::indicator {{
            width: 14px;
            height: 14px;
            border: 1px solid {brd};
            border-radius: 7px;
            background-color: {inp_bg};
        }}
        QRadioButton::indicator:hover {{
            border-color: {acc};
        }}
        QRadioButton::indicator:checked {{
            background-color: {acc};
            border: {radio_border};
        }}
        QMenuBar, QMenuBar::item {{
            background-color: {p_bg};
            color: {txt};
        }}
        QMenuBar::item:selected {{
            background-color: {btn_hv};
        }}
        QMenu {{
            background-color: {inp_bg};
            color: {txt};
            border: 1px solid {brd};
        }}
        QMenu::item:selected {{
            background-color: {acc};
            color: #FFFFFF;
        }}
        QToolBar {{
            background-color: {p_bg};
            border-bottom: 1px solid {brd};
            color: {txt};
        }}
        QDockWidget {{
            background-color: {p_bg};
            color: {txt};
            titlebar-close-icon: url(gui/iconos/close.png);
        }}
        QDockWidget::title {{
            background-color: {dt_bg};
            color: {txt};
            padding: 4px;
        }}
        QGroupBox {{
            font-size: 11px;
            font-weight: bold;
            color: {gt_col};
            border: 1px solid {brd};
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 6px;
            background-color: {p_bg};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 4px;
            color: {gt_col};
        }}
        QListWidget, QListView, QTreeView, QTableView, QTableWidget {{
            background-color: {inp_bg};
            color: {txt};
            border: 1px solid {brd};
            gridline-color: {brd};
        }}
        QListWidget::item, QListView::item, QTreeView::item, QTableWidget::item {{
            color: {txt};
            background-color: {inp_bg};
        }}
        QListWidget::item:selected, QListView::item:selected, QTreeView::item:selected, QTableWidget::item:selected {{
            background-color: {acc};
            color: #FFFFFF;
        }}
        QHeaderView::section {{
            background-color: {p_bg};
            color: {txt};
            border: 1px solid {brd};
            padding: 4px;
            font-weight: bold;
        }}
        QTabWidget::pane {{
            border: none;
            background-color: {c_bg} !important;
        }}
        QTabBar::tab {{
            background: {dt_bg};
            color: {txt};
            border: 1px solid {brd};
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 5px 14px 5px 12px;
            margin-right: 3px;
            font-size: 11px;
        }}
        QTabBar::tab:selected {{
            background: {c_bg} !important;
            color: {txt};
            border-color: {acc};
            font-weight: normal;
        }}
        QTabBar::tab:hover {{
            background: {btn_hv};
            color: {txt};
        }}
        QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {{
            background-color: {c_bg} !important;
            border: none;
        }}
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
            background-color: {inp_bg};
            color: {txt};
            border: 1px solid {brd};
            border-radius: 3px;
            padding: 2px 4px;
        }}
        QToolButton, QPushButton {{
            background-color: {btn_bg};
            color: {txt};
            border: 1px solid {brd};
            border-radius: 3px;
        }}
        QToolButton:hover, QPushButton:hover {{
            background-color: {btn_hv};
        }}
        QToolButton:checked, QPushButton:checked {{
            background-color: {acc};
            border-color: {acc};
            color: #FFFFFF;
        }}
        QToolButton:checked:hover, QPushButton:checked:hover {{
            background-color: {acc};
            border-color: {acc};
            color: #FFFFFF;
        }}
        QToolTip {{
            background-color: #333333;
            color: #FFFFFF;
            border: 1px solid #555555;
        }}
        """
        app.setStyleSheet(qss)

        if main_window:
            if hasattr(main_window, 'tab_widget') and main_window.tab_widget:
                for idx in range(main_window.tab_widget.count()):
                    scroll = main_window.tab_widget.widget(idx)
                    if scroll:
                        scroll.setStyleSheet(f"QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {{ background-color: {c_bg} !important; border: none; }}")
                        if hasattr(scroll, 'viewport') and scroll.viewport():
                            scroll.viewport().setStyleSheet(f"background-color: {c_bg} !important;")
                        if hasattr(scroll, 'widget') and scroll.widget():
                            scroll.widget().update()
            if hasattr(main_window, 'color_panel') and main_window.color_panel:
                main_window.color_panel.setStyleSheet(f"ColorPanelWidget {{ background-color: {p_bg}; }}")
            if hasattr(main_window, 'advanced_color_panel') and main_window.advanced_color_panel and hasattr(main_window.advanced_color_panel, 'actualizar_estilo_tema'):
                main_window.advanced_color_panel.actualizar_estilo_tema()
            if hasattr(main_window, 'effects_panel') and main_window.effects_panel and hasattr(main_window.effects_panel, 'actualizar_estilo_tema'):
                main_window.effects_panel.actualizar_estilo_tema()
            if hasattr(main_window, 'brushes_panel') and main_window.brushes_panel and hasattr(main_window.brushes_panel, 'actualizar_estilo_tema'):
                main_window.brushes_panel.actualizar_estilo_tema()
            if hasattr(main_window, 'top_toolbar') and main_window.top_toolbar and hasattr(main_window.top_toolbar, 'actualizar_estilo_tema'):
                main_window.top_toolbar.actualizar_estilo_tema()
            if hasattr(main_window, 'text_panel') and main_window.text_panel and hasattr(main_window.text_panel, 'actualizar_estilo_tema'):
                main_window.text_panel.actualizar_estilo_tema()
