import math
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath
from tools.base_tool import BaseTool
from tools.brush import _draw_cursor


class EraserTool(BaseTool):
    """Goma de borrar.

    Estrategia: borrado INCREMENTAL — solo se borra el nuevo segmento en cada
    evento de mouse_move.  Esto evita redibujar el path completo (que crea
    artefactos de antialiasing al combinar con CompositionMode_Clear).

    Modo Redondo: QPen RoundCap incremental.
    Modo Cuadrado: stamps de drawRect axis-aligned incrementales
                   (evita la rotación de SquareCap).
    """

    def __init__(self):
        super().__init__("Goma de Borrar", "gui/iconos/eraser.png")
        self.is_drawing = False
        self._last_pos: QPointF | None = None

    # ── cursor de preview ─────────────────────────────────────────────────────

    def draw_handles(self, painter, canvas):
        if canvas.cursor_pos is None:
            return
        pos = canvas.cursor_pos
        size = max(1, getattr(canvas, 'grosor_pincel', 3))
        r = size / 2.0
        forma = getattr(canvas, 'forma_pincel', 'Redondo')

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        painter.setPen(QPen(QColor(0, 0, 0, 200), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        _draw_cursor(painter, pos, r + 0.5, forma)

        painter.setPen(QPen(QColor(255, 255, 255, 255), 1.0))
        painter.setBrush(QBrush(QColor(255, 255, 255, 80)))
        _draw_cursor(painter, pos, r, forma)

        painter.restore()

    # ── eventos de mouse ──────────────────────────────────────────────────────

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.is_drawing = True
            pos = event.position()
            self._last_pos = pos
            # Punto inicial: forma centrada sin dirección
            self._erase_segment(canvas, pos, pos)
            canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        if not self.is_drawing:
            return
        pos = event.position()
        self._erase_segment(canvas, self._last_pos, pos)
        self._last_pos = pos
        if canvas.callback_modificado:
            canvas.callback_modificado()
        canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        self.is_drawing = False
        self._last_pos = None

    # ── borrado por segmento ──────────────────────────────────────────────────

    def _erase_segment(self, canvas, p1: QPointF, p2: QPointF):
        """Borra el segmento p1→p2 según la forma activa."""
        qimg = canvas.layer_mgr.buffer
        grosor = max(1, getattr(canvas, 'grosor_pincel', 3))
        suavizado = getattr(canvas, 'suavizado_pincel', True)
        forma = getattr(canvas, 'forma_pincel', 'Redondo')

        painter = QPainter(qimg)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        if suavizado:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if forma == 'Cuadrado':
            # Stamps axis-aligned: no hay rotación con la dirección del trazo
            _stamp_rect_segment_clear(painter, p1, p2, grosor)
        else:
            # Círculo: QPen RoundCap en el segmento incremental
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
