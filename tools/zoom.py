from PyQt6.QtCore import Qt
from tools.base_tool import BaseTool

class ZoomTool(BaseTool):
    def __init__(self):
        super().__init__("Zoom", "gui/iconos/zoom.png")

    def mouse_press(self, canvas, event, color_activo=None):
        if hasattr(canvas, 'set_zoom'):
            if event.button() == Qt.MouseButton.LeftButton:
                canvas.set_zoom(canvas.scale_factor * 1.25)
            elif event.button() == Qt.MouseButton.RightButton:
                canvas.set_zoom(canvas.scale_factor / 1.25)
