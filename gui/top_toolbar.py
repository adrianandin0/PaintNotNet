from PyQt6.QtWidgets import QToolBar, QWidget, QHBoxLayout, QLabel, QSpinBox, QSlider, QComboBox, QCheckBox, QStyle
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QSettings


class TopToolBarWidget(QToolBar):
    grosor_changed = pyqtSignal(int)
    tolerancia_changed = pyqtSignal(int)

    def __init__(self, main_window=None):
        super().__init__("Barra de Herramientas General", main_window)
        self.main_window = main_window
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(QSize(18, 18))
        self.setStyleSheet("QToolBar { spacing: 4px; padding: 2px; }")

        # 0. Nueva Pestaña (+)
        self.action_nueva_pestana = QAction(QIcon("gui/iconos/add.png"), "Nueva Pestaña", self)
        self.action_nueva_pestana.setToolTip("Nueva Pestaña (Ctrl+N)")
        self.addAction(self.action_nueva_pestana)

        # 1. Abrir
        self.action_abrir = QAction(QIcon("gui/iconos/open.png"), "Abrir", self)
        self.action_abrir.setToolTip("Abrir imagen (Ctrl+O)")
        self.addAction(self.action_abrir)

        # 2. Guardar
        self.action_guardar = QAction(QIcon("gui/iconos/save.png"), "Guardar", self)
        self.action_guardar.setToolTip("Guardar imagen (Ctrl+S)")
        self.addAction(self.action_guardar)

        self.addSeparator()

        # 3. Cortar
        self.action_cortar = QAction(QIcon("gui/iconos/cut.png"), "Cortar", self)
        self.action_cortar.setToolTip("Cortar selección (Ctrl+X)")
        self.addAction(self.action_cortar)

        # 4. Copiar
        self.action_copiar = QAction(QIcon("gui/iconos/copy.png"), "Copiar", self)
        self.action_copiar.setToolTip("Copiar selección (Ctrl+C)")
        self.addAction(self.action_copiar)

        # 5. Pegar
        self.action_pegar = QAction(QIcon("gui/iconos/paste.png"), "Pegar", self)
        self.action_pegar.setToolTip("Pegar contenido (Ctrl+V)")
        self.addAction(self.action_pegar)

        self.addSeparator()

        # 6. Selector de Grosor / Ancho Global
        lbl_grosor = QLabel(" Ancho: ")
        lbl_grosor.setStyleSheet("font-size: 11px; font-weight: bold;")
        self.addWidget(lbl_grosor)

        self.spin_grosor = QSpinBox()
        self.spin_grosor.setRange(1, 100)
        self.spin_grosor.setValue(3)
        self.spin_grosor.setSuffix(" px")
        self.spin_grosor.setFixedWidth(65)
        self.spin_grosor.valueChanged.connect(self._on_grosor_changed)
        self.addWidget(self.spin_grosor)

        self.addSeparator()

        # 7. Selector de Tolerancia Global
        self.lbl_tol = QLabel(" Tolerancia: ")
        self.lbl_tol.setStyleSheet("font-size: 11px; font-weight: bold;")
        self.addWidget(self.lbl_tol)

        self.slider_tol = QSlider(Qt.Orientation.Horizontal)
        self.slider_tol.setRange(0, 100)
        self.slider_tol.setValue(32)
        self.slider_tol.setFixedWidth(65)
        self.slider_tol.valueChanged.connect(self._on_tolerancia_changed)
        self.addWidget(self.slider_tol)

        self.lbl_tol_val = QLabel("32%")
        self.lbl_tol_val.setStyleSheet("font-size: 11px; font-weight: bold; color: #888888;")
        self.addWidget(self.lbl_tol_val)

        self.addSeparator()

        # 8. Selector de Suavizado Global
        self.lbl_suav = QLabel(" Suavizado: ")
        self.lbl_suav.setStyleSheet("font-size: 11px; font-weight: bold;")
        self.addWidget(self.lbl_suav)

        self.slider_suav = QSlider(Qt.Orientation.Horizontal)
        self.slider_suav.setRange(0, 100)
        self.slider_suav.setValue(100)
        self.slider_suav.setFixedWidth(65)
        self.slider_suav.valueChanged.connect(self._on_suavizado_changed)
        self.addWidget(self.slider_suav)

        self.lbl_suav_val = QLabel("100%")
        self.lbl_suav_val.setStyleSheet("font-size: 11px; font-weight: bold; color: #888888;")
        self.addWidget(self.lbl_suav_val)

        self.addSeparator()

        # 9. Selector de Zoom
        self.lbl_zoom = QLabel(" Zoom: ")
        self.lbl_zoom.setStyleSheet("font-size: 11px; font-weight: bold;")
        self.addWidget(self.lbl_zoom)

        self.combo_zoom = QComboBox()
        self.combo_zoom.setEditable(True)
        self.combo_zoom.setFixedWidth(65)
        self.combo_zoom.addItems(["10%", "25%", "50%", "75%", "100%", "125%", "150%", "200%", "300%"])
        self.combo_zoom.setCurrentText("100%")
        self.combo_zoom.setStyleSheet("font-size: 11px; padding: 1px;")
        self.combo_zoom.activated.connect(self._on_zoom_changed)
        if self.combo_zoom.lineEdit():
            self.combo_zoom.lineEdit().editingFinished.connect(self._on_zoom_changed)
        self.addWidget(self.combo_zoom)

        self.addSeparator()

        # 10. Opciones de Línea
        self.lbl_linea = QLabel(" Línea: ")
        self.lbl_linea.setStyleSheet("font-size: 11px; font-weight: bold; color: #888888;")
        self.addWidget(self.lbl_linea)

        combo_style = """
            QComboBox {
                padding: 1px 1px 1px 2px;
                font-size: 11px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 10px;
                border: none;
            }
        """

        self.combo_linea_inicio = QComboBox()
        self.combo_linea_inicio.setStyleSheet(combo_style)
        self.combo_linea_inicio.setIconSize(QSize(18, 18))
        self.combo_linea_inicio.setFixedWidth(36)
        self.combo_linea_inicio.addItem(QIcon("gui/iconos/rectangle.png"), "", "Plana")
        self.combo_linea_inicio.addItem(QIcon("gui/iconos/line_circle_left.png"), "", "Redonda")
        self.combo_linea_inicio.addItem(QIcon("gui/iconos/arrow_left.png"), "", "Flecha")
        self.combo_linea_inicio.addItem(QIcon("gui/iconos/circle.png"), "", "Circulo")
        self.combo_linea_inicio.setToolTip("Punta Inicial: Plana")
        self.combo_linea_inicio.currentIndexChanged.connect(self._on_linea_inicio_changed)
        self.addWidget(self.combo_linea_inicio)

        self.combo_linea_estilo = QComboBox()
        self.combo_linea_estilo.setStyleSheet(combo_style)
        self.combo_linea_estilo.setIconSize(QSize(18, 18))
        self.combo_linea_estilo.setFixedWidth(36)
        self.combo_linea_estilo.addItem(QIcon("gui/iconos/flat.png"), "", "Recta")
        self.combo_linea_estilo.addItem(QIcon("gui/iconos/pointed.png"), "", "Punteada")
        self.combo_linea_estilo.setToolTip("Estilo de Trazo: Recta")
        self.combo_linea_estilo.currentIndexChanged.connect(self._on_linea_estilo_changed)
        self.addWidget(self.combo_linea_estilo)

        self.combo_linea_fin = QComboBox()
        self.combo_linea_fin.setStyleSheet(combo_style)
        self.combo_linea_fin.setIconSize(QSize(18, 18))
        self.combo_linea_fin.setFixedWidth(36)
        self.combo_linea_fin.addItem(QIcon("gui/iconos/rectangle.png"), "", "Plana")
        self.combo_linea_fin.addItem(QIcon("gui/iconos/line_circle_right.png"), "", "Redonda")
        self.combo_linea_fin.addItem(QIcon("gui/iconos/arrow_right.png"), "", "Flecha")
        self.combo_linea_fin.addItem(QIcon("gui/iconos/circle.png"), "", "Circulo")
        self.combo_linea_fin.setToolTip("Punta Final: Plana")
        self.combo_linea_fin.currentIndexChanged.connect(self._on_linea_fin_changed)
        self.addWidget(self.combo_linea_fin)

        self.addSeparator()

        # 11. Opciones de Formas Geométrica
        self.lbl_formas = QLabel(" Formas: ")
        self.lbl_formas.setStyleSheet("font-size: 11px; font-weight: bold; color: #888888;")
        self.addWidget(self.lbl_formas)

        self.chk_formas_redondeado = QCheckBox("Redondeado")
        self.chk_formas_redondeado.setStyleSheet("font-size: 11px;")
        self.chk_formas_redondeado.setToolTip("Esquinas redondeadas para Rectángulos y Triángulos")
        self.addWidget(self.chk_formas_redondeado)

        self.combo_forma_estilo = QComboBox()
        self.combo_forma_estilo.setStyleSheet(combo_style)
        self.combo_forma_estilo.setIconSize(QSize(18, 18))
        self.combo_forma_estilo.setFixedWidth(36)
        self.combo_forma_estilo.addItem(QIcon("gui/iconos/shape.png"), "", "Solo Borde")
        self.combo_forma_estilo.addItem(QIcon("gui/iconos/shapes_solid.png"), "", "Forma Sólida")
        self.combo_forma_estilo.addItem(QIcon("gui/iconos/shapes_colored.png"), "", "Borde y Relleno")
        self.combo_forma_estilo.setToolTip("Estilo de Forma: Solo Borde")
        self.addWidget(self.combo_forma_estilo)

        self.combo_forma_tipo = QComboBox()
        self.combo_forma_tipo.setStyleSheet(combo_style)
        self.combo_forma_tipo.setIconSize(QSize(18, 18))
        self.combo_forma_tipo.setFixedWidth(36)
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_rectangle.png"), "", "Rectángulo")
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_triangle.png"), "", "Triángulo")
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_circle.png"), "", "Elipse")
        self.combo_forma_tipo.setToolTip("Tipo de Forma: Rectángulo")
        self.addWidget(self.combo_forma_tipo)

        self.addSeparator()

        # 12. Opciones de Difuminar / Blur
        self.lbl_blur = QLabel(" Difuminar: ")
        self.lbl_blur.setStyleSheet("font-size: 11px; font-weight: bold; color: #888888;")
        self.addWidget(self.lbl_blur)

        settings = QSettings("PaintNotNet", "PaintNotNet")
        saved_mode = settings.value("blur_modo", "Pixelado")
        saved_val = int(settings.value("blur_val", 0))

        self.combo_blur_modo = QComboBox()
        self.combo_blur_modo.setStyleSheet("font-size: 11px; padding: 1px;")
        self.combo_blur_modo.setFixedWidth(95)
        self.combo_blur_modo.addItem("Pixelado", "Pixelado")
        self.combo_blur_modo.addItem("Gausiano", "Gausiano")
        idx_mode = self.combo_blur_modo.findData(saved_mode)
        if idx_mode >= 0:
            self.combo_blur_modo.setCurrentIndex(idx_mode)
        self.combo_blur_modo.currentIndexChanged.connect(self._on_blur_changed)
        self.addWidget(self.combo_blur_modo)

        self.slider_blur = QSlider(Qt.Orientation.Horizontal)
        self.slider_blur.setRange(0, 100)
        self.slider_blur.setValue(saved_val)
        self.slider_blur.setFixedWidth(65)
        self.slider_blur.valueChanged.connect(self._on_blur_changed)
        self.addWidget(self.slider_blur)

        self.lbl_blur_val = QLabel(f"{saved_val}%")
        self.lbl_blur_val.setStyleSheet("font-size: 11px; font-weight: bold; color: #888888;")
        self.addWidget(self.lbl_blur_val)

        if main_window:
            self.conectar_acciones()

    def _on_blur_changed(self, *args):
        val = self.slider_blur.value()
        modo = self.combo_blur_modo.currentData() or "Pixelado"
        self.lbl_blur_val.setText(f"{val}%")

        settings = QSettings("PaintNotNet", "PaintNotNet")
        settings.setValue("blur_modo", modo)
        settings.setValue("blur_val", val)

        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.aplicar_difuminado(modo, val)

    def update_tool_states(self, tool_obj):
        if not tool_obj:
            return

        from tools.bucket import BucketTool
        from tools.magic_wand import MagicWandTool
        from tools.brush import BrushTool
        from tools.zoom import ZoomTool
        from tools.line import LineTool
        from tools.shapes import ShapesTool
        from tools.blur import BlurTool

        uses_tolerance = isinstance(tool_obj, (BucketTool, MagicWandTool))
        uses_smoothness = isinstance(tool_obj, (BrushTool, LineTool))
        uses_zoom = isinstance(tool_obj, ZoomTool)
        uses_line = isinstance(tool_obj, LineTool)
        uses_shapes = isinstance(tool_obj, ShapesTool)
        uses_blur = isinstance(tool_obj, BlurTool)

        self.lbl_tol.setEnabled(uses_tolerance)
        self.slider_tol.setEnabled(uses_tolerance)
        self.lbl_tol_val.setEnabled(uses_tolerance)

        self.lbl_suav.setEnabled(uses_smoothness)
        self.slider_suav.setEnabled(uses_smoothness)
        self.lbl_suav_val.setEnabled(uses_smoothness)

        self.lbl_zoom.setEnabled(uses_zoom)
        self.combo_zoom.setEnabled(uses_zoom)

        self.lbl_linea.setEnabled(uses_line)
        self.combo_linea_inicio.setEnabled(uses_line)
        self.combo_linea_estilo.setEnabled(uses_line)
        self.combo_linea_fin.setEnabled(uses_line)

        self.lbl_formas.setEnabled(uses_shapes)
        self.chk_formas_redondeado.setEnabled(uses_shapes)
        self.combo_forma_estilo.setEnabled(uses_shapes)
        self.combo_forma_tipo.setEnabled(uses_shapes)

        self.lbl_blur.setEnabled(uses_blur)
        self.combo_blur_modo.setEnabled(uses_blur)
        self.slider_blur.setEnabled(uses_blur)
        self.lbl_blur_val.setEnabled(uses_blur)

    def conectar_acciones(self):
        if self.main_window:
            if hasattr(self.main_window, 'nuevo_archivo'):
                self.action_nueva_pestana.triggered.connect(self.main_window.nuevo_archivo)
            if hasattr(self.main_window, 'menu_archivo'):
                self.action_abrir.triggered.connect(self.main_window.menu_archivo.abrir_archivo)
                self.action_guardar.triggered.connect(self.main_window.menu_archivo.guardar_archivo)
            if hasattr(self.main_window, 'menu_editar'):
                self.action_cortar.triggered.connect(self.main_window.menu_editar.cortar)
                self.action_copiar.triggered.connect(self.main_window.menu_editar.copiar)
                self.action_pegar.triggered.connect(self.main_window.menu_editar.pegar)

    def _on_grosor_changed(self, val):
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.ancho_pincel = val
            self.main_window.lienzo.grosor_pincel = val
            self.main_window.lienzo.update()
        self.grosor_changed.emit(val)

    def _on_tolerancia_changed(self, val):
        self.lbl_tol_val.setText(f"{val}%")
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.tolerancia = val

    def _on_suavizado_changed(self, val):
        self.lbl_suav_val.setText(f"{val}%")
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.suavizado = val

    def _on_zoom_changed(self):
        txt = self.combo_zoom.currentText().replace("%", "").strip()
        try:
            val = int(txt)
            val = max(10, min(500, val))
            if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
                self.main_window.lienzo.zoom_factor = val / 100.0
                self.main_window.lienzo.update()
        except ValueError:
            pass

    def _on_linea_inicio_changed(self, idx):
        pass

    def _on_linea_estilo_changed(self, idx):
        pass

    def _on_linea_fin_changed(self, idx):
        pass
