from tools.base_tool import BaseTool

class InvertSelectionTool(BaseTool):
    def __init__(self):
        super().__init__("Invertir Selección", "gui/iconos/invert.png")

    def mouse_press(self, canvas, event, color_activo=None):
        pass
