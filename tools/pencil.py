from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush
from tools.base_tool import BaseTool

class PencilTool(BaseTool):
    def __init__(self):
        super().__init__("Lápiz", "gui/iconos/pencil.png")
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

        col_pri = QColor(canvas.color_primario)

        # 1. Borde exterior negro para contraste
        pen_outer = QPen(QColor(0, 0, 0, 180), 1.5)
        painter.setPen(pen_outer)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(pos, radius + 0.5, radius + 0.5)

        # 2. Círculo interior con el color elegido
        col_rim = QColor(col_pri)
        col_rim.setAlpha(255)
        pen_inner = QPen(col_rim, 1.0)
        painter.setPen(pen_inner)

        col_fill = QColor(col_pri)
        col_fill.setAlpha(40)
        painter.setBrush(QBrush(col_fill))

        painter.drawEllipse(pos, radius, radius)
        painter.restore()

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.is_drawing = True
            self.last_point = event.position().toPoint()
            color = QColor(color_activo if color_activo else canvas.color_primario)
            color.setAlpha(255)  # Lápiz es siempre 100% sólido, sin alpha

            w = max(1, canvas.grosor_pincel)
            buffer = canvas.layer_mgr.buffer
            painter = QPainter(buffer)
            canvas.aplicar_clip_seleccion(painter)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)  # Lápiz sin suavizado
            x, y = self.last_point.x(), self.last_point.y()
            offset = w // 2
            painter.fillRect(x - offset, y - offset, w, w, color)
            painter.end()
            canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        if self.is_drawing:
            current_point = event.position().toPoint()
            color = QColor(color_activo if color_activo else canvas.color_primario)
            color.setAlpha(255)  # Lápiz es siempre 100% sólido, sin alpha

            w = max(1, canvas.grosor_pincel)
            buffer = canvas.layer_mgr.buffer
            painter = QPainter(buffer)
            canvas.aplicar_clip_seleccion(painter)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)  # Lápiz sin suavizado
            pen = QPen(color, w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
            painter.setPen(pen)
            painter.drawLine(self.last_point, current_point)
            painter.end()

            self.last_point = current_point
            if canvas.callback_modificado:
                canvas.callback_modificado()
            canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        self.is_drawing = False
