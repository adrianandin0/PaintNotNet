from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QSlider, QToolButton
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class PanelPropiedades(QGroupBox):
    def __init__(self, grosor_ini, opacidad_ini, suavizado_ini, forma_ini, 
                 cb_grosor, cb_opacidad, cb_suavizado, cb_forma):
        super().__init__("PROPIEDADES")
        self.cb_grosor = cb_grosor
        self.cb_opacidad = cb_opacidad
        self.cb_suavizado = cb_suavizado
        self.cb_forma = cb_forma

        layout = QVBoxLayout(self)
        # Margen superior en 12px para separar del título
        layout.setContentsMargins(4, 12, 4, 6)
        layout.setSpacing(4)

        # 1. Grosor (Hasta 9999)
        layout_grosor = QHBoxLayout()
        layout_grosor.setSpacing(4)
        lbl_grosor = QLabel("Grosor:")
        self.spin_grosor = QSpinBox()
        self.spin_grosor.setRange(1, 9999)  # Grosor indefinido/ampliado
        self.spin_grosor.setValue(grosor_ini)
        self.spin_grosor.valueChanged.connect(self.cb_grosor)
        layout_grosor.addWidget(lbl_grosor)
        layout_grosor.addWidget(self.spin_grosor)
        layout_grosor.addStretch()

        # 2. Transparencia
        layout_transp = QVBoxLayout()
        layout_transp.setSpacing(1)
        transp_pct = int((1.0 - (opacidad_ini / 255.0)) * 100)
        
        self.lbl_transp_val = QLabel(f"Transparencia: {transp_pct}%")
        self.slider_transp = QSlider(Qt.Orientation.Horizontal)
        self.slider_transp.setRange(0, 100)
        self.slider_transp.setValue(transp_pct)
        self.slider_transp.valueChanged.connect(self.al_cambiar_transparencia)
        
        layout_transp.addWidget(self.lbl_transp_val)
        layout_transp.addWidget(self.slider_transp)

        # 3. Forma del Pincel
        layout_forma = QHBoxLayout()
        layout_forma.setSpacing(2)
        self.lbl_forma = QLabel("Forma:")
        
        fuente_ascii = QFont("DejaVu Sans", 10, QFont.Weight.Bold)
        
        self.btn_forma_circulo = QToolButton()
        self.btn_forma_circulo.setText("●")
        self.btn_forma_circulo.setFont(fuente_ascii)
        self.btn_forma_circulo.setCheckable(True)
        self.btn_forma_circulo.setFixedSize(26, 20)
        self.btn_forma_circulo.setToolTip("Punta Circular")
        self.btn_forma_circulo.clicked.connect(lambda: self.al_cambiar_forma("Circular"))

        self.btn_forma_cuadrado = QToolButton()
        self.btn_forma_cuadrado.setText("■")
        self.btn_forma_cuadrado.setFont(fuente_ascii)
        self.btn_forma_cuadrado.setCheckable(True)
        self.btn_forma_cuadrado.setFixedSize(26, 20)
        self.btn_forma_cuadrado.setToolTip("Punta Cuadrada")
        self.btn_forma_cuadrado.clicked.connect(lambda: self.al_cambiar_forma("Cuadrado"))

        if forma_ini == "Circular":
            self.btn_forma_circulo.setChecked(True)
        else:
            self.btn_forma_cuadrado.setChecked(True)

        layout_forma.addWidget(self.lbl_forma)
        layout_forma.addWidget(self.btn_forma_circulo)
        layout_forma.addWidget(self.btn_forma_cuadrado)
        layout_forma.addStretch()

        # 4. Suavizado
        layout_suavizado = QVBoxLayout()
        layout_suavizado.setSpacing(1)
        self.lbl_suavizado_val = QLabel(f"Suavizado: {suavizado_ini}%")
        self.slider_suavizado = QSlider(Qt.Orientation.Horizontal)
        self.slider_suavizado.setRange(0, 100)
        self.slider_suavizado.setValue(suavizado_ini)
        self.slider_suavizado.valueChanged.connect(self.al_cambiar_suavizado)
        layout_suavizado.addWidget(self.lbl_suavizado_val)
        layout_suavizado.addWidget(self.slider_suavizado)

        layout.addLayout(layout_grosor)
        layout.addLayout(layout_transp)
        layout.addLayout(layout_forma)
        layout.addLayout(layout_suavizado)

        self.actualizar_estado_pincel(False)

    def al_cambiar_transparencia(self, valor_pct):
        self.lbl_transp_val.setText(f"Transparencia: {valor_pct}%")
        opacidad_alfa = int((1.0 - (valor_pct / 100.0)) * 255)
        self.cb_opacidad(opacidad_alfa)

    def al_cambiar_suavizado(self, valor):
        self.lbl_suavizado_val.setText(f"Suavizado: {valor}%")
        self.cb_suavizado(valor)

    def al_cambiar_forma(self, forma):
        self.btn_forma_circulo.setChecked(forma == "Circular")
        self.btn_forma_cuadrado.setChecked(forma == "Cuadrado")
        self.cb_forma(forma)

    def actualizar_estado_pincel(self, es_pincel):
        self.lbl_forma.setEnabled(es_pincel)
        self.btn_forma_circulo.setEnabled(es_pincel)
        self.btn_forma_cuadrado.setEnabled(es_pincel)
        self.lbl_suavizado_val.setEnabled(es_pincel)
        self.slider_suavizado.setEnabled(es_pincel)
