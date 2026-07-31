import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QScrollArea, QDockWidget, QTabWidget
from PyQt6.QtGui import QColor, QCloseEvent, QShortcut, QKeySequence, QIcon
from PyQt6.QtCore import Qt, QSettings, QTimer

if getattr(sys, 'frozen', False):
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    os.chdir(base_dir)

from core.canvas import CanvasWidget
from gui.tool_panel import ToolPanelWidget
from gui.color_panel import ColorPanelWidget
from gui.advanced_color_panel import AdvancedColorPanelWidget
from gui.text_panel import TextPanelWidget
from gui.layers_panel import LayersPanelWidget
from gui.history_panel import HistoryPanelWidget
from gui.top_toolbar import TopToolBarWidget

from gui.menu_archivo import MenuArchivo
from gui.menu_editar import MenuEditar
from gui.menu_imagen import MenuImagen
from gui.menu_opciones import MenuOpciones
from gui.menu_ver import MenuVer
from gui.menu_ajustes import MenuAjustes
from gui.menu_acerca import MenuAcerca

class PaintNotNet(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 50, 1804, 1015)
        self.setWindowIcon(QIcon("gui/iconos/paintdotnet.ico"))
        self.archivo_actual = None
        self.lienzo_modificado = False

        self.setDockOptions(QMainWindow.DockOption.AllowNestedDocks | QMainWindow.DockOption.AnimatedDocks)

        # ==========================================
        # DOCKS LATERALES IZQUIERDOS
        # ==========================================
        self.tools_dock = QDockWidget(self)
        self.tools_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.tool_panel = ToolPanelWidget(main_window=self)
        self.tools_dock.setWidget(self.tool_panel)
        self.tools_dock.setFixedHeight(330)
        self.tools_dock.setFixedWidth(82)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.tools_dock)

        self.color_dock = QDockWidget("", self)
        self.color_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.color_panel = ColorPanelWidget(main_window=self)
        self.color_dock.setWidget(self.color_panel)
        self.color_dock.setFixedHeight(275)
        self.color_dock.setFixedWidth(82)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.color_dock)

        self.splitDockWidget(self.tools_dock, self.color_dock, Qt.Orientation.Vertical)

        # ==========================================
        # DOCKS LATERALES DERECHOS (Title Case)
        # ==========================================
        # 1. Dock de Texto
        self.text_dock = QDockWidget("Texto", self)
        self.text_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.text_panel = TextPanelWidget(main_window=self)
        self.text_dock.setWidget(self.text_panel)
        self.text_dock.setFixedWidth(148)
        self.text_dock.setFixedHeight(252)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.text_dock)

        # 2. Dock de Capas
        self.layers_dock = QDockWidget("Capas", self)
        self.layers_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.layers_panel = LayersPanelWidget(main_window=self)
        self.layers_dock.setWidget(self.layers_panel)
        self.layers_dock.setFixedWidth(148)
        self.layers_dock.setFixedHeight(260)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.layers_dock)
        self.splitDockWidget(self.text_dock, self.layers_dock, Qt.Orientation.Vertical)

        # 3. Dock de Historial
        self.history_dock = QDockWidget("Historial", self)
        self.history_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.history_panel = HistoryPanelWidget(main_window=self)
        self.history_dock.setWidget(self.history_panel)
        self.history_dock.setFixedWidth(148)
        self.history_dock.setFixedHeight(180)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.history_dock)
        self.splitDockWidget(self.layers_dock, self.history_dock, Qt.Orientation.Vertical)

        # 4. Dock de Color
        self.advanced_color_dock = QDockWidget("Color", self)
        self.advanced_color_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.advanced_color_panel = AdvancedColorPanelWidget(main_window=self)
        self.advanced_color_dock.setWidget(self.advanced_color_panel)
        self.advanced_color_dock.setFixedWidth(148)
        self.advanced_color_dock.setFixedHeight(210)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.advanced_color_dock)
        self.splitDockWidget(self.history_dock, self.advanced_color_dock, Qt.Orientation.Vertical)

        import sys
        ico_path = "gui/paintdotnet.ico" if sys.platform == "win32" and os.path.exists("gui/paintdotnet.ico") else "gui/icono.png"
        self.setWindowIcon(QIcon(ico_path))

        # ==========================================
        # ÁREA CENTRAL MULTI-PESTAÑA (TABBED MDI)
        # ==========================================
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #2D2D2D;
            }
            QTabBar::tab {
                background: #353535;
                color: #B0B0B0;
                border: 1px solid #444444;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 5px 8px 5px 12px;
                margin-right: 3px;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background: #2D2D2D;
                color: #FFFFFF;
                border-color: #0078D7;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #404040;
                color: #FFFFFF;
            }
        """)

        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)
        self.tab_widget.tabBarDoubleClicked.connect(self._on_tab_double_clicked)

        self.setCentralWidget(self.tab_widget)

        # --- CONEXIONES DIRECTAS: PANELES -> CANVAS ---
        self.color_panel.color_primario_cambiado.connect(self._on_color_primario_changed)
        self.color_panel.color_secundario_cambiado.connect(self._on_color_secundario_changed)

        self.advanced_color_panel.color_primario_cambiado.connect(self._on_color_primario_changed)
        self.advanced_color_panel.color_secundario_cambiado.connect(self._on_color_secundario_changed)
        self.text_panel.text_config_changed.connect(lambda cfg: self.canvas.actualizar_config_texto(cfg) if hasattr(self, 'canvas') and self.canvas else None)

        from core.i18n import t
        # Crear primera pestaña por defecto
        self.crear_nueva_pestana(800, 600, transparent=False, titulo=t("Sin Título"))

        # ==========================================
        # RESTAURAR PERFIL DE USUARIO SI EXISTE
        # ==========================================
        self._cargar_perfil_usuario()

        # ==========================================
        # MENÚS Y ATAJOS GLOBALES
        # ==========================================
        self.crear_menus()
        if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'active_tool_obj'):
            self.top_toolbar.update_tool_states(self.canvas.active_tool_obj)
        self.actualizar_titulo_ventana()

        self.shortcut_esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.shortcut_esc.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_esc.activated.connect(self._ejecutar_escape_global)

    def _cargar_perfil_usuario(self):
        settings = QSettings("PaintNotNet", "PaintNotNet")
        if settings.value("save_on_close", True, type=bool):
            custom_hexs = settings.value("custom_colors", None)
            if custom_hexs and isinstance(custom_hexs, list):
                for idx, hex_val in enumerate(custom_hexs[:12]):
                    if hex_val:
                        c = QColor(hex_val)
                        if c.isValid():
                            self.color_panel.custom_colors[idx] = c
                            self.color_panel.botones_custom[idx].set_color(c)

    def _on_color_primario_changed(self, color):
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.color_primario = color
        if hasattr(self, 'color_panel') and self.color_panel:
            if self.color_panel.color_primario != color:
                self.color_panel.color_primario = color
                if hasattr(self.color_panel, 'muestra_container'):
                    self.color_panel.muestra_container.set_colores(color, self.color_panel.color_secundario, self.color_panel.modo_color)
        if hasattr(self, 'advanced_color_panel') and self.advanced_color_panel:
            if self.advanced_color_panel.color_primario != color:
                self.advanced_color_panel.color_primario = color
                self.advanced_color_panel._actualizar_interfaz_desde_color(color)

    def _on_color_secundario_changed(self, color):
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.color_secundario = color
        if hasattr(self, 'color_panel') and self.color_panel:
            if self.color_panel.color_secundario != color:
                self.color_panel.color_secundario = color
                if hasattr(self.color_panel, 'muestra_container'):
                    self.color_panel.muestra_container.set_colores(self.color_panel.color_primario, color, self.color_panel.modo_color)
        if hasattr(self, 'advanced_color_panel') and self.advanced_color_panel:
            if self.advanced_color_panel.color_secundario != color:
                self.advanced_color_panel.color_secundario = color
                if hasattr(self.advanced_color_panel, 'muestras'):
                    self.advanced_color_panel.muestras.set_colores(self.advanced_color_panel.color_primario, color, self.advanced_color_panel.modo_color)

    def crear_nueva_pestana(self, width=800, height=600, transparent=True, ruta=None, titulo=None):
        area_scroll = QScrollArea()
        area_scroll.setStyleSheet("QScrollArea { background-color: #2D2D2D; border: none; }")
        area_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        area_scroll.setWidgetResizable(False)

        canvas = CanvasWidget(width, height)
        if not transparent:
            canvas.layer_mgr.buffer.fill(Qt.GlobalColor.white)

        canvas.main_window = self
        canvas.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        canvas.callback_modificado = lambda: self.marcar_modificado_pestana(canvas)
        canvas.archivo_actual = ruta

        if hasattr(self, 'color_panel'):
            canvas.color_primario = self.color_panel.color_primario
            canvas.color_secundario = self.color_panel.color_secundario

        area_scroll.setWidget(canvas)
        area_scroll.viewport().installEventFilter(canvas)
        canvas._ajustar_tamano_widget(width, height)

        if not titulo:
            if ruta:
                titulo = os.path.basename(ruta)
            else:
                from core.i18n import t
                num = self.tab_widget.count() + 1
                base_st = t("Sin Título")
                titulo = f"{base_st} {num}" if self.tab_widget.count() > 0 else base_st

        idx = self.tab_widget.addTab(area_scroll, titulo)
        self.tab_widget.setCurrentIndex(idx)
        return canvas

    def _on_tab_changed(self, index):
        if index < 0 or index >= self.tab_widget.count():
            return

        area_scroll = self.tab_widget.widget(index)
        if area_scroll:
            canvas = area_scroll.widget()
            self.canvas = canvas
            self.lienzo = canvas

            if hasattr(self, 'layers_panel'):
                self.layers_panel.set_canvas(canvas)

            if hasattr(self, 'history_panel'):
                self.history_panel.set_canvas(canvas)

            if hasattr(self, 'color_panel'):
                canvas.color_primario = self.color_panel.color_primario
                canvas.color_secundario = self.color_panel.color_secundario

            self.actualizar_titulo_ventana()

    def _on_tab_close_requested(self, index):
        if index < 0 or index >= self.tab_widget.count():
            return

        if self.tab_widget.count() <= 1:
            if not self.cerrar_pestana_confirmada(index):
                return
            area_scroll = self.tab_widget.widget(index)
            canvas = area_scroll.widget() if area_scroll else getattr(self, 'canvas', None)
            if canvas:
                canvas.crear_nuevo_lienzo(800, 600, es_transparente=True)
                canvas.archivo_actual = None
                canvas.lienzo_modificado = False
            self.actualizar_titulo_pestana(index)
            self.actualizar_titulo_ventana()
            return

        if self.cerrar_pestana_confirmada(index):
            area_scroll = self.tab_widget.widget(index)
            if area_scroll and hasattr(area_scroll, 'widget'):
                canvas = area_scroll.widget()
                if canvas and hasattr(canvas, 'selection_engine'):
                    canvas.selection_engine.clear_selection()

            self.tab_widget.removeTab(index)

            new_index = self.tab_widget.currentIndex()
            if new_index >= 0:
                self._on_tab_changed(new_index)

            if area_scroll:
                area_scroll.deleteLater()

    def cerrar_pestana_confirmada(self, index):
        area_scroll = self.tab_widget.widget(index)
        if not area_scroll:
            return True
        canvas = area_scroll.widget()
        if getattr(canvas, 'lienzo_modificado', False):
            self.tab_widget.setCurrentIndex(index)
            return self.menu_archivo.confirmar_descarte_cambios(target_canvas=canvas)
        return True

    def marcar_modificado_pestana(self, canvas=None):
        if not canvas:
            canvas = self.canvas
        if canvas:
            canvas.lienzo_modificado = True
            idx = self._find_tab_index_for_canvas(canvas)
            if idx >= 0:
                self.actualizar_titulo_pestana(idx)
        self.actualizar_titulo_ventana()
        if hasattr(self, 'layers_panel'):
            self.layers_panel.actualizar_thumbnails()

    def _on_tab_double_clicked(self, index):
        if index < 0 or index >= self.tab_widget.count():
            return
        area_scroll = self.tab_widget.widget(index)
        if not area_scroll:
            return
        canvas = area_scroll.widget()
        nombre_actual = getattr(canvas, 'nombre_personalizado', None)
        if not nombre_actual:
            if canvas.archivo_actual:
                nombre_actual = os.path.splitext(os.path.basename(canvas.archivo_actual))[0]
            else:
                nombre_actual = self.tab_widget.tabText(index).replace(" *", "")

        from PyQt6.QtWidgets import QInputDialog
        nuevo_nombre, ok = QInputDialog.getText(
            self, "Renombrar Pestaña",
            "Ingrese el nombre del documento:",
            text=nombre_actual
        )
        if ok and nuevo_nombre.strip():
            canvas.nombre_personalizado = nuevo_nombre.strip()
            self.actualizar_titulo_pestana(index)
            self.actualizar_titulo_ventana()

    def actualizar_titulo_pestana(self, index):
        area_scroll = self.tab_widget.widget(index)
        if not area_scroll:
            return
        canvas = area_scroll.widget()
        from core.i18n import t
        if getattr(canvas, 'nombre_personalizado', None):
            nombre = canvas.nombre_personalizado
        elif canvas.archivo_actual:
            nombre = os.path.basename(canvas.archivo_actual)
        else:
            nombre = t("Sin Título")
        asterisco = " *" if getattr(canvas, 'lienzo_modificado', False) else ""
        self.tab_widget.setTabText(index, f"{nombre}{asterisco}")

    def _find_tab_index_for_canvas(self, canvas):
        for i in range(self.tab_widget.count()):
            area = self.tab_widget.widget(i)
            if area and area.widget() == canvas:
                return i
        return -1

    def actualizar_titulo_ventana(self):
        if hasattr(self, 'canvas') and self.canvas:
            from core.i18n import t
            if getattr(self.canvas, 'nombre_personalizado', None):
                nombre = self.canvas.nombre_personalizado
            elif self.canvas.archivo_actual:
                nombre = self.canvas.archivo_actual
            else:
                nombre = t("Sin Título")
            asterisco = " *" if getattr(self.canvas, 'lienzo_modificado', False) else ""
            self.setWindowTitle(f"PaintNotNet - {nombre}{asterisco}")
            idx = self._find_tab_index_for_canvas(self.canvas)
            if idx >= 0:
                self.actualizar_titulo_pestana(idx)

    def marcar_modificado(self):
        self.marcar_modificado_pestana()

    def retraducir_ui(self):
        from core.i18n import t
        if hasattr(self, 'menu_archivo'):
            self.menu_archivo.retraducir_menu()
        if hasattr(self, 'menu_editar'):
            self.menu_editar.retraducir_menu()
        if hasattr(self, 'menu_imagen'):
            self.menu_imagen.retraducir_menu()
        if hasattr(self, 'menu_opciones'):
            self.menu_opciones.retraducir_menu()
        if hasattr(self, 'menu_ver'):
            self.menu_ver.retraducir_menu()
        if hasattr(self, 'menu_ajustes'):
            self.menu_ajustes.retraducir_menu()
        if hasattr(self, 'menu_acerca'):
            self.menu_acerca.retraducir_menu()

        if hasattr(self, 'top_toolbar') and hasattr(self.top_toolbar, 'retraducir_toolbar'):
            self.top_toolbar.retraducir_toolbar()

        if hasattr(self, 'tool_panel') and hasattr(self.tool_panel, 'retraducir_tooltips'):
            self.tool_panel.retraducir_tooltips()

        if hasattr(self, 'text_panel') and hasattr(self.text_panel, 'retraducir_panel'):
            self.text_panel.retraducir_panel()
        if hasattr(self, 'layers_panel') and hasattr(self.layers_panel, 'retraducir_panel'):
            self.layers_panel.retraducir_panel()
        if hasattr(self, 'history_panel') and hasattr(self.history_panel, 'retraducir_panel'):
            self.history_panel.retraducir_panel()
        if hasattr(self, 'color_panel') and hasattr(self.color_panel, 'retraducir_panel'):
            self.color_panel.retraducir_panel()

        if hasattr(self, 'text_dock'):
            self.text_dock.setWindowTitle(t("Texto"))
        if hasattr(self, 'tools_dock'):
            self.tools_dock.setWindowTitle(t("Herramientas"))
        if hasattr(self, 'layers_dock'):
            self.layers_dock.setWindowTitle(t("Capas"))
        if hasattr(self, 'history_dock'):
            self.history_dock.setWindowTitle(t("Historial"))
        if hasattr(self, 'color_dock'):
            self.color_dock.setWindowTitle(t("Color"))

        for i in range(self.tab_widget.count()):
            self.actualizar_titulo_pestana(i)

        self.actualizar_titulo_ventana()

    def keyPressEvent(self, event):
        focus_widget = QApplication.focusWidget()
        from PyQt6.QtWidgets import QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox
        if focus_widget and isinstance(focus_widget, (QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox)):
            super().keyPressEvent(event)
            return

        key_text = event.text().upper()
        if key_text and len(key_text) == 1 and not (event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)):
            from gui.dialogo_atajos import cargar_atajos
            atajos = cargar_atajos()

            for tool_name, char in atajos.items():
                if char and char.upper() == key_text:
                    for btn in self.tool_panel.button_group.buttons():
                        tool = btn.property("tool_obj")
                        if tool and hasattr(tool, 'name') and tool.name == tool_name:
                            self.tool_panel.select_tool(tool)
                            return

        super().keyPressEvent(event)

    def crear_menus(self):
        menu_bar = self.menuBar()

        self.menu_archivo = MenuArchivo(self)
        self.menu_archivo.crear_menu(menu_bar)

        self.menu_editar = MenuEditar(self)
        self.menu_editar.crear_menu(menu_bar)

        self.menu_imagen = MenuImagen(self)
        self.menu_imagen.crear_menu(menu_bar)

        self.menu_opciones = MenuOpciones(self)
        self.menu_opciones.crear_menu(menu_bar)

        self.menu_ver = MenuVer(self)
        self.menu_ver.crear_menu(menu_bar)

        self.menu_ajustes = MenuAjustes(self)
        self.menu_ajustes.crear_menu(menu_bar)

        self.menu_acerca = MenuAcerca(self)
        self.menu_acerca.crear_menu(menu_bar)

        self.top_toolbar = TopToolBarWidget(main_window=self)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.top_toolbar)

        self.top_toolbar.action_nueva_pestana.triggered.connect(self.menu_archivo.nuevo_archivo)
        self.top_toolbar.action_abrir.triggered.connect(self.menu_archivo.abrir_archivo)
        self.top_toolbar.action_guardar.triggered.connect(self.menu_archivo.guardar_archivo)
        self.top_toolbar.action_cortar.triggered.connect(self.menu_editar.cortar)
        self.top_toolbar.action_copiar.triggered.connect(self.menu_editar.copiar)
        self.top_toolbar.action_pegar.triggered.connect(self.menu_editar.pegar)

    def activar_herramienta_mover(self):
        from tools.move_select_pixels import MoveSelectPixelsTool
        panel = getattr(self, 'tools_panel', getattr(self, 'tool_panel', getattr(self, 'panel_herramientas', None)))
        if panel:
            for btn in panel.button_group.buttons():
                tool = btn.property("tool_obj")
                if isinstance(tool, MoveSelectPixelsTool):
                    btn.setChecked(True)
                    panel.select_tool(tool)
                    return

    def _on_tolerance_changed(self, val):
        if hasattr(self, 'canvas') and self.canvas:
            if hasattr(self.canvas.active_tool_obj, 'update_tolerance'):
                self.canvas.active_tool_obj.update_tolerance(self.canvas, val)

    def _ejecutar_escape_global(self):
        if hasattr(self, 'canvas') and self.canvas:
            canvas = self.canvas
            if hasattr(canvas.active_tool_obj, 'commit_line'):
                canvas.active_tool_obj.commit_line(canvas)
            if hasattr(canvas.active_tool_obj, 'commit_text'):
                canvas.active_tool_obj.commit_text(canvas, canvas.color_primario)
            canvas.cancelar_o_deseleccionar()

    def closeEvent(self, event: QCloseEvent):
        if hasattr(self, 'menu_archivo'):
            if not self.menu_archivo.confirmar_descarte_cambios():
                event.ignore()
                return

        settings = QSettings("PaintNotNet", "PaintNotNet")
        if settings.value("save_on_close", True, type=bool):
            if hasattr(self, 'color_panel'):
                custom_hexs = []
                for c in self.color_panel.custom_colors:
                    if c and c.isValid():
                        custom_hexs.append(c.name(QColor.NameFormat.HexArgb))
                    else:
                        custom_hexs.append("")
                settings.setValue("custom_colors", custom_hexs)

        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    app.setStyle("Fusion")
    paleta_oscura = app.palette()
    paleta_oscura.setColor(paleta_oscura.ColorRole.Window, QColor(45, 45, 45))
    paleta_oscura.setColor(paleta_oscura.ColorRole.WindowText, Qt.GlobalColor.white)
    paleta_oscura.setColor(paleta_oscura.ColorRole.Base, QColor(30, 30, 30))
    paleta_oscura.setColor(paleta_oscura.ColorRole.AlternateBase, QColor(45, 45, 45))
    paleta_oscura.setColor(paleta_oscura.ColorRole.Text, Qt.GlobalColor.white)
    paleta_oscura.setColor(paleta_oscura.ColorRole.Button, QColor(45, 45, 45))
    paleta_oscura.setColor(paleta_oscura.ColorRole.ButtonText, Qt.GlobalColor.white)
    paleta_oscura.setColor(paleta_oscura.ColorRole.Highlight, QColor(42, 130, 218))
    paleta_oscura.setColor(paleta_oscura.ColorRole.HighlightedText, Qt.GlobalColor.white)
    app.setPalette(paleta_oscura)

    app.setStyleSheet("""
        QWidget { color: #ffffff; }
        QDockWidget::title {
            text-align: center;
            background-color: #353535;
            color: #ffffff;
            font-size: 9px;
            font-weight: bold;
            padding: 2px;
        }
        QGroupBox {
            font-weight: normal;
            font-size: 8px;
            border: 1px solid #5a5a5a;
            border-radius: 3px;
            margin-top: 8px;
            padding-top: 4px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 4px;
            color: #ffffff;
            background-color: transparent;
        }
        QComboBox, QSpinBox, QFontComboBox, QLineEdit {
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #4a4a4a;
            padding: 1px;
            border-radius: 2px;
        }
        QToolButton {
            background-color: #3a3a3a;
            color: #ffffff;
            border: 1px solid #5a5a5a;
            padding: 1px;
            border-radius: 2px;
        }
        QToolButton:checked {
            background-color: #2a82da;
            border-color: #1e5fa0;
        }
    """)

    app.setWindowIcon(QIcon("gui/iconos/paintdotnet.ico"))
    ventana = PaintNotNet()
    if len(sys.argv) > 1:
        ruta_arg = sys.argv[1]
        if os.path.exists(ruta_arg) and not ruta_arg.startswith("-"):
            ventana.menu_archivo.abrir_ruta_especifica(os.path.abspath(ruta_arg))
    ventana.show()
    sys.exit(app.exec())
