class MenuEditar:
    def __init__(self, ventana_principal):
        self.ventana = ventana_principal

    def crear_menu(self, menu_bar):
        menu_editar = menu_bar.addMenu("Editar")

        # 1. Deshacer / Rehacer
        accion_deshacer = menu_editar.addAction("Deshacer")
        accion_deshacer.setShortcut("Ctrl+Z")
        accion_deshacer.triggered.connect(self.ventana.lienzo.deshacer)

        accion_rehacer = menu_editar.addAction("Rehacer")
        accion_rehacer.setShortcut("Ctrl+Y")
        accion_rehacer.triggered.connect(self.ventana.lienzo.rehacer)

        menu_editar.addSeparator()

        # 2. Cortar / Copiar / Pegar
        accion_cortar = menu_editar.addAction("Cortar")
        accion_cortar.setShortcut("Ctrl+X")
        accion_cortar.triggered.connect(self.ventana.lienzo.cortar_seleccion)

        accion_copiar = menu_editar.addAction("Copiar")
        accion_copiar.setShortcut("Ctrl+C")
        accion_copiar.triggered.connect(self.ventana.lienzo.copiar_seleccion)

        accion_pegar = menu_editar.addAction("Pegar")
        accion_pegar.setShortcut("Ctrl+V")
        accion_pegar.triggered.connect(self.pegar_y_sincronizar)

        menu_editar.addSeparator()

        # 3. Selecciones y Borrado
        accion_sel_todo = menu_editar.addAction("Seleccionar todo")
        accion_sel_todo.setShortcut("Ctrl+A")
        accion_sel_todo.triggered.connect(self.seleccionar_todo_y_sincronizar)

        accion_borrar_sel = menu_editar.addAction("Borrar selección")
        accion_borrar_sel.setShortcut("Delete")
        accion_borrar_sel.triggered.connect(self.ventana.lienzo.borrar_seleccion)

        accion_borrar_todo = menu_editar.addAction("Borrar todo")
        accion_borrar_todo.setShortcut("Ctrl+Shift+Delete")
        accion_borrar_todo.triggered.connect(self.ventana.lienzo.borrar_todo)

    def pegar_y_sincronizar(self):
        self.ventana.lienzo.pegar_portapapeles()
        if hasattr(self.ventana, 'panel_herramientas'):
            self.ventana.panel_herramientas.seleccionar("seleccion")

    def seleccionar_todo_y_sincronizar(self):
        self.ventana.lienzo.seleccionar_todo()
        if hasattr(self.ventana, 'panel_herramientas'):
            self.ventana.panel_herramientas.seleccionar("seleccion")
