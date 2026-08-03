import math
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath, QImage, QBrush
from tools.base_tool import BaseTool


class BrushTool(BaseTool):
    def __init__(self):
        super().__init__("Pincel", "gui/iconos/brush.png")
        self.is_drawing = False
        self.path = None
        self._points = []        # puntos crudos del mouse
        self._press_pos = None
        self._has_moved = False

    def draw_handles(self, painter, canvas):
        if canvas.cursor_pos is None:
            return
        pos = canvas.cursor_pos
        size = max(1, getattr(canvas, 'grosor_pincel', 3))
        r = size / 2.0
        forma = getattr(canvas, 'forma_pincel', 'Redondo')

        painter.save()
        suavizado = getattr(canvas, 'suavizado_pincel', True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, suavizado)

        col_pri = QColor(canvas.color_primario)
        pen_outer = QPen(QColor(0, 0, 0, 180), 1.5)
        painter.setPen(pen_outer)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        _draw_cursor(painter, pos, r + 0.5, forma)

        col_rim = QColor(col_pri); col_rim.setAlpha(255)
        painter.setPen(QPen(col_rim, 1.0))
        col_fill = QColor(col_pri); col_fill.setAlpha(40)
        painter.setBrush(QBrush(col_fill))
        _draw_cursor(painter, pos, r, forma)
        painter.restore()

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.is_drawing = True
            self._has_moved = False
            pos = event.position()
            self._press_pos = pos
            self._points = [pos]
            self.path = QPainterPath()
            self.path.moveTo(pos)

            if canvas.capa_trazo_temp.size() != canvas.layer_mgr.buffer.size():
                canvas.capa_trazo_temp = QImage(canvas.layer_mgr.buffer.size(),
                                                QImage.Format.Format_ARGB32_Premultiplied)
            canvas.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

            # Dibujar punto inicial como cuadrado/círculo centrado (sin dirección)
            color = QColor(color_activo if color_activo else canvas.color_primario)
            suavizado = getattr(canvas, 'suavizado_pincel', True)
            forma = getattr(canvas, 'forma_pincel', 'Redondo')
            grosor = max(1, canvas.grosor_pincel)
            _draw_dot(canvas.capa_trazo_temp, pos, grosor, color, forma, suavizado)
            canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        if not self.is_drawing:
            return
        pos = event.position()
        self._has_moved = True
        self._points.append(pos)
        # Reconstruir path suavizado con Bezier cuadráticos
        self.path = _build_smooth_path(self._points)
        self._draw_stroke(canvas, color_activo)
        if canvas.callback_modificado:
            canvas.callback_modificado()
        canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        if self.is_drawing:
            buffer = canvas.layer_mgr.buffer
            painter = QPainter(buffer)
            canvas.aplicar_clip_seleccion(painter)
            painter.drawImage(0, 0, canvas.capa_trazo_temp)
            painter.end()
            canvas.capa_trazo_temp.fill(Qt.GlobalColor.transparent)
            self.path = None
            self._points = []
            self._press_pos = None
            self.is_drawing = False
            canvas.update()

    def _draw_stroke(self, canvas, color_activo):
        """Redibuja el path completo en capa_trazo_temp con QPen SquareCap/RoundCap."""
        canvas.capa_trazo_temp.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas.capa_trazo_temp)
        canvas.aplicar_clip_seleccion(painter)

        color = QColor(color_activo if color_activo else canvas.color_primario)
        suavizado = getattr(canvas, 'suavizado_pincel', True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, suavizado)

        forma = getattr(canvas, 'forma_pincel', 'Redondo')
        grosor = max(1, canvas.grosor_pincel)

        if forma == 'Cuadrado':
            pen = QPen(color, grosor, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
        else:
            pen = QPen(color, grosor, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)

        painter.setPen(pen)
        if self.path:
            painter.drawPath(self.path)
        painter.end()


# ─── helpers ──────────────────────────────────────────────────────────────────

def _draw_cursor(painter, pos, r, forma):
    if forma == 'Cuadrado':
        painter.drawRect(QRectF(pos.x() - r, pos.y() - r, r * 2, r * 2))
    else:
        painter.drawEllipse(pos, r, r)


def _draw_dot(target_img, pos, grosor, color, forma, suavizado):
    """Dibuja un punto inicial centrado sin dirección (para clic sin arrastre)."""
    painter = QPainter(target_img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, suavizado)
    hw = grosor / 2.0
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(color))
    if forma == 'Cuadrado':
        painter.drawRect(QRectF(pos.x() - hw, pos.y() - hw, grosor, grosor))
    else:
        painter.drawEllipse(pos, hw, hw)
    painter.end()


def _build_smooth_path(points):
    """Construye un QPainterPath suavizado a partir de puntos crudos del mouse.

    Usa el algoritmo clásico de Bezier cuadrático por puntos medios:
    - El path pasa por los puntos medios entre eventos consecutivos
    - Cada segmento es una curva quadTo con el punto del mouse como control point
    → elimina los escalones en curvas con SquareCap/RoundCap
    """
    path = QPainterPath()
    n = len(points)
    if n == 0:
        return path
    if n == 1:
        path.moveTo(points[0])
        return path
    if n == 2:
        path.moveTo(points[0])
        path.lineTo(points[1])
        return path

    # Empezar en el primer punto
    path.moveTo(points[0])

    # Primer segmento: línea hasta el midpoint entre [0] y [1]
    mid0 = QPointF((points[0].x() + points[1].x()) / 2,
                   (points[0].y() + points[1].y()) / 2)
    path.lineTo(mid0)

    # Segmentos intermedios: quadTo(punto_mouse, midpoint_siguiente)
    for i in range(1, n - 1):
        mid = QPointF((points[i].x() + points[i + 1].x()) / 2,
                      (points[i].y() + points[i + 1].y()) / 2)
        path.quadTo(points[i], mid)

    # Último segmento: hasta el punto final exacto
    path.lineTo(points[-1])
    return path
