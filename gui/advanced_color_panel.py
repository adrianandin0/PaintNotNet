import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGridLayout, QLabel, QSpinBox, QLineEdit, QFrame, QScrollArea, QAbstractSpinBox
)
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QLinearGradient, QIcon
from PyQt6.QtCore import Qt, QPointF, QRectF, QSize, pyqtSignal

from gui.color_panel import ColorButton, CustomSlotButton, ColorMuestraWidget, ColorWheel
from core.i18n import t


class GradientSliderWidget(QWidget):
    """Control deslizante horizontal con fondo degradado y tirador triangular."""
    valueChanged = pyqtSignal(int)

    def __init__(self, min_val=0, max_val=255, slider_type="red", parent=None):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.slider_type = slider_type
        self._value = min_val
        self.current_color = QColor(0, 0, 0)
        self.setFixedHeight(17)
        self.setMinimumWidth(70)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def value(self):
        return self._value

    def set_value(self, val):
        val = max(self.min_val, min(self.max_val, int(val)))
        if self._value != val:
            self._value = val
            self.update()

    def set_current_color(self, color):
        self.current_color = QColor(color)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._update_val_from_pos(event.position().x())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._update_val_from_pos(event.position().x())

    def _update_val_from_pos(self, x):
        margin = 3
        w = max(1, self.width() - (margin * 2))
        ratio = max(0.0, min(1.0, (x - margin) / float(w)))
        val = int(round(self.min_val + ratio * (self.max_val - self.min_val)))
        if self._value != val:
            self._value = val
            self.valueChanged.emit(self._value)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        bar_h = 11
        margin = 3

        bar_rect = QRectF(margin, 1, w - (margin * 2), bar_h)
        gradient = QLinearGradient(bar_rect.left(), 0, bar_rect.right(), 0)

        h_val, s_val, v_val, _ = self.current_color.getHsv()
        if h_val < 0:
            h_val = 0

        if self.slider_type == "red":
            gradient.setColorAt(0.0, QColor(0, 0, 0))
            gradient.setColorAt(1.0, QColor(255, 0, 0))
        elif self.slider_type == "green":
            gradient.setColorAt(0.0, QColor(0, 0, 0))
            gradient.setColorAt(1.0, QColor(0, 255, 0))
        elif self.slider_type == "blue":
            gradient.setColorAt(0.0, QColor(0, 0, 0))
            gradient.setColorAt(1.0, QColor(0, 0, 255))
        elif self.slider_type == "hue":
            for i in range(7):
                pos = i / 6.0
                hue_angle = int(i * 60) % 360
                gradient.setColorAt(pos, QColor.fromHsv(hue_angle, 255, 255))
        elif self.slider_type == "sat":
            gradient.setColorAt(0.0, QColor(0, 0, 0))
            gradient.setColorAt(1.0, QColor.fromHsv(h_val, 255, 255))
        elif self.slider_type == "val":
            gradient.setColorAt(0.0, QColor(0, 0, 0))
            gradient.setColorAt(1.0, QColor(255, 255, 255))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.drawRect(bar_rect)

        # Tirador triangular inferior (blanco con centro oscuro)
        ratio = (self._value - self.min_val) / float(self.max_val - self.min_val or 1)
        ix = bar_rect.left() + ratio * bar_rect.width()
        iy = bar_rect.bottom() + 1

        tri_h = 4
        tri_w = 4
        painter.setPen(QPen(QColor(240, 240, 240), 1))
        painter.setBrush(QBrush(QColor(20, 20, 20)))

        polygon = [
            QPointF(ix, iy),
            QPointF(ix - tri_w, iy + tri_h),
            QPointF(ix + tri_w, iy + tri_h)
        ]
        painter.drawPolygon(polygon)


class AdvancedColorPanelWidget(QWidget):
    """Panel de Colores Avanzados compacto (sliders RGB/MSV, Hex y rueda de color)."""
    color_primario_cambiado = pyqtSignal(QColor)
    color_secundario_cambiado = pyqtSignal(QColor)

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window

        self.color_primario = QColor(0, 0, 0, 255)
        self.color_secundario = QColor(255, 255, 255, 255)
        self.modo_color = "primario"
        self._updating = False

        lbl_style = "font-size: 11px; font-weight: normal; color: #CCCCCC;"
        input_style = """
            QSpinBox, QLineEdit {
                background-color: #262626;
                color: #EDEDED;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 0px 2px;
                font-size: 11px;
            }
            QSpinBox:focus, QLineEdit:focus {
                border: 1px solid #007ACC;
            }
        """

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 1. Muestras Superpuestas + Botón Swap + Rueda de Color Centrada
        row_top = QHBoxLayout()
        row_top.setContentsMargins(0, 0, 0, 0)
        row_top.setSpacing(6)

        self.muestras = ColorMuestraWidget()
        self.muestras.setFixedSize(42, 30)
        self.muestras.primario_clicked.connect(lambda: self.set_modo_color("primario"))
        self.muestras.secundario_clicked.connect(lambda: self.set_modo_color("secundario"))
        row_top.addWidget(self.muestras)

        btn_swap = QPushButton()
        btn_swap.setIcon(QIcon("gui/iconos/switch.png"))
        btn_swap.setIconSize(QSize(14, 14))
        btn_swap.setToolTip(t("Intercambiar Color Primario / Secundario (X)"))
        btn_swap.setFixedSize(20, 20)
        btn_swap.setStyleSheet("padding: 0;")
        btn_swap.clicked.connect(self.intercambiar_colores)
        row_top.addWidget(btn_swap)

        row_top.addStretch(1)

        self.color_wheel = ColorWheel()
        self.color_wheel.setFixedSize(50, 50)
        self.color_wheel.colorChanged.connect(self._on_wheel_color_changed)
        row_top.addWidget(self.color_wheel)

        row_top.addStretch(1)

        layout.addLayout(row_top)

        # 2. Grid Unificado Compacto: RGB, Hex, MSV
        grid = QGridLayout()
        grid.setContentsMargins(0, 2, 0, 0)
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(3)

        # R
        lbl_r = QLabel("R:")
        lbl_r.setStyleSheet(lbl_style)
        grid.addWidget(lbl_r, 0, 0)
        self.slider_r = GradientSliderWidget(0, 255, "red")
        self.spin_r = QSpinBox()
        self.spin_r.setRange(0, 255)
        self.spin_r.setFixedWidth(38)
        self.spin_r.setFixedHeight(17)
        self.spin_r.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_r.setStyleSheet(input_style)
        grid.addWidget(self.slider_r, 0, 1)
        grid.addWidget(self.spin_r, 0, 2)

        # G (Green)
        lbl_g = QLabel("G:")
        lbl_g.setStyleSheet(lbl_style)
        grid.addWidget(lbl_g, 1, 0)
        self.slider_g = GradientSliderWidget(0, 255, "green")
        self.spin_g = QSpinBox()
        self.spin_g.setRange(0, 255)
        self.spin_g.setFixedWidth(38)
        self.spin_g.setFixedHeight(17)
        self.spin_g.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_g.setStyleSheet(input_style)
        grid.addWidget(self.slider_g, 1, 1)
        grid.addWidget(self.spin_g, 1, 2)

        # B (Blue)
        lbl_b = QLabel("B:")
        lbl_b.setStyleSheet(lbl_style)
        grid.addWidget(lbl_b, 2, 0)
        self.slider_b = GradientSliderWidget(0, 255, "blue")
        self.spin_b = QSpinBox()
        self.spin_b.setRange(0, 255)
        self.spin_b.setFixedWidth(38)
        self.spin_b.setFixedHeight(17)
        self.spin_b.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_b.setStyleSheet(input_style)
        grid.addWidget(self.slider_b, 2, 1)
        grid.addWidget(self.spin_b, 2, 2)

        # Hex.:
        lbl_hex = QLabel("Hex.:")
        lbl_hex.setStyleSheet(lbl_style)
        grid.addWidget(lbl_hex, 3, 0)
        self.txt_hex = QLineEdit("000000")
        self.txt_hex.setMaxLength(7)
        self.txt_hex.setFixedHeight(17)
        self.txt_hex.setStyleSheet(input_style)
        grid.addWidget(self.txt_hex, 3, 1)

        # M (Matiz / Hue)
        lbl_h = QLabel("M:")
        lbl_h.setStyleSheet(lbl_style)
        grid.addWidget(lbl_h, 4, 0)
        self.slider_h = GradientSliderWidget(0, 360, "hue")
        self.spin_h = QSpinBox()
        self.spin_h.setRange(0, 360)
        self.spin_h.setFixedWidth(38)
        self.spin_h.setFixedHeight(17)
        self.spin_h.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_h.setStyleSheet(input_style)
        grid.addWidget(self.slider_h, 4, 1)
        grid.addWidget(self.spin_h, 4, 2)

        # S (Saturación)
        lbl_s = QLabel("S:")
        lbl_s.setStyleSheet(lbl_style)
        grid.addWidget(lbl_s, 5, 0)
        self.slider_s = GradientSliderWidget(0, 100, "sat")
        self.spin_s = QSpinBox()
        self.spin_s.setRange(0, 100)
        self.spin_s.setFixedWidth(38)
        self.spin_s.setFixedHeight(17)
        self.spin_s.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_s.setStyleSheet(input_style)
        grid.addWidget(self.slider_s, 5, 1)
        grid.addWidget(self.spin_s, 5, 2)

        # V (Valor / Brillo)
        lbl_v = QLabel("V:")
        lbl_v.setStyleSheet(lbl_style)
        grid.addWidget(lbl_v, 6, 0)
        self.slider_v = GradientSliderWidget(0, 100, "val")
        self.spin_v = QSpinBox()
        self.spin_v.setRange(0, 100)
        self.spin_v.setFixedWidth(38)
        self.spin_v.setFixedHeight(17)
        self.spin_v.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_v.setStyleSheet(input_style)
        grid.addWidget(self.slider_v, 6, 1)
        grid.addWidget(self.spin_v, 6, 2)

        layout.addLayout(grid)
        layout.addStretch(1)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Conectar señales RGB
        self.slider_r.valueChanged.connect(lambda val: self._on_rgb_slider_changed("r", val))
        self.spin_r.valueChanged.connect(lambda val: self._on_rgb_spin_changed("r", val))

        self.slider_g.valueChanged.connect(lambda val: self._on_rgb_slider_changed("g", val))
        self.spin_g.valueChanged.connect(lambda val: self._on_rgb_spin_changed("g", val))

        self.slider_b.valueChanged.connect(lambda val: self._on_rgb_slider_changed("b", val))
        self.spin_b.valueChanged.connect(lambda val: self._on_rgb_spin_changed("b", val))

        self.txt_hex.editingFinished.connect(self._on_hex_edited)

        # Conectar señales MSV (HSV)
        self.slider_h.valueChanged.connect(lambda val: self._on_hsv_slider_changed("h", val))
        self.spin_h.valueChanged.connect(lambda val: self._on_hsv_spin_changed("h", val))

        self.slider_s.valueChanged.connect(lambda val: self._on_hsv_slider_changed("s", val))
        self.spin_s.valueChanged.connect(lambda val: self._on_hsv_spin_changed("s", val))

        self.slider_v.valueChanged.connect(lambda val: self._on_hsv_slider_changed("v", val))
        self.spin_v.valueChanged.connect(lambda val: self._on_hsv_spin_changed("v", val))

        self.actualizar_estilo_tema()

    def actualizar_estilo_tema(self):
        from core.theme import ThemeManager
        tm = ThemeManager()
        is_dark = (tm.resolver_nombre_tema(tm.current_theme) == "Oscuro")

        p_bg = "#383838" if is_dark else "#DFDFDF"
        txt_col = "#EDEDED" if is_dark else "#222222"
        self.setStyleSheet(f"AdvancedColorPanelWidget, QWidget {{ background-color: {p_bg}; color: {txt_col}; }}")

        self._actualizar_interfaz_desde_color(self.color_primario)

    def set_modo_color(self, modo):
        self.modo_color = modo
        col = self.color_primario if modo == "primario" else self.color_secundario
        self._actualizar_interfaz_desde_color(col)

    def intercambiar_colores(self):
        self.color_primario, self.color_secundario = self.color_secundario, self.color_primario
        self.muestras.set_colores(self.color_primario, self.color_secundario, self.modo_color)
        self.color_primario_cambiado.emit(self.color_primario)
        self.color_secundario_cambiado.emit(self.color_secundario)
        col = self.color_primario if self.modo_color == "primario" else self.color_secundario
        self._actualizar_interfaz_desde_color(col)

    def set_color_activo(self, color):
        qcol = QColor(color)
        if not qcol.isValid():
            return

        if self.modo_color == "primario":
            self.color_primario = qcol
            self.color_primario_cambiado.emit(qcol)
        else:
            self.color_secundario = qcol
            self.color_secundario_cambiado.emit(qcol)

        self.muestras.set_colores(self.color_primario, self.color_secundario, self.modo_color)
        self._actualizar_interfaz_desde_color(qcol)

    def set_color_secundario(self, color):
        qcol = QColor(color)
        if not qcol.isValid():
            return
        self.color_secundario = qcol
        self.color_secundario_cambiado.emit(qcol)
        self.muestras.set_colores(self.color_primario, self.color_secundario, self.modo_color)

    def _actualizar_interfaz_desde_color(self, color):
        if self._updating:
            return
        self._updating = True

        r, g, b = color.red(), color.green(), color.blue()
        h, s, v, _ = color.getHsv()
        if h < 0:
            h = 0

        s_pct = int(round((s / 255.0) * 100))
        v_pct = int(round((v / 255.0) * 100))

        self.slider_r.set_current_color(color)
        self.slider_r.set_value(r)
        self.spin_r.setValue(r)

        self.slider_g.set_current_color(color)
        self.slider_g.set_value(g)
        self.spin_g.setValue(g)

        self.slider_b.set_current_color(color)
        self.slider_b.set_value(b)
        self.spin_b.setValue(b)

        hex_str = color.name(QColor.NameFormat.HexRgb).upper().replace("#", "")
        self.txt_hex.setText(hex_str)

        self.slider_h.set_current_color(color)
        self.slider_h.set_value(h)
        self.spin_h.setValue(h)

        self.slider_s.set_current_color(color)
        self.slider_s.set_value(s_pct)
        self.spin_s.setValue(s_pct)

        self.slider_v.set_current_color(color)
        self.slider_v.set_value(v_pct)
        self.spin_v.setValue(v_pct)

        if hasattr(self, 'color_wheel') and self.color_wheel:
            self.color_wheel.set_color(color)

        self.muestras.set_colores(self.color_primario, self.color_secundario, self.modo_color)
        self._updating = False

    def _on_wheel_color_changed(self, color):
        self.set_color_activo(color)

    def _on_rgb_slider_changed(self, channel, val):
        if self._updating:
            return
        r = val if channel == "r" else self.spin_r.value()
        g = val if channel == "g" else self.spin_g.value()
        b = val if channel == "b" else self.spin_b.value()
        self.set_color_activo(QColor(r, g, b, 255))

    def _on_rgb_spin_changed(self, channel, val):
        if self._updating:
            return
        r = val if channel == "r" else self.spin_r.value()
        g = val if channel == "g" else self.spin_g.value()
        b = val if channel == "b" else self.spin_b.value()
        self.set_color_activo(QColor(r, g, b, 255))

    def _on_hsv_slider_changed(self, channel, val):
        if self._updating:
            return
        h = val if channel == "h" else self.spin_h.value()
        s_pct = val if channel == "s" else self.spin_s.value()
        v_pct = val if channel == "v" else self.spin_v.value()

        s = int(round((s_pct / 100.0) * 255))
        v = int(round((v_pct / 100.0) * 255))

        qcol = QColor.fromHsv(h, s, v, 255)
        self.set_color_activo(qcol)

    def _on_hsv_spin_changed(self, channel, val):
        if self._updating:
            return
        h = val if channel == "h" else self.spin_h.value()
        s_pct = val if channel == "s" else self.spin_s.value()
        v_pct = val if channel == "v" else self.spin_v.value()

        s = int(round((s_pct / 100.0) * 255))
        v = int(round((v_pct / 100.0) * 255))

        qcol = QColor.fromHsv(h, s, v, 255)
        self.set_color_activo(qcol)

    def _on_hex_edited(self):
        if self._updating:
            return
        text = self.txt_hex.text().strip()
        if not text.startswith("#"):
            text = "#" + text
        qcol = QColor(text)
        if qcol.isValid():
            self.set_color_activo(qcol)
