class BaseTool:
    """Clase base para todas las herramientas de PaintNotNet."""
    def __init__(self, name="Base", icon_path="gui/iconos/default.png"):
        self.name = name
        self.icon_path = icon_path

    def mouse_press(self, canvas, event):
        pass

    def mouse_move(self, canvas, event):
        pass

    def mouse_release(self, canvas, event):
        pass
