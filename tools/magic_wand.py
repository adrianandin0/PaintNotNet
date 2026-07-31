import cv2
import numpy as np
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF
from PyQt6.QtGui import QPainterPath
from tools.base_tool import BaseTool


def construir_img3_alpha(buffer, w, h):
    stride = buffer.bytesPerLine()
    ptr = buffer.bits()
    ptr.setsize(h * stride)
    arr = np.frombuffer(ptr, dtype=np.uint8).reshape((h, stride))
    bgra = arr[:, :w * 4].reshape((h, w, 4))

    b = bgra[:, :, 0].astype(np.int16)
    g = bgra[:, :, 1].astype(np.int16)
    r = bgra[:, :, 2].astype(np.int16)
    a = bgra[:, :, 3]

    gray = (0.114 * b + 0.587 * g + 0.299 * r).astype(np.uint8)
    chroma = ((b - r + 256) // 2).astype(np.uint8)

    return np.dstack((a, gray, chroma))


class MagicWandTool(BaseTool):
    def __init__(self):
        super().__init__("Varita Mágica", "gui/iconos/magic.png")
        self.last_seed = None

    def mouse_press(self, canvas, event, color_activo=None):
        pos = event.position().toPoint()
        if 0 <= pos.x() < canvas.layer_mgr.width and 0 <= pos.y() < canvas.layer_mgr.height:
            self.last_seed = pos
            tol = getattr(canvas, 'tolerancia', 32)
            if hasattr(canvas, 'main_window') and canvas.main_window and hasattr(canvas.main_window, 'top_toolbar'):
                tol = canvas.main_window.top_toolbar.slider_tol.value()

            self.ejecutar_seleccion_varita(canvas, pos, tol)

    def update_tolerance(self, canvas, tol):
        if self.last_seed and canvas.selection_engine.has_selection():
            self.ejecutar_seleccion_varita(canvas, self.last_seed, tol)

    def ejecutar_seleccion_varita(self, canvas, seed_point, tolerance):
        w, h = canvas.layer_mgr.width, canvas.layer_mgr.height
        buffer = canvas.layer_mgr.buffer

        img3 = construir_img3_alpha(buffer, w, h)

        seed_x, seed_y = seed_point.x(), seed_point.y()
        mask = np.zeros((h + 2, w + 2), dtype=np.uint8)

        diff_val = int((tolerance / 100.0) * 255.0)
        lo_diff = (diff_val, diff_val, diff_val)
        up_diff = (diff_val, diff_val, diff_val)

        flags = 4 | (255 << 8) | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE

        cv2.floodFill(
            img3, mask, (seed_x, seed_y), 255,
            lo_diff, up_diff,
            flags=flags
        )

        flood_mask = mask[1:h+1, 1:w+1]

        contours, _ = cv2.findContours(flood_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

        path = QPainterPath()
        path.setFillRule(Qt.FillRule.OddEvenFill)

        if contours is not None:
            for cnt in contours:
                if len(cnt) >= 3:
                    sub_path = QPainterPath()
                    p0 = QPointF(float(cnt[0][0][0]), float(cnt[0][0][1]))
                    sub_path.moveTo(p0)
                    for pt in cnt[1:]:
                        sub_path.lineTo(QPointF(float(pt[0][0]), float(pt[0][1])))
                    sub_path.closeSubpath()
                    path.addPath(sub_path)

        if not path.isEmpty():
            canvas.selection_engine.set_path(path)
        else:
            canvas.selection_engine.clear_selection()

        canvas.update()
