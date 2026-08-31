import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QScrollArea, QDockWidget, QTabWidget, QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtGui import QColor, QCloseEvent, QShortcut, QKeySequence, QIcon
from PyQt6.QtCore import Qt, QSettings, QTimer, QSize

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
from gui.bottom_status_bar import BottomStatusBarWidget

from gui.menu_archivo import MenuArchivo
from gui.menu_editar import MenuEditar
from gui.menu_imagen import MenuImagen
from gui.menu_opciones import MenuOpciones
from gui.menu_ver import MenuVer
from gui.menu_ajustes import MenuAjustes
from gui.menu_acerca import MenuAcerca


def obtener_ruta_icono_app() -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    posibles = [
        os.path.join(base, "gui", "icono.png"),
        os.path.join(base, "gui", "paintdotnet.ico"),
        os.path.join(base, "gui", "iconos", "paintdotnet.ico"),
        "/usr/share/pixmaps/paintnotnet.png"
    ]
    for ruta in posibles:
        if os.path.exists(ruta):
            return ruta
    return "gui/icono.png"


class PaintNotNet(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("PaintNotNet", "PaintNotNet")
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(1500, 800)
        self.setWindowIcon(QIcon(obtener_ruta_icono_app()))
        self.archivo_actual = None
        self.lienzo_modificado = False

        self.setDockOptions(QMainWindow.DockOption.AnimatedDocks)

        # ==========================================
        # DOCKS LATERALES IZQUIERDOS: Herramientas / Pinceles / Colores
        # ==========================================
        self.tools_dock = QDockWidget(self)
        self.tools_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.tool_panel = ToolPanelWidget(main_window=self)
        self.tools_dock.setWidget(self.tool_panel)
        self.tools_dock.setTitleBarWidget(self._hacer_titulo_dock("gui/iconos/tools.png", "Herramientas"))
        self.tools_dock.setFixedHeight(270)
        self.tools_dock.setFixedWidth(120)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.tools_dock)

        self.color_dock = QDockWidget(self)
        self.color_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.color_panel = ColorPanelWidget(main_window=self)
        self.color_dock.setWidget(self.color_panel)
        self.color_dock.setTitleBarWidget(self._hacer_titulo_dock("gui/iconos/color.png", "Colores"))
        self.color_dock.setFixedHeight(300)
        self.color_dock.setFixedWidth(120)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.color_dock)

        # ==========================================
        # DOCKS LATERALES DERECHOS: Texto / Colores / Efectos de Texto / Historial / Capas
        # ==========================================
        # 1. Dock de Color avanzado
        self.advanced_color_dock = QDockWidget(self)
        self.advanced_color_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.advanced_color_panel = AdvancedColorPanelWidget(main_window=self)
        self.advanced_color_dock.setWidget(self.advanced_color_panel)
        self.advanced_color_dock.setTitleBarWidget(self._hacer_titulo_dock("gui/iconos/color-plus.png", "Color"))
        self.advanced_color_dock.setFixedWidth(160)
        self.advanced_color_dock.setFixedHeight(220)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.advanced_color_dock)

        # 4. Dock de Historial
        self.history_dock = QDockWidget(self)
        self.history_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.history_panel = HistoryPanelWidget(main_window=self)
        self.history_dock.setWidget(self.history_panel)
        self.history_dock.setTitleBarWidget(self._hacer_titulo_dock("gui/iconos/history.png", "Historial"))
        self.history_dock.setFixedWidth(160)
        self.history_dock.setFixedHeight(180)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.history_dock)

        # 5. Dock de Capas
        self.layers_dock = QDockWidget(self)
        self.layers_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.layers_panel = LayersPanelWidget(main_window=self)
        self.layers_dock.setWidget(self.layers_panel)
        self.layers_dock.setTitleBarWidget(self._hacer_titulo_dock("gui/iconos/layers.png", "Capas"))
        self.layers_dock.setFixedWidth(160)
        self.layers_dock.setFixedHeight(180)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.layers_dock)

        self.setWindowIcon(QIcon(obtener_ruta_icono_app()))

        # ==========================================
        # ÁREA CENTRAL MULTI-PESTAÑA (TABBED MDI)
        # ==========================================
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setObjectName("tab_widget_central")

        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)
        self.tab_widget.tabBarDoubleClicked.connect(self._on_tab_double_clicked)

        central_container = QWidget()
        layout_central = QVBoxLayout(central_container)
        layout_central.setContentsMargins(0, 4, 0, 0)
        layout_central.setSpacing(0)
        layout_central.addWidget(self.tab_widget)

        self.bottom_bar = BottomStatusBarWidget(main_window=self)
        layout_central.addWidget(self.bottom_bar)

        self.setCentralWidget(central_container)

        # --- CONEXIONES DIRECTAS: PANELES -> CANVAS ---
        self.color_panel.color_primario_cambiado.connect(self._on_color_primario_changed)
        self.color_panel.color_secundario_cambiado.connect(self._on_color_secundario_changed)

        self.advanced_color_panel.color_primario_cambiado.connect(self._on_color_primario_changed)
        self.advanced_color_panel.color_secundario_cambiado.connect(self._on_color_secundario_changed)

        # ==========================================
        # MENÚS Y ATAJOS GLOBALES
        # ==========================================
        self.crear_menus()
        self.text_panel = self.top_toolbar
        self.effects_panel = self.top_toolbar

        # Inicializar Gestor de Autoguardado de Emergencia
        from core.emergency_save import EmergencySaveManager
        self.emergency_mgr = EmergencySaveManager(main_window=self)

        from core.i18n import t
        settings = QSettings("PaintNotNet", "PaintNotNet")
        init_w = settings.value("default_canvas_w", 800, type=int)
        init_h = settings.value("default_canvas_h", 600, type=int)
        init_trans = settings.value("default_canvas_transparent", False, type=bool)
        init_dpi = settings.value("default_canvas_dpi", 300, type=int)
        init_profile = settings.value("default_canvas_profile", "sRGB", type=str)

        # Crear primera pestaña por defecto
        self.crear_nueva_pestana(init_w, init_h, transparent=init_trans, dpi=init_dpi, perfil_color=init_profile, titulo=t("Sin Título"))

        # Set active tool state on top toolbar
        if hasattr(self, 'left_toolbar') and hasattr(self.left_toolbar, 'active_tool_obj'):
            self.top_toolbar.update_tool_states(self.left_toolbar.active_tool_obj)

        # ==========================================
        # RESTAURAR PERFIL DE USUARIO SI EXISTE
        # ==========================================
        self._cargar_perfil_usuario()

        # ==========================================
        # APLICAR TEMA DE INTERFAZ (CLARO / OSCURO / SISTEMA)
        # ==========================================
        from core.theme import ThemeManager
        ThemeManager().establecer_tema(ThemeManager().current_theme, self)

        self.actualizar_titulo_ventana()

        self.shortcut_esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.shortcut_esc.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_esc.activated.connect(self._ejecutar_escape_global)

        # Verificar si existen autoguardados de emergencia al iniciar
        QTimer.singleShot(150, self._verificar_respaldos_emergencia_inicio)


    def _hacer_titulo_dock(self, icono_path, tooltip=""):
        """Crea un widget de título mínimo con solo un ícono de 16x16 alineado a la izquierda."""
        widget = QWidget()
        widget.setFixedHeight(21)
        widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 1)
        layout.setSpacing(0)
        lbl = QLabel()
        lbl.setPixmap(QIcon(icono_path).pixmap(QSize(16, 16)))
        if tooltip:
            lbl.setToolTip(tooltip)
        layout.addWidget(lbl)
        layout.addStretch()
        return widget

    def _cargar_perfil_usuario(self):
        settings = QSettings("PaintNotNet", "PaintNotNet")
        saved_vis = settings.value("docks_visible", None)
        if isinstance(saved_vis, dict):
            for attr, is_vis in saved_vis.items():
                if hasattr(self, attr):
                    getattr(self, attr).setVisible(bool(is_vis))

        if settings.value("save_on_close", True, type=bool):
            custom_hexs = settings.value("custom_colors", None)
            if custom_hexs and isinstance(custom_hexs, list):
                for idx, hex_val in enumerate(custom_hexs[:21]):
                    if hex_val and idx < len(self.color_panel.custom_colors):
                        c = QColor(hex_val)
                        if c.isValid():
                            self.color_panel.custom_colors[idx] = c
                            self.color_panel.botones_custom[idx].set_color(c)
                        else:
                            self.color_panel.custom_colors[idx] = None
                            self.color_panel.botones_custom[idx].set_color(None)
                    elif idx < len(self.color_panel.custom_colors):
                        self.color_panel.custom_colors[idx] = None
                        self.color_panel.botones_custom[idx].set_color(None)
            else:
                if hasattr(self, 'color_panel') and self.color_panel:
                    self.color_panel.custom_colors = [None] * 21
                    for btn in self.color_panel.botones_custom:
                        btn.set_color(None)

    def reset_panel_layout_and_preferences(self):
        """Restablece la aplicación a 0 (valores de fábrica)."""
        QSettings("PaintNotNet", "PaintNotNet").clear()
        QSettings("PaintNotNet", "EffectsPanel").clear()
        QSettings("PaintNotNet", "RecentFiles").clear()

        docks_visibles = {
            'tools_dock': True,
            'color_dock': True,
            'advanced_color_dock': True,
            'history_dock': True,
            'layers_dock': True,
        }
        for attr, vis in docks_visibles.items():
            if hasattr(self, attr):
                getattr(self, attr).setVisible(vis)

        if hasattr(self, 'color_panel') and self.color_panel:
            self.color_panel.custom_colors = [None] * 12
            if hasattr(self.color_panel, 'botones_custom'):
                for btn in self.color_panel.botones_custom:
                    btn.set_color(None)

        from core.theme import ThemeManager
        from core.i18n import I18nManager
        ThemeManager().establecer_tema("Definido por el sistema", self)
        I18nManager().establecer_idioma("Español")
        self.retraducir_ui()

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
        # Si la herramienta de texto está activa con selección, aplicar color al texto seleccionado
        canvas = getattr(self, 'lienzo', None)
        if canvas:
            from tools.text import TextTool
            tool = getattr(canvas, 'active_tool_obj', None)
            if isinstance(tool, TextTool) and tool.is_editing and tool._has_selection():
                tool.apply_format_to_selection({"color": color})

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

    def crear_nueva_pestana(self, width=800, height=600, transparent=True, ruta=None, titulo=None, dpi=300, perfil_color="sRGB"):
        from core.theme import ThemeManager
        tm = ThemeManager()
        res_nombre = tm.resolver_nombre_tema(tm.current_theme)
        c_bg = "#525252" if res_nombre == "Oscuro" else "#C8C8C8"

        area_scroll = QScrollArea()
        area_scroll.setStyleSheet(f"QScrollArea, QScrollArea > QWidget > QWidget {{ background-color: {c_bg}; border: none; }}")
        area_scroll.viewport().setStyleSheet(f"background-color: {c_bg};")
        area_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        area_scroll.setWidgetResizable(False)

        canvas = CanvasWidget(width, height)
        if not transparent:
            canvas.layer_mgr.buffer.fill(Qt.GlobalColor.white)

        canvas.dpi = dpi
        canvas.perfil_color = perfil_color

        # Asignar densidad métrica (DPI -> dpm)
        dpm = int(round(dpi * 39.3701))
        canvas.layer_mgr.buffer.setDotsPerMeterX(dpm)
        canvas.layer_mgr.buffer.setDotsPerMeterY(dpm)

        # Configurar espacio de color
        from PyQt6.QtGui import QColorSpace
        if perfil_color == "Adobe RGB":
            canvas.layer_mgr.buffer.setColorSpace(QColorSpace(QColorSpace.NamedColorSpace.AdobeRgb))
        elif perfil_color == "Display P3":
            canvas.layer_mgr.buffer.setColorSpace(QColorSpace(QColorSpace.NamedColorSpace.DisplayP3))
        else:
            canvas.layer_mgr.buffer.setColorSpace(QColorSpace(QColorSpace.NamedColorSpace.SRgb))

        canvas.main_window = self
        canvas.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        canvas.callback_modificado = lambda: self.marcar_modificado_pestana(canvas)
        canvas.archivo_actual = ruta

        if hasattr(self, 'color_panel'):
            canvas.color_primario = self.color_panel.color_primario
            canvas.color_secundario = self.color_panel.color_secundario

        if hasattr(self, 'top_toolbar'):
            tb = self.top_toolbar
            canvas.grosor_pincel = tb.spin_grosor.value()
            canvas.ancho_pincel  = tb.spin_grosor.value()
            if hasattr(canvas, 'tolerancia') and hasattr(tb, 'slider_tol'):
                canvas.tolerancia = tb.slider_tol.value()

        # Propagar herramienta actualmente seleccionada al canvas nuevo
        if hasattr(self, 'tool_panel'):
            herramienta = getattr(self.tool_panel, 'herramienta_anterior', None)
            if herramienta is not None:
                canvas.set_active_tool(herramienta)

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
        # Reemplazar botón cierre nativo con widget propio (con margen derecho)
        btn_cerrar = self._hacer_boton_cerrar()
        self.tab_widget.tabBar().setTabButton(
            idx, self.tab_widget.tabBar().ButtonPosition.RightSide, btn_cerrar
        )
        self.tab_widget.setCurrentIndex(idx)

        if hasattr(self, 'emergency_mgr') and self.emergency_mgr:
            self.emergency_mgr.registrar_canvas(canvas, titulo=titulo)

        return canvas

    def _hacer_boton_cerrar(self):
        """Crea un botón de cierre de pestaña con margen derecho visible."""
        from PyQt6.QtWidgets import QToolButton

        # ID único para identificar este wrapper sin comparación de punteros
        uid = id(self) ^ id(object())

        wrapper = QWidget()
        wrapper.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        wrapper.setProperty("tab_uid", uid)
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(2, 0, 7, 0)  # 7px margen derecho
        layout.setSpacing(0)

        btn = QToolButton()
        btn.setText("✕")
        btn.setFixedSize(14, 14)
        btn.setProperty("tab_uid", uid)
        btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                color: #999999;
                font-size: 10px;
                font-weight: bold;
            }
            QToolButton:hover {
                background: #c42b1c;
                color: #EDEDED;
                border-radius: 2px;
            }
        """)
        layout.addWidget(btn)
        wrapper.setFixedSize(28, 18)

        def on_click(checked=False, _uid=uid):
            tb = self.tab_widget.tabBar()
            for i in range(tb.count()):
                w = tb.tabButton(i, tb.ButtonPosition.RightSide)
                try:
                    if w is not None and w.property("tab_uid") == _uid:
                        QTimer.singleShot(0, lambda idx=i: self.tab_widget.tabCloseRequested.emit(idx))
                        break
                except RuntimeError:
                    pass  # objeto C++ ya destruido, ignorar

        btn.clicked.connect(on_click)
        return wrapper

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

            # Sincronizar formato de texto e interfaz al cambiar de pestaña
            if hasattr(canvas, 'text_config') and canvas.text_config:
                if hasattr(self, 'text_panel') and self.text_panel:
                    self.text_panel.actualizar_desde_formato_dict(canvas.text_config)
                if hasattr(self, 'top_toolbar') and self.top_toolbar:
                    self.top_toolbar.actualizar_desde_formato_dict(canvas.text_config)

            # Sincronizar valores de herramientas
            if hasattr(self, 'top_toolbar'):
                tb = self.top_toolbar
                canvas.grosor_pincel = tb.spin_grosor.value()
                canvas.ancho_pincel  = tb.spin_grosor.value()
                if hasattr(canvas, 'tolerancia') and hasattr(tb, 'slider_tol'):
                    canvas.tolerancia = tb.slider_tol.value()

            # Propagar herramienta actualmente seleccionada al canvas
            if hasattr(self, 'tool_panel'):
                herramienta = getattr(self.tool_panel, 'herramienta_anterior', None)
                if herramienta is not None:
                    canvas.set_active_tool(herramienta)

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
                if canvas:
                    if hasattr(canvas, 'selection_engine'):
                        canvas.selection_engine.clear_selection()
                    if hasattr(self, 'emergency_mgr') and self.emergency_mgr:
                        self.emergency_mgr.eliminar_respaldo_canvas(canvas)

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
            if hasattr(self, 'emergency_mgr') and self.emergency_mgr:
                self.emergency_mgr.solicitar_guardado_emergencia(canvas)
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
        if hasattr(self, 'bottom_bar') and hasattr(self.bottom_bar, 'retraducir_bar'):
            self.bottom_bar.retraducir_bar()

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

    def createPopupMenu(self):
        """Desactiva el menú contextual emergente por defecto de la ventana principal al hacer clic derecho en toolbars/docks."""
        return None

    def _verificar_respaldos_emergencia_inicio(self):
        from core.emergency_save import buscar_respaldos_emergencia, DialogoRestauracionEmergencia, limpiar_todos_los_respaldos
        from core.pnn_format import cargar_proyecto_pnn
        from PyQt6.QtWidgets import QDialog

        archivos = buscar_respaldos_emergencia()
        if not archivos:
            return

        dlg = DialogoRestauracionEmergencia(count_files=len(archivos), parent=self)
        res = dlg.exec()
        if res == QDialog.DialogCode.Accepted:
            first_canvas_reused = False
            for filepath in archivos:
                nombre_base = os.path.basename(filepath)
                parts = nombre_base.split('_')
                if len(parts) >= 3:
                    titulo_orig = "_".join(parts[:-2])
                else:
                    titulo_orig = os.path.splitext(nombre_base)[0]

                if not first_canvas_reused and self.tab_widget.count() == 1:
                    area_scroll = self.tab_widget.widget(0)
                    canvas = area_scroll.widget() if area_scroll else None
                    if canvas and not getattr(canvas, 'lienzo_modificado', False) and len(canvas.layer_mgr.capas) <= 1:
                        if cargar_proyecto_pnn(canvas, filepath):
                            self.tab_widget.setTabText(0, titulo_orig)
                            canvas.lienzo_modificado = True
                            first_canvas_reused = True
                            if hasattr(self, 'emergency_mgr'):
                                self.emergency_mgr.registrar_canvas(canvas, titulo=titulo_orig)
                            continue

                canvas_nuevo = self.crear_nueva_pestana(800, 600, transparent=True, titulo=titulo_orig)
                if cargar_proyecto_pnn(canvas_nuevo, filepath):
                    canvas_nuevo.lienzo_modificado = True
                    if hasattr(self, 'emergency_mgr'):
                        self.emergency_mgr.registrar_canvas(canvas_nuevo, titulo=titulo_orig)

            for f in archivos:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception:
                    pass
        else:
            limpiar_todos_los_respaldos()

    def closeEvent(self, event: QCloseEvent):
        if hasattr(self, 'menu_archivo'):
            if not self.menu_archivo.confirmar_descarte_cambios():
                event.ignore()
                return

        settings = QSettings("PaintNotNet", "PaintNotNet")
        settings.setValue("geometry", self.saveGeometry())

        docks_attr = [
            'tools_dock', 'color_dock',
            'layers_dock', 'history_dock', 'advanced_color_dock'
        ]
        docks_visibles = {attr: getattr(self, attr).isVisible() for attr in docks_attr if hasattr(self, attr)}
        settings.setValue("docks_visible", docks_visibles)

        if settings.value("save_on_close", True, type=bool):
            if hasattr(self, 'color_panel'):
                custom_hexs = []
                for c in self.color_panel.custom_colors:
                    if c and c.isValid():
                        custom_hexs.append(c.name(QColor.NameFormat.HexArgb))
                    else:
                        custom_hexs.append("")
                settings.setValue("custom_colors", custom_hexs)

        if hasattr(self, 'emergency_mgr') and self.emergency_mgr:
            self.emergency_mgr.limpiar_todos()

        event.accept()

from PyQt6.QtNetwork import QLocalServer, QLocalSocket


def obtener_nombre_servidor_unico() -> str:
    import getpass
    try:
        usuario = getpass.getuser()
    except Exception:
        usuario = "default_user"
    return f"PaintNotNet_SingleInstance_Server_{usuario}"


def verificar_instancia_unica(files_to_open: list) -> bool:
    socket = QLocalSocket()
    server_name = obtener_nombre_servidor_unico()
    socket.connectToServer(server_name)
    if socket.waitForConnected(500):
        payload = "\n".join(files_to_open) if files_to_open else "__FOCUS__"
        socket.write(payload.encode('utf-8'))
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        return True
    return False


def iniciar_servidor_instancia_unica(ventana: PaintNotNet):
    server_name = obtener_nombre_servidor_unico()
    QLocalServer.removeServer(server_name)

    server = QLocalServer()
    if not server.listen(server_name):
        return server

    def _on_new_connection():
        client_socket = server.nextPendingConnection()
        if not client_socket:
            return
        if client_socket.waitForReadyRead(1000):
            raw_data = client_socket.readAll().data().decode('utf-8', errors='ignore')
            lines = [line.strip() for line in raw_data.split('\n') if line.strip()]
            for line in lines:
                if line != "__FOCUS__" and os.path.exists(line):
                    ventana.menu_archivo.abrir_ruta_especifica(os.path.abspath(line))

        if ventana.isMinimized():
            ventana.showNormal()
        ventana.show()
        ventana.raise_()
        ventana.activateWindow()

    server.newConnection.connect(_on_new_connection)
    return server


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Filtrar argumentos de la línea de comandos para obtener rutas de archivos válidas
    archivos_args = []
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg and not arg.startswith("-") and os.path.exists(arg):
                archivos_args.append(os.path.abspath(arg))

    # Comprobar si ya existe una instancia activa ejecutándose
    if verificar_instancia_unica(archivos_args):
        # Ya había una instancia abierta: se le notificaron los archivos y se finaliza este proceso secundario.
        sys.exit(0)

    from core.theme import ThemeManager
    from core.i18n import I18nManager

    app.setWindowIcon(QIcon(obtener_ruta_icono_app()))
    I18nManager().cargar_idioma_configurado()

    ventana = PaintNotNet()
    ThemeManager().establecer_tema(ThemeManager().current_theme, ventana)

    # Iniciar servidor IPC para recibir solicitudes de apertura de archivos de futuras instancias
    ventana._single_instance_server = iniciar_servidor_instancia_unica(ventana)

    # Re-traducir toda la UI para que coincida con el idioma cargado.
    ventana.retraducir_ui()

    if archivos_args:
        for ruta in archivos_args:
            ventana.menu_archivo.abrir_ruta_especifica(ruta)

    ventana.show()
    sys.exit(app.exec())
