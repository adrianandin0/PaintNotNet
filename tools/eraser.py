import math
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath
from tools.base_tool import BaseTool
from tools.brush import _draw_cursor


from PyQt6.QtWidgets import QApplication


class EraserTool(BaseTool):
    def __init__(self):
        super().__init__("Goma de Borrar", "gui/iconos/eraser.png")
        self.is_drawing = False
        self._last_pos: QPointF | None = None
        self.shift_anchor: QPointF | None = None

    # ── cursor de preview ─────────────────────────────────────────────────────

    def draw_handles(self, painter, canvas):
        if canvas.cursor_pos is None:
            return
        px = math.floor(canvas.cursor_pos.x())
        py = math.floor(canvas.cursor_pos.y())
        pos = QPointF(px + 0.5, py + 0.5)
        size = max(1, getattr(canvas, 'grosor_pincel', 3))
        r = size / 2.0
        forma = getattr(canvas, 'forma_pincel', 'Redondo')

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        pen1 = QPen(QColor(0, 0, 0, 200), 1.5)
        pen1.setCosmetic(True)
        painter.setPen(pen1)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        _draw_cursor(painter, pos, r + 0.5, forma)

        pen2 = QPen(QColor(255, 255, 255, 255), 1.0)
        pen2.setCosmetic(True)
        painter.setPen(pen2)
        painter.setBrush(QBrush(QColor(255, 255, 255, 80)))
        _draw_cursor(painter, pos, r, forma)

        painter.restore()

    # ── eventos de mouse ──────────────────────────────────────────────────────

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.is_drawing = True
            px = math.floor(event.position().x())
            py = math.floor(event.position().y())
            pos = QPointF(px + 0.5, py + 0.5)
            self._last_pos = pos
            self._points = [pos]
            self._last_drawn_index = 0
            self.shift_anchor = None
            self._erase_segment(canvas, pos, pos)
            if hasattr(canvas.layer_mgr, 'invalidate_cache'):
                canvas.layer_mgr.invalidate_cache()
            canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        if not self.is_drawing or self._last_pos is None:
            return
        px = math.floor(event.position().x())
        py = math.floor(event.position().y())
        raw_pos = QPointF(px + 0.5, py + 0.5)
        modifiers = QApplication.keyboardModifiers()
        is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

        if is_shift:
            if self.shift_anchor is None:
                self.shift_anchor = QPointF(self._last_pos)
            dx = raw_pos.x() - self.shift_anchor.x()
            dy = raw_pos.y() - self.shift_anchor.y()
            if abs(dx) >= abs(dy):
                pos = QPointF(raw_pos.x(), self.shift_anchor.y())
            else:
                pos = QPointF(self.shift_anchor.x(), raw_pos.y())
        else:
            self.shift_anchor = None
            pos = raw_pos

        if not hasattr(self, '_points') or not self._points:
            self._points = [self._last_pos]
            self._last_drawn_index = 0

        self._points.append(pos)
        n = len(self._points)
        start_idx = max(0, getattr(self, '_last_drawn_index', 0))

        if start_idx < n - 1:
            qimg = canvas.layer_mgr.buffer
            grosor = max(1, getattr(canvas, 'grosor_pincel', 3))
            suavizado = getattr(canvas, 'suavizado_pincel', True)
            forma = getattr(canvas, 'forma_pincel', 'Redondo')

            painter = QPainter(qimg)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            if suavizado:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            step_px = max(0.5, grosor * 0.25)
            hw = grosor / 2.0
            pen = QPen(QColor(0, 0, 0, 255), grosor, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor(0, 0, 0, 255)))

            for i in range(start_idx, n - 1):
                p0 = self._points[max(0, i - 1)]
                p1 = self._points[i]
                p2 = self._points[i + 1]
                p3 = self._points[min(n - 1, i + 2)]

                dx = p2.x() - p1.x()
                dy = p2.y() - p1.y()
                dist = math.hypot(dx, dy)
                steps = max(1, int(math.ceil(dist / step_px)))

                for s in range(steps):
                    t = (s + 1) / steps
                    t2 = t * t
                    t3 = t2 * t
                    x = 0.5 * ((2 * p1.x()) + (-p0.x() + p2.x()) * t + (2 * p0.x() - 5 * p1.x() + 4 * p2.x() - p3.x()) * t2 + (-p0.x() + 3 * p1.x() - 3 * p2.x() + p3.x()) * t3)
                    y = 0.5 * ((2 * p1.y()) + (-p0.y() + p2.y()) * t + (2 * p0.y() - 5 * p1.y() + 4 * p2.y() - p3.y()) * t2 + (-p0.y() + 3 * p1.y() - 3 * p2.y() + p3.y()) * t3)
                    pt = QPointF(x, y)

                    if forma == 'Cuadrado':
                        painter.drawRect(QRectF(x - hw, y - hw, grosor, grosor))
                    else:
                        painter.drawEllipse(pt, hw, hw)

            painter.end()
            self._last_drawn_index = n - 1

        self._last_pos = pos
        if hasattr(canvas.layer_mgr, 'invalidate_cache'):
            canvas.layer_mgr.invalidate_cache()
        if canvas.callback_modificado:
            canvas.callback_modificado()
        canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        self.is_drawing = False
        self._last_pos = None
        self.shift_anchor = None
        self._points = []
        self._last_drawn_index = 0

    # ── borrado por segmento ──────────────────────────────────────────────────

    def _erase_segment(self, canvas, p1: QPointF, p2: QPointF):
        """Borra el punto inicial o segmento p1→p2 según la forma activa."""
        qimg = canvas.layer_mgr.buffer
        grosor = max(1, getattr(canvas, 'grosor_pincel', 3))
        suavizado = getattr(canvas, 'suavizado_pincel', True)
        forma = getattr(canvas, 'forma_pincel', 'Redondo')

        painter = QPainter(qimg)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        if suavizado:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if forma == 'Cuadrado':
            _stamp_rect_segment_clear(painter, p1, p2, grosor)
        else:
            pen = QPen(QColor(0, 0, 0, 255), grosor, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            if p1 == p2:
                painter.drawPoint(p1)
            else:
                painter.drawLine(p1, p2)

        painter.end()


# ── helpers ───────────────────────────────────────────────────────────────────

def _stamp_rect_segment_clear(painter: QPainter,
                               p1: QPointF, p2: QPointF,
                               grosor: float):
    """Estampa drawRect axis-aligned de p1 a p2 en modo Clear.
    El painter ya debe tener CompositionMode_Clear seteado.
    Paso = 30% del lado para garantizar superposición sin huecos."""
    hw = grosor / 2.0
    paso = max(0.5, grosor * 0.30)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(0, 0, 0, 255)))

    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()
    length = math.sqrt(dx * dx + dy * dy)

    if length <= 0:
        painter.drawRect(QRectF(p1.x() - hw, p1.y() - hw, grosor, grosor))
        return

    n = max(1, int(length / paso))
    for i in range(n + 1):
        t = i / n
        x = p1.x() + dx * t
        y = p1.y() + dy * t
        painter.drawRect(QRectF(x - hw, y - hw, grosor, grosor))
