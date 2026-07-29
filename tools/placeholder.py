from tools.base_tool import BaseTool

class PlaceholderTool(BaseTool):
    def __init__(self, id_num):
        super().__init__(f"Reservado {id_num}", "")

    def mouse_press(self, canvas, event, color_activo=None):
        pass
