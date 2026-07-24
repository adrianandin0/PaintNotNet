from PyQt6.QtGui import QAction

class MenuImagen:
    def __init__(self, ventana_principal):
        self.ventana = ventana_principal

    def crear_menu(self, menu_bar):
        menu = menu_bar.addMenu("Imagen")

        accion_tamano_lienzo = QAction("Tamaño del Lienzo...", self.ventana)
        menu.addAction(accion_tamano_lienzo)

        accion_tamano_imagen = QAction("Tamaño de la Imagen...", self.ventana)
        menu.addAction(accion_tamano_imagen)

        menu.addSeparator()

        accion_voltear_h = QAction("Voltear Horizontalmente", self.ventana)
        menu.addAction(accion_voltear_h)

        accion_voltear_v = QAction("Voltear Verticalmente", self.ventana)
        menu.addAction(accion_voltear_v)

        accion_rotar = QAction("Rotar 90°", self.ventana)
        menu.addAction(accion_rotar)
