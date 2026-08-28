import math
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath, QImage, QBrush
from tools.base_tool import BaseTool


from PyQt6.QtWidgets import QApplication

class BrushTool(BaseTool):
    def __init__(self):
        super().__init__("Pincel", "gui/iconos/brush.png")
        self.is_drawing = False
        self.path = None
        self._points = []        # puntos crudos del mouse
        self._press_pos = None
        self._has_moved = False
        self.shift_anchor = None

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
            self.shift_anchor = None
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
        raw_pos = event.position()
        modifiers = QApplication.keyboardModifiers()
        is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

        if is_shift:
            if self.shift_anchor is None:
                self.shift_anchor = self._points[-1] if self._points else raw_pos
            dx = raw_pos.x() - self.shift_anchor.x()
            dy = raw_pos.y() - self.shift_anchor.y()
            if abs(dx) >= abs(dy):
                pos = QPointF(raw_pos.x(), self.shift_anchor.y())
            else:
                pos = QPointF(self.shift_anchor.x(), raw_pos.y())
        else:
            self.shift_anchor = None
            pos = raw_pos

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
            self.shift_anchor = None
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
                       Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.RoundJoin)
        else:
            pen = QPen(color, grosor, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        pen.setMiterLimit(2.0)

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
    - Filtra micro-juegos/puntos duplicados (< 1.5px) para evitar cúspides degeneradas.
    - El path pasa por los puntos medios entre eventos consecutivos
    - Cada segmento es una curva quadTo con el punto del mouse como control point
    → elimina picos y cortes raros en giros cerrados.
    """
    path = QPainterPath()
    if not points:
        return path

    filtered = [points[0]]
    for p in points[1:]:
        dx = p.x() - filtered[-1].x()
        dy = p.y() - filtered[-1].y()
        if (dx * dx + dy * dy) >= 2.25:
            filtered.append(p)

    if len(points) > 1 and filtered[-1] != points[-1]:
        filtered.append(points[-1])

    n = len(filtered)
    if n == 0:
        return path
    if n == 1:
        path.moveTo(filtered[0])
        return path
    if n == 2:
        path.moveTo(filtered[0])
        path.lineTo(filtered[1])
        return path

    # Empezar en el primer punto
    path.moveTo(filtered[0])

    # Primer segmento: línea hasta el midpoint entre [0] y [1]
    mid0 = QPointF((filtered[0].x() + filtered[1].x()) / 2.0,
                   (filtered[0].y() + filtered[1].y()) / 2.0)
    path.lineTo(mid0)

    # Segmentos intermedios: quadTo(punto_mouse, midpoint_siguiente)
    for i in range(1, n - 1):
        mid = QPointF((filtered[i].x() + filtered[i + 1].x()) / 2.0,
                      (filtered[i].y() + filtered[i + 1].y()) / 2.0)
        path.quadTo(filtered[i], mid)

    # Último segmento: hasta el punto final exacto
    path.lineTo(filtered[-1])
    return path
