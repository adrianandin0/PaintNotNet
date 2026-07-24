import os
from PyQt6.QtWidgets import (QFileDialog, QMessageBox, QDialog, QVBoxLayout,
                             QHBoxLayout, QLabel, QSpinBox, QRadioButton,
                             QPushButton, QButtonGroup)
from PyQt6.QtCore import Qt


class DialogoNuevoArchivo(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Lienzo")
        self.setFixedWidth(240)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

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

        layout.addWidget(QLabel("Color de Fondo:"))
        self.rad_blanco = QRadioButton("Fondo Blanco")
        self.rad_transparente = QRadioButton("Fondo Transparente")
        self.rad_blanco.setChecked(True)

        self.grupo_fondo = QButtonGroup(self)
        self.grupo_fondo.addButton(self.rad_blanco)
        self.grupo_fondo.addButton(self.rad_transparente)

        layout.addWidget(self.rad_blanco)
        layout.addWidget(self.rad_transparente)

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
            self.rad_transparente.isChecked()
        )


class MenuArchivo:
    def __init__(self, ventana_principal):
        self.ventana = ventana_principal

    def obtener_home_real(self):
        """Devuelve el home del usuario real incluso si se ejecuta con sudo"""
        usuario_real = os.environ.get('SUDO_USER') or os.environ.get('LOGNAME') or os.environ.get('USER')
        if usuario_real and usuario_real != 'root':
            ruta_home = os.path.join('/home', usuario_real)
            if os.path.exists(ruta_home):
                return ruta_home
        return os.path.expanduser("~")

    def crear_menu(self, menu_bar):
        menu_archivo = menu_bar.addMenu("Archivo")

        accion_nuevo = menu_archivo.addAction("Nuevo")
        accion_nuevo.setShortcut("Ctrl+N")
        accion_nuevo.triggered.connect(self.nuevo_archivo)

        accion_abrir = menu_archivo.addAction("Abrir...")
        accion_abrir.setShortcut("Ctrl+O")
        accion_abrir.triggered.connect(self.abrir_archivo)

        accion_insertar = menu_archivo.addAction("Insertar...")
        accion_insertar.setShortcut("Ctrl+I")
        accion_insertar.triggered.connect(self.insertar_imagen)

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

        dir_home = self.obtener_home_real()

        ruta, _ = QFileDialog.getOpenFileName(
            self.ventana,
            "Abrir Imagen",
            dir_home,
            "Imágenes (*.png *.jpg *.jpeg *.bmp);;Todos los archivos (*)"
        )
        if ruta:
            if self.ventana.lienzo.cargar_imagen(ruta):
                self.ventana.archivo_actual = ruta
                self.ventana.lienzo_modificado = False
                self.ventana.actualizar_titulo_ventana()

    def insertar_imagen(self):
        """Inserta una imagen sobre el lienzo actual como selección flotante"""
        dir_home = self.obtener_home_real()

        ruta, _ = QFileDialog.getOpenFileName(
            self.ventana,
            "Insertar Imagen",
            dir_home,
            "Imágenes (*.png *.jpg *.jpeg *.bmp);;Todos los archivos (*)"
        )
        if ruta:
            if self.ventana.lienzo.insertar_imagen(ruta):
                if hasattr(self.ventana, 'panel_herramientas'):
                    self.ventana.panel_herramientas.seleccionar("seleccion")

    def guardar_como(self):
        dir_home = self.obtener_home_real()

        filtro_png = "Imagen PNG (*.png)"
        filtro_jpg = "Imagen JPG (*.jpg *.jpeg)"
        filtro_bmp = "Imagen BMP (*.bmp)"

        filtros = f"{filtro_png};;{filtro_jpg};;{filtro_bmp}"

        nombre_sugerido = "sin_titulo.png"
        if self.ventana.archivo_actual:
            nombre_sugerido = os.path.basename(self.ventana.archivo_actual)

        ruta_inicial = os.path.join(dir_home, nombre_sugerido)

        ruta_elegida, filtro_seleccionado = QFileDialog.getSaveFileName(
            self.ventana,
            "Guardar Imagen Como",
            ruta_inicial,
            filtros
        )

        if ruta_elegida:
            ext_por_defecto = {
                filtro_png: ".png",
                filtro_jpg: ".jpg",
                filtro_bmp: ".bmp"
            }

            _, ext_actual = os.path.splitext(ruta_elegida)

            # Si el usuario no escribió extensión, le asignamos la estándar según el filtro seleccionado
            if not ext_actual:
                extension_estandar = ext_por_defecto.get(filtro_seleccionado, ".png")
                ruta_elegida += extension_estandar

            if self.ventana.lienzo.guardar_imagen(ruta_elegida):
                self.ventana.archivo_actual = ruta_elegida
                self.ventana.lienzo_modificado = False
                self.ventana.actualizar_titulo_ventana()
                return True

        return False

    def guardar_archivo(self):
        if not self.ventana.archivo_actual:
            return self.guardar_como()

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

        return False

    def generar_nombre_copia(self, ruta_original):
        directorio, nombre_archivo = os.path.split(ruta_original)
        nombre_base, extension = os.path.splitext(nombre_archivo)

        candidato = os.path.join(directorio, f"{nombre_base} copia{extension}")
        if not os.path.exists(candidato):
            return candidato

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
            return True
        else:
            return False
