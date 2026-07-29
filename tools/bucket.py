import cv2
import numpy as np
from PyQt6.QtGui import QImage, QPainter, QColor, QBrush
from PyQt6.QtCore import Qt, QRect
from tools.base_tool import BaseTool
from tools.magic_wand import construir_img3_alpha


class BucketTool(BaseTool):
    def __init__(self):
        super().__init__("Balde de Pintura", "gui/iconos/bucket.png")

    def mouse_press(self, canvas, event, color_activo=None):
        pos = event.position().toPoint()
        x, y = pos.x(), pos.y()

        qimg = canvas.layer_mgr.buffer
        w, h = qimg.width(), qimg.height()

        if not (0 <= x < w and 0 <= y < h):
            return

        color = color_activo if color_activo else canvas.color_primario
        tolerancia = getattr(canvas, 'tolerancia', 32)
        if hasattr(canvas, 'main_window') and canvas.main_window and hasattr(canvas.main_window, 'top_toolbar'):
            tolerancia = canvas.main_window.top_toolbar.slider_tol.value()

        if tolerancia >= 100:
            painter = QPainter(canvas.layer_mgr.buffer)
            if canvas.selection_engine.has_selection():
                painter.setClipPath(canvas.selection_engine.active_path)
            painter.fillRect(QRect(0, 0, w, h), QBrush(color))
            painter.end()
            canvas.push_document_state("Balde de Pintura")
            canvas.update()
            return

        img3 = construir_img3_alpha(qimg, w, h)
        mask = np.zeros((h + 2, w + 2), dtype=np.uint8)

        diff_val = int((tolerancia / 100.0) * 255.0)
        lo_diff = (diff_val, diff_val, diff_val)
        up_diff = (diff_val, diff_val, diff_val)

        flags = 4 | (255 << 8) | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE

        cv2.floodFill(
            image=img3,
            mask=mask,
            seedPoint=(x, y),
            newVal=255,
            loDiff=lo_diff,
            upDiff=up_diff,
            flags=flags
        )

        flood_mask = mask[1:h+1, 1:w+1]

        r, g, b, a = color.red(), color.green(), color.blue(), color.alpha()

        painter = QPainter(canvas.layer_mgr.buffer)
        if canvas.selection_engine.has_selection():
            painter.setClipPath(canvas.selection_engine.active_path)

        fill_image = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
        fill_image.fill(Qt.GlobalColor.transparent)

        f_ptr = fill_image.bits()
        f_ptr.setsize(h * fill_image.bytesPerLine())
        f_arr = np.frombuffer(f_ptr, dtype=np.uint8).reshape((h, fill_image.bytesPerLine()))
        f_rgba = f_arr[:, :w * 4].reshape((h, w, 4))

        f_rgba[flood_mask > 0] = [b, g, r, a]

        painter.drawImage(0, 0, fill_image)
        painter.end()

        canvas.push_document_state("Balde de Pintura")
        canvas.update()
