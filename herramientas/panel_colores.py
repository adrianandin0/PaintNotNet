from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QColorDialog, QGridLayout, QLabel, QFrame
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QSize, pyqtSignal


class PanelColores(QWidget):
    """Panel flotante de colores adaptado a 66px de ancho."""
    color_primario_cambiado = pyqtSignal(QColor)
    color_secundario_cambiado = pyqtSignal(QColor)

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window

        self.color_primario = QColor(0, 0, 0)         # Negro por defecto
        self.color_secundario = QColor(255, 255, 255) # Blanco por defecto
        self.modo_color = "primario"                   # "primario" o "secundario"

        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        # --- 1. Muestra de Colores Activos (Primario / Secundario) ---
        muestra_layout = QHBoxLayout()
        muestra_layout.setSpacing(2)

        self.btn_primario = QPushButton()
        self.btn_primario.setFixedSize(26, 26)
        self.btn_primario.setToolTip("Color Primario")
        self.btn_primario.clicked.connect(lambda: self.set_modo("primario"))

        self.btn_secundario = QPushButton()
        self.btn_secundario.setFixedSize(26, 26)
        self.btn_secundario.setToolTip("Color Secundario")
        self.btn_secundario.clicked.connect(lambda: self.set_modo("secundario"))

        muestra_layout.addWidget(self.btn_primario)
        muestra_layout.addWidget(self.btn_secundario)
        layout.addLayout(muestra_layout)

        # --- 2. Botón Abrir Rueda / Selector Avanzado ---
        btn_mas_colores = QPushButton("Color...")
        btn_mas_colores.setFixedHeight(22)
        btn_mas_colores.setStyleSheet("font-size: 10px; padding: 0;")
        btn_mas_colores.setToolTip("Abrir selector de color avanzado")
        btn_mas_colores.clicked.connect(self.abrir_selector_dialogo)
        layout.addWidget(btn_mas_colores)

        # --- 3. Paleta Rápida (4 Columnas x 10 Filas, Cuadritos de 10x10 px) ---
        grid_paleta = QGridLayout()
        grid_paleta.setSpacing(1)

        # 40 colores ordenados para la paleta compacta
        paleta_colores = [
            # Fila 1 a 5: Escala de Grises y Primarios
            "#000000", "#404040", "#808080", "#C0C0C0",
            "#FFFFFF", "#800000", "#FF0000", "#804000",
            "#FF8000", "#808000", "#FFFF00", "#408000",
            "#00FF00", "#008000", "#008040", "#00FF80",
            "#008080", "#00FFFF", "#004080", "#0080FF",
            # Fila 6 a 10: Azul, Violeta, Rosa y Tonos Piel/Cálidos
            "#0000FF", "#000080", "#400080", "#8000FF",
            "#800080", "#FF00FF", "#800040", "#FF0080",
            "#400000", "#804040", "#FF8080", "#FFC0C0",
            "#FFE0C0", "#806040", "#C08040", "#FFC080",
            "#808040", "#FFFF80", "#80FF80", "#80FFFF"
        ]

        for idx, hex_color in enumerate(paleta_colores):
            row = idx // 4
            col = idx % 4
            btn_color = QPushButton()
            btn_color.setFixedSize(10, 10)
            btn_color.setStyleSheet(f"background-color: {hex_color}; border: none;")
            btn_color.clicked.connect(lambda checked, c=hex_color: self.seleccionar_hex_paleta(c))
            grid_paleta.addWidget(btn_color, row, col)

        layout.addLayout(grid_paleta)

        # --- 4. Información RGB / HEX Numérica Compacta ---
        self.lbl_info = QLabel("R: 0 G: 0\nB: 0\n#000000")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_info.setStyleSheet("font-size: 9px; color: #aaa; margin-top: 2px;")
        layout.addWidget(self.lbl_info)

        self.setLayout(layout)

        # Mismo ancho exacto que el panel de herramientas (66px)
        self.setFixedWidth(66)
        self.actualizar_vista_muestra()

    def set_modo(self, modo):
        self.modo_color = modo
        self.actualizar_vista_muestra()

    def seleccionar_hex_paleta(self, hex_code):
        color = QColor(hex_code)
        self.aplicar_color(color)

    def abrir_selector_dialogo(self):
        color_actual = self.color_primario if self.modo_color == "primario" else self.color_secundario
        nuevo_color = QColorDialog.getColor(color_actual, self, "Seleccionar Color")
        if nuevo_color.isValid():
            self.aplicar_color(nuevo_color)

    def aplicar_color(self, color):
        if self.modo_color == "primario":
            self.color_primario = color
            if self.main_window and hasattr(self.main_window, 'canvas'):
                self.main_window.canvas.color_primario = color
            self.color_primario_cambiado.emit(color)
        else:
            self.color_secundario = color
            if self.main_window and hasattr(self.main_window, 'canvas'):
                self.main_window.canvas.color_secundario = color
            self.color_secundario_cambiado.emit(color)

        self.actualizar_vista_muestra()

    def actualizar_vista_muestra(self):
        # Borde blanco para indicar cuál está activo
        style_pri = f"background-color: {self.color_primario.name()}; border: {'2px solid white' if self.modo_color == 'primario' else '1px solid #444'};"
        style_sec = f"background-color: {self.color_secundario.name()}; border: {'2px solid white' if self.modo_color == 'secundario' else '1px solid #444'};"

        self.btn_primario.setStyleSheet(style_pri)
        self.btn_secundario.setStyleSheet(style_sec)

        # Actualiza valores RGB / HEX del color activo
        c = self.color_primario if self.modo_color == "primario" else self.color_secundario
        self.lbl_info.setText(f"R:{c.red()} G:{c.green()}\nB:{c.blue()}\n{c.name().upper()}")
