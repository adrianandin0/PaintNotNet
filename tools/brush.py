from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath, QImage
from tools.base_tool import BaseTool

class BrushTool(BaseTool):
    def __init__(self):
        super().__init__("Pincel", "gui/iconos/brush.png")
        self.is_drawing = False
        self.path = None

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.is_drawing = True
            pos = event.position()
            self.path = QPainterPath()
            self.path.moveTo(pos)
            self.path.lineTo(pos.x() + 0.001, pos.y() + 0.001)

            if canvas.capa_trazo_temp.size() != canvas.layer_mgr.buffer.size():
                canvas.capa_trazo_temp = QImage(canvas.layer_mgr.buffer.size(), QImage.Format.Format_ARGB32_Premultiplied)
            canvas.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

            self._draw_stroke(canvas, color_activo)
            canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        if self.is_drawing and self.path:
            self.path.lineTo(event.position())
            self._draw_stroke(canvas, color_activo)

            if canvas.callback_modificado:
                canvas.callback_modificado()
            canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        if self.is_drawing:
            buffer = canvas.layer_mgr.buffer
            painter = QPainter(buffer)
            painter.drawImage(0, 0, canvas.capa_trazo_temp)
            painter.end()

            canvas.capa_trazo_temp.fill(Qt.GlobalColor.transparent)
            self.path = None
            self.is_drawing = False
            canvas.update()

    def _draw_stroke(self, canvas, color_activo):
        canvas.capa_trazo_temp.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas.capa_trazo_temp)
        color = QColor(color_activo if color_activo else canvas.color_primario)

        suavizado = getattr(canvas, 'suavizado_pincel', True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, suavizado)

        # El pincel es siempre redondo
        pen = QPen(color, max(1, canvas.grosor_pincel), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        if self.path:
            painter.drawPath(self.path)
        painter.end()
