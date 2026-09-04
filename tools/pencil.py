import math
import random
from PyQt6.QtCore import Qt, QPoint, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush
from PyQt6.QtWidgets import QApplication
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
        radius = size / 2.0
        modo = getattr(canvas, 'pencil_modo', 'pixelado')

        painter.save()
        # En modo realista usamos antialiasing para el cursor circular; en pixelado, pixel-perfect
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, (modo == 'realista'))

        col_pri = QColor(canvas.color_primario)

        pen_outer = QPen(QColor(0, 0, 0, 180), 1.5)
        painter.setPen(pen_outer)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(pos, radius + 0.5, radius + 0.5)

        col_rim = QColor(col_pri)
        col_rim.setAlpha(255)
        pen_inner = QPen(col_rim, 1.0)
        painter.setPen(pen_inner)

        col_fill = QColor(col_pri)
        col_fill.setAlpha(40)
        painter.setBrush(QBrush(col_fill))

        painter.drawEllipse(pos, radius, radius)
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
        # Lápiz <= 10% (duro) -> dust_prob = 0.0 (cero polvo)
        # Lápiz > 10% -> dust_prob se incrementa gradualmente de forma claramente visible
        if polvo and dureza > 10:
            softness_dust = (dureza - 10.0) / 90.0  # 0.0 a 10% .. 1.0 a 100%
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
            self.last_point = event.position().toPoint()
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
            raw_pos = event.position().toPoint()
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
                current_point = raw_pos

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
                painter.drawLine(self.last_point, current_point)
            else:
                dureza = getattr(canvas, 'pencil_dureza', 50)
                polvo = getattr(canvas, 'pencil_polvo', True)

                dx = current_point.x() - self.last_point.x()
                dy = current_point.y() - self.last_point.y()
                dist = math.hypot(dx, dy)
                is_slow = (dist <= 3.0)

                step = max(0.5, w * 0.25)
                steps = max(1, int(math.ceil(dist / step)))

                for i in range(1, steps + 1):
                    t = i / steps
                    px = self.last_point.x() + dx * t
                    py = self.last_point.y() + dy * t
                    pt = QPoint(int(round(px)), int(round(py)))
                    self._draw_realistic_stamp(painter, pt, w, color, dureza, polvo, is_slow)

            painter.end()

            self.last_point = current_point
            if canvas.callback_modificado:
                canvas.callback_modificado()
            canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        self.is_drawing = False
        self.shift_anchor = None
