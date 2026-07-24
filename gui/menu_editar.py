from PyQt6.QtGui import QAction, QKeySequence

class MenuEditar:
    def __init__(self, ventana_principal):
        self.ventana = ventana_principal

    def crear_menu(self, menu_bar):
        menu = menu_bar.addMenu("Editar")

        accion_cortar = QAction("Cortar", self.ventana)
        accion_cortar.setShortcut(QKeySequence.StandardKey.Cut)
        accion_cortar.triggered.connect(lambda: self.ventana.lienzo.cortar_seleccion())
        menu.addAction(accion_cortar)

        accion_copiar = QAction("Copiar", self.ventana)
        accion_copiar.setShortcut(QKeySequence.StandardKey.Copy)
        accion_copiar.triggered.connect(lambda: self.ventana.lienzo.copiar_seleccion())
        menu.addAction(accion_copiar)

        accion_pegar = QAction("Pegar", self.ventana)
        accion_pegar.setShortcut(QKeySequence.StandardKey.Paste)
        accion_pegar.triggered.connect(lambda: self.ventana.lienzo.pegar_portapapeles())
        menu.addAction(accion_pegar)

        accion_borrar = QAction("Borrar Selección", self.ventana)
        accion_borrar.setShortcut(QKeySequence.StandardKey.Delete)
        accion_borrar.triggered.connect(lambda: self.ventana.lienzo.borrar_seleccion())
        menu.addAction(accion_borrar)
