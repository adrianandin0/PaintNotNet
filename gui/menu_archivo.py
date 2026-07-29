import os
from PyQt6.QtWidgets import (QFileDialog, QMessageBox, QDialog, QVBoxLayout,
                             QHBoxLayout, QLabel, QSpinBox, QRadioButton,
                             QPushButton, QButtonGroup, QApplication)
from PyQt6.QtCore import Qt, QSettings


class DialogoNuevoArchivo(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Lienzo")
        self.setFixedWidth(240)

        # Detectar tamaño de imagen en el portapapeles si existe
        cb = QApplication.clipboard()
        cb_img = cb.image() if cb else None
        def_w = 800
        def_h = 600
        if cb_img and not cb_img.isNull() and cb_img.width() > 0 and cb_img.height() > 0:
            def_w = cb_img.width()
            def_h = cb_img.height()

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        layout_ancho = QHBoxLayout()
        layout_ancho.addWidget(QLabel("Ancho (px):"))
        self.spin_ancho = QSpinBox()
        self.spin_ancho.setRange(10, 99999)
        self.spin_ancho.setValue(def_w)
        layout_ancho.addWidget(self.spin_ancho)

        layout_alto = QHBoxLayout()
        layout_alto.addWidget(QLabel("Alto (px):"))
        self.spin_alto = QSpinBox()
        self.spin_alto.setRange(10, 99999)
        self.spin_alto.setValue(def_h)
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
        btn_ok.setDefault(True)
        btn_ok.setAutoDefault(True)
        btn_cancel = QPushButton("Cancelar")

        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        layout_btns.addWidget(btn_ok)
        layout_btns.addWidget(btn_cancel)
        layout.addLayout(layout_btns)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.accept()
            return
        super().keyPressEvent(event)

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

        # Submenú de Archivos Recientes
        self.menu_recientes = menu_archivo.addMenu("Recientes")
        self.actualizar_menu_recientes()

        accion_insertar = menu_archivo.addAction("Insertar...")
        accion_insertar.setShortcut("Ctrl+I")
        accion_insertar.triggered.connect(self.insertar_imagen)

        menu_archivo.addSeparator()

        accion_guardar = menu_archivo.addAction("Guardar")
        accion_guardar.setShortcut("Ctrl+S")
        accion_guardar.triggered.connect(self.guardar_archivo)

        accion_guardar_capa = menu_archivo.addAction("Guardar capa...")
        accion_guardar_capa.setShortcut("Ctrl+Shift+L")
        accion_guardar_capa.triggered.connect(self.guardar_capa)

        accion_guardar_como = menu_archivo.addAction("Guardar como...")
        accion_guardar_como.setShortcut("Ctrl+Shift+S")
        accion_guardar_como.triggered.connect(self.guardar_como)

        menu_archivo.addSeparator()

        accion_salir = menu_archivo.addAction("Salir")
        accion_salir.setShortcut("Ctrl+Q")
        accion_salir.triggered.connect(self.salir_programa)

    EXTENSIONES_IMAGEN_VALIDAS = ('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.pnn')

    def obtener_archivos_recientes(self):
        settings = QSettings("PaintNotNet", "RecentFiles")
        val = settings.value("recientes", [], type=list)
        archivos = []
        for item in val:
            if item:
                path_str = str(item)
                ext = os.path.splitext(path_str)[1].lower()
                if ext in self.EXTENSIONES_IMAGEN_VALIDAS:
                    archivos.append(path_str)
        return archivos

    def agregar_archivo_reciente(self, ruta):
        if not ruta or not os.path.exists(ruta):
            return
        ext = os.path.splitext(ruta)[1].lower()
        if ext not in self.EXTENSIONES_IMAGEN_VALIDAS:
            return

        settings = QSettings("PaintNotNet", "RecentFiles")
        recientes = self.obtener_archivos_recientes()

        if ruta in recientes:
            recientes.remove(ruta)

        recientes.insert(0, ruta)
        recientes = recientes[:5]

        settings.setValue("recientes", recientes)
        self.actualizar_menu_recientes()

    def actualizar_menu_recientes(self):
        if not hasattr(self, 'menu_recientes') or self.menu_recientes is None:
            return

        self.menu_recientes.clear()
        recientes = self.obtener_archivos_recientes()
        recientes_validos = [r for r in recientes if os.path.exists(r)]

        if not recientes_validos:
            action_vacio = self.menu_recientes.addAction("No hay archivos recientes")
            action_vacio.setEnabled(False)
            return

        def _make_reciente_handler(filepath):
            return lambda *args: self.abrir_archivo_reciente(filepath)

        for idx, ruta in enumerate(recientes_validos, 1):
            nombre = os.path.basename(ruta)
            action = self.menu_recientes.addAction(f"{idx}. {nombre}")
            action.setToolTip(ruta)
            action.triggered.connect(_make_reciente_handler(ruta))

    def abrir_archivo_reciente(self, ruta):
        if not os.path.exists(ruta):
            QMessageBox.warning(self.ventana, "Archivo no encontrado", f"El archivo ya no existe en la ruta:\n{ruta}")
            self.actualizar_menu_recientes()
            return

        tab_widget = self.ventana.tab_widget
        canvas_actual = self.ventana.lienzo
        era_inicial_limpia = (
            tab_widget.count() == 1 and
            canvas_actual and
            canvas_actual.archivo_actual is None and
            not getattr(canvas_actual, 'lienzo_modificado', False) and
            len(canvas_actual.history_mgr.history_stack) <= 1 and
            len(canvas_actual.layer_mgr.capas) == 1
        )

        canvas_nuevo = self.ventana.crear_nueva_pestana(800, 600, transparent=True, ruta=ruta, titulo=os.path.basename(ruta))
        if canvas_nuevo.cargar_imagen(ruta):
            canvas_nuevo.archivo_actual = ruta
            canvas_nuevo.lienzo_modificado = False
            self.ventana.actualizar_titulo_ventana()
            self.agregar_archivo_reciente(ruta)

            if era_inicial_limpia and tab_widget.count() > 1:
                tab_widget.removeTab(0)

    def nuevo_archivo(self):
        dialogo = DialogoNuevoArchivo(self.ventana)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            ancho, alto, es_transparente = dialogo.obtener_configuracion()
            self.ventana.crear_nueva_pestana(ancho, alto, transparent=es_transparente)

    def abrir_archivo(self):
        dir_home = self.obtener_home_real()
        filtros = "Todos los archivos soportados (*.pnn *.png *.jpg *.jpeg *.bmp *.webp);;Borrador PaintNotNet (*.pnn);;Imágenes (*.png *.jpg *.jpeg *.bmp *.webp);;Todos los archivos (*)"

        ruta, _ = QFileDialog.getOpenFileName(
            self.ventana,
            "Abrir Imagen o Borrador",
            dir_home,
            filtros
        )
        if ruta:
            tab_widget = self.ventana.tab_widget
            canvas_actual = self.ventana.lienzo
            era_inicial_limpia = (
                tab_widget.count() == 1 and
                canvas_actual and
                canvas_actual.archivo_actual is None and
                not getattr(canvas_actual, 'lienzo_modificado', False) and
                len(canvas_actual.history_mgr.history_stack) <= 1 and
                len(canvas_actual.layer_mgr.capas) == 1
            )

            canvas_nuevo = self.ventana.crear_nueva_pestana(800, 600, transparent=True, ruta=ruta, titulo=os.path.basename(ruta))
            if canvas_nuevo.cargar_imagen(ruta):
                canvas_nuevo.archivo_actual = ruta
                canvas_nuevo.lienzo_modificado = False
                self.ventana.actualizar_titulo_ventana()
                self.agregar_archivo_reciente(ruta)

                if era_inicial_limpia and tab_widget.count() > 1:
                    tab_widget.removeTab(0)

    def insertar_imagen(self):
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

    def guardar_capa(self):
        dir_home = self.obtener_home_real()
        canvas = self.ventana.lienzo
        capa_activa = canvas.layer_mgr.capas[canvas.layer_mgr.indice_activo]
        nombre_sugerido = f"{capa_activa.name}.png"
        ruta_inicial = os.path.join(dir_home, nombre_sugerido)

        filtro_png = "Imagen PNG (*.png)"
        filtro_jpg = "Imagen JPG (*.jpg *.jpeg)"
        filtro_bmp = "Imagen BMP (*.bmp)"

        filtros = f"{filtro_png};;{filtro_jpg};;{filtro_bmp}"

        ruta_elegida, filtro_seleccionado = QFileDialog.getSaveFileName(
            self.ventana,
            "Guardar Capa Actual",
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

            if not ext_actual:
                extension_estandar = ext_por_defecto.get(filtro_seleccionado, ".png")
                ruta_elegida += extension_estandar

            if canvas.guardar_imagen(ruta_elegida):
                return True

        return False

    def guardar_como(self, target_canvas=None):
        dir_home = self.obtener_home_real()
        filtro_pnn = "Borrador PaintNotNet (*.pnn)"
        filtro_png = "Imagen PNG (*.png)"
        filtro_jpg = "Imagen JPG (*.jpg *.jpeg)"
        filtro_bmp = "Imagen BMP (*.bmp)"

        canvas = target_canvas if target_canvas else self.ventana.lienzo
        num_capas = len(canvas.layer_mgr.capas) if (canvas and hasattr(canvas, 'layer_mgr')) else 1

        if canvas and getattr(canvas, 'nombre_personalizado', None):
            base_nombre = canvas.nombre_personalizado
        elif canvas and canvas.archivo_actual:
            base_nombre = os.path.splitext(os.path.basename(canvas.archivo_actual))[0]
        else:
            base_nombre = "sin_titulo"

        if num_capas > 1:
            ext_defecto = ".pnn"
            filtro_defecto = filtro_pnn
            filtros = f"{filtro_pnn};;{filtro_png};;{filtro_jpg};;{filtro_bmp}"
        else:
            ext_defecto = ".png"
            filtro_defecto = filtro_png
            filtros = f"{filtro_png};;{filtro_pnn};;{filtro_jpg};;{filtro_bmp}"

        sug_nombre = base_nombre if base_nombre.lower().endswith(ext_defecto) else f"{base_nombre}{ext_defecto}"
        sug_path = os.path.join(dir_home, sug_nombre)

        ruta_elegida, filtro_seleccionado = QFileDialog.getSaveFileName(
            self.ventana,
            "Guardar como...",
            sug_path,
            filtros,
            initialFilter=filtro_defecto
        )

        if ruta_elegida:
            ext_por_defecto = {
                filtro_pnn: ".pnn",
                filtro_png: ".png",
                filtro_jpg: ".jpg",
                filtro_bmp: ".bmp"
            }

            _, ext_actual = os.path.splitext(ruta_elegida)

            if not ext_actual:
                extension_estandar = ext_por_defecto.get(filtro_seleccionado, ext_defecto)
                ruta_elegida += extension_estandar

            if canvas.guardar_imagen(ruta_elegida):
                canvas.archivo_actual = ruta_elegida
                canvas.lienzo_modificado = False
                self.ventana.actualizar_titulo_ventana()
                self.agregar_archivo_reciente(ruta_elegida)
                return True

        return False

    def guardar_archivo(self, target_canvas=None):
        canvas = target_canvas if target_canvas else self.ventana.lienzo
        if not canvas or not canvas.archivo_actual:
            return self.guardar_como(target_canvas=canvas)

        if canvas.guardar_imagen(canvas.archivo_actual):
            canvas.lienzo_modificado = False
            self.ventana.actualizar_titulo_ventana()
            self.agregar_archivo_reciente(canvas.archivo_actual)
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
        if getattr(self.ventana.lienzo, 'lienzo_modificado', False):
            if self.confirmar_descarte_cambios():
                self.ventana.close()
        else:
            self.ventana.close()

    def confirmar_descarte_cambios(self, target_canvas=None):
        canvas = target_canvas if target_canvas else self.ventana.lienzo
        msg_box = QMessageBox(self.ventana)
        msg_box.setWindowTitle("Cambios no guardados")
        
        nombre_doc = "el archivo"
        if canvas:
            if getattr(canvas, 'nombre_personalizado', None):
                nombre_doc = f'"{canvas.nombre_personalizado}"'
            elif canvas.archivo_actual:
                nombre_doc = f'"{os.path.basename(canvas.archivo_actual)}"'

        msg_box.setText(f"Se realizaron cambios en {nombre_doc}. ¿Desea guardarlos antes de continuar?")

        btn_si = msg_box.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        btn_no = msg_box.addButton("No", QMessageBox.ButtonRole.NoRole)
        btn_cancelar = msg_box.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)

        msg_box.exec()
        btn = msg_box.clickedButton()

        if btn == btn_si:
            return self.guardar_archivo(target_canvas=canvas)
        elif btn == btn_no:
            return True
        else:
            return False
