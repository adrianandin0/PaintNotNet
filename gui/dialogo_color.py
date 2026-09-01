"""
dialogo_color.py — Diálogo independiente de selección de color para efectos y herramientas.

Incluye:
  - Muestra de color actual con ajedrez de alpha y slider de Alfa
  - Círculo de color HSV (ColorWheel)
  - Paleta fija de 70 colores (7x10)
  - Deslizadores y campos numéricos para RGB (R, G, B), Hexadecimal y HSV (H, S, V)
  - Paleta de colores guardados (21 slots), sincronizada con el panel lateral de colores
  - Vista previa en tiempo real
  - Botones de Aceptar y Cancelar
"""
import math
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QSlider, QLineEdit, QGridLayout, QFrame, QSizePolicy
)
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QLinearGradient
from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from core.i18n import t
from gui.color_panel import (
    ColorButton, CustomSlotButton, ColorWheel,
    cargar_custom_colors, guardar_custom_colors,
    registrar_listener_custom, desregistrar_listener_custom, notificar_cambio_custom_slots
)


class ColorSwatchWidget(QWidget):
    """Muestra de color actual con fondo de ajedrez para transparencia."""
    def __init__(self, color=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(54, 54)
        self.color = QColor(color) if color else QColor(255, 255, 255)

    def set_color(self, color):
        self.color = QColor(color) if color else QColor(255, 255, 255)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        w, h = self.width(), self.height()

        # 1. Fondo ajedrez
        sq = 6
        c1 = QColor(255, 255, 255)
        c2 = QColor(200, 200, 200)
        for y in range(0, h, sq):
            for x in range(0, w, sq):
                c = c1 if ((x // sq) + (y // sq)) % 2 == 0 else c2
                painter.fillRect(x, y, sq, sq, c)

        # 2. Color con Alfa
        if self.color and self.color.isValid():
            painter.fillRect(0, 0, w, h, self.color)

        # 3. Borde
        painter.setPen(QPen(QColor(120, 120, 120), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(0, 0, w - 1, h - 1)


class SingleColorPickerDialog(QDialog):
    """
    Diálogo completo para seleccionar un único color con vista previa en tiempo real.
    """
    color_preview_changed = pyqtSignal(QColor)

    def __init__(self, initial_color: QColor = QColor(255, 255, 255), parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("Seleccionar color"))
        self.setFixedWidth(340)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)

        self.initial_color = QColor(initial_color) if (initial_color and initial_color.isValid()) else QColor(255, 255, 255)
        self.current_color = QColor(self.initial_color)
        self._updating = False

        self.custom_colors = cargar_custom_colors()

        self._build_ui()
        registrar_listener_custom(self)
        self.set_color(self.initial_color, emit_preview=False)
        self._apply_theme_style()

    def _apply_theme_style(self):
        from core.theme import ThemeManager
        tm = ThemeManager()
        is_dark = (tm.resolver_nombre_tema(tm.current_theme) == "Oscuro")

        bg_col = "#262626" if is_dark else "#F0F0F0"
        txt_col = "#FFFFFF" if is_dark else "#141414"
        inp_bg = "#1E1E1E" if is_dark else "#FFFFFF"
        brd_col = "#444444" if is_dark else "#CCCCCC"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_col};
                color: {txt_col};
                font-size: 11px;
            }}
            QLabel {{
                color: {txt_col};
                font-size: 11px;
                font-weight: normal;
            }}
            QLineEdit, QSpinBox {{
                background-color: {inp_bg};
                color: {txt_col};
                border: 1px solid {brd_col};
                border-radius: 4px;
                padding: 1px 3px;
                font-size: 11px;
            }}
            QPushButton {{
                background-color: {"#3B3B3B" if is_dark else "#E1E1E1"};
                color: {txt_col};
                border: 1px solid {brd_col};
                border-radius: 4px;
                padding: 4px 14px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {"#4A4A4A" if is_dark else "#D4D4D4"};
            }}
            QPushButton#btn_ok {{
                background-color: #0078D7;
                color: #FFFFFF;
                border: 1px solid #005A9E;
            }}
            QPushButton#btn_ok:hover {{
                background-color: #1A8FE8;
            }}
        """)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # --- SECCIÓN SUPERIOR: Swatch + Alpha | ColorWheel ---
        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)

        # Izquierda: Muestra de Color + Slider Alpha
        left_top = QVBoxLayout()
        left_top.setSpacing(4)
        left_top.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.swatch = ColorSwatchWidget(self.current_color)
        left_top.addWidget(self.swatch, alignment=Qt.AlignmentFlag.AlignCenter)

        self.lbl_alpha = QLabel(t("Alfa:"))
        self.lbl_alpha.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_top.addWidget(self.lbl_alpha)

        self.slider_alpha = QSlider(Qt.Orientation.Horizontal)
        self.slider_alpha.setRange(0, 255)
        self.slider_alpha.setValue(self.current_color.alpha())
        self.slider_alpha.setFixedHeight(14)
        self.slider_alpha.setFixedWidth(80)
        self.slider_alpha.valueChanged.connect(self._on_alpha_slider)
        left_top.addWidget(self.slider_alpha, alignment=Qt.AlignmentFlag.AlignCenter)

        # Derecha: Color Wheel
        self.wheel = ColorWheel()
        self.wheel.setFixedSize(68, 68)
        self.wheel.colorChanged.connect(self._on_wheel_changed)

        top_layout.addLayout(left_top)
        top_layout.addStretch()
        top_layout.addWidget(self.wheel, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addLayout(top_layout)

        # --- SECCIÓN CENTRAL: Paleta Fija (7x10) + Controles RGB / Hex / HSV ---
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(10)

        # Paleta Fija (7 columnas x 10 filas)
        grid_paleta = QGridLayout()
        grid_paleta.setSpacing(1)
        grid_paleta.setContentsMargins(0, 0, 0, 0)

        self.paleta_fija = [
            "#000000", "#333333", "#555555", "#888888", "#AAAAAA", "#CCCCCC", "#FFFFFF",
            "#4A0000", "#800000", "#CC0000", "#FF0000", "#FF4D4D", "#FF8080", "#FFB3B3",
            "#662200", "#804000", "#CC6600", "#FF7F00", "#FFA040", "#FFC080", "#FFE0C0",
            "#2A1B17", "#3E2723", "#5D4037", "#795548", "#8D6E63", "#BCAAA4", "#D7CCC8",
            "#4D4D00", "#808000", "#CCCC00", "#FFFF00", "#FFFF55", "#FFFF80", "#FFFFC0",
            "#004D00", "#008000", "#00CC00", "#00FF00", "#55FF55", "#80FF80", "#C0FFC0",
            "#004D4D", "#008080", "#00CCCC", "#00FFFF", "#55FFFF", "#80FFFF", "#C0FFFF",
            "#00004D", "#000080", "#0000CC", "#0000FF", "#4D4DFF", "#8080FF", "#B3B3FF",
            "#2A004D", "#4B0082", "#800080", "#A000FF", "#C055FF", "#D8B4FE", "#F0E0FF",
            "#4D0026", "#800040", "#CC0066", "#FF007F", "#FF55A3", "#FFB3D9", "#FFE6F2"
        ]

        def _make_pal_handler(hex_code):
            return lambda: self._on_palette_clicked(hex_code)

        for idx, hex_color in enumerate(self.paleta_fija):
            row = idx // 7
            col = idx % 7
            btn = ColorButton(hex_color)
            btn.left_clicked.connect(_make_pal_handler(hex_color))
            btn.right_clicked.connect(_make_pal_handler(hex_color))
            grid_paleta.addWidget(btn, row, col)

        mid_layout.addLayout(grid_paleta)

        # Controles numéricos y sliders (RGB + Hex + HSV)
        right_ctrls = QVBoxLayout()
        right_ctrls.setSpacing(3)

        # Helpers para filas de slider + spin
        def _make_row(label_text, min_val, max_val):
            row = QHBoxLayout()
            row.setSpacing(4)
            lbl = QLabel(label_text)
            lbl.setFixedWidth(26)
            lbl.setStyleSheet("font-size: 11px;")

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(min_val, max_val)
            slider.setFixedHeight(14)
            slider.setFixedWidth(90)

            spin = QSpinBox()
            spin.setRange(min_val, max_val)
            spin.setFixedWidth(44)
            spin.setFixedHeight(20)

            row.addWidget(lbl)
            row.addWidget(slider)
            row.addWidget(spin)
            return row, slider, spin

        # RGB Rows
        row_r, self.slider_r, self.spin_r = _make_row("R:", 0, 255)
        row_g, self.slider_g, self.spin_g = _make_row("G:", 0, 255)
        row_b, self.slider_b, self.spin_b = _make_row("B:", 0, 255)

        right_ctrls.addLayout(row_r)
        right_ctrls.addLayout(row_g)
        right_ctrls.addLayout(row_b)

        # Hex Row
        row_hex = QHBoxLayout()
        row_hex.setSpacing(4)
        lbl_hex = QLabel("Hex.:")
        lbl_hex.setFixedWidth(34)
        lbl_hex.setStyleSheet("font-size: 11px;")
        self.edit_hex = QLineEdit()
        self.edit_hex.setMaxLength(6)
        self.edit_hex.setFixedWidth(70)
        self.edit_hex.setFixedHeight(20)
        self.edit_hex.textEdited.connect(self._on_hex_edited)

        row_hex.addWidget(lbl_hex)
        row_hex.addWidget(self.edit_hex)
        row_hex.addStretch()
        right_ctrls.addLayout(row_hex)

        # HSV Rows
        row_h, self.slider_h, self.spin_h = _make_row("H:", 0, 360)
        row_s, self.slider_s, self.spin_s = _make_row("S:", 0, 255)
        row_v, self.slider_v, self.spin_v = _make_row("V:", 0, 255)

        right_ctrls.addLayout(row_h)
        right_ctrls.addLayout(row_s)
        right_ctrls.addLayout(row_v)

        mid_layout.addLayout(right_ctrls)
        main_layout.addLayout(mid_layout)

        # Conectar RGB sliders & spins
        self.slider_r.valueChanged.connect(lambda v: self._on_rgb_changed())
        self.spin_r.valueChanged.connect(lambda v: self._on_rgb_changed())
        self.slider_g.valueChanged.connect(lambda v: self._on_rgb_changed())
        self.spin_g.valueChanged.connect(lambda v: self._on_rgb_changed())
        self.slider_b.valueChanged.connect(lambda v: self._on_rgb_changed())
        self.spin_b.valueChanged.connect(lambda v: self._on_rgb_changed())

        # Conectar HSV sliders & spins
        self.slider_h.valueChanged.connect(lambda v: self._on_hsv_changed())
        self.spin_h.valueChanged.connect(lambda v: self._on_hsv_changed())
        self.slider_s.valueChanged.connect(lambda v: self._on_hsv_changed())
        self.spin_s.valueChanged.connect(lambda v: self._on_hsv_changed())
        self.slider_v.valueChanged.connect(lambda v: self._on_hsv_changed())
        self.spin_v.valueChanged.connect(lambda v: self._on_hsv_changed())

        # --- SECCIÓN INFERIOR: Colores Guardados (21 slots) ---
        self.lbl_saved = QLabel(t("Guardadas:"))
        self.lbl_saved.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.lbl_saved)

        grid_custom = QGridLayout()
        grid_custom.setSpacing(1)
        grid_custom.setContentsMargins(0, 0, 0, 0)
        grid_custom.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.botones_custom = []
        for idx in range(21):
            row = idx // 7
            col = idx % 7
            btn_slot = CustomSlotButton(idx)
            btn_slot.setToolTip(t("Slot vacío: Clic para Guardar | Slot lleno: Clic para Usar (Shift+Clic Reemplazar, Ctrl+Clic Eliminar)"))
            btn_slot.slot_interacted.connect(self._on_custom_slot_interacted)

            grid_custom.addWidget(btn_slot, row, col)
            self.botones_custom.append(btn_slot)

        main_layout.addLayout(grid_custom)
        self.actualizar_custom_slots_ui()

        # --- BOTONES DE ACCIÓN: Aceptar / Cancelar ---
        layout_btns = QHBoxLayout()
        layout_btns.setSpacing(8)

        btn_ok = QPushButton(t("Aceptar"))
        btn_ok.setObjectName("btn_ok")
        btn_ok.clicked.connect(self._on_accept)

        btn_cancel = QPushButton(t("Cancelar"))
        btn_cancel.clicked.connect(self._on_cancel)

        layout_btns.addStretch()
        layout_btns.addWidget(btn_ok)
        layout_btns.addWidget(btn_cancel)
        main_layout.addLayout(layout_btns)

    # Lógica de Actualización y Cambio de Color

    def set_color(self, color: QColor, emit_preview=True):
        if self._updating:
            return
        self._updating = True
        self.current_color = QColor(color)

        r, g, b, a = self.current_color.red(), self.current_color.green(), self.current_color.blue(), self.current_color.alpha()
        h, s, v, _ = self.current_color.getHsv()
        if h < 0:
            h = 0

        self.swatch.set_color(self.current_color)
        self.wheel.set_color(self.current_color)

        self.slider_alpha.blockSignals(True)
        self.slider_alpha.setValue(a)
        self.slider_alpha.blockSignals(False)

        # Sync RGB
        for widget, val in [(self.slider_r, r), (self.spin_r, r),
                            (self.slider_g, g), (self.spin_g, g),
                            (self.slider_b, b), (self.spin_b, b)]:
            widget.blockSignals(True)
            widget.setValue(val)
            widget.blockSignals(False)

        # Sync Hex
        self.edit_hex.blockSignals(True)
        self.edit_hex.setText(f"{r:02X}{g:02X}{b:02X}")
        self.edit_hex.blockSignals(False)

        # Sync HSV
        for widget, val in [(self.slider_h, h), (self.spin_h, h),
                            (self.slider_s, s), (self.spin_s, s),
                            (self.slider_v, v), (self.spin_v, v)]:
            widget.blockSignals(True)
            widget.setValue(val)
            widget.blockSignals(False)

        self._updating = False

        if emit_preview:
            self.color_preview_changed.emit(QColor(self.current_color))

    def get_color(self) -> QColor:
        return QColor(self.current_color)

    def _on_alpha_slider(self, val):
        c = QColor(self.current_color)
        c.setAlpha(val)
        self.set_color(c)

    def _on_wheel_changed(self, color):
        c = QColor(color)
        c.setAlpha(self.slider_alpha.value())
        self.set_color(c)

    def _on_palette_clicked(self, hex_code):
        c = QColor(hex_code)
        c.setAlpha(self.slider_alpha.value())
        self.set_color(c)

    def _on_rgb_changed(self):
        if self._updating:
            return
        r = self.sender().value() if isinstance(self.sender(), (QSlider, QSpinBox)) else self.spin_r.value()
        # Tomar valores de spinboxes
        r = self.spin_r.value() if self.sender() in (self.slider_r, self.spin_r) else self.spin_r.value()
        if self.sender() == self.slider_r:
            r = self.slider_r.value()
        g = self.slider_g.value() if self.sender() == self.slider_g else self.spin_g.value()
        b = self.slider_b.value() if self.sender() == self.slider_b else self.spin_b.value()

        c = QColor(r, g, b, self.slider_alpha.value())
        self.set_color(c)

    def _on_hex_edited(self, text):
        if len(text) == 6:
            try:
                r = int(text[0:2], 16)
                g = int(text[2:4], 16)
                b = int(text[4:6], 16)
                c = QColor(r, g, b, self.slider_alpha.value())
                self.set_color(c)
            except ValueError:
                pass

    def _on_hsv_changed(self):
        if self._updating:
            return
        h = self.slider_h.value() if self.sender() == self.slider_h else self.spin_h.value()
        s = self.slider_s.value() if self.sender() == self.slider_s else self.spin_s.value()
        v = self.slider_v.value() if self.sender() == self.slider_v else self.spin_v.value()

        c = QColor.fromHsv(h, s, v, self.slider_alpha.value())
        self.set_color(c)

    # Sincronización de Custom Slots

    def actualizar_custom_slots_ui(self):
        self.custom_colors = cargar_custom_colors()
        for idx, btn in enumerate(self.botones_custom):
            if idx < len(self.custom_colors):
                btn.set_color(self.custom_colors[idx])

    def _on_custom_slot_interacted(self, index, button, is_shift, is_ctrl):
        color_existente = self.custom_colors[index] if index < len(self.custom_colors) else None

        if is_ctrl:
            self.custom_colors[index] = None
            guardar_custom_colors(self.custom_colors)
            notificar_cambio_custom_slots()
            return

        if color_existente is None or is_shift:
            color_a_guardar = QColor(self.current_color)
            self.custom_colors[index] = color_a_guardar
            guardar_custom_colors(self.custom_colors)
            notificar_cambio_custom_slots()
        else:
            self.set_color(QColor(color_existente))

    # Cierre y Aceptar / Cancelar

    def _on_accept(self):
        desregistrar_listener_custom(self)
        self.accept()

    def _on_cancel(self):
        desregistrar_listener_custom(self)
        self.color_preview_changed.emit(QColor(self.initial_color))
        self.reject()

    def closeEvent(self, event):
        desregistrar_listener_custom(self)
        super().closeEvent(event)
