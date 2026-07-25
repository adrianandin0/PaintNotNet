import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QFontComboBox, QCheckBox, QGroupBox, QSizePolicy
)
from PyQt6.QtGui import QFont, QPainter, QBrush, QPen, QColor
from PyQt6.QtCore import Qt, QPointF, pyqtSignal


class LightDirectionWidget(QWidget):
    """Control circular 2D compacto para la dirección de la luz."""
    lightVectorChanged = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(32, 32)
        self.light_x = 0.0
        self.light_y = 0.0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        radius = (self.width() - 4) / 2.0
        center = QPointF(self.width() / 2.0, self.height() / 2.0)

        # Fondo circular
        painter.setBrush(QBrush(QColor("#2B2B2B")))
        painter.setPen(QPen(QColor("#555555"), 1))
        painter.drawEllipse(center, radius, radius)

        # Guías de centro
        painter.setPen(QPen(QColor("#444444"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(int(center.x()), 2, int(center.x()), self.height() - 2)
        painter.drawLine(2, int(center.y()), self.width() - 2, int(center.y()))

        # Posición de la bolita
        ix = center.x() + (self.light_x * radius)
        iy = center.y() + (self.light_y * radius)

        # Bolita indicadora
        painter.setBrush(QBrush(QColor("#00AAFF")))
        painter.setPen(QPen(Qt.GlobalColor.white, 1))
        painter.drawEllipse(QPointF(ix, iy), 3.0, 3.0)

    def mousePressEvent(self, event):
        self.update_vector_from_pos(event.position().toPoint())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.update_vector_from_pos(event.position().toPoint())

    def update_vector_from_pos(self, pos):
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        radius = (self.width() - 4) / 2.0

        dx = (pos.x() - center_x) / radius
        dy = (pos.y() - center_y) / radius

        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 1.0:
            dx /= dist
            dy /= dist

        self.light_x = dx
        self.light_y = dy

        self.lightVectorChanged.emit(self.light_x, self.light_y)
        self.update()


class TextPanelWidget(QWidget):
    """Panel de configuración de texto con diseño optimizado."""
    text_config_changed = pyqtSignal(dict)

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window

        lbl_style = "color: #FFFFFF; font-size: 9px; font-weight: normal;"

        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- 1. Fuente y Tamaño ---
        lbl_fuente = QLabel("FUENTE:")
        lbl_fuente.setStyleSheet(lbl_style)
        layout.addWidget(lbl_fuente)

        self.font_combo = QFontComboBox()
        self.font_combo.setFixedHeight(18)
        self.font_combo.setStyleSheet("font-size: 9px; color: #FFFFFF;")
        self.font_combo.currentFontChanged.connect(self.emitir_configuracion)
        layout.addWidget(self.font_combo)

        tam_layout = QHBoxLayout()
        tam_layout.setSpacing(2)
        lbl_tam = QLabel("TAMAÑO:")
        lbl_tam.setStyleSheet(lbl_style)

        self.spin_size = QSpinBox()
        self.spin_size.setRange(1, 9999)
        self.spin_size.setValue(24)
        self.spin_size.setFixedHeight(18)
        self.spin_size.setStyleSheet("font-size: 9px; color: #FFFFFF;")
        self.spin_size.valueChanged.connect(self.emitir_configuracion)

        tam_layout.addWidget(lbl_tam)
        tam_layout.addWidget(self.spin_size)
        layout.addLayout(tam_layout)

        # --- 2. Estilos (B, I, U, S) ---
        styles_layout = QHBoxLayout()
        styles_layout.setSpacing(2)
        styles_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_bold = QPushButton("B")
        self.btn_bold.setCheckable(True)
        self.btn_bold.setFixedSize(22, 18)
        self.btn_bold.setStyleSheet("font-weight: bold; font-size: 10px; color: #FFFFFF;")
        self.btn_bold.toggled.connect(self.emitir_configuracion)

        self.btn_italic = QPushButton("I")
        self.btn_italic.setCheckable(True)
        self.btn_italic.setFixedSize(22, 18)
        self.btn_italic.setStyleSheet("font-style: italic; font-size: 10px; color: #FFFFFF;")
        self.btn_italic.toggled.connect(self.emitir_configuracion)

        self.btn_underline = QPushButton("U")
        self.btn_underline.setCheckable(True)
        self.btn_underline.setFixedSize(22, 18)
        self.btn_underline.setStyleSheet("text-decoration: underline; font-size: 10px; color: #FFFFFF;")
        self.btn_underline.toggled.connect(self.emitir_configuracion)

        self.btn_strike = QPushButton("S")
        self.btn_strike.setCheckable(True)
        self.btn_strike.setFixedSize(22, 18)
        self.btn_strike.setStyleSheet("text-decoration: line-through; font-size: 10px; color: #FFFFFF;")
        self.btn_strike.toggled.connect(self.emitir_configuracion)

        styles_layout.addWidget(self.btn_bold)
        styles_layout.addWidget(self.btn_italic)
        styles_layout.addWidget(self.btn_underline)
        styles_layout.addWidget(self.btn_strike)
        layout.addLayout(styles_layout)

        # Style estandarizado de GroupBox con Título Blanco
        group_style = (
            "QGroupBox { font-size: 9px; color: #FFFFFF; font-weight: normal; margin-top: 6px; padding-top: 2px; border: 1px solid #444; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; color: #FFFFFF; background-color: transparent; }"
        )

        # --- 3. BORDE ---
        group_borde = QGroupBox("BORDE")
        group_borde.setStyleSheet(group_style)
        borde_layout = QVBoxLayout()
        borde_layout.setContentsMargins(2, 2, 2, 2)
        borde_layout.setSpacing(2)

        self.chk_borde = QCheckBox("ACTIVAR")
        self.chk_borde.setStyleSheet(lbl_style)
        self.chk_borde.toggled.connect(self.emitir_configuracion)
        borde_layout.addWidget(self.chk_borde)

        b_size_layout = QHBoxLayout()
        b_size_layout.setSpacing(2)
        lbl_b_size = QLabel("GROSOR:")
        lbl_b_size.setStyleSheet(lbl_style)
        self.spin_borde_size = QSpinBox()
        self.spin_borde_size.setRange(1, 100)
        self.spin_borde_size.setValue(3)
        self.spin_borde_size.setFixedHeight(18)
        self.spin_borde_size.setStyleSheet("font-size: 9px; color: #FFFFFF;")
        self.spin_borde_size.valueChanged.connect(self.emitir_configuracion)
        b_size_layout.addWidget(lbl_b_size)
        b_size_layout.addWidget(self.spin_borde_size)
        borde_layout.addLayout(b_size_layout)

        group_borde.setLayout(borde_layout)
        layout.addWidget(group_borde)

        # --- 4. SOMBRA (Fila Superior: ACTIVAR + LUZ CIRCULAR / Fila Inferior: DISTANCIA) ---
        group_sombra = QGroupBox("SOMBRA")
        group_sombra.setStyleSheet(group_style)
        sombra_layout = QVBoxLayout()
        sombra_layout.setContentsMargins(2, 2, 2, 2)
        sombra_layout.setSpacing(2)

        # FILA 1: ACTIVAR a la izquierda + LUZ + Círculo a la derecha (Exacto como marcaste en violeta)
        top_sombra_row = QHBoxLayout()
        top_sombra_row.setSpacing(2)

        self.chk_sombra = QCheckBox("ACTIVAR")
        self.chk_sombra.setStyleSheet(lbl_style)
        self.chk_sombra.toggled.connect(self.emitir_configuracion)

        lbl_luz = QLabel("")
        lbl_luz.setStyleSheet(lbl_style)
        self.light_widget = LightDirectionWidget()
        self.light_widget.lightVectorChanged.connect(self.emitir_configuracion)

        top_sombra_row.addWidget(self.chk_sombra)
        top_sombra_row.addStretch() # Empuja LUZ y el círculo a la derecha
        top_sombra_row.addWidget(lbl_luz)
        top_sombra_row.addWidget(self.light_widget)
        sombra_layout.addLayout(top_sombra_row)

        # FILA 2: DISTANCIA abajo
        s_dist_layout = QHBoxLayout()
        s_dist_layout.setSpacing(2)
        lbl_dist = QLabel("DISTANCIA:")
        lbl_dist.setStyleSheet(lbl_style)
        self.spin_sombra_dist = QSpinBox()
        self.spin_sombra_dist.setRange(1, 200)
        self.spin_sombra_dist.setValue(5)
        self.spin_sombra_dist.setFixedHeight(18)
        self.spin_sombra_dist.setStyleSheet("font-size: 9px; color: #FFFFFF;")
        self.spin_sombra_dist.valueChanged.connect(self.emitir_configuracion)
        s_dist_layout.addWidget(lbl_dist)
        s_dist_layout.addWidget(self.spin_sombra_dist)
        sombra_layout.addLayout(s_dist_layout)

        group_sombra.setLayout(sombra_layout)
        layout.addWidget(group_sombra)

        self.setLayout(layout)
        self.setFixedWidth(140)
        self.setFixedHeight(220) # Se recortó aún más el alto
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def get_config(self):
        return {
            "font_family": self.font_combo.currentFont().family(),
            "font_size": self.spin_size.value(),
            "bold": self.btn_bold.isChecked(),
            "italic": self.btn_italic.isChecked(),
            "underline": self.btn_underline.isChecked(),
            "strike": self.btn_strike.isChecked(),
            "borde_enabled": self.chk_borde.isChecked(),
            "borde_size": self.spin_borde_size.value(),
            "sombra_enabled": self.chk_sombra.isChecked(),
            "sombra_offset_x": self.light_widget.light_x * self.spin_sombra_dist.value(),
            "sombra_offset_y": self.light_widget.light_y * self.spin_sombra_dist.value(),
        }

    def emitir_configuracion(self):
        config = self.get_config()
        self.text_config_changed.emit(config)
        if self.main_window and hasattr(self.main_window, 'canvas'):
            self.main_window.canvas.actualizar_config_texto(config)
            self.main_window.canvas.update()  # <--- FORZAR REDIBUJADO EN TIEMPO REAL
