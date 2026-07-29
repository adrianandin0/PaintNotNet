from gui.dialogo_opciones import DialogoOpciones

class MenuOpciones:
    """Clase para construir el menú Opciones en la barra principal."""
    def __init__(self, main_window):
        self.main_window = main_window

    def crear_menu(self, menu_bar):
        menu = menu_bar.addMenu("Opciones")

        action_pref = menu.addAction("Preferencias de Usuario...")
        action_pref.triggered.connect(self._abrir_preferencias)

    def _abrir_preferencias(self):
        dlg = DialogoOpciones(self.main_window)
        dlg.exec()
