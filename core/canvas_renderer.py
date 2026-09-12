"""
core/canvas_renderer.py — Motor de composición gráfica y dibujo para el lienzo de PaintNotNet.
"""
from PyQt6.QtCore import QRectF, QPointF, Qt
from PyQt6.QtGui import QPainter, QImage, QPen, QColor, QBrush, QPixmap


class CanvasRenderer:
    """Encapsula las rutinas de composición gráfica, fondo de ajedrez y renderizado multicapa."""

    def __init__(self, canvas):
        self.canvas = canvas

    def draw_checkerboard_pattern(self, painter: QPainter, rect_w: int, rect_h: int, tile_size: int = 12):
        """Dibuja el fondo de tablero de ajedrez representativo de transparencia."""
        from core.theme import ThemeManager
        tm = ThemeManager()
        is_light = (tm.resolver_nombre_tema(tm.current_theme) == "Claro")

        c1 = QColor(240, 240, 240) if is_light else QColor(42, 42, 42)
        c2 = QColor(210, 210, 210) if is_light else QColor(58, 58, 58)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        for y in range(0, rect_h, tile_size):
            for x in range(0, rect_w, tile_size):
                col = c1 if ((x // tile_size) + (y // tile_size)) % 2 == 0 else c2
                tw = min(tile_size, rect_w - x)
                th = min(tile_size, rect_h - y)
                painter.fillRect(x, y, tw, th, QBrush(col))

        painter.restore()

    def draw_pixel_grid(self, painter: QPainter, width: int, height: int, scale_factor: float):
        """Dibuja una rejilla fina de píxeles cuando el nivel de zoom es elevado (>= 150%)."""
        if scale_factor < 1.5:
            return

        painter.save()
        pen_dark = QPen(QColor(0, 0, 0, 100), 0, Qt.PenStyle.SolidLine)
        pen_dark.setCosmetic(True)
        pen_light = QPen(QColor(255, 255, 255, 140), 0, Qt.PenStyle.DotLine)
        pen_light.setCosmetic(True)

        painter.setPen(pen_dark)
        for x in range(1, width):
            painter.drawLine(QPointF(float(x), 0.0), QPointF(float(x), float(height)))
        for y in range(1, height):
            painter.drawLine(QPointF(0.0, float(y)), QPointF(float(width), float(y)))

        painter.setPen(pen_light)
        for x in range(1, width):
            painter.drawLine(QPointF(float(x), 0.0), QPointF(float(x), float(height)))
        for y in range(1, height):
            painter.drawLine(QPointF(0.0, float(y)), QPointF(float(width), float(y)))

        painter.restore()

    def render_layers_composite(self, layer_mgr, selection_engine, capa_trazo_temp=None) -> QImage:
        """Compone todas las capas del documento en una QImage final respetando opacidades y selección flotante."""
        w, h = layer_mgr.width, layer_mgr.height
        comp = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
        comp.fill(Qt.GlobalColor.transparent)

        p = QPainter(comp)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        has_floating = bool(selection_engine and selection_engine.floating_image and not selection_engine.floating_image.isNull())

        for i, capa in enumerate(reversed(layer_mgr.capas)):
            if not getattr(capa, 'visible', True):
                continue

            idx_real = len(layer_mgr.capas) - 1 - i
            op = float(getattr(capa, 'opacity', 1.0))
            p.setOpacity(op)

            # Dibujar la imagen de la capa
            p.drawImage(0, 0, capa.image)

            # Si es la capa activa y hay trazo temporal de pincel activo
            if idx_real == layer_mgr.indice_activo and capa_trazo_temp and not capa_trazo_temp.isNull():
                stroke_alpha = float(getattr(layer_mgr, 'active_stroke_alpha', 1.0))
                p.setOpacity(op * stroke_alpha)
                p.drawImage(0, 0, capa_trazo_temp)
                p.setOpacity(op)

            # Si es la capa activa y hay selección flotante en movimiento
            if has_floating and idx_real == layer_mgr.indice_activo:
                p.drawImage(selection_engine.original_image_pos, selection_engine.floating_image)

        p.end()
        return comp
