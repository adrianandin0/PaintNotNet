from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QLinearGradient, QBrush
from tools.base_tool import BaseTool


class GradientTool(BaseTool):
    def __init__(self):
        super().__init__("Degradado", "gui/iconos/gradient.png")
        self.p_start = None
        self.p_end = None
        self.is_dragging = False

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            self.p_start = QPointF(pos)
            self.p_end = QPointF(pos)
            self.is_dragging = True
            canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        if self.is_dragging:
            self.p_end = QPointF(event.position())
            canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        if self.is_dragging and event.button() == Qt.MouseButton.LeftButton:
            self.p_end = QPointF(event.position())
            self.is_dragging = False
            self.commit_gradient(canvas)

    def commit_gradient(self, canvas):
        if not self.p_start or not self.p_end:
            return

        if self.p_start == self.p_end:
            self.p_start = QPointF(0, 0)
            self.p_end = QPointF(canvas.layer_mgr.width, 0)

        painter = QPainter(canvas.layer_mgr.buffer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        if canvas.selection_engine.has_selection():
            painter.setClipPath(canvas.selection_engine.active_path)

        grad = QLinearGradient(self.p_start, self.p_end)
        grad.setColorAt(0.0, canvas.color_primario)
        grad.setColorAt(1.0, canvas.color_secundario)

        brush = QBrush(grad)
        w, h = canvas.layer_mgr.width, canvas.layer_mgr.height
        painter.fillRect(0, 0, w, h, brush)
        painter.end()

        self.p_start = None
        self.p_end = None
        canvas.actualizar_historial_gui()
        canvas.update()

    def draw_preview(self, painter, canvas):
        if self.is_dragging and self.p_start and self.p_end:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            if canvas.selection_engine.has_selection():
                painter.setClipPath(canvas.selection_engine.active_path)

            grad = QLinearGradient(self.p_start, self.p_end)
            grad.setColorAt(0.0, canvas.color_primario)
            grad.setColorAt(1.0, canvas.color_secundario)

            brush = QBrush(grad)
            w, h = canvas.layer_mgr.width, canvas.layer_mgr.height
            painter.fillRect(0, 0, w, h, brush)
            painter.restore()

            pen = QPen(QColor(255, 255, 255), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawLine(self.p_start, self.p_end)

            s = 8
            s2 = s / 2.0
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.setBrush(QBrush(canvas.color_primario))
            painter.drawEllipse(QRectF(self.p_start.x() - s2, self.p_start.y() - s2, s, s))

            painter.setBrush(QBrush(canvas.color_secundario))
            painter.drawEllipse(QRectF(self.p_end.x() - s2, self.p_end.y() - s2, s, s))
