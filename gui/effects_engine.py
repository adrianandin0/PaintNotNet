"""
effects_engine.py — Motor de aplicación de efectos (Borde, Resplandor, Sombra).

Funciona sobre una QImage fuente con canal alpha y produce una QImage
resultado con los efectos compositeados debajo/alrededor de la fuente.

Uso:
    result = apply_effects(source_image, config)
    # config dict:
    {
        "borde_enabled": bool, "borde_width": int,  "borde_color": QColor,
        "glow_enabled":  bool, "glow_width":  int,  "glow_color":  QColor,
        "shadow_enabled":bool, "shadow_width":int,  "shadow_color":QColor,
        "shadow_dx": float, "shadow_dy": float,
    }
"""

import cv2
import numpy as np
from PyQt6.QtGui import QImage, QPainter, QColor, QPen, QBrush
from PyQt6.QtCore import Qt, QPoint


def _dilate_alpha(src: QImage, radius: int) -> QImage:
    """
    Crea una 'máscara dilatada' expandiendo los píxeles opacos en `radius` px.
    Utiliza OpenCV cv2.dilate con un elemento estructurante elíptico para velocidad ultrarrápida.
    """
    w, h = src.width(), src.height()
    if radius <= 0 or w == 0 or h == 0:
        return src

    src_conv = src.convertToFormat(QImage.Format.Format_ARGB32)
    ptr = src_conv.bits()
    ptr.setsize(src_conv.sizeInBytes())
    arr = np.frombuffer(ptr, dtype=np.uint8).reshape((h, w, 4))
    alpha_channel = arr[:, :, 3]

    ksize = radius * 2 + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    dilated_alpha = cv2.dilate(alpha_channel, kernel)

    out_arr = np.zeros((h, w, 4), dtype=np.uint8)
    out_arr[:, :, 3] = dilated_alpha

    out = QImage(out_arr.data, w, h, w * 4, QImage.Format.Format_ARGB32).copy()
    return out


def _paint_color_mask(mask: QImage, color: QColor) -> QImage:
    """Colorea una máscara alpha con un color sólido."""
    colored = QImage(mask.width(), mask.height(), QImage.Format.Format_ARGB32)
    colored.fill(Qt.GlobalColor.transparent)
    painter = QPainter(colored)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
    painter.drawImage(0, 0, mask)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(colored.rect(), QBrush(color))
    painter.end()
    return colored


def _build_glow(source: QImage, radius: int, color: QColor) -> QImage:
    """
    Construye un halo de resplandor: serie de máscaras dilatadas
    con alpha decreciente (exterior = transparente, interior = opaco).
    """
    w, h = source.width(), source.height()
    glow_img = QImage(w, h, QImage.Format.Format_ARGB32)
    glow_img.fill(Qt.GlobalColor.transparent)
    if radius <= 0:
        return glow_img

    painter = QPainter(glow_img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    steps = min(radius, 20)
    for step in range(steps, 0, -1):
        r = max(1, (radius * step) // steps)
        t_val = step / steps           # 1.0 = outer (transparent), 0 = inner (bright)
        alpha = int(200 * ((1.0 - t_val) ** 1.5)) + 30
        alpha = min(255, alpha)
        mask = _dilate_alpha(source, r)
        col = QColor(color.red(), color.green(), color.blue(), alpha)
        colored = _paint_color_mask(mask, col)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.drawImage(0, 0, colored)

    painter.end()
    return glow_img


def apply_effects(source: QImage, config: dict) -> QImage:
    """
    Aplica Borde, Resplandor y Sombra a `source` (QImage ARGB32).
    Devuelve una nueva imagen compuesta con todos los efectos.

    Todos los efectos se dibujan DEBAJO de la imagen fuente para
    preservar la imagen original intacta encima.
    """
    borde_enabled  = config.get("borde_enabled",  False)
    borde_width    = max(1, int(config.get("borde_width",  5)))
    borde_color    = config.get("borde_color",    QColor(255, 255, 255))

    glow_enabled   = config.get("glow_enabled",   False)
    glow_width     = max(1, int(config.get("glow_width",   10)))
    glow_color     = config.get("glow_color",     QColor(255, 255, 100))

    shadow_enabled = config.get("shadow_enabled", False)
    shadow_width   = max(1, int(config.get("shadow_width", 10)))
    shadow_color   = config.get("shadow_color",   QColor(0, 0, 0, 180))
    shadow_dx      = float(config.get("shadow_dx", 0.5))
    shadow_dy      = float(config.get("shadow_dy", 0.5))

    src = source.convertToFormat(QImage.Format.Format_ARGB32)
    w, h = src.width(), src.height()

    # Canvas donde acumulamos los efectos (debajo de la imagen)
    result = QImage(w, h, QImage.Format.Format_ARGB32)
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)

    # 1. Sombra paralela (va primero, más abajo)
    if shadow_enabled:
        offset = int(shadow_width * 0.5)
        off_x  = int(shadow_dx * offset)
        off_y  = int(shadow_dy * offset)
        shadow_mask = _dilate_alpha(src, shadow_width // 2)
        shadow_colored = _paint_color_mask(shadow_mask, shadow_color)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.drawImage(QPoint(off_x, off_y), shadow_colored)

    # 2. Resplandor
    if glow_enabled:
        glow_img = _build_glow(src, glow_width, glow_color)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.drawImage(0, 0, glow_img)

    # 3. Borde (dilatado y coloreado)
    if borde_enabled:
        border_mask = _dilate_alpha(src, borde_width)
        border_colored = _paint_color_mask(border_mask, borde_color)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.drawImage(0, 0, border_colored)

    # 4. Imagen fuente encima de todo
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
    painter.drawImage(0, 0, src)
    painter.end()

    return result
