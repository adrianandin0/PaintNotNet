"""
gui/bottom_status_bar.py — Barra inferior estática para PaintNotNet.
Contiene:
- Cuadrícula de píxeles (conmutador)
- Botones de alineación de selección (Izquierda, Derecha, Arriba, Abajo, Centrar)
- Coordenadas de posición del cursor fijas a la derecha.
- Adaptabilidad dinámica al tema activo (fuente Negra en tema claro, Blanca en tema oscuro, 11px).
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QToolButton, QFrame, QCheckBox
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon
from core.i18n import t


class BottomStatusBarWidget(QWidget):
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setFixedHeight(30)
        self.setObjectName("bottom_status_bar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 12, 2)
        layout.setSpacing(6)

        # 1. Opción Cuadrícula de píxeles
        self.chk_grid = QCheckBox(t("Cuadrícula de píxeles"))
        self.chk_grid.setIcon(QIcon("gui/iconos/transparency.png"))
        self.chk_grid.setToolTip(t("Muestra un borde fino negro/blanco alrededor de cada píxel al hacer zoom."))
        self.chk_grid.toggled.connect(self._on_toggle_grid)
        layout.addWidget(self.chk_grid)

        # Separador vertical 1
        self.sep1 = QFrame()
        self.sep1.setFrameShape(QFrame.Shape.VLine)
        self.sep1.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(self.sep1)

        # 2. Alineación de Selección
        self.lbl_align = QLabel(t("Alinear selección:"))
        layout.addWidget(self.lbl_align)

        # Botón Alinear Izquierda
        self.btn_align_left = QToolButton()
        self.btn_align_left.setIcon(QIcon("gui/iconos/align_left.png"))
        self.btn_align_left.setIconSize(QSize(18, 18))
        self.btn_align_left.setToolTip(t("Alinear a la izquierda"))
        self.btn_align_left.clicked.connect(lambda: self._on_align("left"))
        layout.addWidget(self.btn_align_left)

        # Botón Alinear Derecha
        self.btn_align_right = QToolButton()
        self.btn_align_right.setIcon(QIcon("gui/iconos/align_right.png"))
        self.btn_align_right.setIconSize(QSize(18, 18))
        self.btn_align_right.setToolTip(t("Alinear a la derecha"))
        self.btn_align_right.clicked.connect(lambda: self._on_align("right"))
        layout.addWidget(self.btn_align_right)

        # Botón Alinear Arriba
        self.btn_align_top = QToolButton()
        self.btn_align_top.setIcon(QIcon("gui/iconos/align_top.png"))
        self.btn_align_top.setIconSize(QSize(18, 18))
        self.btn_align_top.setToolTip(t("Alinear arriba"))
        self.btn_align_top.clicked.connect(lambda: self._on_align("top"))
        layout.addWidget(self.btn_align_top)

        # Botón Alinear Abajo
        self.btn_align_bottom = QToolButton()
        self.btn_align_bottom.setIcon(QIcon("gui/iconos/align_bottom.png"))
        self.btn_align_bottom.setIconSize(QSize(18, 18))
        self.btn_align_bottom.setToolTip(t("Alinear abajo"))
        self.btn_align_bottom.clicked.connect(lambda: self._on_align("bottom"))
        layout.addWidget(self.btn_align_bottom)

        # Botón Centrar Selección
        self.btn_align_center = QToolButton()
        self.btn_align_center.setIcon(QIcon("gui/iconos/align_center.png"))
        self.btn_align_center.setIconSize(QSize(18, 18))
        self.btn_align_center.setToolTip(t("Centrar selección"))
        self.btn_align_center.clicked.connect(lambda: self._on_align("center"))
        layout.addWidget(self.btn_align_center)

        layout.addStretch()

        # 3. Label de Mensajes de Estado / Alertas (a la izquierda de las coordenadas X, Y)
        self.lbl_msg = QLabel("")
        layout.addWidget(self.lbl_msg)

        # Timer para auto-ocultar mensajes
        self.msg_timer = QTimer(self)
        self.msg_timer.setSingleShot(True)
        self.msg_timer.timeout.connect(lambda: self.lbl_msg.setText(""))

        # Separador vertical 2
        self.sep2 = QFrame()
        self.sep2.setFrameShape(QFrame.Shape.VLine)
        self.sep2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(self.sep2)

        # 4. Coordenadas del Cursor (Fijas a la derecha de la barra estática)
        self.lbl_cursor_pos = QLabel("X: -- px, Y: -- px")
        layout.addWidget(self.lbl_cursor_pos)

        # Aplicar diseño y estilos según el tema activo
        self.actualizar_estilo_tema()

    def actualizar_estilo_tema(self):
        from core.theme import ThemeManager
        tm = ThemeManager()
        res_nombre = tm.resolver_nombre_tema(tm.current_theme)
        is_dark = (res_nombre == "Oscuro")
        pal = tm._palettes.get(res_nombre, tm._palettes["Oscuro" if is_dark else "Claro"])

        bg_col = pal.get("panel_bg", "#383838" if is_dark else "#DFDFDF")
        brd_col = pal.get("border_color", "#686868" if is_dark else "#B0B0B0")
        btn_hv = pal.get("button_hover", "#555555" if is_dark else "#D4D4D4")

        # Texto Negro en tema claro, Blanco en tema oscuro (tamaño 11px, respetando fuente del sistema)
        text_color_exact = "#FFFFFF" if is_dark else "#000000"
        border_subtle = "#555555" if is_dark else "#A0A0A0"
        msg_color = "#64B4FF" if is_dark else "#0055B8"

        self.setStyleSheet(f"""
            QWidget#bottom_status_bar {{
                background-color: {bg_col};
                border-top: 1px solid {brd_col};
                color: {text_color_exact};
                font-size: 11px;
            }}
            QToolButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 2px;
            }}
            QToolButton:hover {{
                background-color: {btn_hv};
                border: 1px solid {brd_col};
            }}
            QToolButton:pressed {{
                background-color: #0078D7;
            }}
            QCheckBox {{
                font-size: 11px;
                color: {text_color_exact};
            }}
            QLabel {{
                font-size: 11px;
                color: {text_color_exact};
            }}
        """)

        self._msg_color = msg_color
        label_style = f"font-size: 11px; font-weight: normal; color: {text_color_exact};"
        self.lbl_align.setStyleSheet(label_style)
        self.lbl_cursor_pos.setStyleSheet(label_style)
        self.lbl_msg.setStyleSheet(f"font-size: 11px; font-weight: normal; font-style: normal; color: {msg_color}; padding: 0 4px;")
        self.sep1.setStyleSheet(f"color: {border_subtle}; background-color: {border_subtle};")
        self.sep2.setStyleSheet(f"color: {border_subtle}; background-color: {border_subtle};")

    def _on_toggle_grid(self, checked: bool):
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            canvas = self.main_window.lienzo
            canvas.show_pixel_grid = checked
            canvas.update()

    def _on_align(self, alignment: str):
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            canvas = self.main_window.lienzo
            if hasattr(canvas, 'align_selection'):
                canvas.align_selection(alignment)

    def actualizar_posicion_cursor(self, x: int | None, y: int | None):
        if x is not None and y is not None:
            self.lbl_cursor_pos.setText(f"X: {x} px, Y: {y} px")
        else:
            self.lbl_cursor_pos.setText("X: -- px, Y: -- px")

    def mostrar_mensaje(self, text: str, msecs: int = 2500, italic: bool = False):
        font_style = "italic" if italic else "normal"
        msg_color = getattr(self, '_msg_color', '#007acc')
        self.lbl_msg.setStyleSheet(f"font-size: 11px; font-weight: normal; font-style: {font_style}; color: {msg_color}; padding: 0 4px;")
        self.lbl_msg.setText(text)
        self.msg_timer.start(msecs)

    def retraducir_bar(self):
        self.chk_grid.setText(t("Cuadrícula de píxeles"))
        self.chk_grid.setToolTip(t("Muestra un borde fino negro/blanco alrededor de cada píxel al hacer zoom."))
        self.lbl_align.setText(t("Alinear selección:"))
        self.btn_align_left.setToolTip(t("Alinear a la izquierda"))
        self.btn_align_right.setToolTip(t("Alinear a la derecha"))
        self.btn_align_top.setToolTip(t("Alinear arriba"))
        self.btn_align_bottom.setToolTip(t("Alinear abajo"))
        self.btn_align_center.setToolTip(t("Centrar selección"))
