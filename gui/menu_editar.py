from PyQt6.QtGui import QKeySequence, QIcon


class MenuEditar:
    def __init__(self, ventana_principal):
        self.ventana = ventana_principal

    def _get_canvas(self):
        return getattr(self.ventana, 'canvas', getattr(self.ventana, 'lienzo', None))

    def deshacer(self):
        c = self._get_canvas()
        if c:
            c.deshacer()

    def rehacer(self):
        c = self._get_canvas()
        if c:
            c.rehacer()

    def cortar(self):
        c = self._get_canvas()
        if c:
            c.cortar_seleccion()

    def copiar(self):
        c = self._get_canvas()
        if c:
            c.copiar_seleccion()

    def pegar(self):
        c = self._get_canvas()
        if c:
            c.pegar_portapapeles()
        if hasattr(self.ventana, 'activar_herramienta_mover'):
            self.ventana.activar_herramienta_mover()

    pegar_y_sincronizar = pegar

    def seleccionar_todo(self):
        c = self._get_canvas()
        if c:
            c.seleccionar_todo()
        if hasattr(self.ventana, 'activar_herramienta_mover'):
            self.ventana.activar_herramienta_mover()

    seleccionar_todo_y_sincronizar = seleccionar_todo

    def borrar_seleccion(self):
        c = self._get_canvas()
        if c:
            c.borrar_seleccion()

    def borrar_todo(self):
        c = self._get_canvas()
        if c:
            c.borrar_todo()

    def crear_menu(self, menu_bar):
        self.menu_bar = menu_bar
        self.retraducir_menu()

    def retraducir_menu(self):
        from core.i18n import t
        if hasattr(self, 'menu_editar') and self.menu_editar:
            self.menu_bar.removeAction(self.menu_editar.menuAction())

        self.menu_editar = self.menu_bar.addMenu(t("Editar"))

        # 1. Deshacer / Rehacer
        accion_deshacer = self.menu_editar.addAction(QIcon("gui/iconos/back.png"), t("Deshacer"))
        accion_deshacer.setShortcut("Ctrl+Z")
        accion_deshacer.triggered.connect(self.deshacer)

        accion_rehacer = self.menu_editar.addAction(QIcon("gui/iconos/forward.png"), t("Rehacer"))
        accion_rehacer.setShortcut("Ctrl+Y")
        accion_rehacer.triggered.connect(self.rehacer)

        self.menu_editar.addSeparator()

        # 2. Cortar / Copiar / Pegar
        accion_cortar = self.menu_editar.addAction(QIcon("gui/iconos/cut.png"), t("Cortar"))
        accion_cortar.setShortcut("Ctrl+X")
        accion_cortar.triggered.connect(self.cortar)

        accion_copiar = self.menu_editar.addAction(QIcon("gui/iconos/copy.png"), t("Copiar"))
        accion_copiar.setShortcut("Ctrl+C")
        accion_copiar.triggered.connect(self.copiar)

        accion_pegar = self.menu_editar.addAction(QIcon("gui/iconos/paste.png"), t("Pegar"))
        accion_pegar.setShortcut("Ctrl+V")
        accion_pegar.triggered.connect(self.pegar)

        self.menu_editar.addSeparator()

        # 3. Selecciones y Borrado
        accion_sel_todo = self.menu_editar.addAction(QIcon("gui/iconos/move_select_pixels.png"), t("Seleccionar Todo"))
        accion_sel_todo.setShortcut("Ctrl+A")
        accion_sel_todo.triggered.connect(self.seleccionar_todo)

        accion_desel = self.menu_editar.addAction(QIcon("gui/iconos/cancel.png"), t("Deseleccionar"))
        accion_desel.setShortcut("Ctrl+D")
        accion_desel.triggered.connect(self.desechar_seleccion)

        accion_invert = self.menu_editar.addAction(QIcon("gui/iconos/invert.png"), t("Invertir Selección"))
        accion_invert.setShortcut("Ctrl+I")
        accion_invert.triggered.connect(self.invertir_seleccion)

        self.menu_editar.addSeparator()

        accion_borrar_sel = self.menu_editar.addAction(QIcon("gui/iconos/bin.png"), t("Eliminar Selección"))
        accion_borrar_sel.setShortcut(QKeySequence.StandardKey.Delete)
        accion_borrar_sel.triggered.connect(self.borrar_seleccion)

    def desechar_seleccion(self):
        c = self._get_canvas()
        if c and hasattr(c, 'selection_engine'):
            c.selection_engine.clear_selection()
            c.update()

    def invertir_seleccion(self):
        c = self._get_canvas()
        if c and hasattr(c, 'invertir_seleccion'):
            c.invertir_seleccion()
