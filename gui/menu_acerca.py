from gui.dialogo_acerca import DialogoAcerca

class MenuAcerca:
    """Clase para construir el menú 'Acerca de...' en la barra principal."""
    def __init__(self, main_window):
        self.main_window = main_window

    def crear_menu(self, menu_bar):
        self.menu_bar = menu_bar
        self.retraducir_menu()

    def retraducir_menu(self):
        from core.i18n import t
        if hasattr(self, 'action') and self.action:
            self.menu_bar.removeAction(self.action)

        self.action = self.menu_bar.addAction(t("Acerca de..."))
        self.action.triggered.connect(self._abrir_acerca)

    def _abrir_acerca(self):
        dlg = DialogoAcerca(self.main_window)
        dlg.exec()
