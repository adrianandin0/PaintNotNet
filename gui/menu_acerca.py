from gui.dialogo_acerca import DialogoAcerca

class MenuAcerca:
    """Clase para construir el menú 'Acerca de...' en la barra principal."""
    def __init__(self, main_window):
        self.main_window = main_window

    def crear_menu(self, menu_bar):
        action = menu_bar.addAction("Acerca de...")
        action.triggered.connect(self._abrir_acerca)

    def _abrir_acerca(self):
        dlg = DialogoAcerca(self.main_window)
        dlg.exec()
