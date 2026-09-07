import math
import random
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush
from PyQt6.QtWidgets import QApplication
from core.stroke_smoother import generate_smooth_stroke_points, smooth_mouse_input
from tools.base_tool import BaseTool


class PencilTool(BaseTool):
    def __init__(self):
        super().__init__("Lápiz", "gui/iconos/pencil.png")
        self.last_point = QPoint()
        self.is_drawing = False
        self.shift_anchor = None

    def draw_handles(self, painter, canvas):
        if canvas.cursor_pos is None:
            return
        pos = canvas.cursor_pos
        size = max(1, getattr(canvas, 'grosor_pincel', 3))
        modo = getattr(canvas, 'pencil_modo', 'pixelado')

        painter.save()
        col_pri = QColor(canvas.color_primario)

        px = float(math.floor(pos.x()))
        py = float(math.floor(pos.y()))

        if modo == 'pixelado' and size == 1:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            pen_outer = QPen(QColor(0, 0, 0, 220), 1.0)
            pen_outer.setCosmetic(True)
            painter.setPen(pen_outer)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(px, py, 1.0, 1.0))

            col_rim = QColor(col_pri)
            col_rim.setAlpha(255)
            pen_inner = QPen(col_rim, 1.0)
            pen_inner.setCosmetic(True)
            painter.setPen(pen_inner)
            painter.drawRect(QRectF(px + 0.1, py + 0.1, 0.8, 0.8))
            painter.restore()
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, (modo == 'realista'))
        radius = size / 2.0
        center = QPointF(px + 0.5, py + 0.5)

        pen_outer = QPen(QColor(0, 0, 0, 180), 1.5)
        pen_outer.setCosmetic(True)
        painter.setPen(pen_outer)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, radius + 0.5, radius + 0.5)

        col_rim = QColor(col_pri)
        col_rim.setAlpha(255)
        pen_inner = QPen(col_rim, 1.0)
        pen_inner.setCosmetic(True)
        painter.setPen(pen_inner)

        col_fill = QColor(col_pri)
        col_fill.setAlpha(40)
        painter.setBrush(QBrush(col_fill))

        painter.drawEllipse(center, radius, radius)
        painter.restore()

    def _draw_realistic_stamp(self, painter, point, width, color, dureza, polvo, is_slow):
        """
        Dibuja un sello de grafito realista:
        - Dureza 1%: Línea muy definida y limpia, trazo firme y duro, prácticamente cero polvo.
        - Dureza 50%: Trazo intermedio con suave textura de grafito.
        - Dureza 100%: Trazo blando y denso, bordes difuminados/manchados y mayor cantidad de miguitas de polvo.
        """
        radius = max(0.5, width / 2.0)
        softness = max(0.01, min(1.0, dureza / 100.0))  # 0.01 (Duro) .. 1.0 (Blando)
        hard_factor = 1.0 - softness                    # 0.99 (Duro) .. 0.0 (Blando)

        painter.save()

        # 1. Sello principal del trazo
        alpha_core = int(160 + softness * 95)  # 160 (1% duro) .. 255 (100% blando)
        stamp_col = QColor(color)
        stamp_col.setAlpha(alpha_core)

        pt_f = QPointF(point)

        if hard_factor > 0.6:
            # Lápiz Duro (1% - 40%): Trazo bien definido y limpio
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(stamp_col))
            painter.drawEllipse(pt_f, radius, radius)
        else:
            # Lápiz Blando (40% - 100%): Trazo con bordes suavemente difuminados / manchados
            aura_radius = radius + (softness * 0.8)
            aura_alpha = int(25 + softness * 40)
            aura_col = QColor(color)
            aura_col.setAlpha(aura_alpha)

            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(aura_col))
            painter.drawEllipse(pt_f, aura_radius, aura_radius)

            # Núcleo denso
            painter.setBrush(QBrush(stamp_col))
            painter.drawEllipse(pt_f, radius, radius)

        # 2. Textura interna de grano de papel
        if radius >= 1.0:
            num_grain = int(max(1, radius * (0.3 + softness * 0.7)))
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            pen_grain = QPen(color, 1.0)
            painter.setPen(pen_grain)
            for _ in range(num_grain):
                ang = random.uniform(0, 2 * math.pi)
                r_offset = random.uniform(0, radius * 0.85)
                gx = int(round(point.x() + math.cos(ang) * r_offset))
                gy = int(round(point.y() + math.sin(ang) * r_offset))
                painter.drawPoint(gx, gy)

        # 3. Polvo / Miguitas de grafito (escalado por la blandura del lápiz)
        if polvo and dureza > 10:
            softness_dust = (dureza - 10.0) / 90.0
            dust_prob = softness_dust * 0.14
            if is_slow:
                dust_prob *= 1.5

            if random.random() < dust_prob:
                num_crumbs = 1 if (softness_dust < 0.6 or random.random() > 0.4) else random.randint(1, 3)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
                pen_dust = QPen(color, 1.0)
                painter.setPen(pen_dust)
                for _ in range(num_crumbs):
                    ang = random.uniform(0, 2 * math.pi)
                    dust_dist = radius + random.uniform(0.6, 2.4)
                    dx = int(round(point.x() + math.cos(ang) * dust_dist))
                    dy = int(round(point.y() + math.sin(ang) * dust_dist))
                    painter.drawPoint(dx, dy)

        painter.restore()

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.is_drawing = True
            px = int(math.floor(event.position().x()))
            py = int(math.floor(event.position().y()))
            pos = QPoint(px, py)
            self.last_point = pos
            self._points = [pos]
            self._last_drawn_index = 0
            self.shift_anchor = None

            modo = getattr(canvas, 'pencil_modo', 'pixelado')
            color = QColor(color_activo if color_activo else canvas.color_primario)
            color.setAlpha(255)

            w = max(1, canvas.grosor_pincel)
            buffer = canvas.layer_mgr.buffer
            painter = QPainter(buffer)
            canvas.aplicar_clip_seleccion(painter)

            if modo == 'pixelado':
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
                pen = QPen(color, w, Qt.PenStyle.SolidLine,
                           Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawPoint(self.last_point)
            else:
                dureza = getattr(canvas, 'pencil_dureza', 50)
                polvo = getattr(canvas, 'pencil_polvo', True)
                self._draw_realistic_stamp(painter, self.last_point, w, color, dureza, polvo, is_slow=True)

            painter.end()
            canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        if self.is_drawing:
            px = int(math.floor(event.position().x()))
            py = int(math.floor(event.position().y()))
            raw_pos = QPoint(px, py)
            modifiers = QApplication.keyboardModifiers()
            is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

            if is_shift:
                if self.shift_anchor is None:
                    self.shift_anchor = QPoint(self.last_point)
                dx = raw_pos.x() - self.shift_anchor.x()
                dy = raw_pos.y() - self.shift_anchor.y()
                if abs(dx) >= abs(dy):
                    current_point = QPoint(raw_pos.x(), self.shift_anchor.y())
                else:
                    current_point = QPoint(self.shift_anchor.x(), raw_pos.y())
            else:
                self.shift_anchor = None
                sm_pos = smooth_mouse_input(self.last_point, QPointF(raw_pos))
                current_point = QPoint(int(round(sm_pos.x())), int(round(sm_pos.y())))

            if not hasattr(self, '_points') or not self._points:
                self._points = [self.last_point]
                self._last_drawn_index = 0

            self._points.append(current_point)
            self._draw_pencil_stroke(canvas, color_activo, is_final=False)

            self.last_point = current_point
            if canvas.callback_modificado:
                canvas.callback_modificado()

            w = max(1, canvas.grosor_pincel)
            dirty_rect = QRect(self._points[-1], current_point).normalized().adjusted(-w - 4, -w - 4, w + 8, w + 8)
            canvas.actualizar_region_sucia(dirty_rect)

    def mouse_release(self, canvas, event, color_activo=None):
        if self.is_drawing:
            self._draw_pencil_stroke(canvas, color_activo, is_final=True)
            self.is_drawing = False
            self.shift_anchor = None
            self._points = []
            self._last_drawn_index = 0

    def _draw_pencil_stroke(self, canvas, color_activo, is_final=False):
        pts = getattr(self, '_points', [])
        if not pts:
            return

        modo = getattr(canvas, 'pencil_modo', 'pixelado')
        color = QColor(color_activo if color_activo else canvas.color_primario)
        color.setAlpha(255)
        w = max(1, canvas.grosor_pincel)
        dureza = getattr(canvas, 'pencil_dureza', 50)
        polvo = getattr(canvas, 'pencil_polvo', True)
        step_px = max(0.5, w * 0.25) if modo != 'pixelado' else 1.0

        sub_points, new_start_idx = generate_smooth_stroke_points(
            pts, self._last_drawn_index, is_final=is_final, step_px=step_px
        )

        buffer = canvas.layer_mgr.buffer
        painter = QPainter(buffer)
        canvas.aplicar_clip_seleccion(painter)

        if modo == 'pixelado':
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            pen = QPen(color, w, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)

        for pt_f, dist in sub_points:
            pt = QPoint(int(round(pt_f.x())), int(round(pt_f.y())))
            if modo == 'pixelado':
                painter.drawPoint(pt)
            else:
                self._draw_realistic_stamp(painter, pt, w, color, dureza, polvo, is_slow=(dist <= 3.0))

        painter.end()
        self._last_drawn_index = new_start_idx
