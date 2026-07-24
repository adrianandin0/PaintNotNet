import os
from PyQt6.QtWidgets import (QFileDialog, QMessageBox, QDialog, QVBoxLayout, 
                             QHBoxLayout, QLabel, QSpinBox, QRadioButton, 
                             QPushButton, QButtonGroup)
from PyQt6.QtCore import Qt


class DialogoNuevoArchivo(QDialog):
    """Diálogo para configurar ancho, alto y fondo del nuevo lienzo"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Lienzo")
        self.setFixedWidth(240)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 1. Ancho y Alto
        layout_ancho = QHBoxLayout()
        layout_ancho.addWidget(QLabel("Ancho (px):"))
        self.spin_ancho = QSpinBox()
        self.spin_ancho.setRange(10, 9999)
        self.spin_ancho.setValue(800)
        layout_ancho.addWidget(self.spin_ancho)

        layout_alto = QHBoxLayout()
        layout_alto.addWidget(QLabel("Alto (px):"))
        self.spin_alto = QSpinBox()
        self.spin_alto.setRange(10, 9999)
        self.spin_alto.setValue(600)
        layout_alto.addWidget(self.spin_alto)

        layout.addLayout(layout_ancho)
        layout.addLayout(layout_alto)

        # 2. Opciones de Fondo (Exclusivas)
        layout.addWidget(QLabel("Color de Fondo:"))
        self.rad_blanco = QRadioButton("Fondo Blanco")
        self.rad_transparente = QRadioButton("Fondo Transparente")
        self.rad_blanco.setChecked(True)

        self.grupo_fondo = QButtonGroup(self)
        self.grupo_fondo.addButton(self.rad_blanco)
        self.grupo_fondo.addButton(self.rad_transparente)

        layout.addWidget(self.rad_blanco)
        layout.addWidget(self.rad_transparente)

        # 3. Botones Aceptar / Cancelar
        layout_btns = QHBoxLayout()
        btn_ok = QPushButton("Crear")
        btn_cancel = QPushButton("Cancelar")

        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        layout_btns.addWidget(btn_ok)
        layout_btns.addWidget(btn_cancel)
        layout.addLayout(layout_btns)

    def obtener_configuracion(self):
        return (
            self.spin_ancho.value(),
            self.spin_alto.value(),
            self.rad_transparente.isChecked()  # True si es transparente
        )


class MenuArchivo:
    def __init__(self, ventana_principal):
        self.ventana = ventana_principal

    def crear_menu(self, menu_bar):
        menu_archivo = menu_bar.addMenu("Archivo")

        accion_nuevo = menu_archivo.addAction("Nuevo")
        accion_nuevo.setShortcut("Ctrl+N")
        accion_nuevo.triggered.connect(self.nuevo_archivo)

        accion_abrir = menu_archivo.addAction("Abrir...")
        accion_abrir.setShortcut("Ctrl+O")
        accion_abrir.triggered.connect(self.abrir_archivo)

        menu_archivo.addSeparator()

        accion_guardar = menu_archivo.addAction("Guardar")
        accion_guardar.setShortcut("Ctrl+S")
        accion_guardar.triggered.connect(self.guardar_archivo)

        accion_guardar_como = menu_archivo.addAction("Guardar como...")
        accion_guardar_como.setShortcut("Ctrl+Shift+S")
        accion_guardar_como.triggered.connect(self.guardar_como)

        menu_archivo.addSeparator()

        accion_salir = menu_archivo.addAction("Salir")
        accion_salir.setShortcut("Ctrl+Q")
        accion_salir.triggered.connect(self.salir_programa)

    def nuevo_archivo(self):
        if self.ventana.lienzo_modificado:
            if not self.confirmar_descarte_cambios():
                return

        dialogo = DialogoNuevoArchivo(self.ventana)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            ancho, alto, es_transparente = dialogo.obtener_configuracion()
            self.ventana.lienzo.crear_nuevo_lienzo(ancho, alto, es_transparente)
            self.ventana.archivo_actual = None
            self.ventana.lienzo_modificado = False
            self.ventana.actualizar_titulo_ventana()

    def abrir_archivo(self):
        if self.ventana.lienzo_modificado:
            if not self.confirmar_descarte_cambios():
                return

        ruta, _ = QFileDialog.getOpenFileName(
            self.ventana,
            "Abrir Imagen",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp);;Todos los archivos (*)"
        )
        if ruta:
            if self.ventana.lienzo.cargar_imagen(ruta):
                self.ventana.archivo_actual = ruta
                self.ventana.lienzo_modificado = False
                self.ventana.actualizar_titulo_ventana()

    def guardar_como(self):
        ruta_inicial = self.ventana.archivo_actual if self.ventana.archivo_actual else "sin_titulo.png"
        ruta, _ = QFileDialog.getSaveFileName(
            self.ventana,
            "Guardar Imagen Como",
            ruta_inicial,
            "Imagen PNG (*.png);;Imagen JPG (*.jpg *.jpeg);;Imagen BMP (*.bmp)"
        )
        if ruta:
            if self.ventana.lienzo.guardar_imagen(ruta):
                self.ventana.archivo_actual = ruta
                self.ventana.lienzo_modificado = False
                self.ventana.actualizar_titulo_ventana()
                return True
        return False

    def guardar_archivo(self):
        if not self.ventana.archivo_actual:
            return self.guardar_como()

        # Si el archivo ya existe, preguntamos si pisar, hacer copia o cancelar
        msg_box = QMessageBox(self.ventana)
        msg_box.setWindowTitle("Guardar Imagen")
        msg_box.setText("¿Desea guardar los cambios o generar una copia?")

        btn_guardar = msg_box.addButton("Guardar cambios", QMessageBox.ButtonRole.AcceptRole)
        btn_copia = msg_box.addButton("Crear copia", QMessageBox.ButtonRole.ActionRole)
        btn_cancelar = msg_box.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)

        msg_box.exec()
        btn_presionado = msg_box.clickedButton()

        if btn_presionado == btn_guardar:
            if self.ventana.lienzo.guardar_imagen(self.ventana.archivo_actual):
                self.ventana.lienzo_modificado = False
                self.ventana.actualizar_titulo_ventana()
                return True

        elif btn_presionado == btn_copia:
            ruta_copia = self.generar_nombre_copia(self.ventana.archivo_actual)
            if self.ventana.lienzo.guardar_imagen(ruta_copia):
                self.ventana.archivo_actual = ruta_copia
                self.ventana.lienzo_modificado = False
                self.ventana.actualizar_titulo_ventana()
                return True

        return False  # Cancelar no hace nada

    def generar_nombre_copia(self, ruta_original):
        directorio, nombre_archivo = os.path.split(ruta_original)
        nombre_base, extension = os.path.splitext(nombre_archivo)

        # Intento 1: "archivo copia.ext"
        candidato = os.path.join(directorio, f"{nombre_base} copia{extension}")
        if not os.path.exists(candidato):
            return candidato

        # Intentos subsiguientes: "archivo copia 2.ext", "archivo copia 3.ext"...
        contador = 2
        while True:
            candidato = os.path.join(directorio, f"{nombre_base} copia {contador}{extension}")
            if not os.path.exists(candidato):
                return candidato
            contador += 1

    def salir_programa(self):
        if self.ventana.lienzo_modificado:
            if self.confirmar_descarte_cambios():
                self.ventana.close()
        else:
            self.ventana.close()

    def confirmar_descarte_cambios(self):
        """Muestra cuadro para Sí (guardar), No (descartar), Cancelar"""
        msg_box = QMessageBox(self.ventana)
        msg_box.setWindowTitle("Cambios no guardados")
        msg_box.setText("Se realizaron cambios en el lienzo. ¿Desea guardarlos antes de continuar?")
        
        btn_si = msg_box.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        btn_no = msg_box.addButton("No", QMessageBox.ButtonRole.NoRole)
        btn_cancelar = msg_box.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)

        msg_box.exec()
        btn = msg_box.clickedButton()

        if btn == btn_si:
            return self.guardar_archivo()
        elif btn == btn_no:
            return True  # Continúa descartando
        else:
            return False  # Cancelar aborta la acción
