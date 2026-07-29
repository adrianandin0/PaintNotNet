from PyQt6.QtWidgets import QToolBar, QWidget, QHBoxLayout, QLabel, QSpinBox, QSlider, QComboBox, QStyle
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QSize, pyqtSignal


class TopToolBarWidget(QToolBar):
    grosor_changed = pyqtSignal(int)
    tolerancia_changed = pyqtSignal(int)

    def __init__(self, main_window=None):
        super().__init__("Barra de Herramientas General", main_window)
        self.main_window = main_window
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(QSize(18, 18))
        self.setStyleSheet("QToolBar { spacing: 6px; padding: 2px; }")

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

        # 7. Selector de Tolerancia Global (Acortado)
        self.lbl_tol = QLabel(" Tolerancia: ")
        self.lbl_tol.setStyleSheet("font-size: 11px; font-weight: bold;")
        self.addWidget(self.lbl_tol)

        self.slider_tol = QSlider(Qt.Orientation.Horizontal)
        self.slider_tol.setRange(0, 100)
        self.slider_tol.setValue(32)
        self.slider_tol.setFixedWidth(75)
        self.slider_tol.valueChanged.connect(self._on_tolerancia_changed)
        self.addWidget(self.slider_tol)

        self.lbl_tol_val = QLabel("32%")
        self.lbl_tol_val.setStyleSheet("font-size: 11px; font-weight: bold; color: #888888;")
        self.addWidget(self.lbl_tol_val)

        self.addSeparator()

        # 8. Selector de Suavizado Global (Acortado)
        self.lbl_suav = QLabel(" Suavizado: ")
        self.lbl_suav.setStyleSheet("font-size: 11px; font-weight: bold;")
        self.addWidget(self.lbl_suav)

        self.slider_suav = QSlider(Qt.Orientation.Horizontal)
        self.slider_suav.setRange(0, 100)
        self.slider_suav.setValue(100)
        self.slider_suav.setFixedWidth(75)
        self.slider_suav.valueChanged.connect(self._on_suavizado_changed)
        self.addWidget(self.slider_suav)

        self.lbl_suav_val = QLabel("100%")
        self.lbl_suav_val.setStyleSheet("font-size: 11px; font-weight: bold; color: #888888;")
        self.addWidget(self.lbl_suav_val)

        self.addSeparator()

        # 9. Selector de Zoom (Desplegable y editable 1% a 300%)
        self.lbl_zoom = QLabel(" Zoom: ")
        self.lbl_zoom.setStyleSheet("font-size: 11px; font-weight: bold;")
        self.addWidget(self.lbl_zoom)

        self.combo_zoom = QComboBox()
        self.combo_zoom.setEditable(True)
        self.combo_zoom.setFixedWidth(75)
        self.combo_zoom.addItems(["10%", "25%", "50%", "75%", "100%", "125%", "150%", "200%", "300%"])
        self.combo_zoom.setCurrentText("100%")
        self.combo_zoom.setStyleSheet("font-size: 11px; padding: 1px;")
        self.combo_zoom.activated.connect(self._on_zoom_changed)
        if self.combo_zoom.lineEdit():
            self.combo_zoom.lineEdit().editingFinished.connect(self._on_zoom_changed)
        self.addWidget(self.combo_zoom)

        self.addSeparator()

        # 10. Opciones de Línea (Inicio, Estilo, Fin - Compactos con Solo Ícono)
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

        # Combo Inicio (Solo Icono)
        self.combo_linea_inicio = QComboBox()
        self.combo_linea_inicio.setStyleSheet(combo_style)
        self.combo_linea_inicio.setIconSize(QSize(18, 18))
        self.combo_linea_inicio.setFixedWidth(38)
        self.combo_linea_inicio.addItem(QIcon("gui/iconos/rectangle.png"), "", "Plana")
        self.combo_linea_inicio.addItem(QIcon("gui/iconos/line_circle_left.png"), "", "Redonda")
        self.combo_linea_inicio.addItem(QIcon("gui/iconos/arrow_left.png"), "", "Flecha")
        self.combo_linea_inicio.addItem(QIcon("gui/iconos/circle.png"), "", "Circulo")
        self.combo_linea_inicio.setToolTip("Punta Inicial: Plana")
        if self.combo_linea_inicio.view():
            self.combo_linea_inicio.view().setFixedWidth(34)
        self.combo_linea_inicio.currentIndexChanged.connect(self._on_linea_inicio_changed)
        self.addWidget(self.combo_linea_inicio)

        # Combo Estilo (Solo Icono)
        self.combo_linea_estilo = QComboBox()
        self.combo_linea_estilo.setStyleSheet(combo_style)
        self.combo_linea_estilo.setIconSize(QSize(18, 18))
        self.combo_linea_estilo.setFixedWidth(38)
        self.combo_linea_estilo.addItem(QIcon("gui/iconos/flat.png"), "", "Recta")
        self.combo_linea_estilo.addItem(QIcon("gui/iconos/pointed.png"), "", "Punteada")
        self.combo_linea_estilo.setToolTip("Estilo de Trazo: Recta")
        if self.combo_linea_estilo.view():
            self.combo_linea_estilo.view().setFixedWidth(34)
        self.combo_linea_estilo.currentIndexChanged.connect(self._on_linea_estilo_changed)
        self.addWidget(self.combo_linea_estilo)

        # Combo Fin (Solo Icono)
        self.combo_linea_fin = QComboBox()
        self.combo_linea_fin.setStyleSheet(combo_style)
        self.combo_linea_fin.setIconSize(QSize(18, 18))
        self.combo_linea_fin.setFixedWidth(38)
        self.combo_linea_fin.addItem(QIcon("gui/iconos/rectangle.png"), "", "Plana")
        self.combo_linea_fin.addItem(QIcon("gui/iconos/line_circle_right.png"), "", "Redonda")
        self.combo_linea_fin.addItem(QIcon("gui/iconos/arrow_right.png"), "", "Flecha")
        self.combo_linea_fin.addItem(QIcon("gui/iconos/circle.png"), "", "Circulo")
        self.combo_linea_fin.setToolTip("Punta Final: Plana")
        if self.combo_linea_fin.view():
            self.combo_linea_fin.view().setFixedWidth(34)
        self.combo_linea_fin.currentIndexChanged.connect(self._on_linea_fin_changed)
        self.addWidget(self.combo_linea_fin)

        if main_window:
            self.conectar_acciones()

    def update_tool_states(self, tool_obj):
        if not tool_obj:
            return

        from tools.bucket import BucketTool
        from tools.magic_wand import MagicWandTool
        from tools.brush import BrushTool
        from tools.zoom import ZoomTool
        from tools.line import LineTool

        uses_tolerance = isinstance(tool_obj, (BucketTool, MagicWandTool))
        uses_smoothness = isinstance(tool_obj, (BrushTool, LineTool))
        uses_zoom = isinstance(tool_obj, ZoomTool)
        uses_line = isinstance(tool_obj, LineTool)

        # Tolerancia
        self.lbl_tol.setEnabled(uses_tolerance)
        self.slider_tol.setEnabled(uses_tolerance)
        self.lbl_tol_val.setEnabled(uses_tolerance)
        col_tol = "#64B4FF" if uses_tolerance else "#888888"
        self.lbl_tol_val.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {col_tol};")

        # Suavizado
        self.lbl_suav.setEnabled(uses_smoothness)
        self.slider_suav.setEnabled(uses_smoothness)
        self.lbl_suav_val.setEnabled(uses_smoothness)
        col_suav = "#64B4FF" if uses_smoothness else "#888888"
        self.lbl_suav_val.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {col_suav};")

        # Zoom
        self.lbl_zoom.setEnabled(uses_zoom)
        self.combo_zoom.setEnabled(uses_zoom)

        # Línea (Deshabilitadas cuando no es LineTool)
        self.lbl_linea.setEnabled(uses_line)
        self.combo_linea_inicio.setEnabled(uses_line)
        self.combo_linea_estilo.setEnabled(uses_line)
        self.combo_linea_fin.setEnabled(uses_line)
        col_linea = "#FFFFFF" if uses_line else "#888888"
        self.lbl_linea.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {col_linea};")

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
            if hasattr(self.main_window.lienzo.active_tool_obj, 'update_tolerance'):
                self.main_window.lienzo.active_tool_obj.update_tolerance(self.main_window.lienzo, val)
            self.main_window.lienzo.update()
        self.tolerancia_changed.emit(val)

    def _on_suavizado_changed(self, val):
        self.lbl_suav_val.setText(f"{val}%")
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            canvas = self.main_window.lienzo
            if val == 0:
                canvas.suavizado_pincel = False
                canvas.opacidad_pincel = 255
            else:
                canvas.suavizado_pincel = True
                canvas.opacidad_pincel = int(255 * (val / 100.0))
            canvas.update()

    def _on_zoom_changed(self):
        texto = self.combo_zoom.currentText().replace("%", "").strip()
        try:
            val = int(texto)
            val = max(1, min(300, val))
        except ValueError:
            val = 100

        scale = val / 100.0
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.set_zoom(scale)

        self.combo_zoom.blockSignals(True)
        self.combo_zoom.setEditText(f"{val}%")
        self.combo_zoom.blockSignals(False)

    def sync_zoom_from_canvas(self, scale_factor):
        val = int(round(scale_factor * 100.0))
        self.combo_zoom.blockSignals(True)
        self.combo_zoom.setEditText(f"{val}%")
        self.combo_zoom.blockSignals(False)

    def _on_linea_inicio_changed(self, idx):
        val = self.combo_linea_inicio.currentData() or "Plana"
        self.combo_linea_inicio.setToolTip(f"Punta Inicial: {val}")
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.linea_cap_inicio = val
            self.main_window.lienzo.update()

    def _on_linea_estilo_changed(self, idx):
        val = self.combo_linea_estilo.currentData() or "Recta"
        self.combo_linea_estilo.setToolTip(f"Estilo de Trazo: {val}")
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.linea_estilo = val
            self.main_window.lienzo.update()

    def _on_linea_fin_changed(self, idx):
        val = self.combo_linea_fin.currentData() or "Plana"
        self.combo_linea_fin.setToolTip(f"Punta Final: {val}")
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.linea_cap_fin = val
            self.main_window.lienzo.update()
