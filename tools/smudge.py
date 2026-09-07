import math
from PyQt6.QtCore import Qt, QPointF, QRectF, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QImage, QBrush
from tools.base_tool import BaseTool
from core.stroke_smoother import generate_smooth_stroke_points, smooth_mouse_input


class SmudgeTool(BaseTool):
    """Herramienta Difuminar con el dedo (Smudge Tool)."""
    def __init__(self):
        super().__init__("Difuminar (Dedo)", "gui/iconos/finger.png")
        self.is_drawing = False
        self.last_pos = None
        self.intensidad = 50  # 1-100%
        self.smudge_buffer = None
        self._points = []
        self._last_drawn_index = 0

    def draw_handles(self, painter, canvas):
        if canvas.cursor_pos is None:
            return
        pos = canvas.cursor_pos
        size = max(1, getattr(canvas, 'grosor_pincel', 20))
        r = size / 2.0

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        pen_outer = QPen(QColor(0, 0, 0, 180), 1.5)
        pen_outer.setCosmetic(True)
        painter.setPen(pen_outer)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(pos, r, r)

        pen_dash = QPen(QColor(255, 255, 255, 200), 1.0, Qt.PenStyle.DashLine)
        pen_dash.setCosmetic(True)
        painter.setPen(pen_dash)
        painter.drawEllipse(pos, r - 0.5, r - 0.5)

        painter.restore()

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.is_drawing = True
            pos = event.position()
            self.last_pos = pos
            self._points = [pos]
            self._last_drawn_index = 0
            self._capture_buffer(canvas, pos)

    def mouse_move(self, canvas, event, color_activo=None):
        if self.is_drawing and self.last_pos:
            raw_pos = event.position()
            pos = smooth_mouse_input(self.last_pos, raw_pos)
            self._points.append(pos)
            self._smudge_stroke(canvas, is_final=False)
            self.last_pos = pos
            canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        if self.is_drawing:
            self._smudge_stroke(canvas, is_final=True)
            self.is_drawing = False
            self.last_pos = None
            self.smudge_buffer = None
            self._points = []
            self._last_drawn_index = 0
            if hasattr(canvas, 'push_document_state'):
                canvas.push_document_state(self.name)
            canvas.update()

    def _smudge_stroke(self, canvas, is_final=False):
        pts = getattr(self, '_points', [])
        if not pts:
            return

        grosor = max(2, getattr(canvas, 'grosor_pincel', 20))
        radius = max(1, int(grosor / 2.0))
        step_px = max(1.0, radius * 0.3)

        sub_points, new_start_idx = generate_smooth_stroke_points(
            pts, self._last_drawn_index, is_final=is_final, step_px=step_px
        )

        p_prev = pts[self._last_drawn_index] if self._last_drawn_index < len(pts) else pts[0]
        for pt_f, _ in sub_points:
            self._smudge_segment(canvas, p_prev, pt_f)
            p_prev = pt_f

        self._last_drawn_index = new_start_idx

    def _capture_buffer(self, canvas, pos: QPointF):
        active_layer = canvas.layer_mgr.get_active_layer()
        if not active_layer or not active_layer.image:
            return

        grosor = max(2, getattr(canvas, 'grosor_pincel', 20))
        radius = max(1, int(grosor / 2.0))
        img = active_layer.image
        w, h = img.width(), img.height()
        cx, cy = int(pos.x()), int(pos.y())

        buf_size = radius * 2 + 1
        self.smudge_buffer = QImage(buf_size, buf_size, QImage.Format.Format_ARGB32)
        self.smudge_buffer.fill(QColor(0, 0, 0, 0))

        for py in range(-radius, radius + 1):
            for px in range(-radius, radius + 1):
                if math.hypot(px, py) <= radius:
                    ix, iy = cx + px, cy + py
                    if 0 <= ix < w and 0 <= iy < h:
                        self.smudge_buffer.setPixelColor(px + radius, py + radius, img.pixelColor(ix, iy))
                    else:
                        self.smudge_buffer.setPixelColor(px + radius, py + radius, QColor(0, 0, 0, 0))

    def _smudge_segment(self, canvas, p1: QPointF, p2: QPointF):
        active_layer = canvas.layer_mgr.get_active_layer()
        if not active_layer or not active_layer.visible or active_layer.locked:
            return

        if not self.smudge_buffer:
            self._capture_buffer(canvas, p1)

        grosor = max(2, getattr(canvas, 'grosor_pincel', 20))
        radius = max(1, int(grosor / 2.0))

        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        dist = math.hypot(dx, dy)
        if dist < 0.5:
            return

        steps = max(1, int(dist / max(1.0, radius * 0.3)))

        intensity_val = getattr(canvas.main_window.top_toolbar, 'slider_smudge_intensidad', None) if (hasattr(canvas, 'main_window') and hasattr(canvas.main_window, 'top_toolbar')) else None
        strength = (intensity_val.value() / 100.0) if intensity_val else (self.intensidad / 100.0)
        strength = max(0.05, min(1.0, strength))

        img = active_layer.image
        w, h = img.width(), img.height()

        for step in range(1, steps + 1):
            t = step / steps
            cx = int(p1.x() + dx * t)
            cy = int(p1.y() + dy * t)

            # 1. Estampar el buffer capturado sobre la capa activa
            for py in range(-radius, radius + 1):
                for px in range(-radius, radius + 1):
                    dist_c = math.hypot(px, py)
                    if dist_c <= radius:
                        ix, iy = cx + px, cy + py
                        if 0 <= ix < w and 0 <= iy < h:
                            buf_col = self.smudge_buffer.pixelColor(px + radius, py + radius)
                            if buf_col.alpha() > 0:
                                dst_col = img.pixelColor(ix, iy)
                                falloff = (1.0 - (dist_c / radius)) ** 0.5
                                alpha_factor = (buf_col.alpha() / 255.0) * falloff * strength * 0.5

                                r_new = int(dst_col.red() * (1 - alpha_factor) + buf_col.red() * alpha_factor)
                                g_new = int(dst_col.green() * (1 - alpha_factor) + buf_col.green() * alpha_factor)
                                b_new = int(dst_col.blue() * (1 - alpha_factor) + buf_col.blue() * alpha_factor)
                                a_new = int(dst_col.alpha() * (1 - alpha_factor) + buf_col.alpha() * alpha_factor)

                                img.setPixelColor(ix, iy, QColor(r_new, g_new, b_new, a_new))

            # 2. Actualizar el buffer recogiendo color fresco del lienzo a medida que se desliza
            pickup_rate = (1.0 - strength * 0.7) * 0.3
            for py in range(-radius, radius + 1):
                for px in range(-radius, radius + 1):
                    if math.hypot(px, py) <= radius:
                        ix, iy = cx + px, cy + py
                        if 0 <= ix < w and 0 <= iy < h:
                            curr_buf = self.smudge_buffer.pixelColor(px + radius, py + radius)
                            canv_col = img.pixelColor(ix, iy)

                            r_b = int(curr_buf.red() * (1 - pickup_rate) + canv_col.red() * pickup_rate)
                            g_b = int(curr_buf.green() * (1 - pickup_rate) + canv_col.green() * pickup_rate)
                            b_b = int(curr_buf.blue() * (1 - pickup_rate) + canv_col.blue() * pickup_rate)
                            a_b = int(curr_buf.alpha() * (1 - pickup_rate) + canv_col.alpha() * pickup_rate)

                            self.smudge_buffer.setPixelColor(px + radius, py + radius, QColor(r_b, g_b, b_b, a_b))
