from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from tools.base_tool import BaseTool

class EyedropperTool(BaseTool):
    def __init__(self):
        super().__init__("Cuentagotas", "gui/iconos/eyedropper.png")

    def mouse_press(self, canvas, event, color_activo=None):
        pos = event.position().toPoint()
        x, y = pos.x(), pos.y()

        qimg = canvas.layer_mgr.buffer
        if 0 <= x < qimg.width() and 0 <= y < qimg.height():
            pixel_color = qimg.pixelColor(x, y)

            main_win = getattr(canvas, 'main_window', None)
            if not main_win and hasattr(canvas, 'parent'):
                p = canvas.parent()
                while p:
                    if hasattr(p, 'color_panel'):
                        main_win = p
                        break
                    p = p.parent() if hasattr(p, 'parent') else None

            if event.button() == Qt.MouseButton.LeftButton:
                canvas.color_primario = pixel_color
                if main_win and hasattr(main_win, 'color_panel'):
                    main_win.color_panel.modo_color = "primario"
                    main_win.color_panel.set_color_activo(pixel_color)
            elif event.button() == Qt.MouseButton.RightButton:
                canvas.color_secundario = pixel_color
                if main_win and hasattr(main_win, 'color_panel'):
                    main_win.color_panel.modo_color = "secundario"
                    main_win.color_panel.set_color_activo(pixel_color)

            canvas.update()
