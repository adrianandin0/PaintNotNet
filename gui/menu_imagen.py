from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QSpinBox, QCheckBox, QRadioButton, QPushButton,
                             QButtonGroup)
from PyQt6.QtCore import Qt


class DialogoTamanoBase(QDialog):
    def __init__(self, titulo, ancho_actual, alto_actual, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setFixedWidth(280)
        self.ancho_orig = ancho_actual
        self.alto_orig = alto_actual
        self.ratio = ancho_actual / float(alto_actual) if alto_actual > 0 else 1.0

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Modo de Entrada (Píxeles vs Porcentaje)
        layout_modo = QHBoxLayout()
        self.rad_px = QRadioButton("Píxeles")
        self.rad_porcentaje = QRadioButton("Porcentaje (%)")
        self.rad_px.setChecked(True)

        self.grupo_modo = QButtonGroup(self)
        self.grupo_modo.addButton(self.rad_px)
        self.grupo_modo.addButton(self.rad_porcentaje)

        layout_modo.addWidget(self.rad_px)
        layout_modo.addWidget(self.rad_porcentaje)
        layout.addLayout(layout_modo)

        # Controles Ancho / Alto
        layout_ancho = QHBoxLayout()
        layout_ancho.addWidget(QLabel("Ancho:"))
        self.spin_ancho = QSpinBox()
        self.spin_ancho.setRange(1, 99999)
        self.spin_ancho.setValue(ancho_actual)
        layout_ancho.addWidget(self.spin_ancho)

        layout_alto = QHBoxLayout()
        layout_alto.addWidget(QLabel("Alto:"))
        self.spin_alto = QSpinBox()
        self.spin_alto.setRange(1, 99999)
        self.spin_alto.setValue(alto_actual)
        layout_alto.addWidget(self.spin_alto)

        layout.addLayout(layout_ancho)
        layout.addLayout(layout_alto)

        # Mantener proporciones
        self.chk_proporcional = QCheckBox("Mantener proporciones")
        self.chk_proporcional.setChecked(True)
        layout.addWidget(self.chk_proporcional)

        # Conectar Eventos
        self.rad_px.toggled.connect(self.cambiar_modo)
        self.spin_ancho.valueChanged.connect(self.al_cambiar_ancho)
        self.spin_alto.valueChanged.connect(self.al_cambiar_alto)

        # Botones Confirmar / Cancelar
        layout_btns = QHBoxLayout()
        btn_ok = QPushButton("Aceptar")
        btn_cancel = QPushButton("Cancelar")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        layout_btns.addWidget(btn_ok)
        layout_btns.addWidget(btn_cancel)
        layout.addLayout(layout_btns)

        self._bloqueo_signals = False

    def cambiar_modo(self):
        self._bloqueo_signals = True
        if self.rad_porcentaje.isChecked():
            self.spin_ancho.setValue(100)
            self.spin_alto.setValue(100)
        else:
            self.spin_ancho.setValue(self.ancho_orig)
            self.spin_alto.setValue(self.alto_orig)
        self._bloqueo_signals = False

    def al_cambiar_ancho(self, valor):
        if self._bloqueo_signals or not self.chk_proporcional.isChecked():
            return
        self._bloqueo_signals = True
        if self.rad_px.isChecked():
            nuevo_alto = int(valor / self.ratio) if self.ratio > 0 else valor
            self.spin_alto.setValue(max(1, nuevo_alto))
        else:
            self.spin_alto.setValue(valor)
        self._bloqueo_signals = False

    def al_cambiar_alto(self, valor):
        if self._bloqueo_signals or not self.chk_proporcional.isChecked():
            return
        self._bloqueo_signals = True
        if self.rad_px.isChecked():
            nuevo_ancho = int(valor * self.ratio)
            self.spin_ancho.setValue(max(1, nuevo_ancho))
        else:
            self.spin_ancho.setValue(valor)
        self._bloqueo_signals = False

    def obtener_dimensiones_finales(self):
        val_w = self.spin_ancho.value()
        val_h = self.spin_alto.value()

        if self.rad_porcentaje.isChecked():
            ancho_f = max(1, int(self.ancho_orig * (val_w / 100.0)))
            alto_f = max(1, int(self.alto_orig * (val_h / 100.0)))
            return ancho_f, alto_f
        return val_w, val_h


class MenuImagen:
    def __init__(self, ventana_principal):
        self.ventana = ventana_principal

    def crear_menu(self, menu_bar):
        menu_img = menu_bar.addMenu("Imagen")

        accion_tam_lienzo = menu_img.addAction("Tamaño del lienzo...")
        accion_tam_lienzo.triggered.connect(self.cambiar_tamano_lienzo)

        accion_tam_img = menu_img.addAction("Tamaño de la imagen...")
        accion_tam_img.triggered.connect(self.cambiar_tamano_imagen)

        menu_img.addSeparator()

        accion_v_horiz = menu_img.addAction("Voltear horizontalmente")
        accion_v_horiz.triggered.connect(lambda: self.ventana.lienzo.voltear_contenido(horizontal=True))

        accion_v_vert = menu_img.addAction("Voltear verticalmente")
        accion_v_vert.triggered.connect(lambda: self.ventana.lienzo.voltear_contenido(horizontal=False))

        menu_img.addSeparator()

        accion_rot_90_der = menu_img.addAction("Rotar 90° a la derecha")
        accion_rot_90_der.triggered.connect(lambda: self.ventana.lienzo.rotar_contenido(grados=90))

        accion_rot_90_izq = menu_img.addAction("Rotar 90° a la izquierda")
        accion_rot_90_izq.triggered.connect(lambda: self.ventana.lienzo.rotar_contenido(grados=-90))

    def cambiar_tamano_lienzo(self):
        lienzo = self.ventana.lienzo
        dialogo = DialogoTamanoBase("Tamaño del Lienzo", lienzo.width(), lienzo.height(), self.ventana)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            nuevo_w, nuevo_h = dialogo.obtener_dimensiones_finales()
            lienzo.redimensionar_lienzo(nuevo_w, nuevo_h)

    def cambiar_tamano_imagen(self):
        lienzo = self.ventana.lienzo
        dialogo = DialogoTamanoBase("Tamaño de la Imagen", lienzo.width(), lienzo.height(), self.ventana)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            nuevo_w, nuevo_h = dialogo.obtener_dimensiones_finales()
            lienzo.escalar_imagen(nuevo_w, nuevo_h)
