from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QIcon

class _MenuVerSticky(QMenu):
    """QMenu que no se cierra al hacer clic en acciones checkables."""
    def mouseReleaseEvent(self, event):
        action = self.activeAction()
        if action and action.isCheckable():
            action.trigger()
            return  # no cerrar
        super().mouseReleaseEvent(event)


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

        self.menu = _MenuVerSticky(t("Ver"), self.menu_bar)
        self.menu_bar.addMenu(self.menu)

        self._add_toggle(self.menu, t("Herramientas"),   'tools_dock',          "gui/iconos/tools.png")
        self._add_toggle(self.menu, t("Color"),           'color_dock',          "gui/iconos/color.png")
        self._add_toggle(self.menu, t("Capas"),           'layers_dock',         "gui/iconos/layers.png")
        self._add_toggle(self.menu, t("Historial"),       'history_dock',        "gui/iconos/history.png")
        self._add_toggle(self.menu, t("Color avanzado"), 'advanced_color_dock',  "gui/iconos/color-plus.png")

        self.menu.addSeparator()

        accion_reset = self.menu.addAction(QIcon("gui/iconos/reset.png"), t("Restablecer paneles"))
        accion_reset.triggered.connect(self._restablecer_paneles)

    def _add_toggle(self, menu, title, dock_attr, icono_path=None):
        if hasattr(self.main_window, dock_attr):
            dock = getattr(self.main_window, dock_attr)
            action = dock.toggleViewAction()
            action.setText(title)
            if icono_path:
                action.setIcon(QIcon(icono_path))
            menu.addAction(action)

    def _restablecer_paneles(self):
        """Muestra todos los paneles laterales."""
        docks = [
            'tools_dock', 'color_dock',
            'layers_dock', 'history_dock', 'advanced_color_dock'
        ]
        for attr in docks:
            if hasattr(self.main_window, attr):
                dock = getattr(self.main_window, attr)
                dock.setVisible(True)
