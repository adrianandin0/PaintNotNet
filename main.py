import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QScrollArea, QDockWidget
from PyQt6.QtGui import QColor, QCloseEvent, QShortcut, QKeySequence, QIcon
from PyQt6.QtCore import Qt

# Módulos Core y GUI nuevos
from core.canvas import CanvasWidget
from gui.tool_panel import ToolPanelWidget
from gui.color_panel import ColorPanelWidget
from gui.text_panel import TextPanelWidget
from gui.menu_archivo import MenuArchivo
from gui.menu_editar import MenuEditar
from gui.menu_imagen import MenuImagen
from gui.layers_panel import LayersPanelWidget

class PaintNotNet(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 1100, 800)
        self.archivo_actual = None
        self.lienzo_modificado = False

        # --- Configuración de Docks (Permite apilar y mover sin superponerse) ---
        self.setDockOptions(QMainWindow.DockOption.AllowNestedDocks | QMainWindow.DockOption.AnimatedDocks)

        # ==========================================
        # DOCKS LATERALES (NUEVOS PANELES MODULARES)
        # ==========================================

        # 1. Dock de Herramientas
        self.tools_dock = QDockWidget(self)
        self.tools_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.tool_panel = ToolPanelWidget(main_window=self)
        self.tools_dock.setWidget(self.tool_panel)
        self.tools_dock.setFixedHeight(330)
        self.tools_dock.setFixedWidth(82)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.tools_dock)

        # 2. Dock de Colores
        self.color_dock = QDockWidget("", self)
        self.color_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.color_panel = ColorPanelWidget(main_window=self)
        self.color_dock.setWidget(self.color_panel)
        self.color_dock.setFixedHeight(400)
        self.color_dock.setFixedWidth(82)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.color_dock)

        # Apilar inicialmente el panel de colores DEBAJO del de herramientas
        self.splitDockWidget(self.tools_dock, self.color_dock, Qt.Orientation.Vertical)

        # 3. Dock de Texto (Ubicado a la derecha)
        self.text_dock = QDockWidget(self)
        self.text_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.text_panel = TextPanelWidget(main_window=self)
        self.text_dock.setWidget(self.text_panel)
        self.text_dock.setFixedWidth(148)
        self.text_dock.setFixedHeight(225)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.text_dock)

        # ==========================================
        # 4. NUEVO: Dock de Capas (A la derecha)
        # ==========================================
        self.layers_dock = QDockWidget("Capas", self)
        self.layers_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.layers_panel = LayersPanelWidget(main_window=self)
        self.layers_dock.setWidget(self.layers_panel)
        self.layers_dock.setFixedWidth(148)
        self.layers_dock.setFixedHeight(320)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.layers_dock)

        # Apilar el panel de capas DEBAJO del panel de texto
        self.splitDockWidget(self.text_dock, self.layers_dock, Qt.Orientation.Vertical)

        self.setWindowIcon(QIcon("gui/icono.png"))

        # ==========================================
        # ÁREA CENTRAL (LIENZO / CANVAS)
        # ==========================================
        self.area_scroll = QScrollArea()
        self.area_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.area_scroll.setWidgetResizable(False)

        self.canvas = CanvasWidget(800, 600)
        self.canvas.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.lienzo = self.canvas  # <--- AGREGAR ESTA LÍNEA AQUÍ
        self.canvas.callback_modificado = self.marcar_modificado

        # --- CONEXIONES DIRECTAS: PANELES -> CANVAS ---
        self.color_panel.color_primario_cambiado.connect(lambda c: setattr(self.canvas, 'color_primario', c))
        self.color_panel.color_secundario_cambiado.connect(lambda c: setattr(self.canvas, 'color_secundario', c))
        self.text_panel.text_config_changed.connect(self.canvas.actualizar_config_texto)

        self.area_scroll.setWidget(self.canvas)
        self.setCentralWidget(self.area_scroll)

        # ==========================================
        # MENÚS Y ATAJOS GLOBALES
        # ==========================================
        self.crear_menus()
        self.actualizar_titulo_ventana()

        # --- DENTRO DEL __init__ DE TU MAINWINDOW ---
        self.shortcut_esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.shortcut_esc.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_esc.activated.connect(self._ejecutar_escape_global)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if hasattr(self, 'canvas') and hasattr(self.canvas.active_tool_obj, 'commit_text'):
                self.canvas.active_tool_obj.commit_text(self.canvas, self.canvas.color_primario)
                self.canvas.update()
                return
        super().keyPressEvent(event)

    def marcar_modificado(self):
        if not self.lienzo_modificado:
            self.lienzo_modificado = True
            self.actualizar_titulo_ventana()

    def actualizar_titulo_ventana(self):
        nombre = self.archivo_actual if self.archivo_actual else "Sin Titulo"
        asterisco = " *" if self.lienzo_modificado else ""
        self.setWindowTitle(f"PaintNotNet - {nombre}{asterisco}")

    def crear_menus(self):
        menu_bar = self.menuBar()

        self.menu_archivo = MenuArchivo(self)
        self.menu_archivo.crear_menu(menu_bar)

        self.menu_editar = MenuEditar(self)
        self.menu_editar.crear_menu(menu_bar)

        self.menu_imagen = MenuImagen(self)
        self.menu_imagen.crear_menu(menu_bar)

    def _ejecutar_escape_global(self):
        if hasattr(self, 'canvas') and hasattr(self.canvas.active_tool_obj, 'commit_text'):
            self.canvas.active_tool_obj.commit_text(self.canvas, self.canvas.color_primario)
            self.canvas.update()

    def closeEvent(self, event: QCloseEvent):
        if hasattr(self, 'menu_archivo'):
            if not self.menu_archivo.confirmar_descarte_cambios():
                event.ignore()
                return
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # --- Tema Oscuro Global ---
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

    # --- Estilos CSS Adicionales ---
    app.setStyleSheet("""
        QWidget { color: #ffffff; }
        QGroupBox {
            font-weight: normal;
            font-size: 10px;
            border: 1px solid #5a5a5a;
            border-radius: 3px;
            margin-top: 10px;
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

    ventana = PaintNotNet()
    ventana.show()
    sys.exit(app.exec())
