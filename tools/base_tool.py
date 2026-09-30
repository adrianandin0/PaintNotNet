class BaseTool:
    """Clase base para todas las herramientas de PaintNotNet."""
    def __init__(self, name="Base", icon_path="gui/iconos/default.png"):
        self.name = name
        self.icon_path = icon_path

    def mouse_press(self, canvas, event, color_activo=None):
        pass

    def mouse_move(self, canvas, event, color_activo=None):
        pass

    def mouse_release(self, canvas, event, color_activo=None):
        pass

    def draw_preview(self, painter, canvas):
        pass

    def key_press(self, canvas, event, color_activo=None):
        return False

