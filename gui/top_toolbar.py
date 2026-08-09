from PyQt6.QtWidgets import QToolBar, QWidget, QHBoxLayout, QLabel, QSpinBox, QSlider, QComboBox, QCheckBox, QStyle, QAbstractSpinBox
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
        self.setIconSize(QSize(24, 24))
        self.setStyleSheet("QToolBar { spacing: 4px; padding: 2px; }")

        # 0. Nueva Pestaña (+)
        self.action_nueva_pestana = QAction(QIcon("gui/iconos/new.png"), "Nueva Pestaña", self)
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

        # 6. Recortar a selección
        self.action_crop = QAction(QIcon("gui/iconos/crop.png"), "Recortar", self)
        self.action_crop.setToolTip("Recortar a selección")
        self.action_crop.triggered.connect(self._on_crop_clicked)
        self.addAction(self.action_crop)

        self.addSeparator()

        # 6. Selector de Grosor / Ancho Global
        self.lbl_grosor = QLabel(" Grosor: ")
        self.lbl_grosor.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.addWidget(self.lbl_grosor)

        self.spin_grosor = QSpinBox()
        self.spin_grosor.setRange(1, 9999)
        self.spin_grosor.setValue(3)
        self.spin_grosor.setSuffix(" px")
        self.spin_grosor.setFixedWidth(65)
        self.spin_grosor.setFixedHeight(22)
        self.spin_grosor.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_grosor.setStyleSheet("font-size: 11px; padding: 1px 4px;")
        self.spin_grosor.valueChanged.connect(self._on_grosor_changed)
        self.addWidget(self.spin_grosor)

        self.addSeparator()

        # 7. Selector de Tolerancia Global
        self.lbl_tol = QLabel(" Tolerancia: ")
        self.lbl_tol.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.addWidget(self.lbl_tol)

        self.slider_tol = QSlider(Qt.Orientation.Horizontal)
        self.slider_tol.setRange(0, 100)
        self.slider_tol.setValue(32)
        self.slider_tol.setFixedWidth(65)
        self.slider_tol.valueChanged.connect(self._on_tolerancia_changed)
        self.addWidget(self.slider_tol)

        self.lbl_tol_val = QLabel("50%")
        self.lbl_tol_val.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.lbl_tol_val.setFixedWidth(36)
        self.lbl_tol_val.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.addWidget(self.lbl_tol_val)

        self.addSeparator()

        # 8. Selector de Suavizado Global
        self.lbl_suav = QLabel(" Suavizado: ")
        self.lbl_suav.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.addWidget(self.lbl_suav)

        self.slider_suav = QSlider(Qt.Orientation.Horizontal)
        self.slider_suav.setRange(0, 100)
        self.slider_suav.setValue(100)
        self.slider_suav.setFixedWidth(65)
        self.slider_suav.valueChanged.connect(self._on_suavizado_changed)
        self.addWidget(self.slider_suav)

        self.lbl_suav_val = QLabel("100%")
        self.lbl_suav_val.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.lbl_suav_val.setFixedWidth(36)
        self.lbl_suav_val.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.addWidget(self.lbl_suav_val)

        self.addSeparator()

        # 9. Selector de Zoom
        self.lbl_zoom = QLabel()
        self.lbl_zoom.setPixmap(QIcon("gui/iconos/zoom.png").pixmap(QSize(24, 24)))
        self.lbl_zoom.setToolTip("Zoom")
        self.lbl_zoom.setContentsMargins(4, 0, 2, 0)
        self.addWidget(self.lbl_zoom)

        self.combo_zoom = QComboBox()
        self.combo_zoom.setEditable(True)
        self.combo_zoom.setFixedWidth(80)
        self.combo_zoom.setFixedHeight(22)
        self.combo_zoom.addItems([
            "10%", "25%", "50%", "75%",
            "100%", "200%", "300%", "400%", "500%",
            "750%", "1000%", "1250%", "1500%",
            "2000%", "2500%", "3000%"
        ])
        self.combo_zoom.setCurrentText("100%")
        self.combo_zoom.setStyleSheet("font-size: 11px; padding: 1px;")
        self.combo_zoom.activated.connect(self._on_zoom_changed)
        if self.combo_zoom.lineEdit():
            self.combo_zoom.lineEdit().editingFinished.connect(self._on_zoom_changed)
        self.addWidget(self.combo_zoom)

        self.addSeparator()

        # 10. Opciones de Línea
        self.lbl_linea = QLabel()
        self.lbl_linea.setPixmap(QIcon("gui/iconos/line.png").pixmap(QSize(24, 24)))
        self.lbl_linea.setToolTip("Línea")
        self.lbl_linea.setContentsMargins(4, 0, 2, 0)
        self.addWidget(self.lbl_linea)

        combo_style = """
            QComboBox {
                padding: 1px 2px;
                font-size: 11px;
            }
            QComboBox::drop-down {
                width: 0px;
                border: none;
                image: none;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
            }
            QComboBox QAbstractItemView {
                min-width: 34px;
            }
        """

        self.combo_linea_inicio = QComboBox()
        self.combo_linea_inicio.setStyleSheet(combo_style)
        self.combo_linea_inicio.setIconSize(QSize(18, 18))
        self.combo_linea_inicio.setFixedWidth(24)
        self.combo_linea_inicio.addItem(QIcon("gui/iconos/plain_point_left.png"), "", "Plana")
        self.combo_linea_inicio.addItem(QIcon("gui/iconos/round_point_left.png"), "", "Redonda")
        self.combo_linea_inicio.addItem(QIcon("gui/iconos/arrow_point_left.png"), "", "Flecha")
        self.combo_linea_inicio.addItem(QIcon("gui/iconos/circle_point_left.png"), "", "Circulo")
        self.combo_linea_inicio.setToolTip("Punta Inicial: Plana")
        self.combo_linea_inicio.currentIndexChanged.connect(self._on_linea_inicio_changed)
        self.addWidget(self.combo_linea_inicio)

        self.combo_linea_estilo = QComboBox()
        self.combo_linea_estilo.setStyleSheet(combo_style)
        self.combo_linea_estilo.setIconSize(QSize(18, 18))
        self.combo_linea_estilo.setFixedWidth(24)
        self.combo_linea_estilo.addItem(QIcon("gui/iconos/flat.png"), "", "Recta")
        self.combo_linea_estilo.addItem(QIcon("gui/iconos/pointed.png"), "", "Punteada")
        self.combo_linea_estilo.setToolTip("Estilo de Trazo: Recta")
        self.combo_linea_estilo.currentIndexChanged.connect(self._on_linea_estilo_changed)
        self.addWidget(self.combo_linea_estilo)

        self.combo_linea_fin = QComboBox()
        self.combo_linea_fin.setStyleSheet(combo_style)
        self.combo_linea_fin.setIconSize(QSize(18, 18))
        self.combo_linea_fin.setFixedWidth(24)
        self.combo_linea_fin.addItem(QIcon("gui/iconos/plain_point_right.png"), "", "Plana")
        self.combo_linea_fin.addItem(QIcon("gui/iconos/round_point_right.png"), "", "Redonda")
        self.combo_linea_fin.addItem(QIcon("gui/iconos/arrow_point_right.png"), "", "Flecha")
        self.combo_linea_fin.addItem(QIcon("gui/iconos/circle_point_right.png"), "", "Circulo")
        self.combo_linea_fin.setToolTip("Punta Final: Plana")
        self.combo_linea_fin.currentIndexChanged.connect(self._on_linea_fin_changed)
        self.addWidget(self.combo_linea_fin)

        self.addSeparator()

        # 11. Opciones de Formas Geométrica
        self.lbl_formas = QLabel()
        self.lbl_formas.setPixmap(QIcon("gui/iconos/shapes.png").pixmap(QSize(24, 24)))
        self.lbl_formas.setToolTip("Formas")
        self.lbl_formas.setContentsMargins(4, 0, 2, 0)
        self.addWidget(self.lbl_formas)

        self.chk_formas_redondeado = QCheckBox("Redondeado")
        self.chk_formas_redondeado.setStyleSheet("font-size: 11px;")
        self.chk_formas_redondeado.setToolTip("Esquinas redondeadas para Rectángulos y Triángulos")
        self.addWidget(self.chk_formas_redondeado)

        self.combo_forma_estilo = QComboBox()
        self.combo_forma_estilo.setStyleSheet(combo_style)
        self.combo_forma_estilo.setIconSize(QSize(18, 18))
        self.combo_forma_estilo.setFixedWidth(24)
        self.combo_forma_estilo.addItem(QIcon("gui/iconos/shape.png"), "", "Solo Borde")
        self.combo_forma_estilo.addItem(QIcon("gui/iconos/shapes_solid.png"), "", "Forma Sólida")
        self.combo_forma_estilo.addItem(QIcon("gui/iconos/shapes_colored.png"), "", "Borde y Relleno")
        self.combo_forma_estilo.setToolTip("Estilo de Forma: Solo Borde")
        self.combo_forma_estilo.currentIndexChanged.connect(self._on_forma_estilo_changed)
        self.addWidget(self.combo_forma_estilo)

        self.combo_forma_tipo = QComboBox()
        self.combo_forma_tipo.setStyleSheet(combo_style)
        self.combo_forma_tipo.setIconSize(QSize(18, 18))
        self.combo_forma_tipo.setFixedWidth(24)
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_rectangle.png"), "", "Rectángulo")
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_triangle.png"), "", "Triángulo")
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_circle.png"), "", "Elipse")
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_cloud.png"), "", "Nube")
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_heart.png"), "", "Corazón")
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_chat.png"), "", "Chat")
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_star.png"), "", "Estrella")
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_flower.png"), "", "Flor")
        self.combo_forma_tipo.setToolTip("Tipo de Forma: Rectángulo")
        self.combo_forma_tipo.currentIndexChanged.connect(self._on_forma_tipo_changed)
        self.addWidget(self.combo_forma_tipo)

        self.addSeparator()

        # 12. Opciones de Difuminar / Blur
        self.lbl_blur = QLabel()
        self.lbl_blur.setPixmap(QIcon("gui/iconos/blur.png").pixmap(QSize(24, 24)))
        self.lbl_blur.setToolTip("Difuminar")
        self.lbl_blur.setContentsMargins(4, 0, 2, 0)
        self.addWidget(self.lbl_blur)

        settings = QSettings("PaintNotNet", "PaintNotNet")
        saved_mode = settings.value("blur_modo", "Pixelado")
        if saved_mode == "Gausiano":
            saved_mode = "Gaussiano"
        saved_val = int(settings.value("blur_val", 0))

        self.combo_blur_modo = QComboBox()
        self.combo_blur_modo.setStyleSheet("font-size: 11px; padding: 1px;")
        self.combo_blur_modo.setFixedWidth(100)
        self.combo_blur_modo.setFixedHeight(22)
        self.combo_blur_modo.addItem("Pixelado", "Pixelado")
        self.combo_blur_modo.addItem("Gaussiano", "Gaussiano")
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
        self.lbl_blur_val.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.lbl_blur_val.setFixedWidth(36)
        self.lbl_blur_val.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.addWidget(self.lbl_blur_val)

        if main_window:
            self.conectar_acciones()

        self.actualizar_estilo_tema()

    def actualizar_estilo_tema(self):
        from core.theme import ThemeManager
        tm = ThemeManager()
        is_dark = (tm.resolver_nombre_tema(tm.current_theme) == "Oscuro")
        suf = "_d.png" if is_dark else "_l.png"

        if hasattr(self, 'combo_linea_inicio'):
            self.combo_linea_inicio.setItemIcon(0, QIcon(f"gui/iconos/plain_point_left{suf}"))
            self.combo_linea_inicio.setItemIcon(1, QIcon(f"gui/iconos/round_point_left{suf}"))
            self.combo_linea_inicio.setItemIcon(2, QIcon(f"gui/iconos/arrow_point_left{suf}"))
            self.combo_linea_inicio.setItemIcon(3, QIcon(f"gui/iconos/circle_point_left{suf}"))

        if hasattr(self, 'combo_linea_estilo'):
            self.combo_linea_estilo.setItemIcon(0, QIcon(f"gui/iconos/flat{suf}"))
            self.combo_linea_estilo.setItemIcon(1, QIcon(f"gui/iconos/pointed{suf}"))

        if hasattr(self, 'combo_linea_fin'):
            self.combo_linea_fin.setItemIcon(0, QIcon(f"gui/iconos/plain_point_right{suf}"))
            self.combo_linea_fin.setItemIcon(1, QIcon(f"gui/iconos/round_point_right{suf}"))
            self.combo_linea_fin.setItemIcon(2, QIcon(f"gui/iconos/arrow_point_right{suf}"))
            self.combo_linea_fin.setItemIcon(3, QIcon(f"gui/iconos/circle_point_right{suf}"))

        if hasattr(self, 'combo_forma_estilo'):
            self.combo_forma_estilo.setItemIcon(0, QIcon(f"gui/iconos/shape{suf}"))

    def _on_blur_changed(self, *args):
        val = self.slider_blur.value()
        modo = self.combo_blur_modo.currentData() or "Pixelado"
        self.lbl_blur_val.setText(f"{val}%")

        settings = QSettings("PaintNotNet", "PaintNotNet")
        settings.setValue("blur_modo", modo)
        settings.setValue("blur_val", val)

        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            canvas = self.main_window.lienzo
            if hasattr(canvas, 'selection_engine') and canvas.selection_engine.has_selection():
                canvas.actualizar_preview_difuminado_seleccion(modo, val)
            else:
                canvas.update()

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
        from tools.eraser import EraserTool

        uses_tolerance = isinstance(tool_obj, (BucketTool, MagicWandTool))
        uses_smoothness = isinstance(tool_obj, (BrushTool, LineTool, EraserTool))
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
        if uses_line and self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.linea_cap_inicio = self.combo_linea_inicio.currentData() or "Plana"
            self.main_window.lienzo.linea_estilo = self.combo_linea_estilo.currentData() or "Recta"
            self.main_window.lienzo.linea_cap_fin = self.combo_linea_fin.currentData() or "Plana"

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

    def _on_crop_clicked(self):
        from core.i18n import t
        canvas = None
        if self.main_window and hasattr(self.main_window, 'lienzo'):
            canvas = self.main_window.lienzo
        if canvas and hasattr(canvas, 'recortar_a_seleccion'):
            ok = canvas.recortar_a_seleccion()
            if not ok:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self.main_window,
                    t("Sin selección"),
                    t("No hay selección activa para recortar.")
                )

    def _on_grosor_changed(self, val):
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.ancho_pincel = val
            self.main_window.lienzo.grosor_pincel = val
            self.main_window.lienzo.update()
        self.grosor_changed.emit(val)

    def _on_tolerancia_changed(self, val):
        self.lbl_tol_val.setText(f"{val}%")
        canvas = None
        if self.main_window:
            canvas = getattr(self.main_window, 'lienzo', getattr(self.main_window, 'canvas', None))
        if canvas:
            canvas.tolerancia = val
            if hasattr(canvas, 'active_tool_obj') and hasattr(canvas.active_tool_obj, 'update_tolerance'):
                canvas.active_tool_obj.update_tolerance(canvas, val)

    def _on_suavizado_changed(self, val):
        self.lbl_suav_val.setText(f"{val}%")
        # suavizado_pincel es bool: cualquier valor > 0 activa antialiasing
        suav_bool = val > 0
        if self.main_window and hasattr(self.main_window, 'tab_widget'):
            for i in range(self.main_window.tab_widget.count()):
                area = self.main_window.tab_widget.widget(i)
                canvas = area.widget() if (area and hasattr(area, 'widget')) else area
                if canvas and hasattr(canvas, 'suavizado_pincel'):
                    canvas.suavizado_pincel = suav_bool
        elif self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.suavizado_pincel = suav_bool

    def _on_zoom_changed(self):
        txt = self.combo_zoom.currentText().replace("%", "").strip()
        try:
            val = int(txt)
            val = max(1, min(3000, val))
            if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
                self.main_window.lienzo.set_zoom(val / 100.0)
        except ValueError:
            pass

    def sync_zoom_from_canvas(self, scale_factor):
        """Sincroniza el combo de zoom con el valor actual del canvas."""
        pct = int(round(scale_factor * 100))
        txt = f"{pct}%"
        if hasattr(self, 'combo_zoom') and self.combo_zoom.currentText() != txt:
            self.combo_zoom.blockSignals(True)
            self.combo_zoom.setCurrentText(txt)
            self.combo_zoom.blockSignals(False)

    def _on_linea_inicio_changed(self, idx):
        from core.i18n import t
        val = self.combo_linea_inicio.itemData(idx) or "Plana"
        self.combo_linea_inicio.setToolTip(f"{t('Punta Inicial:')} {t(val)}")
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.linea_cap_inicio = val
            self.main_window.lienzo.update()

    def _on_linea_estilo_changed(self, idx):
        from core.i18n import t
        val = self.combo_linea_estilo.itemData(idx) or "Recta"
        self.combo_linea_estilo.setToolTip(f"{t('Estilo de Trazo:')} {t(val)}")
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.linea_estilo = val
            self.main_window.lienzo.update()

    def _on_linea_fin_changed(self, idx):
        from core.i18n import t
        val = self.combo_linea_fin.itemData(idx) or "Plana"
        self.combo_linea_fin.setToolTip(f"{t('Punta Final:')} {t(val)}")
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.linea_cap_fin = val
            self.main_window.lienzo.update()

    def _on_forma_tipo_changed(self, idx):
        from core.i18n import t
        val = self.combo_forma_tipo.itemData(idx) or "Rectángulo"
        self.combo_forma_tipo.setToolTip(f"{t('Tipo de Forma:')} {t(val)}")

    def _on_forma_estilo_changed(self, idx):
        from core.i18n import t
        val = self.combo_forma_estilo.itemData(idx) or "Solo Borde"
        self.combo_forma_estilo.setToolTip(f"{t('Estilo de Forma:')} {t(val)}")

    def retraducir_toolbar(self):
        from core.i18n import t
        self.action_nueva_pestana.setToolTip(f"{t('Nuevo')} (Ctrl+N)")
        self.action_abrir.setToolTip(f"{t('Abrir...')} (Ctrl+O)")
        self.action_guardar.setToolTip(f"{t('Guardar')} (Ctrl+S)")
        self.action_cortar.setToolTip(f"{t('Cortar')} (Ctrl+X)")
        self.action_copiar.setToolTip(f"{t('Copiar')} (Ctrl+C)")
        self.action_pegar.setToolTip(f"{t('Pegar')} (Ctrl+V)")
        if hasattr(self, 'action_crop'):
            self.action_crop.setToolTip(t('Recortar a selección'))
        if hasattr(self, 'lbl_grosor'):
            self.lbl_grosor.setText(f" {t('Grosor:')} ")
        if hasattr(self, 'lbl_tol'):
            self.lbl_tol.setText(f" {t('Tolerancia:')} ")
        if hasattr(self, 'lbl_suav'):
            self.lbl_suav.setText(f" {t('Suavizado:')} ")
        if hasattr(self, 'lbl_zoom'):
            self.lbl_zoom.setToolTip(t("Zoom"))
        if hasattr(self, 'lbl_linea'):
            self.lbl_linea.setToolTip(t("Línea"))
        if hasattr(self, 'lbl_formas'):
            self.lbl_formas.setToolTip(t("Formas"))
        if hasattr(self, 'lbl_blur'):
            self.lbl_blur.setToolTip(t("Difuminar"))
        if hasattr(self, 'chk_formas_redondeado'):
            self.chk_formas_redondeado.setText(t("Redondeado"))

        # Actualizar tooltips traducidos de los combos
        val_ini = self.combo_linea_inicio.currentData() or "Plana"
        self.combo_linea_inicio.setToolTip(f"{t('Punta Inicial:')} {t(val_ini)}")
        val_est = self.combo_linea_estilo.currentData() or "Recta"
        self.combo_linea_estilo.setToolTip(f"{t('Estilo de Trazo:')} {t(val_est)}")
        val_fin = self.combo_linea_fin.currentData() or "Plana"
        self.combo_linea_fin.setToolTip(f"{t('Punta Final:')} {t(val_fin)}")

        val_f_est = self.combo_forma_estilo.currentData() or "Solo Borde"
        self.combo_forma_estilo.setToolTip(f"{t('Estilo de Forma:')} {t(val_f_est)}")
        val_f_tipo = self.combo_forma_tipo.currentData() or "Rectángulo"
        self.combo_forma_tipo.setToolTip(f"{t('Tipo de Forma:')} {t(val_f_tipo)}")

        if hasattr(self, 'combo_blur_modo'):
            self.combo_blur_modo.blockSignals(True)
            self.combo_blur_modo.setItemText(0, t("Pixelado"))
            self.combo_blur_modo.setItemText(1, t("Gaussiano"))
            self.combo_blur_modo.blockSignals(False)

