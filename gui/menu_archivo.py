import os
from PyQt6.QtWidgets import (QMessageBox, QDialog, QVBoxLayout,
                             QHBoxLayout, QLabel, QSpinBox, QRadioButton,
                             QPushButton, QButtonGroup, QApplication)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QIcon
from gui.dialogo_archivo import DialogoArchivo


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
        settings = QSettings("PaintNotNet", "PaintNotNet")
        dir_guardado = settings.value("default_dir", None)
        if dir_guardado and os.path.isdir(str(dir_guardado)):
            return str(dir_guardado)

        usuario_real = os.environ.get('SUDO_USER') or os.environ.get('LOGNAME') or os.environ.get('USER')
        if usuario_real and usuario_real != 'root':
            ruta_home = os.path.join('/home', usuario_real)
            if os.path.exists(ruta_home):
                return ruta_home
        return os.path.expanduser("~")

    def crear_menu(self, menu_bar):
        self.menu_bar = menu_bar
        self.retraducir_menu()

    def retraducir_menu(self):
        from core.i18n import t
        if hasattr(self, 'menu_archivo') and self.menu_archivo:
            self.menu_bar.removeAction(self.menu_archivo.menuAction())

        self.menu_archivo = self.menu_bar.addMenu(t("Archivo"))

        accion_nuevo = self.menu_archivo.addAction(QIcon("gui/iconos/new.png"), t("Nuevo"))
        accion_nuevo.setShortcut("Ctrl+N")
        accion_nuevo.triggered.connect(self.nuevo_archivo)

        accion_abrir = self.menu_archivo.addAction(QIcon("gui/iconos/open.png"), t("Abrir..."))
        accion_abrir.setShortcut("Ctrl+O")
        accion_abrir.triggered.connect(self.abrir_archivo)

        self.menu_recientes = self.menu_archivo.addMenu(t("Recientes"))
        self.menu_recientes.setIcon(QIcon("gui/iconos/history.png"))
        self.actualizar_menu_recientes()

        accion_insertar = self.menu_archivo.addAction(QIcon("gui/iconos/picture.png"), t("Insertar..."))
        accion_insertar.setShortcut("Ctrl+I")
        accion_insertar.triggered.connect(self.insertar_imagen)

        self.menu_archivo.addSeparator()

        accion_guardar = self.menu_archivo.addAction(QIcon("gui/iconos/save.png"), t("Guardar"))
        accion_guardar.setShortcut("Ctrl+S")
        accion_guardar.triggered.connect(self.guardar_archivo)

        accion_guardar_como = self.menu_archivo.addAction(QIcon("gui/iconos/save.png"), t("Guardar como..."))
        accion_guardar_como.setShortcut("Ctrl+Shift+S")
        accion_guardar_como.triggered.connect(self.guardar_como)

        self.menu_archivo.addSeparator()

        accion_imprimir = self.menu_archivo.addAction(QIcon("gui/iconos/printer.png"), t("Imprimir..."))
        accion_imprimir.setShortcut("Ctrl+P")
        accion_imprimir.triggered.connect(self.imprimir_lienzo)

        accion_pdf = self.menu_archivo.addAction(QIcon("gui/iconos/pdf.png"), t("Exportar PDF..."))
        accion_pdf.setShortcut("Ctrl+Shift+P")
        accion_pdf.triggered.connect(self.exportar_pdf)

        self.menu_archivo.addSeparator()

        accion_salir = self.menu_archivo.addAction(QIcon("gui/iconos/close.png"), t("Salir"))
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
            ext = os.path.splitext(ruta)[1].lower()
            icono = QIcon("gui/iconos/pnn.png") if ext == ".pnn" else QIcon("gui/iconos/picture.png")
            action = self.menu_recientes.addAction(icono, f"{idx}. {nombre}")
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

    def abrir_ruta_especifica(self, ruta):
        self.abrir_archivo_reciente(ruta)

    def nuevo_archivo(self):
        dialogo = DialogoNuevoArchivo(self.ventana)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            ancho, alto, es_transparente = dialogo.obtener_configuracion()
            self.ventana.crear_nueva_pestana(ancho, alto, transparent=es_transparente)

    def abrir_archivo(self):
        dir_home = self.obtener_home_real()
        filtros = [
            ("Todos los archivos soportados", "*.pnn *.png *.jpg *.jpeg *.bmp *.webp"),
            ("Borrador PaintNotNet",          "*.pnn"),
            ("Imágenes",                      "*.png *.jpg *.jpeg *.bmp *.webp"),
            ("Todos los archivos",            "*"),
        ]
        dialogo = DialogoArchivo(
            self.ventana,
            modo="abrir",
            directorio=dir_home,
            filtros=filtros,
            titulo="Abrir Imagen o Borrador"
        )
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        ruta = dialogo.ruta_seleccionada()
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
        filtros = [
            ("Imágenes",          "*.png *.jpg *.jpeg *.bmp *.webp"),
            ("Todos los archivos", "*"),
        ]
        dialogo = DialogoArchivo(
            self.ventana,
            modo="abrir",
            directorio=dir_home,
            filtros=filtros,
            titulo="Insertar Imagen"
        )
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        ruta = dialogo.ruta_seleccionada()
        if ruta:
            if self.ventana.lienzo.insertar_imagen(ruta):
                if hasattr(self.ventana, 'panel_herramientas'):
                    self.ventana.panel_herramientas.seleccionar("seleccion")



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

        settings = QSettings("PaintNotNet", "PaintNotNet")
        fmt_config = settings.value("default_format", None)

        if num_capas > 1:
            ext_defecto = ".pnn"
            filtro_defecto = filtro_pnn
            filtros = f"{filtro_pnn};;{filtro_png};;{filtro_jpg};;{filtro_bmp}"
        else:
            if fmt_config and "pnn" in str(fmt_config).lower():
                ext_defecto = ".pnn"
                filtro_defecto = filtro_pnn
                filtros = f"{filtro_pnn};;{filtro_png};;{filtro_jpg};;{filtro_bmp}"
            elif fmt_config and "jpg" in str(fmt_config).lower():
                ext_defecto = ".jpg"
                filtro_defecto = filtro_jpg
                filtros = f"{filtro_jpg};;{filtro_png};;{filtro_pnn};;{filtro_bmp}"
            elif fmt_config and "bmp" in str(fmt_config).lower():
                ext_defecto = ".bmp"
                filtro_defecto = filtro_bmp
                filtros = f"{filtro_bmp};;{filtro_png};;{filtro_pnn};;{filtro_jpg}"
            else:
                ext_defecto = ".png"
                filtro_defecto = filtro_png
                filtros = f"{filtro_png};;{filtro_pnn};;{filtro_jpg};;{filtro_bmp}"

        sug_nombre = base_nombre if base_nombre.lower().endswith(ext_defecto) else f"{base_nombre}{ext_defecto}"
        sug_path = os.path.join(dir_home, sug_nombre)

        # Construir lista de filtros para DialogoArchivo
        filtros_dialogo = [
            ("Borrador PaintNotNet", "*.pnn"),
            ("Imagen PNG",          "*.png"),
            ("Imagen JPG",          "*.jpg *.jpeg"),
            ("Imagen BMP",          "*.bmp"),
        ]
        # Poner el filtro por defecto primero
        _orden = {"pnn": 0, "png": 1, "jpg": 2, "bmp": 3}
        idx_defecto = _orden.get(ext_defecto.lstrip('.'), 1)
        filtros_dialogo = (
            filtros_dialogo[idx_defecto:idx_defecto+1] +
            [f for i, f in enumerate(filtros_dialogo) if i != idx_defecto]
        )

        dialogo = DialogoArchivo(
            self.ventana,
            modo="guardar",
            directorio=dir_home,
            filtros=filtros_dialogo,
            nombre_sugerido=sug_nombre,
            titulo="Guardar como…"
        )
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return False
        ruta_elegida = dialogo.ruta_seleccionada()

        if ruta_elegida:
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

    def _obtener_imagen_compuesta(self):
        """Devuelve la imagen aplanada del canvas activo."""
        canvas = self.ventana.canvas
        from PyQt6.QtGui import QImage, QPainter
        from PyQt6.QtCore import Qt
        img = QImage(canvas.layer_mgr.width, canvas.layer_mgr.height,
                     QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.white)
        painter = QPainter(img)
        for capa in canvas.layer_mgr.capas:
            if capa.visible:
                painter.drawImage(0, 0, capa.image)
        painter.end()
        return img

    def imprimir_lienzo(self):
        from core.i18n import t
        from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog
        from PyQt6.QtGui import QPainter
        from PyQt6.QtCore import QRectF
        from PyQt6.QtWidgets import QMessageBox

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        preview = QPrintPreviewDialog(printer, self.ventana)
        preview.setWindowTitle(t("Vista previa de impresión..."))

        def render_page(prn):
            try:
                img = self._obtener_imagen_compuesta()
                painter = QPainter(prn)
                page_rect = QRectF(prn.pageRect(QPrinter.Unit.DevicePixel))
                src_rect = QRectF(img.rect())
                # Escala manteniendo proporción
                scale = min(page_rect.width() / src_rect.width(),
                            page_rect.height() / src_rect.height())
                w = src_rect.width() * scale
                h = src_rect.height() * scale
                x = (page_rect.width() - w) / 2
                y = (page_rect.height() - h) / 2
                painter.drawImage(QRectF(x, y, w, h), img, src_rect)
                painter.end()
            except Exception as e:
                QMessageBox.critical(self.ventana,
                                     t("Error de impresión"),
                                     t("No se pudo imprimir el lienzo.") + f"\n{e}")

        preview.paintRequested.connect(render_page)
        preview.resize(900, 700)
        preview.exec()

    def exportar_pdf(self):
        from core.i18n import t
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtGui import QPainter
        from PyQt6.QtCore import QRectF
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import os

        ruta, _ = QFileDialog.getSaveFileName(
            self.ventana,
            t("Guardar PDF"),
            os.path.expanduser("~"),
            t("Archivos PDF (*.pdf)")
        )
        if not ruta:
            return
        if not ruta.lower().endswith(".pdf"):
            ruta += ".pdf"

        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(ruta)

            img = self._obtener_imagen_compuesta()
            painter = QPainter(printer)
            page_rect = QRectF(printer.pageRect(QPrinter.Unit.DevicePixel))
            src_rect = QRectF(img.rect())
            scale = min(page_rect.width() / src_rect.width(),
                        page_rect.height() / src_rect.height())
            w = src_rect.width() * scale
            h = src_rect.height() * scale
            x = (page_rect.width() - w) / 2
            y = (page_rect.height() - h) / 2
            painter.drawImage(QRectF(x, y, w, h), img, src_rect)
            painter.end()
            QMessageBox.information(self.ventana,
                                    t("Exportar PDF..."),
                                    t("PDF guardado en") + f":\n{ruta}")
        except Exception as e:
            QMessageBox.critical(self.ventana,
                                 t("Error al exportar PDF"),
                                 t("No se pudo exportar el PDF.") + f"\n{e}")

    def salir_programa(self):
        if getattr(self.ventana.lienzo, 'lienzo_modificado', False):
            if self.confirmar_descarte_cambios():
                self.ventana.close()
        else:
            self.ventana.close()

    def confirmar_descarte_cambios(self, target_canvas=None):
        from core.i18n import t
        canvas = target_canvas if target_canvas else self.ventana.lienzo
        msg_box = QMessageBox(self.ventana)
        msg_box.setWindowTitle(t("Cambios no guardados"))

        nombre_doc = "el archivo"
        if canvas:
            if getattr(canvas, 'nombre_personalizado', None):
                nombre_doc = f'"{canvas.nombre_personalizado}"'
            elif canvas.archivo_actual:
                nombre_doc = f'"{os.path.basename(canvas.archivo_actual)}"'

        msg_fmt = t("Se realizaron cambios en %1. ¿Desea guardarlos antes de continuar?")
        msg_box.setText(msg_fmt.replace("%1", nombre_doc))

        btn_si = msg_box.addButton(t("Sí"), QMessageBox.ButtonRole.YesRole)
        btn_no = msg_box.addButton(t("No"), QMessageBox.ButtonRole.NoRole)
        btn_cancelar = msg_box.addButton(t("Cancelar"), QMessageBox.ButtonRole.RejectRole)

        msg_box.exec()
        btn = msg_box.clickedButton()

        if btn == btn_si:
            return self.guardar_archivo(target_canvas=canvas)
        elif btn == btn_no:
            return True
        else:
            return False
