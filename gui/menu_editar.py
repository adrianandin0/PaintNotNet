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
        menu_editar = menu_bar.addMenu("Editar")

        # 1. Deshacer / Rehacer
        accion_deshacer = menu_editar.addAction("Deshacer")
        accion_deshacer.setShortcut("Ctrl+Z")
        accion_deshacer.triggered.connect(self.deshacer)

        accion_rehacer = menu_editar.addAction("Rehacer")
        accion_rehacer.setShortcut("Ctrl+Y")
        accion_rehacer.triggered.connect(self.rehacer)

        menu_editar.addSeparator()

        # 2. Cortar / Copiar / Pegar
        accion_cortar = menu_editar.addAction("Cortar")
        accion_cortar.setShortcut("Ctrl+X")
        accion_cortar.triggered.connect(self.cortar)

        accion_copiar = menu_editar.addAction("Copiar")
        accion_copiar.setShortcut("Ctrl+C")
        accion_copiar.triggered.connect(self.copiar)

        accion_pegar = menu_editar.addAction("Pegar")
        accion_pegar.setShortcut("Ctrl+V")
        accion_pegar.triggered.connect(self.pegar)

        menu_editar.addSeparator()

        # 3. Selecciones y Borrado
        accion_sel_todo = menu_editar.addAction("Seleccionar todo")
        accion_sel_todo.setShortcut("Ctrl+A")
        accion_sel_todo.triggered.connect(self.seleccionar_todo)

        accion_borrar_sel = menu_editar.addAction("Borrar selección")
        accion_borrar_sel.setShortcut("Delete")
        accion_borrar_sel.triggered.connect(self.borrar_seleccion)

        accion_borrar_todo = menu_editar.addAction("Borrar todo")
        accion_borrar_todo.setShortcut("Ctrl+Shift+Delete")
        accion_borrar_todo.triggered.connect(self.borrar_todo)
