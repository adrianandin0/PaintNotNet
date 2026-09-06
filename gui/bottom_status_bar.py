"""
gui/bottom_status_bar.py — Barra inferior estática para PaintNotNet.
Contiene:
- Cuadrícula de píxeles (conmutador)
- Botones de alineación de selección (Izquierda, Derecha, Arriba, Abajo, Centrar)
- Control de Zoom del lienzo (lupa, selector desplegable de zoom y botón reset 100%)
- Tamaño del lienzo en píxeles (icono pixel.png + dimensión ej: 800 x 600 (px))
- Coordenadas de posición del cursor fijas con icono pin.png.
- Adaptabilidad dinámica al tema activo.
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QToolButton, QFrame, QCheckBox, QComboBox
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

        # 1. Opción Cuadrícula y Reglas
        self.chk_grid = QCheckBox(t("Cuadrícula"))
        self.chk_grid.setIcon(QIcon("gui/iconos/transparency.png"))
        self.chk_grid.setToolTip(t("Muestra un borde fino negro/blanco alrededor de cada píxel al hacer zoom."))
        self.chk_grid.toggled.connect(self._on_toggle_grid)
        layout.addWidget(self.chk_grid)

        self.chk_rulers = QCheckBox(t("Reglas"))
        self.chk_rulers.setIcon(QIcon("gui/iconos/ruler.png"))
        self.chk_rulers.setToolTip(t("Muestra u oculta las reglas graduadas en centímetros en los bordes del lienzo."))
        self.chk_rulers.toggled.connect(self._on_toggle_rulers)
        layout.addWidget(self.chk_rulers)

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

        # Botón Centrar Horizontalmente
        self.btn_align_center_h = QToolButton()
        self.btn_align_center_h.setIcon(QIcon("gui/iconos/align_center_h.png"))
        self.btn_align_center_h.setIconSize(QSize(18, 18))
        self.btn_align_center_h.setToolTip(t("Centrar horizontalmente"))
        self.btn_align_center_h.clicked.connect(lambda: self._on_align("center_h"))
        layout.addWidget(self.btn_align_center_h)

        # Botón Centrar Verticalmente
        self.btn_align_center_v = QToolButton()
        self.btn_align_center_v.setIcon(QIcon("gui/iconos/align_center_v.png"))
        self.btn_align_center_v.setIconSize(QSize(18, 18))
        self.btn_align_center_v.setToolTip(t("Centrar verticalmente"))
        self.btn_align_center_v.clicked.connect(lambda: self._on_align("center_v"))
        layout.addWidget(self.btn_align_center_v)

        # Botón Centrar en Ambos Ejes
        self.btn_align_center = QToolButton()
        self.btn_align_center.setIcon(QIcon("gui/iconos/align_center.png"))
        self.btn_align_center.setIconSize(QSize(18, 18))
        self.btn_align_center.setToolTip(t("Centrar en ambos ejes"))
        self.btn_align_center.clicked.connect(lambda: self._on_align("center"))
        layout.addWidget(self.btn_align_center)

        # --- SECCIÓN ZOOM DE LIENZO ---
        self.sep_zoom = QFrame()
        self.sep_zoom.setFrameShape(QFrame.Shape.VLine)
        self.sep_zoom.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(self.sep_zoom)

        self.lbl_zoom_icon = QLabel()
        self.lbl_zoom_icon.setPixmap(QIcon("gui/iconos/zoom.png").pixmap(QSize(16, 16)))
        self.lbl_zoom_icon.setToolTip(t("Zoom del lienzo"))
        layout.addWidget(self.lbl_zoom_icon)

        self.combo_zoom = QComboBox()
        self.combo_zoom.setEditable(True)
        self.combo_zoom.setFixedWidth(75)
        self.combo_zoom.setFixedHeight(22)
        self.combo_zoom.addItems([
            "10%", "25%", "50%", "75%",
            "100%", "150%", "200%", "300%", "400%", "500%",
            "800%", "1000%", "1500%", "2000%", "3000%"
        ])
        self.combo_zoom.setCurrentText("100%")
        self.combo_zoom.setStyleSheet("font-size: 11px; padding: 1px;")
        self.combo_zoom.activated.connect(self._on_zoom_combobox_changed)
        if self.combo_zoom.lineEdit():
            self.combo_zoom.lineEdit().editingFinished.connect(self._on_zoom_combobox_changed)
        layout.addWidget(self.combo_zoom)

        self.btn_zoom_reset = QToolButton()
        self.btn_zoom_reset.setIcon(QIcon("gui/iconos/reset.png"))
        self.btn_zoom_reset.setIconSize(QSize(16, 16))
        self.btn_zoom_reset.setToolTip(t("Restablecer zoom a 100%"))
        self.btn_zoom_reset.setFixedSize(22, 22)
        self.btn_zoom_reset.clicked.connect(self._on_zoom_reset_clicked)
        layout.addWidget(self.btn_zoom_reset)

        layout.addStretch()

        # Label de Mensajes de Estado / Alertas
        self.lbl_msg = QLabel("")
        layout.addWidget(self.lbl_msg)

        # Timer para auto-ocultar mensajes
        self.msg_timer = QTimer(self)
        self.msg_timer.setSingleShot(True)
        self.msg_timer.timeout.connect(lambda: self.lbl_msg.setText(""))

        # --- SECCIÓN TAMAÑO DE LIENZO EN PIXELES ---
        self.sep_size = QFrame()
        self.sep_size.setFrameShape(QFrame.Shape.VLine)
        self.sep_size.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(self.sep_size)

        self.lbl_pixel_icon = QLabel()
        self.lbl_pixel_icon.setPixmap(QIcon("gui/iconos/pixel.png").pixmap(QSize(16, 16)))
        self.lbl_pixel_icon.setToolTip(t("Tamaño del lienzo en píxeles"))
        layout.addWidget(self.lbl_pixel_icon)

        self.lbl_canvas_size = QLabel("800 x 600 (px)")
        layout.addWidget(self.lbl_canvas_size)

        # --- COORDENADAS DEL CURSOR ---
        self.sep2 = QFrame()
        self.sep2.setFrameShape(QFrame.Shape.VLine)
        self.sep2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(self.sep2)

        self.lbl_pin_icon = QLabel()
        self.lbl_pin_icon.setPixmap(QIcon("gui/iconos/pin.png").pixmap(QSize(16, 16)))
        self.lbl_pin_icon.setToolTip(t("Posición del cursor"))
        layout.addWidget(self.lbl_pin_icon)

        self.lbl_cursor_pos = QLabel("-- x -- (px)")
        self.lbl_cursor_pos.setFixedWidth(110)
        self.lbl_cursor_pos.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
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
        self.lbl_canvas_size.setStyleSheet(label_style)
        self.lbl_cursor_pos.setStyleSheet(label_style)
        self.lbl_msg.setStyleSheet(f"font-size: 11px; font-weight: normal; font-style: normal; color: {msg_color}; padding: 0 4px;")

        sep_style = f"color: {border_subtle}; background-color: {border_subtle};"
        self.sep1.setStyleSheet(sep_style)
        self.sep_zoom.setStyleSheet(sep_style)
        self.sep_size.setStyleSheet(sep_style)
        self.sep2.setStyleSheet(sep_style)

    def _on_toggle_grid(self, checked: bool):
        if self.main_window and hasattr(self.main_window, 'tab_widget'):
            for i in range(self.main_window.tab_widget.count()):
                container = self.main_window.tab_widget.widget(i)
                canvas = container.widget() if (container and hasattr(container, 'widget')) else container
                if canvas:
                    canvas.show_pixel_grid = checked
                    canvas.update()
        elif self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.show_pixel_grid = checked
            self.main_window.lienzo.update()

    def _on_toggle_rulers(self, checked: bool):
        if self.main_window and hasattr(self.main_window, 'tab_widget'):
            for i in range(self.main_window.tab_widget.count()):
                container = self.main_window.tab_widget.widget(i)
                if container and hasattr(container, 'set_rulers_visible'):
                    container.set_rulers_visible(checked)

    def _on_align(self, alignment: str):
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            canvas = self.main_window.lienzo
            if hasattr(canvas, 'align_selection'):
                canvas.align_selection(alignment)

    def _on_zoom_combobox_changed(self, *args):
        text = self.combo_zoom.currentText().replace("%", "").strip()
        try:
            val = float(text)
            scale = val / 100.0
            if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
                self.main_window.lienzo.set_zoom(scale)
        except ValueError:
            pass

    def _on_zoom_reset_clicked(self):
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.set_zoom(1.0)

    def sync_zoom_from_canvas(self, scale_factor: float):
        if hasattr(self, 'combo_zoom'):
            pct = int(round(scale_factor * 100))
            txt = f"{pct}%"
            self.combo_zoom.blockSignals(True)
            self.combo_zoom.setCurrentText(txt)
            self.combo_zoom.blockSignals(False)

    def actualizar_tamano_lienzo(self, w: int, h: int):
        if hasattr(self, 'lbl_canvas_size'):
            self.lbl_canvas_size.setText(f"{w} x {h} (px)")

    def actualizar_posicion_cursor(self, x: int | None, y: int | None):
        if x is not None and y is not None:
            self.lbl_cursor_pos.setText(f"{x} x {y} (px)")
        else:
            self.lbl_cursor_pos.setText("-- x -- (px)")

    def mostrar_mensaje(self, text: str, msecs: int = 2500, italic: bool = False):
        font_style = "italic" if italic else "normal"
        msg_color = getattr(self, '_msg_color', '#007acc')
        self.lbl_msg.setStyleSheet(f"font-size: 11px; font-weight: normal; font-style: {font_style}; color: {msg_color}; padding: 0 4px;")
        self.lbl_msg.setText(text)
        self.msg_timer.start(msecs)

    def retraducir_bar(self):
        self.chk_grid.setText(t("Cuadrícula"))
        self.chk_grid.setToolTip(t("Muestra un borde fino negro/blanco alrededor de cada píxel al hacer zoom."))
        self.chk_rulers.setText(t("Reglas"))
        self.chk_rulers.setToolTip(t("Muestra u oculta las reglas graduadas en centímetros en los bordes del lienzo."))
        self.lbl_align.setText(t("Alinear selección:"))
        self.btn_align_left.setToolTip(t("Alinear a la izquierda"))
        self.btn_align_right.setToolTip(t("Alinear a la derecha"))
        self.btn_align_top.setToolTip(t("Alinear arriba"))
        self.btn_align_bottom.setToolTip(t("Alinear abajo"))
        self.btn_align_center_h.setToolTip(t("Centrar horizontalmente"))
        self.btn_align_center_v.setToolTip(t("Centrar verticalmente"))
        self.btn_align_center.setToolTip(t("Centrar en ambos ejes"))
        self.lbl_zoom_icon.setToolTip(t("Zoom del lienzo"))
        self.btn_zoom_reset.setToolTip(t("Restablecer zoom a 100%"))
        self.lbl_pixel_icon.setToolTip(t("Tamaño del lienzo en píxeles"))
        self.lbl_pin_icon.setToolTip(t("Posición del cursor"))
