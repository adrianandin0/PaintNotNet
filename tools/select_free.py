import math
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF
from PyQt6.QtGui import QPainterPath, QPen, QColor
from PyQt6.QtWidgets import QApplication
from tools.base_tool import BaseTool


class SelectFreeTool(BaseTool):
    def __init__(self):
        super().__init__("Selección Libre", "gui/iconos/select_free.png")
        self.points = []
        self.is_selecting = False
        self.hover_point = QPoint()

    def _get_pixel_pos(self, event):
        return QPoint(int(math.floor(event.position().x())), int(math.floor(event.position().y())))

    def mouse_press(self, canvas, event, color_activo=None):
        engine = canvas.selection_engine
        hit = engine.hit_test(event.position(), canvas.scale_factor) if engine.has_selection() else engine.HANDLE_NONE

        if hit != engine.HANDLE_NONE and not self.is_selecting:
            engine.begin_transform(event.position(), event.button(), hit)
            return

        pos = self._get_pixel_pos(event)

        if not self.is_selecting:
            self.points = [pos]
            self.hover_point = pos
            self.is_selecting = True
        else:
            if len(self.points) > 2:
                self._cerrar_seleccion(canvas)
            else:
                self.is_selecting = False
                self.points.clear()

        canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        engine = canvas.selection_engine
        if engine.is_moving or engine.is_rotating:
            is_shift = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier)
            engine.update_transform(event.position(), is_shift=is_shift)
            canvas.update()
        elif self.is_selecting:
            pos = self._get_pixel_pos(event)
            self.hover_point = pos

            if not self.points or (pos - self.points[-1]).manhattanLength() > 2:
                self.points.append(pos)

            if len(self.points) > 10:
                dist_origen = (pos - self.points[0]).manhattanLength()
                if dist_origen <= 10:
                    self._cerrar_seleccion(canvas)

            canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        engine = canvas.selection_engine
        if engine.is_moving or engine.is_rotating:
            engine.end_transform()

    def key_press(self, canvas, event, color_activo=None):
        if event.key() == Qt.Key.Key_Escape and self.is_selecting:
            self.is_selecting = False
            self.points.clear()
            canvas.update()
            return True
        return False

    def _cerrar_seleccion(self, canvas):
        if len(self.points) > 2:
            path = QPainterPath()
            path.moveTo(QPointF(self.points[0]))
            for p in self.points[1:]:
                path.lineTo(QPointF(p))
            path.closeSubpath()

            canvas.selection_engine.set_path(path)
            canvas.push_document_state("Selección Libre", force=True)
            if hasattr(canvas, 'main_window') and canvas.main_window:
                canvas.main_window.activar_herramienta_mover()

        self.is_selecting = False
        self.points.clear()
        canvas.update()

    def draw_handles(self, painter, canvas):
        if self.is_selecting and self.points:
            pen = QPen(QColor(0, 120, 215), 1, Qt.PenStyle.DashLine)
            pen.setCosmetic(True)
            painter.setPen(pen)

            for i in range(len(self.points) - 1):
                painter.drawLine(self.points[i], self.points[i+1])

            if self.hover_point:
                painter.drawLine(self.points[-1], self.hover_point)

            sf = max(0.001, getattr(canvas, 'scale_factor', 1.0))
            r_sz = 5.0 / sf
            pen_red = QPen(QColor(255, 0, 0), 2)
            pen_red.setCosmetic(True)
            painter.setPen(pen_red)
            painter.drawEllipse(QRectF(float(self.points[0].x()) - r_sz, float(self.points[0].y()) - r_sz, r_sz * 2.0, r_sz * 2.0))
