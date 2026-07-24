from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QSlider
from PyQt6.QtCore import Qt

class PanelPropiedades(QGroupBox):
    def __init__(self, grosor_inicial, opacidad_inicial, callback_grosor, callback_opacidad):
        super().__init__("PROPIEDADES")
        self.callback_grosor = callback_grosor
        self.callback_opacidad = callback_opacidad

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 4)
        layout.setSpacing(2)

        # Grosor
        layout_grosor = QHBoxLayout()
        lbl_grosor = QLabel("Grosor:")
        self.spin_grosor = QSpinBox()
        self.spin_grosor.setRange(1, 100)
        self.spin_grosor.setValue(grosor_inicial)
        self.spin_grosor.valueChanged.connect(self.callback_grosor)
        layout_grosor.addWidget(lbl_grosor)
        layout_grosor.addWidget(self.spin_grosor)

        # Opacidad
        layout_transp = QVBoxLayout()
        self.lbl_transp_val = QLabel(f"Opacidad: {int(opacidad_inicial / 255 * 100)}%")
        self.slider_transp = QSlider(Qt.Orientation.Horizontal)
        self.slider_transp.setRange(0, 100)
        self.slider_transp.setValue(int(opacidad_inicial / 255 * 100))
        self.slider_transp.valueChanged.connect(self.al_cambiar_opacidad)

        layout_transp.addWidget(self.lbl_transp_val)
        layout_transp.addWidget(self.slider_transp)

        layout.addLayout(layout_grosor)
        layout.addLayout(layout_transp)

    def al_cambiar_opacidad(self, valor_porcentaje):
        self.lbl_transp_val.setText(f"Opacidad: {valor_porcentaje}%")
        self.callback_opacidad(valor_porcentaje)
