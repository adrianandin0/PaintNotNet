from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QSpinBox, QCheckBox, QRadioButton, QPushButton,
                             QButtonGroup, QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt


class AnclajeWidget(QGroupBox):
    """Matriz 3x3 de botones para elegir hacia dónde se expande/achica el lienzo."""
    def __init__(self, parent=None):
        super().__init__("", parent)
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #444444;
                border-radius: 4px;
                margin-top: 4px;
                padding-top: 4px;
            }
        """)

        layout = QGridLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(6, 6, 6, 6)

        self.button_group = QButtonGroup(self)

        # Mapeo de posiciones (Fila, Columna) -> (ID, Ícono/Flecha)
        self.anchors = {
            (0, 0): ("top-left", "↖"),
            (0, 1): ("top-center", "↑"),
            (0, 2): ("top-right", "↗"),
            (1, 0): ("middle-left", "←"),
            (1, 1): ("center", "•"),
            (1, 2): ("middle-right", "→"),
            (2, 0): ("bottom-left", "↙"),
            (2, 1): ("bottom-center", "↓"),
            (2, 2): ("bottom-right", "↘"),
        }

        self.selected_anchor = "top-left"  # Por defecto arriba-izquierda

        btn_style = """
            QPushButton {
                background-color: #3b3b3b;
                color: #ffffff;
                border: 1px solid #555555;
                font-weight: bold;
                font-size: 13px;
                border-radius: 3px;
            }
            QPushButton:checked {
                background-color: #007acc;
                border: 1px solid #00aaff;
            }
            QPushButton:hover {
                background-color: #4f4f4f;
            }
        """

        for (r, c), (anchor_id, label) in self.anchors.items():
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedSize(28, 28)
            btn.setStyleSheet(btn_style)
            btn.setProperty("anchor_id", anchor_id)

            if anchor_id == self.selected_anchor:
                btn.setChecked(True)

            self.button_group.addButton(btn)
            layout.addWidget(btn, r, c)

        self.button_group.buttonClicked.connect(self._on_button_clicked)

    def _on_button_clicked(self, button):
        self.selected_anchor = button.property("anchor_id")

    def obtener_anclaje(self):
        return self.selected_anchor


class DialogoTamanoBase(QDialog):
    def __init__(self, titulo, ancho_actual, alto_actual, parent=None, incluir_anclaje=False):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setFixedWidth(290)
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

        # Anclaje (Solo si se solicita, ej: Tamaño del Lienzo)
        self.widget_anclaje = None
        if incluir_anclaje:
            self.widget_anclaje = AnclajeWidget(self)
            layout.addWidget(self.widget_anclaje, alignment=Qt.AlignmentFlag.AlignCenter)

        # Conectar Eventos
        self.rad_px.toggled.connect(self.cambiar_modo)
        self.spin_ancho.valueChanged.connect(self.al_cambiar_ancho)
        self.spin_alto.valueChanged.connect(self.al_cambiar_alto)

        # Botones Confirmar / Cancelar
        layout_btns = QHBoxLayout()
        btn_ok = QPushButton("Aceptar")
        btn_ok.setDefault(True)
        btn_ok.setAutoDefault(True)
        btn_cancel = QPushButton("Cancelar")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        layout_btns.addWidget(btn_ok)
        layout_btns.addWidget(btn_cancel)
        layout.addLayout(layout_btns)

        self._bloqueo_signals = False

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.accept()
            return
        super().keyPressEvent(event)

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

    def obtener_anclaje(self):
        if self.widget_anclaje:
            return self.widget_anclaje.obtener_anclaje()
        return "top-left"


class MenuImagen:
    def __init__(self, ventana_principal):
        self.ventana = ventana_principal

    def crear_menu(self, menu_bar):
        self.menu_bar = menu_bar
        self.retraducir_menu()

    def retraducir_menu(self):
        from core.i18n import t
        if hasattr(self, 'menu_img') and self.menu_img:
            self.menu_bar.removeAction(self.menu_img.menuAction())

        self.menu_img = self.menu_bar.addMenu(t("Imagen"))

        accion_tam_img = self.menu_img.addAction(t("Cambiar Tamaño de Imagen..."))
        accion_tam_img.triggered.connect(self.cambiar_tamano_imagen)

        accion_tam_lienzo = self.menu_img.addAction(t("Cambiar Tamaño de Lienzo..."))
        accion_tam_lienzo.triggered.connect(self.cambiar_tamano_lienzo)

        self.menu_img.addSeparator()

        accion_v_horiz = self.menu_img.addAction(t("Voltearse Horizontalmente"))
        accion_v_horiz.triggered.connect(lambda: self.ventana.lienzo.voltear_contenido(horizontal=True))

        accion_v_vert = self.menu_img.addAction(t("Voltearse Verticalmente"))
        accion_v_vert.triggered.connect(lambda: self.ventana.lienzo.voltear_contenido(horizontal=False))

        self.menu_img.addSeparator()

        accion_rot_90_der = self.menu_img.addAction(t("Rotar 90° a la Derecha"))
        accion_rot_90_der.triggered.connect(lambda: self.ventana.lienzo.rotar_contenido(grados=90))

        accion_rot_90_izq = self.menu_img.addAction(t("Rotar 90° a la Izquierda"))
        accion_rot_90_izq.triggered.connect(lambda: self.ventana.lienzo.rotar_contenido(grados=-90))

    def cambiar_tamano_lienzo(self):
        from core.i18n import t
        lienzo = self.ventana.lienzo
        dialogo = DialogoTamanoBase(t("Cambiar Tamaño de Lienzo..."), lienzo.layer_mgr.width, lienzo.layer_mgr.height, self.ventana, incluir_anclaje=True)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            nuevo_w, nuevo_h = dialogo.obtener_dimensiones_finales()
            anclaje = dialogo.obtener_anclaje()
            lienzo.redimensionar_lienzo(nuevo_w, nuevo_h, anchor=anclaje)

    def cambiar_tamano_imagen(self):
        from core.i18n import t
        lienzo = self.ventana.lienzo
        engine = lienzo.selection_engine

        if engine.has_selection():
            sel_rect = engine.active_rect
            ancho_init = max(1, int(round(sel_rect.width())))
            alto_init = max(1, int(round(sel_rect.height())))
            dialogo = DialogoTamanoBase(t("Cambiar Tamaño de Imagen..."), ancho_init, alto_init, self.ventana, incluir_anclaje=False)
            if dialogo.exec() == QDialog.DialogCode.Accepted:
                nuevo_w, nuevo_h = dialogo.obtener_dimensiones_finales()
                lienzo.escalar_seleccion(nuevo_w, nuevo_h)
        else:
            dialogo = DialogoTamanoBase(t("Cambiar Tamaño de Imagen..."), lienzo.layer_mgr.width, lienzo.layer_mgr.height, self.ventana, incluir_anclaje=False)
            if dialogo.exec() == QDialog.DialogCode.Accepted:
                nuevo_w, nuevo_h = dialogo.obtener_dimensiones_finales()
                lienzo.escalar_imagen(nuevo_w, nuevo_h)
