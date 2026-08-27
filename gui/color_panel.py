import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGridLayout, QLabel, QSpinBox, QSlider, QLineEdit
)
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QConicalGradient, QIcon
from PyQt6.QtCore import Qt, QPointF, QRectF, QSize, pyqtSignal
from core.i18n import t


class ColorButton(QPushButton):
    """Botón de color genérico para paleta fija con fondo cuadriculado de transparencia."""
    left_clicked = pyqtSignal()
    right_clicked = pyqtSignal()

    def __init__(self, hex_color="#000000", parent=None):
        super().__init__(parent)
        self.color = QColor(hex_color)
        self.setFixedSize(16, 16)

    def set_color(self, color):
        self.color = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        w, h = self.width(), self.height()

        # 1. Fondo cuadriculado de transparencia (ajedrez 4x4px)
        sq = 4
        c1 = QColor(255, 255, 255)
        c2 = QColor(200, 200, 200)
        for y in range(0, h, sq):
            for x in range(0, w, sq):
                c = c1 if ((x // sq) + (y // sq)) % 2 == 0 else c2
                painter.fillRect(x, y, sq, sq, c)

        # 2. Color con su Alfa real
        if self.color and self.color.isValid():
            painter.fillRect(0, 0, w, h, self.color)

        # 3. Borde sutil
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(0, 0, w - 1, h - 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.left_clicked.emit()
        elif event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit()
        super().mousePressEvent(event)


class CustomSlotButton(QPushButton):
    """Botón de slot inteligente con soporte de transparencia cuadriculada y eliminación con Ctrl+Clic."""
    slot_interacted = pyqtSignal(int, Qt.MouseButton, bool, bool)

    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.color = None
        self.setFixedSize(16, 16)

    def set_color(self, color):
        self.color = QColor(color) if (color is not None and QColor(color).isValid()) else None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        w, h = self.width(), self.height()

        if self.color is not None and self.color.isValid():
            # 1. Fondo cuadriculado de transparencia (4x4px ajedrez)
            sq = 4
            c1 = QColor(255, 255, 255)
            c2 = QColor(200, 200, 200)
            for y in range(0, h, sq):
                for x in range(0, w, sq):
                    c = c1 if ((x // sq) + (y // sq)) % 2 == 0 else c2
                    painter.fillRect(x, y, sq, sq, c)

            # 2. Color con canal Alfa real
            painter.fillRect(0, 0, w, h, self.color)

            # 3. Borde visible
            painter.setPen(QPen(QColor(160, 160, 160), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(0, 0, w - 1, h - 1)
        else:
            # Slot vacío: fondo según tema con borde continuo o punteado
            from core.theme import ThemeManager
            tm = ThemeManager()
            if tm.resolver_nombre_tema(tm.current_theme) == "Claro":
                painter.fillRect(0, 0, w, h, QColor(225, 225, 225))
                pen = QPen(QColor(120, 120, 120), 1, Qt.PenStyle.SolidLine)
            else:
                painter.fillRect(0, 0, w, h, QColor(35, 35, 35))
                pen = QPen(QColor(100, 100, 100), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(0, 0, w - 1, h - 1)

    def mousePressEvent(self, event):
        is_shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        is_ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        self.slot_interacted.emit(self.index, event.button(), is_shift, is_ctrl)
        super().mousePressEvent(event)


class ColorMuestraWidget(QWidget):
    """Muestras de color Primario y Secundario superpuestas con fondo de ajedrez."""
    primario_clicked = pyqtSignal()
    secundario_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(42, 30)
        self.color_primario = QColor(0, 0, 0, 255)
        self.color_secundario = QColor(255, 255, 255, 255)
        self.modo = "primario"

    def set_colores(self, pri, sec, modo):
        self.color_primario = QColor(pri)
        self.color_secundario = QColor(sec)
        self.modo = modo
        self.update()

    def _draw_swatch(self, painter, rect, color, is_active):
        x, y, w, h = int(rect.x()), int(rect.y()), int(rect.width()), int(rect.height())

        # Fondo cuadriculado de transparencia
        sq = 4
        c1 = QColor(255, 255, 255)
        c2 = QColor(200, 200, 200)
        for cy in range(y, y + h, sq):
            for cx in range(x, x + w, sq):
                cw = min(sq, x + w - cx)
                ch = min(sq, y + h - cy)
                c = c1 if (((cx - x) // sq) + ((cy - y) // sq)) % 2 == 0 else c2
                painter.fillRect(cx, cy, cw, ch, c)

        # Color con alfa
        painter.fillRect(x, y, w, h, color)

        # Borde
        if is_active:
            painter.setPen(QPen(QColor(255, 255, 255), 2))
        else:
            painter.setPen(QPen(QColor(40, 40, 40), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(x, y, w - 1, h - 1)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # Secundario atrás
        rect_sec = QRectF(14, 6, 22, 22)
        self._draw_swatch(painter, rect_sec, self.color_secundario, is_active=(self.modo == "secundario"))

        # Primario adelante
        rect_pri = QRectF(2, 0, 22, 22)
        self._draw_swatch(painter, rect_pri, self.color_primario, is_active=(self.modo == "primario"))

    def mousePressEvent(self, event):
        pos = event.position()
        rect_pri = QRectF(2, 0, 22, 22)
        if rect_pri.contains(pos):
            self.primario_clicked.emit()
        else:
            self.secundario_clicked.emit()


class ColorWheel(QWidget):
    """Círculo de color (HSV) compacto de 58x58px."""
    colorChanged = pyqtSignal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(58, 58)
        self.hue = 0
        self.sat = 255
        self.val = 255

    def set_color(self, color):
        qcol = QColor(color)
        if not qcol.isValid():
            return
        h, s, v, _ = qcol.getHsv()
        if h >= 0:
            self.hue = h
        self.sat = s
        self.val = v
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        radius = self.width() / 2.0
        center = QPointF(radius, radius)

        gradient = QConicalGradient(center, 0.0)
        for i in range(360):
            gradient.setColorAt(i / 360.0, QColor.fromHsv(i, 255, 255))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius, radius)

        angle_rad = self.hue * (math.pi / 180.0)
        r_indicator = (self.sat / 255.0) * (radius - 3)

        ix = radius + r_indicator * math.cos(angle_rad)
        iy = radius - r_indicator * math.sin(angle_rad)

        painter.setPen(QPen(Qt.GlobalColor.white, 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(ix, iy), 2.5, 2.5)

    def mousePressEvent(self, event):
        self.update_color_from_pos(event.position().toPoint())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.update_color_from_pos(event.position().toPoint())

    def update_color_from_pos(self, pos):
        radius = self.width() / 2.0
        dx = pos.x() - radius
        dy = pos.y() - radius
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > radius:
            dist = radius

        angle = math.degrees(math.atan2(-dy, dx)) % 360
        self.hue = int(angle)
        self.sat = int((dist / radius) * 255)

        color = QColor.fromHsv(self.hue, self.sat, self.val)
        self.colorChanged.emit(color)
        self.update()


class ColorPanelWidget(QWidget):
    """Panel flotante con muestras cuadriculadas y slots de guardado perfectos."""
    color_primario_cambiado = pyqtSignal(QColor)
    color_secundario_cambiado = pyqtSignal(QColor)

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window

        self.color_primario = QColor(0, 0, 0, 255)
        self.color_secundario = QColor(255, 255, 255, 255)
        self.modo_color = "primario"

        self.custom_colors = [None] * 21

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.setStyleSheet("ColorPanelWidget { background-color: #2D2D2D; }")
        self.setAutoFillBackground(True)

        # 1. Muestras Superpuestas + Swap
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(6)
        top_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.muestra_container = ColorMuestraWidget()
        self.muestra_container.primario_clicked.connect(lambda: self.set_modo("primario"))
        self.muestra_container.secundario_clicked.connect(lambda: self.set_modo("secundario"))

        btn_swap = QPushButton()
        btn_swap.setIcon(QIcon("gui/iconos/switch.png"))
        btn_swap.setIconSize(QSize(14, 14))
        btn_swap.setFixedSize(20, 20)
        btn_swap.setStyleSheet("padding: 0;")
        btn_swap.setToolTip(t("Intercambiar colores"))
        btn_swap.clicked.connect(self.intercambiar_colores)

        top_layout.addWidget(self.muestra_container)
        top_layout.addWidget(btn_swap)
        layout.addLayout(top_layout)

        # 2. Slider de Alpha
        alpha_layout = QVBoxLayout()
        alpha_layout.setSpacing(1)
        alpha_layout.setContentsMargins(0, 2, 0, 2)
        alpha_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_alpha = QLabel(t("Alfa:"))
        self.lbl_alpha.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.lbl_alpha.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.slider_alpha = QSlider(Qt.Orientation.Horizontal)
        self.slider_alpha.setRange(0, 255)
        self.slider_alpha.setValue(255)
        self.slider_alpha.setFixedHeight(14)
        self.slider_alpha.setFixedWidth(90)
        self.slider_alpha.valueChanged.connect(self.on_alpha_slider_changed)

        alpha_layout.addWidget(self.lbl_alpha)
        alpha_layout.addWidget(self.slider_alpha)
        layout.addLayout(alpha_layout)

        # 3. Cuadrícula de Colores Predeterminados (7 por fila, 1px de separación exacta)
        grid_paleta = QGridLayout()
        grid_paleta.setSpacing(1)
        grid_paleta.setContentsMargins(0, 0, 0, 0)
        grid_paleta.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.paleta_fija = [
            "#000000", "#333333", "#555555", "#888888", "#AAAAAA", "#CCCCCC", "#FFFFFF",  # Fila 1 (Acromáticos)
            "#4A0000", "#800000", "#CC0000", "#FF0000", "#FF4D4D", "#FF8080", "#FFB3B3",  # Fila 2 (Rojos)
            "#662200", "#804000", "#CC6600", "#FF7F00", "#FFA040", "#FFC080", "#FFE0C0",  # Fila 3 (Naranjas)
            "#2A1B17", "#3E2723", "#5D4037", "#795548", "#8D6E63", "#BCAAA4", "#D7CCC8",  # Fila 4 (Marrones)
            "#4D4D00", "#808000", "#CCCC00", "#FFFF00", "#FFFF55", "#FFFF80", "#FFFFC0",  # Fila 5 (Amarillos)
            "#004D00", "#008000", "#00CC00", "#00FF00", "#55FF55", "#80FF80", "#C0FFC0",  # Fila 6 (Verdes)
            "#004D4D", "#008080", "#00CCCC", "#00FFFF", "#55FFFF", "#80FFFF", "#C0FFFF",  # Fila 7 (Cianes)
            "#00004D", "#000080", "#0000CC", "#0000FF", "#4D4DFF", "#8080FF", "#B3B3FF",  # Fila 8 (Azules)
            "#2A004D", "#4B0082", "#800080", "#A000FF", "#C055FF", "#D8B4FE", "#F0E0FF",  # Fila 9 (Púrpuras)
            "#4D0026", "#800040", "#CC0066", "#FF007F", "#FF55A3", "#FFB3D9", "#FFE6F2"   # Fila 10 (Rosas)
        ]

        def _make_color_handler(hex_val, mode):
            return lambda *args: self.seleccionar_hex_directo(hex_val, modo=mode)

        self.botones_paleta = []
        for idx, hex_color in enumerate(self.paleta_fija):
            row = idx // 7
            col = idx % 7
            btn_color = ColorButton(hex_color)
            btn_color.left_clicked.connect(_make_color_handler(hex_color, "primario"))
            btn_color.right_clicked.connect(_make_color_handler(hex_color, "secundario"))

            grid_paleta.addWidget(btn_color, row, col)
            self.botones_paleta.append(btn_color)

        layout.addLayout(grid_paleta)

        # 4. Slots de Usuario (Guardados - 7 por fila)
        self.lbl_custom = QLabel("Guardadas:")
        self.lbl_custom.setStyleSheet("font-size: 11px; font-weight: normal; margin-top: 2px;")
        layout.addWidget(self.lbl_custom, alignment=Qt.AlignmentFlag.AlignCenter)

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
            btn_slot.slot_interacted.connect(self.on_slot_custom_interacted)

            grid_custom.addWidget(btn_slot, row, col)
            self.botones_custom.append(btn_slot)

        layout.addLayout(grid_custom)

        self.setLayout(layout)
        self.setFixedWidth(118)
        self.actualizar_ui()

    def set_modo(self, modo):
        self.modo_color = modo
        self.actualizar_ui()

    def intercambiar_colores(self):
        self.color_primario, self.color_secundario = self.color_secundario, self.color_primario
        self.notificar_cambio()
        self.actualizar_ui()

    def color_activo(self):
        return self.color_primario if self.modo_color == "primario" else self.color_secundario

    def set_color_activo(self, color):
        if self.modo_color == "primario":
            self.color_primario = QColor(color)
        else:
            self.color_secundario = QColor(color)
        self.notificar_cambio()
        self.actualizar_ui()

    def on_alpha_slider_changed(self, val):
        c = self.color_activo()
        c.setAlpha(val)
        self.set_color_activo(c)

    def seleccionar_hex_directo(self, hex_code, modo="primario"):
        color = QColor(hex_code)
        color.setAlpha(self.slider_alpha.value())
        self.modo_color = modo
        self.set_color_activo(color)

    def on_slot_custom_interacted(self, index, button, is_shift, is_ctrl):
        color_existente = self.custom_colors[index]

        if is_ctrl:
            self.custom_colors[index] = None
            self.botones_custom[index].set_color(None)
            return

        if color_existente is None or is_shift:
            color_a_guardar = QColor(self.color_primario if button == Qt.MouseButton.LeftButton else self.color_secundario)
            self.custom_colors[index] = color_a_guardar
            self.botones_custom[index].set_color(color_a_guardar)
        else:
            modo = "primario" if button == Qt.MouseButton.LeftButton else "secundario"
            self.modo_color = modo
            self.set_color_activo(QColor(color_existente))

    def notificar_cambio(self):
        if self.main_window and hasattr(self.main_window, 'canvas'):
            self.main_window.canvas.color_primario = self.color_primario
            self.main_window.canvas.color_secundario = self.color_secundario

        self.color_primario_cambiado.emit(self.color_primario)
        self.color_secundario_cambiado.emit(self.color_secundario)

    def actualizar_ui(self):
        self.muestra_container.set_colores(self.color_primario, self.color_secundario, self.modo_color)
        c = self.color_activo()
        self.slider_alpha.blockSignals(True)
        self.slider_alpha.setValue(c.alpha())
        self.slider_alpha.blockSignals(False)

    def retraducir_panel(self):
        if hasattr(self, 'lbl_alpha'):
            self.lbl_alpha.setText(t("Alfa:"))
        if hasattr(self, 'lbl_custom'):
            self.lbl_custom.setText(t("Guardadas:"))
        if hasattr(self, 'botones_custom'):
            tip = t("Slot vacío: Clic para Guardar | Slot lleno: Clic para Usar (Shift+Clic Reemplazar, Ctrl+Clic Eliminar)")
            for btn_slot in self.botones_custom:
                btn_slot.setToolTip(tip)
