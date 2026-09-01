import cv2
import numpy as np
from PyQt6.QtCore import Qt, QRect, QRectF
from PyQt6.QtGui import QPainter, QImage, QPen, QColor, QBrush, QPainterPath
from tools.base_tool import BaseTool


class BlurTool(BaseTool):
    def __init__(self):
        super().__init__("Difuminar", "gui/iconos/blur.png")
        self.is_drawing = False
        self.show_cursor_badge = False

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            if canvas.selection_engine.has_selection():
                canvas.actualizar_preview_difuminado_seleccion()
            else:
                self.is_drawing = True
                self._apply_blur_at(canvas, event.position().toPoint())

    def mouse_move(self, canvas, event, color_activo=None):
        if self.is_drawing:
            self._apply_blur_at(canvas, event.position().toPoint())

    def mouse_release(self, canvas, event, color_activo=None):
        if self.is_drawing:
            self.is_drawing = False
            canvas.push_document_state("Difuminar")
            canvas.update()

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
