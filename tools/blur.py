from tools.base_tool import BaseTool

class BlurTool(BaseTool):
    def __init__(self):
        super().__init__("Difuminar", "gui/iconos/blur.png")

    def mouse_press(self, canvas, event, color_activo=None):
        pass
