import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QScrollArea, QToolBar
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from lienzo import Lienzo
from herramientas.panel_herramientas import PanelHerramientas
from herramientas.panel_propiedades import PanelPropiedades
from herramientas.panel_texto import PanelTexto
from herramientas.panel_colores import PanelColores

from gui.menu_archivo import MenuArchivo
from gui.menu_editar import MenuEditar
from gui.menu_imagen import MenuImagen


class PaintNotNet(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PaintNotNet - Nuevo Archivo")
        self.setGeometry(100, 100, 1100, 800)
        self.archivo_actual = None

        self.area_scroll = QScrollArea()
        self.area_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.area_scroll.setWidgetResizable(False)

        self.lienzo = Lienzo(800, 600)
        self.area_scroll.setWidget(self.lienzo)
        self.setCentralWidget(self.area_scroll)

        self.crear_barra_herramientas()
        self.crear_menus()

    def crear_menus(self):
        menu_bar = self.menuBar()
        self.menu_archivo = MenuArchivo(self)
        self.menu_archivo.crear_menu(menu_bar)

        self.menu_editar = MenuEditar(self)
        self.menu_editar.crear_menu(menu_bar)

        self.menu_imagen = MenuImagen(self)
        self.menu_imagen.crear_menu(menu_bar)

    def crear_barra_herramientas(self):
        barra = QToolBar("Herramientas")
        barra.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        barra.setMovable(False)
        barra.setFixedWidth(160)
        
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, barra)

        # Panel Herramientas
        self.panel_herramientas = PanelHerramientas(self.cambiar_herramienta)
        barra.addWidget(self.panel_herramientas)

        # Panel Propiedades
        self.panel_propiedades = PanelPropiedades(
            self.lienzo.grosor_pincel,
            self.lienzo.opacidad_pincel,
            self.lienzo.suavizado_pincel,
            self.lienzo.forma_pincel,
            self.cambiar_grosor,
            self.cambiar_opacidad,
            self.cambiar_suavizado,
            self.cambiar_forma
        )
        barra.addWidget(self.panel_propiedades)

        # Panel Texto
        self.panel_texto = PanelTexto(
            self.lienzo.fuente_texto, 
            self.cambiar_fuente, 
            self.lienzo.color_secundario
        )
        barra.addWidget(self.panel_texto)
        self.panel_texto.setVisible(False)

        # Panel Colores
        self.panel_colores = PanelColores(self.cambiar_colores)
        barra.addWidget(self.panel_colores)

    def cambiar_herramienta(self, nombre):
        if nombre != "texto":
            self.lienzo.fijar_texto_si_existe()
            self.panel_texto.setVisible(False)
        else:
            self.panel_texto.setVisible(True)

        es_pincel = (nombre == "pincel")
        self.panel_propiedades.actualizar_estado_pincel(es_pincel)

        self.lienzo.herramienta = nombre

    def cambiar_grosor(self, valor):
        self.lienzo.grosor_pincel = valor

    def cambiar_opacidad(self, alfa):
        # Aseguramos que el valor alfa se mantenga estrictamente entre 0 y 255
        alfa_clamped = max(0, min(255, int(alfa)))
        self.lienzo.opacidad_pincel = alfa_clamped

    def cambiar_suavizado(self, porcentaje):
        self.lienzo.suavizado_pincel = porcentaje

    def cambiar_forma(self, forma):
        self.lienzo.forma_pincel = forma

    def cambiar_fuente(self, fuente):
        self.lienzo.fuente_texto = fuente
        borde, sombra = self.panel_texto.obtener_configuraciones()
        self.lienzo.config_borde = borde
        self.lienzo.config_sombra = sombra

        if self.lienzo.editor_texto:
            self.lienzo.editor_texto.fuente = fuente
            self.lienzo.editor_texto.actualizar_estilo()
        
        self.lienzo.update()

    def cambiar_colores(self, principal, secundario):
        self.lienzo.color_principal = principal
        self.lienzo.color_secundario = secundario

        # 1. Actualizamos los colores de uso directo en el lienzo
        self.lienzo.color_actual_uso = principal

        # 2. Notificamos al panel de texto para que actualice la muestra visual del borde
        self.panel_texto.set_color_secundario(secundario)

        # 3. Actualizamos la caja interactiva activa (si existe)
        if self.lienzo.editor_texto:
            self.lienzo.editor_texto.color = principal
            borde, sombra = self.panel_texto.obtener_configuraciones()
            self.lienzo.config_borde = borde
            self.lienzo.config_sombra = sombra
            self.lienzo.editor_texto.actualizar_estilo()

        # 4. Redibujamos el lienzo en vivo
        self.lienzo.update()


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
        QGroupBox {
            font-weight: bold;
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
            color: #2a82da;
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
