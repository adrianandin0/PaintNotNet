from PyQt6.QtGui import QAction

class MenuEditar:
    def __init__(self, ventana_principal):
        self.ventana = ventana_principal

    def crear_menu(self, menu_bar):
        menu = menu_bar.addMenu("Editar")

        accion_deshacer = QAction("Deshacer", self.ventana)
        menu.addAction(accion_deshacer)

        accion_rehacer = QAction("Rehacer", self.ventana)
        menu.addAction(accion_rehacer)

        menu.addSeparator()

        accion_cortar = QAction("Cortar", self.ventana)
        menu.addAction(accion_cortar)

        accion_copiar = QAction("Copiar", self.ventana)
        menu.addAction(accion_copiar)

        accion_pegar = QAction("Pegar", self.ventana)
        menu.addAction(accion_pegar)

        accion_borrar = QAction("Borrar Selección", self.ventana)
        menu.addAction(accion_borrar)
