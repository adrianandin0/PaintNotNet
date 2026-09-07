import math
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath, QImage, QBrush
from tools.base_tool import BaseTool


from PyQt6.QtWidgets import QApplication
from core.stroke_smoother import generate_smooth_stroke_points, smooth_mouse_input

class BrushTool(BaseTool):
    def __init__(self):
        super().__init__("Pincel", "gui/iconos/brush.png")
        self.is_drawing = False
        self.path = None
        self._points = []        # puntos crudos del mouse
        self._last_drawn_index = 0
        self._press_pos = None
        self._has_moved = False
        self.shift_anchor = None

    def draw_handles(self, painter, canvas):
        if canvas.cursor_pos is None:
            return
        px = math.floor(canvas.cursor_pos.x())
        py = math.floor(canvas.cursor_pos.y())
        pos = QPointF(px + 0.5, py + 0.5)
        size = max(1, getattr(canvas, 'grosor_pincel', 5))
        r = size / 2.0
        forma = getattr(canvas, 'forma_pincel', 'Redondo')

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        pen_outer = QPen(QColor(0, 0, 0, 180), 1.5)
        pen_outer.setCosmetic(True)
        painter.setPen(pen_outer)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        _draw_cursor(painter, pos, r + 0.5, forma)

        col_pri = QColor(canvas.color_primario)
        col_rim = QColor(col_pri)
        col_rim.setAlpha(255)
        pen_inner = QPen(col_rim, 1.0)
        pen_inner.setCosmetic(True)
        painter.setPen(pen_inner)

        col_fill = QColor(col_pri)
        col_fill.setAlpha(40)
        painter.setBrush(QBrush(col_fill))

        _draw_cursor(painter, pos, r, forma)
        painter.restore()

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.is_drawing = True
            px = math.floor(event.position().x())
            py = math.floor(event.position().y())
            pos = QPointF(px + 0.5, py + 0.5)
            self._press_pos = pos
            self._has_moved = False
            self._points = [pos]
            self._last_drawn_index = 0
            self.shift_anchor = None

            if not hasattr(canvas, 'capa_trazo_temp') or canvas.capa_trazo_temp.isNull():
                canvas.capa_trazo_temp = QImage(canvas.layer_mgr.width, canvas.layer_mgr.height, QImage.Format.Format_ARGB32_Premultiplied)
                canvas.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

            self._draw_incremental_stroke(canvas, color_activo, is_final=False)

            if hasattr(canvas.layer_mgr, 'invalidate_cache'):
                canvas.layer_mgr.invalidate_cache()
            canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        if not self.is_drawing or not self._points:
            return
        px = math.floor(event.position().x())
        py = math.floor(event.position().y())
        raw_pos = QPointF(px + 0.5, py + 0.5)
        modifiers = QApplication.keyboardModifiers()
        is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

        if is_shift:
            if self.shift_anchor is None:
                self.shift_anchor = self._points[0]
            dx = raw_pos.x() - self.shift_anchor.x()
            dy = raw_pos.y() - self.shift_anchor.y()
            if abs(dx) >= abs(dy):
                pos = QPointF(raw_pos.x(), self.shift_anchor.y())
            else:
                pos = QPointF(self.shift_anchor.x(), raw_pos.y())
        else:
            self.shift_anchor = None
            pos = smooth_mouse_input(self._points[-1], raw_pos)

        self._has_moved = True
        self._points.append(pos)
        self._draw_incremental_stroke(canvas, color_activo, is_final=False)
        if canvas.callback_modificado:
            canvas.callback_modificado()

        grosor = max(1, canvas.grosor_pincel)
        p_last = self._points[-2] if len(self._points) >= 2 else pos
        dirty_rect = QRectF(p_last, pos).normalized().toRect().adjusted(-grosor - 4, -grosor - 4, grosor + 8, grosor + 8)
        canvas.actualizar_region_sucia(dirty_rect)

    def mouse_release(self, canvas, event, color_activo=None):
        if self.is_drawing:
            self._draw_incremental_stroke(canvas, color_activo, is_final=True)

            color = QColor(color_activo if color_activo else canvas.color_primario)
            alpha_norm = color.alpha() / 255.0

            buffer = canvas.layer_mgr.buffer
            painter = QPainter(buffer)
            canvas.aplicar_clip_seleccion(painter)
            painter.setOpacity(alpha_norm)
            painter.drawImage(0, 0, canvas.capa_trazo_temp)
            painter.end()

            canvas.capa_trazo_temp.fill(Qt.GlobalColor.transparent)
            if hasattr(canvas.layer_mgr, 'active_stroke_alpha'):
                canvas.layer_mgr.active_stroke_alpha = 1.0
            if hasattr(canvas.layer_mgr, 'invalidate_cache'):
                canvas.layer_mgr.invalidate_cache()

            self.path = None
            self._points = []
            self._last_drawn_index = 0
            self.shift_anchor = None
            self.is_drawing = False
            canvas.update()

    def _draw_incremental_stroke(self, canvas, color_activo, is_final=False):
        """Dibuja de forma incremental con suavizado Bézier C^1 continuo sin esquinas angulosas."""
        pts = self._points
        if len(pts) == 0:
            return

        forma = getattr(canvas, 'forma_pincel', 'Redondo')
        grosor = max(1, canvas.grosor_pincel)
        step_px = max(0.5, grosor * 0.15)

        sub_points, new_start_idx = generate_smooth_stroke_points(
            pts, self._last_drawn_index, is_final=is_final, step_px=step_px
        )

        painter = QPainter(canvas.capa_trazo_temp)
        canvas.aplicar_clip_seleccion(painter)

        color = QColor(color_activo if color_activo else canvas.color_primario)
        color_solid = QColor(color)
        color_solid.setAlpha(255)

        if hasattr(canvas.layer_mgr, 'active_stroke_alpha'):
            canvas.layer_mgr.active_stroke_alpha = color.alpha() / 255.0

        suavizado = getattr(canvas, 'suavizado_pincel', True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, suavizado)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color_solid))

        r = grosor / 2.0
        hw = r

        if len(pts) == 1 and self._last_drawn_index == 0:
            p = pts[0]
            if forma == 'Cuadrado':
                painter.drawRect(QRectF(p.x() - hw, p.y() - hw, grosor, grosor))
            else:
                painter.drawEllipse(p, r, r)
        else:
            for pt, _ in sub_points:
                if forma == 'Cuadrado':
                    painter.drawRect(QRectF(pt.x() - hw, pt.y() - hw, grosor, grosor))
                else:
                    painter.drawEllipse(pt, r, r)

        self._last_drawn_index = new_start_idx
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
