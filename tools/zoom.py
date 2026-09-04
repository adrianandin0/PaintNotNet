from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QPen, QColor
from tools.base_tool import BaseTool


class ZoomTool(BaseTool):
    def __init__(self):
        super().__init__("Zoom", "gui/iconos/zoom.png")
        self.start_point = QPoint()
        self.current_point = QPoint()
        self.is_dragging = False
        self.button_pressed = Qt.MouseButton.LeftButton

    def mouse_press(self, canvas, event, color_activo=None):
        pos = event.position().toPoint()
        self.start_point = pos
        self.current_point = pos
        self.is_dragging = True
        self.button_pressed = event.button()
        canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        if self.is_dragging:
            self.current_point = event.position().toPoint()
            canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        if self.is_dragging:
            self.is_dragging = False
            rect = QRect(self.start_point, self.current_point).normalized()

            # Si se arrastró un área rectangular significativa (> 5px en ancho y alto)
            if rect.width() > 5 and rect.height() > 5:
                if hasattr(canvas, 'zoom_to_rect'):
                    canvas.zoom_to_rect(rect)
                elif hasattr(canvas, 'set_zoom'):
                    canvas.set_zoom(canvas.scale_factor * 1.5)
            else:
                # Clic puntual sin arrastre
                if self.button_pressed == Qt.MouseButton.LeftButton:
                    if hasattr(canvas, 'zoom_at_point'):
                        canvas.zoom_at_point(self.start_point, canvas.scale_factor * 1.25)
                    elif hasattr(canvas, 'set_zoom'):
                        canvas.set_zoom(canvas.scale_factor * 1.25)
                elif self.button_pressed == Qt.MouseButton.RightButton:
                    if hasattr(canvas, 'zoom_at_point'):
                        canvas.zoom_at_point(self.start_point, canvas.scale_factor / 1.25)
                    elif hasattr(canvas, 'set_zoom'):
                        canvas.set_zoom(canvas.scale_factor / 1.25)

            canvas.update()

    def draw_handles(self, painter, canvas):
        if self.is_dragging:
            rect = QRect(self.start_point, self.current_point).normalized()
            if rect.width() > 1 and rect.height() > 1:
                painter.save()
                pen_dark = QPen(QColor(0, 0, 0, 200), 1, Qt.PenStyle.SolidLine)
                pen_dark.setCosmetic(True)
                pen_light = QPen(QColor(0, 120, 215), 1, Qt.PenStyle.DashLine)
                pen_light.setCosmetic(True)

                painter.setPen(pen_dark)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(rect)
                painter.setPen(pen_light)
                painter.drawRect(rect)
                painter.restore()
