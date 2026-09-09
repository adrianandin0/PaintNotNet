import math
import numpy as np
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
            if hasattr(canvas.layer_mgr, 'invalidate_cache'):
                canvas.layer_mgr.invalidate_cache()

            grosor = max(2, getattr(canvas, 'grosor_pincel', 20))
            p_prev = self._points[-2] if len(self._points) >= 2 else pos
            dirty_rect = QRectF(p_prev, pos).normalized().toRect().adjusted(-grosor - 6, -grosor - 6, grosor + 12, grosor + 12)
            canvas.actualizar_region_sucia(dirty_rect)

    def mouse_release(self, canvas, event, color_activo=None):
        if self.is_drawing:
            self._smudge_stroke(canvas, is_final=True)
            self.is_drawing = False
            self.last_pos = None
            self.smudge_buffer = None
            self._points = []
            self._last_drawn_index = 0
            if hasattr(canvas.layer_mgr, 'invalidate_cache'):
                canvas.layer_mgr.invalidate_cache()
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
        self.smudge_buffer = np.zeros((buf_size, buf_size, 4), dtype=np.float32)

        rx = max(0, cx - radius)
        ry = max(0, cy - radius)
        rw = min(w - rx, radius * 2 + 1)
        rh = min(h - ry, radius * 2 + 1)

        if rw <= 0 or rh <= 0:
            return

        stride = img.bytesPerLine()
        ptr = img.bits()
        ptr.setsize(h * stride)
        img_arr = np.frombuffer(ptr, dtype=np.uint8).reshape((h, stride // 4, 4))

        bx = rx - (cx - radius)
        by = ry - (cy - radius)
        self.smudge_buffer[by:by+rh, bx:bx+rw] = img_arr[ry:ry+rh, rx:rx+rw, :4].astype(np.float32)

    def _smudge_segment(self, canvas, p1: QPointF, p2: QPointF):
        active_layer = canvas.layer_mgr.get_active_layer()
        if not active_layer or not active_layer.visible or active_layer.locked:
            return

        if self.smudge_buffer is None:
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
        stride = img.bytesPerLine()
        ptr = img.bits()
        ptr.setsize(h * stride)
        img_arr = np.frombuffer(ptr, dtype=np.uint8).reshape((h, stride // 4, 4))

        buf_size = radius * 2 + 1
        y, x = np.ogrid[-radius:radius+1, -radius:radius+1]
        dist_c = np.hypot(x, y)
        circle_mask = dist_c <= radius
        falloff = np.clip(1.0 - (dist_c / float(radius)), 0.0, 1.0) ** 0.5

        for step in range(1, steps + 1):
            t = step / steps
            cx = int(p1.x() + dx * t)
            cy = int(p1.y() + dy * t)

            rx = max(0, cx - radius)
            ry = max(0, cy - radius)
            rw = min(w - rx, buf_size)
            rh = min(h - ry, buf_size)

            if rw <= 0 or rh <= 0:
                continue

            bx = rx - (cx - radius)
            by = ry - (cy - radius)

            sub_mask = circle_mask[by:by+rh, bx:bx+rw]
            sub_falloff = falloff[by:by+rh, bx:bx+rw]
            sub_buf = self.smudge_buffer[by:by+rh, bx:bx+rw]

            alpha_factor = (sub_buf[:, :, 3] / 255.0) * sub_falloff * strength * 0.5
            alpha_factor = np.expand_dims(alpha_factor, axis=-1)

            target_roi = img_arr[ry:ry+rh, rx:rx+rw, :4].astype(np.float32)
            blended = (target_roi * (1.0 - alpha_factor) + sub_buf * alpha_factor)
            
            # Apply blended back to target ROI for pixels in circle mask
            mask_3d = np.repeat(sub_mask[:, :, np.newaxis], 4, axis=2)
            np.copyto(img_arr[ry:ry+rh, rx:rx+rw, :4], np.clip(blended, 0, 255).astype(np.uint8), where=mask_3d)

            # Update buffer with fresh color pickup
            pickup_rate = (1.0 - strength * 0.7) * 0.3
            fresh_roi = img_arr[ry:ry+rh, rx:rx+rw, :4].astype(np.float32)
            updated_buf = sub_buf * (1.0 - pickup_rate) + fresh_roi * pickup_rate
            np.copyto(self.smudge_buffer[by:by+rh, bx:bx+rw], updated_buf, where=mask_3d)
