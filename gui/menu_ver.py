class MenuVer:
    """Clase para construir el menú Ver con conmutadores de visibilidad de paneles."""
    def __init__(self, main_window):
        self.main_window = main_window

    def crear_menu(self, menu_bar):
        menu = menu_bar.addMenu("Ver")

        self._add_toggle(menu, "Panel de herramientas", 'tools_dock')
        self._add_toggle(menu, "Panel de colores", 'color_dock')
        self._add_toggle(menu, "Panel de color avanzado", 'advanced_color_dock')
        self._add_toggle(menu, "Panel de texto", 'text_dock')
        self._add_toggle(menu, "Panel de capas", 'layers_dock')
        self._add_toggle(menu, "Panel de pincel", 'stroke_dock')
        self._add_toggle(menu, "Panel de historial", 'history_dock')

    def _add_toggle(self, menu, title, dock_attr):
        if hasattr(self.main_window, dock_attr):
            dock = getattr(self.main_window, dock_attr)
            action = dock.toggleViewAction()
            action.setText(title)
            menu.addAction(action)
