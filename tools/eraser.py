from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush
from tools.base_tool import BaseTool

class EraserTool(BaseTool):
    def __init__(self):
        super().__init__("Goma de Borrar", "gui/iconos/eraser.png")
        self.last_point = QPoint()
        self.is_drawing = False

    def draw_handles(self, painter, canvas):
        if canvas.cursor_pos is None:
            return
        pos = canvas.cursor_pos
        size = max(1, getattr(canvas, 'grosor_pincel', 3))
        radius = size / 2.0

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 1. Borde exterior oscuro para contraste en fondos claros/blancos
        pen_outer = QPen(QColor(0, 0, 0, 200), 1.5)
        painter.setPen(pen_outer)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(pos, radius + 0.5, radius + 0.5)

        # 2. Círculo blanco para la goma de borrar
        pen_inner = QPen(QColor(255, 255, 255, 255), 1.0)
        painter.setPen(pen_inner)

        col_fill = QColor(255, 255, 255, 80)
        painter.setBrush(QBrush(col_fill))

        painter.drawEllipse(pos, radius, radius)
        painter.restore()

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.is_drawing = True
            self.last_point = event.position().toPoint()
            self._erase(canvas, self.last_point, self.last_point)
            canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        if self.is_drawing:
            current_point = event.position().toPoint()
            self._erase(canvas, self.last_point, current_point)
            self.last_point = current_point
            if canvas.callback_modificado:
                canvas.callback_modificado()
            canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        self.is_drawing = False

    def _erase(self, canvas, p1, p2):
        qimg = canvas.layer_mgr.buffer
        painter = QPainter(qimg)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)

        if getattr(canvas, 'suavizado_pincel', True):
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        grosor = max(1, getattr(canvas, 'grosor_pincel', 3))
        pen = QPen(Qt.GlobalColor.transparent, grosor, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        if p1 == p2:
            painter.drawPoint(p1)
        else:
            painter.drawLine(p1, p2)

        painter.end()
