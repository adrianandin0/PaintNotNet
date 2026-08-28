import math
import random
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QImage
from tools.base_tool import BaseTool


from PyQt6.QtWidgets import QApplication

class SprayTool(BaseTool):
    """Herramienta Aerosol / Spray Paint."""
    def __init__(self):
        super().__init__("Aerosol", "gui/iconos/spray.png")
        self.is_drawing = False
        self.shift_anchor = None
        self._last_pos = None

    def draw_handles(self, painter, canvas):
        if canvas.cursor_pos is None:
            return
        pos = canvas.cursor_pos
        size = max(1, getattr(canvas, 'grosor_pincel', 15))
        r = size / 2.0
        suavizado = getattr(canvas, 'suavizado_pincel', True)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, suavizado)

        # Círculo guía exterior del área de aerosol
        pen_outer = QPen(QColor(0, 0, 0, 180), 1.0, Qt.PenStyle.DashLine)
        painter.setPen(pen_outer)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(pos, r, r)

        # Círculo guía interior
        col_pri = QColor(canvas.color_primario)
        col_rim = QColor(col_pri)
        col_rim.setAlpha(220)
        painter.setPen(QPen(col_rim, 0.8))
        painter.drawEllipse(pos, r - 0.5, r - 0.5)

        painter.restore()

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.is_drawing = True
            pos = event.position()
            self._last_pos = pos
            self.shift_anchor = None
            color = color_activo if color_activo else (canvas.color_primario if event.button() == Qt.MouseButton.LeftButton else canvas.color_secundario)
            self._spray_at(canvas, pos, color)
            canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        if self.is_drawing:
            raw_pos = event.position()
            modifiers = QApplication.keyboardModifiers()
            is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

            if is_shift:
                if self.shift_anchor is None:
                    self.shift_anchor = QPointF(self._last_pos) if self._last_pos else raw_pos
                dx = raw_pos.x() - self.shift_anchor.x()
                dy = raw_pos.y() - self.shift_anchor.y()
                if abs(dx) >= abs(dy):
                    pos = QPointF(raw_pos.x(), self.shift_anchor.y())
                else:
                    pos = QPointF(self.shift_anchor.x(), raw_pos.y())
            else:
                self.shift_anchor = None
                pos = raw_pos

            self._last_pos = pos
            color = color_activo if color_activo else (canvas.color_primario if event.buttons() & Qt.MouseButton.LeftButton else canvas.color_secundario)
            self._spray_at(canvas, pos, color)
            canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        if self.is_drawing:
            self.is_drawing = False
            self.shift_anchor = None
            self._last_pos = None
            if hasattr(canvas, 'push_document_state'):
                canvas.push_document_state(self.name)
            canvas.update()

    def _spray_at(self, canvas, point: QPointF, color: QColor):
        active_layer = canvas.layer_mgr.get_active_layer()
        if not active_layer or not active_layer.visible or active_layer.locked:
            return

        grosor = max(2, getattr(canvas, 'grosor_pincel', 15))
        radius = grosor / 2.0
        suavizado = getattr(canvas, 'suavizado_pincel', True)

        painter = QPainter(active_layer.image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, suavizado)

        # Número de partículas proporcional al radio
        density = max(12, int(radius * 3.5))

        base_color = QColor(color)
        pen_dot = QPen(base_color, 1.2)
        painter.setPen(pen_dot)

        for _ in range(density):
            # Distribución aleatoria dentro del círculo
            r_ratio = math.sqrt(random.random()) * radius
            angle = random.uniform(0, 2 * math.pi)
            px = point.x() + r_ratio * math.cos(angle)
            py = point.y() + r_ratio * math.sin(angle)

            if suavizado:
                # Modificar alpha suavemente hacia los bordes
                falloff = 1.0 - (r_ratio / radius) * 0.5
                c = QColor(base_color)
                c.setAlpha(max(1, int(c.alpha() * falloff)))
                painter.setPen(QPen(c, 1.2))

            painter.drawPoint(QPointF(px, py))

        painter.end()
