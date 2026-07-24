from PyQt6.QtWidgets import QGroupBox, QGridLayout, QToolButton
from PyQt6.QtGui import QFont

class PanelHerramientas(QGroupBox):
    def __init__(self, callback_cambio_herramienta):
        super().__init__("HERRAMIENTAS")
        self.callback_cambio_herramienta = callback_cambio_herramienta
        
        grid = QGridLayout(self)
        grid.setContentsMargins(2, 6, 2, 2)
        grid.setSpacing(2)

        herramientas_info = [
            ("lapiz", "LAPIZ", "Lápiz"),
            ("goma", "GOMA", "Goma"),
            ("balde", "BALDE", "Balde de Pintura"),
            ("texto", "TEXTO", "Texto"),
            ("seleccion", "SELECCION", "Selección Rectangular")
        ]

        fuente_btn_texto = QFont("Sans Serif", 7, QFont.Weight.Bold)
        self.botones = {}

        for i, (nombre, texto_label, tooltip) in enumerate(herramientas_info):
            btn = QToolButton()
            btn.setText(texto_label)
            btn.setFont(fuente_btn_texto)
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setFixedSize(72, 22)
            btn.clicked.connect(lambda checked, n=nombre: self.seleccionar(n))
            grid.addWidget(btn, i // 2, i % 2)
            self.botones[nombre] = btn

        self.botones["lapiz"].setChecked(True)

    def seleccionar(self, nombre):
        for n, btn in self.botones.items():
            btn.setChecked(n == nombre)
        self.callback_cambio_herramienta(nombre)
