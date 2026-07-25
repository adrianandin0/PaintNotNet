import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGridLayout, QLabel, QSpinBox, QSlider, QLineEdit
)
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QConicalGradient
from PyQt6.QtCore import Qt, QPointF, pyqtSignal


class ColorButton(QPushButton):
    """Botón de color genérico para paleta fija (Clic Izq: Primario / Clic Der: Secundario)."""
    left_clicked = pyqtSignal()
    right_clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.left_clicked.emit()
        elif event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit()
        super().mousePressEvent(event)


class CustomSlotButton(QPushButton):
    """Botón de slot inteligente: guarda si está vacío o carga si ya tiene color."""
    slot_interacted = pyqtSignal(int, Qt.MouseButton, bool)

    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index

    def mousePressEvent(self, event):
        is_shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        self.slot_interacted.emit(self.index, event.button(), is_shift)
        super().mousePressEvent(event)


class ColorWheel(QWidget):
    """Círculo de color (HSV) compacto de 58x58px."""
    colorChanged = pyqtSignal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(58, 58)
        self.hue = 0
        self.sat = 255
        self.val = 255

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
    """Panel flotante con slots de guardado intuitivos (Guardar vacíos / Usar guardados / Reemplazar con Shift)."""
    color_primario_cambiado = pyqtSignal(QColor)
    color_secundario_cambiado = pyqtSignal(QColor)

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window

        self.color_primario = QColor(0, 0, 0, 255)
        self.color_secundario = QColor(255, 255, 255, 255)
        self.modo_color = "primario"

        self.custom_colors = [None] * 12

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # 1. Muestras Superpuestas + Swap
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(6)
        top_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.muestra_container = QWidget()
        self.muestra_container.setFixedSize(40, 28)

        self.btn_secundario = QPushButton(self.muestra_container)
        self.btn_secundario.setGeometry(12, 6, 22, 22)
        self.btn_secundario.setToolTip("Color Secundario")
        self.btn_secundario.clicked.connect(lambda: self.set_modo("secundario"))

        self.btn_primario = QPushButton(self.muestra_container)
        self.btn_primario.setGeometry(0, 0, 22, 22)
        self.btn_primario.setToolTip("Color Primario")
        self.btn_primario.clicked.connect(lambda: self.set_modo("primario"))

        btn_swap = QPushButton("⇆")
        btn_swap.setFixedSize(20, 20)
        btn_swap.setStyleSheet("font-size: 11px; padding: 0;")
        btn_swap.setToolTip("Intercambiar colores")
        btn_swap.clicked.connect(self.intercambiar_colores)

        top_layout.addWidget(self.muestra_container)
        top_layout.addWidget(btn_swap)
        layout.addLayout(top_layout)

        # 2. Círculo de Color
        self.wheel = ColorWheel()
        self.wheel.colorChanged.connect(self.on_wheel_color_changed)
        layout.addWidget(self.wheel, alignment=Qt.AlignmentFlag.AlignCenter)

        # 3. Slider de Alpha
        alpha_layout = QHBoxLayout()
        alpha_layout.setSpacing(3)
        alpha_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_a = QLabel("A:")
        lbl_a.setStyleSheet("font-size: 9px; font-weight: bold;")

        self.slider_alpha = QSlider(Qt.Orientation.Horizontal)
        self.slider_alpha.setRange(0, 255)
        self.slider_alpha.setValue(255)
        self.slider_alpha.setFixedHeight(14)
        self.slider_alpha.setFixedWidth(54)
        self.slider_alpha.valueChanged.connect(self.on_alpha_slider_changed)

        alpha_layout.addWidget(lbl_a)
        alpha_layout.addWidget(self.slider_alpha)
        layout.addLayout(alpha_layout)

        # 4. Inputs RGB Numéricos
        rgb_grid = QGridLayout()
        rgb_grid.setSpacing(3)
        rgb_grid.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.spins_rgb = {}
        canales = ["R", "G", "B"]
        for idx, canal in enumerate(canales):
            r = idx // 2
            c = (idx % 2) * 2

            lbl = QLabel(f"{canal}:")
            lbl.setStyleSheet("font-size: 9px;")
            spin = QSpinBox()
            spin.setRange(0, 255)
            spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
            spin.setFixedSize(22, 16)
            spin.setStyleSheet("font-size: 9px; padding: 0;")
            spin.valueChanged.connect(self.on_rgb_spin_changed)

            rgb_grid.addWidget(lbl, r, c)
            rgb_grid.addWidget(spin, r, c + 1)
            self.spins_rgb[canal] = spin

        layout.addLayout(rgb_grid)

        # 5. Entrada Hexadecimal (#HEX)
        hex_layout = QHBoxLayout()
        hex_layout.setSpacing(2)
        hex_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_hex = QLabel("#:")
        lbl_hex.setStyleSheet("font-size: 9px; font-weight: bold;")

        self.input_hex = QLineEdit("#000000")
        self.input_hex.setMaxLength(7)
        self.input_hex.setFixedHeight(18)
        self.input_hex.setFixedWidth(52)
        self.input_hex.setStyleSheet("font-size: 9px; padding: 0;")
        self.input_hex.editingFinished.connect(self.on_hex_input_changed)

        hex_layout.addWidget(lbl_hex)
        hex_layout.addWidget(self.input_hex)
        layout.addLayout(hex_layout)

        # 6. Cuadrícula de Colores Predeterminados
        grid_paleta = QGridLayout()
        grid_paleta.setSpacing(1)
        grid_paleta.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.paleta_fija = [
            "#000000", "#404040", "#808080", "#C0C0C0",
            "#FFFFFF", "#800000", "#FF0000", "#804000",
            "#FF8000", "#808000", "#FFFF00", "#408000",
            "#00FF00", "#008000", "#008040", "#00FF80",
            "#008080", "#00FFFF", "#004080", "#0080FF",
            "#0000FF", "#000080", "#400080", "#8000FF",
            "#800080", "#FF00FF", "#800040", "#FF0080",
            "#400000", "#804040", "#FF8080", "#FFC0C0",
            "#FFE0C0", "#806040", "#C08040", "#FFC080",
            "#808040", "#FFFF80", "#80FF80", "#80FFFF"
        ]

        for idx, hex_color in enumerate(self.paleta_fija):
            row = idx // 4
            col = idx % 4
            btn_color = ColorButton()
            btn_color.setFixedSize(16, 16)
            btn_color.setStyleSheet(f"background-color: {hex_color}; border: none;")

            btn_color.left_clicked.connect(lambda h=hex_color: self.seleccionar_hex_directo(h, modo="primario"))
            btn_color.right_clicked.connect(lambda h=hex_color: self.seleccionar_hex_directo(h, modo="secundario"))

            grid_paleta.addWidget(btn_color, row, col)

        layout.addLayout(grid_paleta)

        # 7. Slots de Usuario
        lbl_custom = QLabel("Guardados:")
        lbl_custom.setStyleSheet("font-size: 9px; font-weight: bold; margin-top: 2px;")
        layout.addWidget(lbl_custom, alignment=Qt.AlignmentFlag.AlignCenter)

        grid_custom = QGridLayout()
        grid_custom.setSpacing(1)
        grid_custom.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.botones_custom = []
        for idx in range(12):
            row = idx // 4
            col = idx % 4
            btn_slot = CustomSlotButton(idx)
            btn_slot.setFixedSize(16, 16)
            btn_slot.setToolTip("Slot vacío: Clic para Guardar | Slot lleno: Clic para Usar (Shift+Clic para Reemplazar)")
            btn_slot.setStyleSheet("background-color: transparent; border: 1px dashed #666;")
            btn_slot.slot_interacted.connect(self.on_slot_custom_interacted)

            grid_custom.addWidget(btn_slot, row, col)
            self.botones_custom.append(btn_slot)

        layout.addLayout(grid_custom)

        self.setLayout(layout)
        self.setFixedWidth(82)
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
            self.color_primario = color
        else:
            self.color_secundario = color
        self.notificar_cambio()
        self.actualizar_ui()

    def on_wheel_color_changed(self, color):
        c_actual = self.color_activo()
        color.setAlpha(c_actual.alpha())
        self.set_color_activo(color)

    def on_alpha_slider_changed(self, val):
        c = self.color_activo()
        c.setAlpha(val)
        self.set_color_activo(c)

    def on_rgb_spin_changed(self):
        r = self.spins_rgb["R"].value()
        g = self.spins_rgb["G"].value()
        b = self.spins_rgb["B"].value()
        a = self.slider_alpha.value()
        self.set_color_activo(QColor(r, g, b, a))

    def on_hex_input_changed(self):
        texto = self.input_hex.text().strip()
        if not texto.startswith("#"):
            texto = "#" + texto
        color = QColor(texto)
        if color.isValid():
            color.setAlpha(self.slider_alpha.value())
            self.set_color_activo(color)

    def seleccionar_hex_directo(self, hex_code, modo="primario"):
        color = QColor(hex_code)
        color.setAlpha(self.slider_alpha.value())
        self.modo_color = modo
        self.set_color_activo(color)

    def on_slot_custom_interacted(self, index, button, is_shift):
        color_existente = self.custom_colors[index]

        # Si está VACÍO o se mantiene apretado SHIFT: GUARDAR
        if color_existente is None or is_shift:
            color_a_guardar = QColor(self.color_primario if button == Qt.MouseButton.LeftButton else self.color_secundario)
            self.custom_colors[index] = color_a_guardar

            c = color_a_guardar
            rgba_str = f"rgba({c.red()}, {c.green()}, {c.blue()}, {c.alpha()/255})"
            self.botones_custom[index].setStyleSheet(
                f"background-color: {rgba_str}; border: 1px solid white;"
            )
        # Si YA TIENE UN COLOR y es clic simple: CARGAR
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
        style_pri = f"background-color: rgba({self.color_primario.red()}, {self.color_primario.green()}, {self.color_primario.blue()}, {self.color_primario.alpha()/255}); border: {'1.5px solid white' if self.modo_color == 'primario' else '1px solid #333'};"
        style_sec = f"background-color: rgba({self.color_secundario.red()}, {self.color_secundario.green()}, {self.color_secundario.blue()}, {self.color_secundario.alpha()/255}); border: {'1.5px solid white' if self.modo_color == 'secundario' else '1px solid #333'};"

        self.btn_primario.setStyleSheet(style_pri)
        self.btn_secundario.setStyleSheet(style_sec)

        c = self.color_activo()

        for spin in self.spins_rgb.values():
            spin.blockSignals(True)
        self.slider_alpha.blockSignals(True)
        self.input_hex.blockSignals(True)

        self.spins_rgb["R"].setValue(c.red())
        self.spins_rgb["G"].setValue(c.green())
        self.spins_rgb["B"].setValue(c.blue())
        self.slider_alpha.setValue(c.alpha())
        self.input_hex.setText(c.name().upper())

        for spin in self.spins_rgb.values():
            spin.blockSignals(False)
        self.slider_alpha.blockSignals(False)
        self.input_hex.blockSignals(False)
