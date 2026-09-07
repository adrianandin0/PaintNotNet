import math
import cv2
import numpy as np
from PyQt6.QtCore import Qt, QRect, QRectF, QPoint, QPointF
from PyQt6.QtGui import QPainter, QImage, QPen, QColor, QBrush, QPainterPath
from tools.base_tool import BaseTool
from core.stroke_smoother import generate_smooth_stroke_points, smooth_mouse_input


class BlurTool(BaseTool):
    def __init__(self):
        super().__init__("Difuminar", "gui/iconos/blur.png")
        self.is_drawing = False
        self._points = []
        self._last_drawn_index = 0

    def _get_pixel_pos(self, event):
        return QPoint(int(math.floor(event.position().x())), int(math.floor(event.position().y())))

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            if canvas.selection_engine.has_selection():
                canvas.actualizar_preview_difuminado_seleccion()
            else:
                self.is_drawing = True
                pos = QPointF(event.position())
                self._points = [pos]
                self._last_drawn_index = 0
                self._apply_blur_at(canvas, QPoint(int(pos.x()), int(pos.y())))

    def mouse_move(self, canvas, event, color_activo=None):
        if self.is_drawing:
            raw_pos = event.position()
            pos = smooth_mouse_input(self._points[-1] if self._points else None, raw_pos)
            self._points.append(pos)
            self._apply_blur_stroke(canvas, is_final=False)

    def mouse_release(self, canvas, event, color_activo=None):
        if self.is_drawing:
            self._apply_blur_stroke(canvas, is_final=True)
            self.is_drawing = False
            self._points = []
            self._last_drawn_index = 0
            canvas.push_document_state("Difuminar")
            canvas.update()

    def _apply_blur_stroke(self, canvas, is_final=False):
        pts = getattr(self, '_points', [])
        if not pts:
            return

        grosor = max(5, getattr(canvas, 'grosor_pincel', 15))
        step_px = max(1.0, grosor * 0.25)

        sub_points, new_start_idx = generate_smooth_stroke_points(
            pts, self._last_drawn_index, is_final=is_final, step_px=step_px
        )

        for pt_f, _ in sub_points:
            pt = QPoint(int(round(pt_f.x())), int(round(pt_f.y())))
            self._apply_blur_at(canvas, pt)

        self._last_drawn_index = new_start_idx

    def _apply_blur_at(self, canvas, pos):
        if not hasattr(canvas, 'main_window') or not canvas.main_window:
            return
        top_bar = getattr(canvas.main_window, 'top_toolbar', None)
        modo = top_bar.combo_blur_modo.currentData() if top_bar else "Pixelado"
        val = top_bar.slider_blur.value() if top_bar else 20
        if val <= 0:
            val = 20

        grosor = max(5, getattr(canvas, 'grosor_pincel', 15))
        radius = grosor // 2

        capa = canvas.layer_mgr.capas[canvas.layer_mgr.indice_activo]
        img = capa.image
        w, h = img.width(), img.height()

        rx = max(0, pos.x() - radius)
        ry = max(0, pos.y() - radius)
        rw = min(w - rx, radius * 2)
        rh = min(h - ry, radius * 2)

        if rw <= 1 or rh <= 1:
            return

        sub_img = img.copy(rx, ry, rw, rh).convertToFormat(QImage.Format.Format_ARGB32)
        ptr = sub_img.bits()
        ptr.setsize(rh * sub_img.bytesPerLine())
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((rh, sub_img.bytesPerLine() // 4, 4))[:, :rw, :].copy()

        if modo == "Pixelado":
            factor = max(2, int((val / 100.0) * 15))
            sw = max(1, rw // factor)
            sh = max(1, rh // factor)
            small = cv2.resize(arr, (sw, sh), interpolation=cv2.INTER_NEAREST)
            blurred = cv2.resize(small, (rw, rh), interpolation=cv2.INTER_NEAREST)
        else:
            ksize = max(3, (int((val / 100.0) * 25) // 2) * 2 + 1)
            blurred = cv2.GaussianBlur(arr, (ksize, ksize), 0)

        result_sub = QImage(blurred.data, rw, rh, rw * 4, QImage.Format.Format_ARGB32).copy()

        painter = QPainter(capa.image)
        if canvas.selection_engine.has_selection() and not canvas.selection_engine.active_path.isEmpty():
            painter.setClipPath(canvas.selection_engine.active_path)

        clip_path = QPainterPath()
        clip_path.addEllipse(float(pos.x() - radius), float(pos.y() - radius), float(radius * 2), float(radius * 2))
        painter.setClipPath(clip_path, Qt.ClipOperation.IntersectClip)

        painter.drawImage(rx, ry, result_sub)
        painter.end()

        canvas.update()
