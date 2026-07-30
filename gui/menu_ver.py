class MenuVer:
    """Clase para construir el menú Ver con conmutadores de visibilidad de paneles."""
    def __init__(self, main_window):
        self.main_window = main_window

    def crear_menu(self, menu_bar):
        self.menu_bar = menu_bar
        self.retraducir_menu()

    def retraducir_menu(self):
        from core.i18n import t
        if hasattr(self, 'menu') and self.menu:
            self.menu_bar.removeAction(self.menu.menuAction())

        self.menu = self.menu_bar.addMenu(t("Ver"))

        self._add_toggle(self.menu, t("Herramientas"), 'tools_dock')
        self._add_toggle(self.menu, t("Color"), 'color_dock')
        self._add_toggle(self.menu, t("Capas"), 'layers_dock')
        self._add_toggle(self.menu, t("Historial"), 'history_dock')

    def _add_toggle(self, menu, title, dock_attr):
        if hasattr(self.main_window, dock_attr):
            dock = getattr(self.main_window, dock_attr)
            action = dock.toggleViewAction()
            action.setText(title)
            menu.addAction(action)
