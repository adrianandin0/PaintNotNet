from PyQt6.QtGui import QIcon
from gui.dialogo_opciones import DialogoOpciones

class MenuOpciones:
    """Clase para construir el menú Opciones en la barra principal."""
    def __init__(self, main_window):
        self.main_window = main_window

    def crear_menu(self, menu_bar):
        self.menu_bar = menu_bar
        self.retraducir_menu()

    def retraducir_menu(self):
        from core.i18n import t
        if hasattr(self, 'menu') and self.menu:
            self.menu_bar.removeAction(self.menu.menuAction())

        self.menu = self.menu_bar.addMenu(t("Opciones"))

        action_pref = self.menu.addAction(QIcon("gui/iconos/config.png"), t("Preferencias de usuario..."))
        action_pref.triggered.connect(self._abrir_preferencias)

        action_atajos = self.menu.addAction(QIcon("gui/iconos/keyboard.png"), t("Atajos de teclado..."))
        action_atajos.triggered.connect(self._abrir_atajos)

    def _abrir_preferencias(self):
        dlg = DialogoOpciones(self.main_window)
        dlg.exec()

    def _abrir_atajos(self):
        from gui.dialogo_atajos import DialogoAtajos
        dlg = DialogoAtajos(self.main_window)
        if dlg.exec():
            if hasattr(self.main_window, 'tool_panel'):
                self.main_window.tool_panel.actualizar_insignias_atajos()
