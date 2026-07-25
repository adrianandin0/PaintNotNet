import cv2
import numpy as np
from PyQt6.QtGui import QImage
from PyQt6.QtCore import Qt
from tools.base_tool import BaseTool

class BucketTool(BaseTool):
    def __init__(self):
        super().__init__("Balde", "gui/iconos/bucket.png")

    def mouse_press(self, canvas, event, color_activo):
        x = int(event.position().x())
        y = int(event.position().y())

        qimg = canvas.layer_mgr.buffer
        if not (0 <= x < qimg.width() and 0 <= y < qimg.height()):
            return

        tolerancia = getattr(canvas, 'tolerancia_balde', 30)

        # 1. Convertir a RGB888 (3 canales) para que OpenCV no proteste
        img_rgb = qimg.convertToFormat(QImage.Format.Format_RGB888)
        width = img_rgb.width()
        height = img_rgb.height()

        ptr = img_rgb.bits()
        ptr.setsize(height * width * 3)
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((height, width, 3)).copy()

        # 2. Máscara para cv2.floodFill
        h, w = arr.shape[:2]
        mask = np.zeros((h + 2, w + 2), dtype=np.uint8)

        # 3. Extraer color RGB (ignorar alpha para OpenCV)
        r, g, b, a = color_activo.red(), color_activo.green(), color_activo.blue(), color_activo.alpha()
        fill_color_rgb = (r, g, b)

        diff = (tolerancia, tolerancia, tolerancia)

        # 4. Rellenar con OpenCV en 3 canales
        cv2.floodFill(
            image=arr,
            mask=mask,
            seedPoint=(x, y),
            newVal=fill_color_rgb,
            loDiff=diff,
            upDiff=diff,
            flags=cv2.FLOODFILL_FIXED_RANGE
        )

        # 5. Volver a convertir a QImage
        new_qimg = QImage(arr.data, w, h, w * 3, QImage.Format.Format_RGB888)
        final_qimg = new_qimg.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)

        # 6. Si el color elegido tiene transparencia parcial, la aplicamos
        if a < 255:
            # Aplicar opacidad sobre la zona rellenada si es necesario
            pass

        # Reemplazar el buffer de la capa activa
        canvas.layer_mgr.buffer = final_qimg
