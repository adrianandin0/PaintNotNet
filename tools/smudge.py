import math
from PyQt6.QtCore import Qt, QPointF, QRectF, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QImage, QBrush
from tools.base_tool import BaseTool


class SmudgeTool(BaseTool):
    """Herramienta Difuminar con el dedo (Smudge Tool)."""
    def __init__(self):
        super().__init__("Difuminar (Dedo)", "gui/iconos/finger.png")
        self.is_drawing = False
        self.last_pos = None
        self.intensidad = 50  # 1-100%

    def draw_handles(self, painter, canvas):
        if canvas.cursor_pos is None:
            return
        pos = canvas.cursor_pos
        size = max(1, getattr(canvas, 'grosor_pincel', 20))
        r = size / 2.0

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        pen_outer = QPen(QColor(0, 0, 0, 180), 1.5)
        painter.setPen(pen_outer)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(pos, r, r)

        painter.setPen(QPen(QColor(255, 255, 255, 200), 1.0, Qt.PenStyle.DashLine))
        painter.drawEllipse(pos, r - 0.5, r - 0.5)

        painter.restore()

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.is_drawing = True
            self.last_pos = event.position()

    def mouse_move(self, canvas, event, color_activo=None):
        if self.is_drawing and self.last_pos:
            curr_pos = event.position()
            self._smudge_segment(canvas, self.last_pos, curr_pos)
            self.last_pos = curr_pos
            canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        if self.is_drawing:
            self.is_drawing = False
            self.last_pos = None
            if hasattr(canvas, 'push_document_state'):
                canvas.push_document_state(self.name)
            canvas.update()

    def _smudge_segment(self, canvas, p1: QPointF, p2: QPointF):
        active_layer = canvas.layer_mgr.get_active_layer()
        if not active_layer or not active_layer.visible or active_layer.locked:
            return

        grosor = max(2, getattr(canvas, 'grosor_pincel', 20))
        radius = int(grosor / 2.0)
        if radius < 1:
            radius = 1

        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        dist = math.hypot(dx, dy)
        if dist < 0.5:
            return

        steps = max(1, int(dist / max(1.0, radius * 0.4)))
        intensity_val = getattr(canvas.main_window.top_toolbar, 'slider_smudge_intensidad', None) if (hasattr(canvas, 'main_window') and hasattr(canvas.main_window, 'top_toolbar')) else None
        strength = (intensity_val.value() / 100.0) if intensity_val else (self.intensidad / 100.0)
        strength = max(0.05, min(1.0, strength))

        img = active_layer.image
        w, h = img.width(), img.height()

        for step in range(1, steps + 1):
            t = step / steps
            cx = int(p1.x() + dx * t)
            cy = int(p1.y() + dy * t)

            # Extraer región cuadrada y difuminar en círculo
            rx1 = max(0, cx - radius)
            ry1 = max(0, cy - radius)
            rx2 = min(w - 1, cx + radius)
            ry2 = min(h - 1, cy + radius)

            for y in range(ry1, ry2 + 1):
                for x in range(rx1, rx2 + 1):
                    dist_center = math.hypot(x - cx, y - cy)
                    if dist_center <= radius:
                        # Vector de desplazamiento hacia atrás (origen de muestra)
                        src_x = int(x - dx * 0.4 * strength)
                        src_y = int(y - dy * 0.4 * strength)

                        if 0 <= src_x < w and 0 <= src_y < h:
                            c_src = QColor(img.pixelColor(src_x, src_y))
                            c_dst = QColor(img.pixelColor(x, y))

                            # Meclar pixeles según fuerza y distancia al centro
                            weight = (1.0 - (dist_center / radius)) * strength * 0.6
                            r_new = int(c_dst.red() * (1 - weight) + c_src.red() * weight)
                            g_new = int(c_dst.green() * (1 - weight) + c_src.green() * weight)
                            b_new = int(c_dst.blue() * (1 - weight) + c_src.blue() * weight)
                            a_new = int(c_dst.alpha() * (1 - weight) + c_src.alpha() * weight)

                            img.setPixelColor(x, y, QColor(r_new, g_new, b_new, a_new))
