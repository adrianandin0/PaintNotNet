from PyQt6.QtCore import Qt, QPoint, QPointF
from PyQt6.QtGui import QPainterPath, QPen, QColor
from tools.base_tool import BaseTool


class SelectFreeTool(BaseTool):
    def __init__(self):
        super().__init__("Selección Libre", "gui/iconos/select_free.png")
        self.points = []
        self.is_selecting = False
        self.hover_point = QPoint()

    def mouse_press(self, canvas, event, color_activo=None):
        pos = event.position().toPoint()

        if not self.is_selecting:
            self.points = [pos]
            self.hover_point = pos
            self.is_selecting = True
        else:
            first_point = self.points[0]
            distancia = (pos - first_point).manhattanLength()

            # Si hace clic a <= 5px del primer punto, se cierra la selección
            if distancia <= 5 and len(self.points) > 2:
                self._cerrar_seleccion(canvas)
            else:
                self.points.append(pos)
                self.hover_point = pos

        canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        if self.is_selecting:
            self.hover_point = event.position().toPoint()
            canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        pass

    def key_press(self, canvas, event, color_activo=None):
        if event.key() == Qt.Key.Key_Escape and self.is_selecting:
            self.is_selecting = False
            self.points.clear()
            canvas.update()
            return True
        return False

    def _cerrar_seleccion(self, canvas):
        path = QPainterPath()
        # Convertimos explícitamente los QPoint a QPointF para PyQt6
        path.moveTo(QPointF(self.points[0]))
        for p in self.points[1:]:
            path.lineTo(QPointF(p))
        path.closeSubpath()

        canvas.selection_engine.set_path(path)
        self.is_selecting = False
        self.points.clear()

    def draw_preview(self, painter, canvas):
        if self.is_selecting and self.points:
            pen = QPen(QColor(0, 120, 215), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)

            for i in range(len(self.points) - 1):
                painter.drawLine(self.points[i], self.points[i+1])

            painter.drawLine(self.points[-1], self.hover_point)

            # Punto de origen resaltado para fácil atino
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.drawEllipse(self.points[0], 4, 4)
