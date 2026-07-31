import math
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath, QBrush, QTransform
from PyQt6.QtWidgets import QApplication
from tools.base_tool import BaseTool


def _draw_cap(painter, pt, dir_vec, cap_type, color, stroke_width):
    if cap_type == "Plana" or not cap_type:
        return

    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(color))

    norm = math.hypot(dir_vec.x(), dir_vec.y())
    if norm < 1e-5:
        painter.restore()
        return

    u = QPointF(dir_vec.x() / norm, dir_vec.y() / norm)
    p_perp = QPointF(-u.y(), u.x())

    if cap_type == "Redonda":
        # Semicírculo del ancho exacto de la línea (tipo trazo de pincel)
        r = stroke_width / 2.0
        painter.drawEllipse(pt, r, r)

    elif cap_type == "Circulo":
        # Círculo más grande decorativo (como la punta de flecha)
        r = max(4.5, stroke_width * 1.3)
        painter.drawEllipse(pt, r, r)

    elif cap_type == "Flecha":
        # Flecha más corta y compacta para no sobresalir del trazo
        length = max(8.0, stroke_width * 2.4)
        width = max(10.0, stroke_width * 2.8)

        p_tip = pt + u * (length * 0.2)
        p_back = pt - u * (length * 0.8)
        p_left = p_back + p_perp * (width * 0.5)
        p_right = p_back - p_perp * (width * 0.5)

        arrow_path = QPainterPath()
        arrow_path.moveTo(p_tip)
        arrow_path.lineTo(p_left)
        arrow_path.lineTo(p_right)
        arrow_path.closeSubpath()
        painter.drawPath(arrow_path)

    painter.restore()


class LineTool(BaseTool):
    HANDLE_NONE = 0
    HANDLE_P0 = 1
    HANDLE_P1 = 2
    HANDLE_P2 = 3
    HANDLE_P3 = 4

    HANDLE_SIZE = 8

    def __init__(self):
        super().__init__("Línea", "gui/iconos/line.png")
        self.p0 = None
        self.p1 = None
        self.p2 = None
        self.p3 = None

        self.state = 0  # 0: sin iniciar, 1: creando fin, 2: colocado con tiradores
        self.active_handle = self.HANDLE_NONE
        self.is_rotating = False
        self.rotation_center = QPointF()
        self.initial_angle = 0.0

        self.orig_p0 = None
        self.orig_p1 = None
        self.orig_p2 = None
        self.orig_p3 = None

    def reset(self):
        self.p0 = None
        self.p1 = None
        self.p2 = None
        self.p3 = None
        self.state = 0
        self.active_handle = self.HANDLE_NONE
        self.is_rotating = False

    def _init_points(self, p0, p3):
        self.p0 = QPointF(p0)
        self.p3 = QPointF(p3)
        vec = self.p3 - self.p0
        self.p1 = self.p0 + vec * (1.0 / 3.0)
        self.p2 = self.p0 + vec * (2.0 / 3.0)

    def hit_test(self, pos):
        if self.state != 2:
            return self.HANDLE_NONE

        s2 = self.HANDLE_SIZE / 2.0
        pts = [
            (self.HANDLE_P0, self.p0),
            (self.HANDLE_P1, self.p1),
            (self.HANDLE_P2, self.p2),
            (self.HANDLE_P3, self.p3),
        ]

        for h_id, pt in pts:
            if pt and QRectF(pt.x() - s2, pt.y() - s2, self.HANDLE_SIZE, self.HANDLE_SIZE).contains(pos):
                return h_id
        return self.HANDLE_NONE

    def mouse_press(self, canvas, event, color_activo=None):
        pos = event.position()

        if self.state == 2:
            if event.button() == Qt.MouseButton.RightButton:
                self.is_rotating = True
                self.rotation_center = self.p0 + (self.p3 - self.p0) * 0.5
                dx = pos.x() - self.rotation_center.x()
                dy = pos.y() - self.rotation_center.y()
                self.initial_angle = math.atan2(dy, dx)

                self.orig_p0 = QPointF(self.p0)
                self.orig_p1 = QPointF(self.p1)
                self.orig_p2 = QPointF(self.p2)
                self.orig_p3 = QPointF(self.p3)
                return

            hit = self.hit_test(pos)
            if hit != self.HANDLE_NONE:
                self.active_handle = hit
                return
            else:
                self.commit_line(canvas)

        if self.state == 0 and event.button() == Qt.MouseButton.LeftButton:
            self._init_points(pos, pos)
            self.state = 1
            canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        pos = event.position()
        modifiers = QApplication.keyboardModifiers()
        is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

        if self.state == 1:
            self._init_points(self.p0, pos)
            canvas.update()
        elif self.state == 2:
            if self.is_rotating:
                dx = pos.x() - self.rotation_center.x()
                dy = pos.y() - self.rotation_center.y()
                current_angle = math.atan2(dy, dx)
                delta_rad = current_angle - self.initial_angle
                deg = math.degrees(delta_rad)

                t = QTransform()
                t.translate(self.rotation_center.x(), self.rotation_center.y())
                t.rotate(deg)
                t.translate(-self.rotation_center.x(), -self.rotation_center.y())

                self.p0 = t.map(self.orig_p0)
                self.p1 = t.map(self.orig_p1)
                self.p2 = t.map(self.orig_p2)
                self.p3 = t.map(self.orig_p3)
                canvas.update()
            elif self.active_handle != self.HANDLE_NONE:
                if self.active_handle == self.HANDLE_P0:
                    self.p0 = QPointF(pos)
                    if is_shift:
                        vec = self.p3 - self.p0
                        self.p1 = self.p0 + vec * (1.0 / 3.0)
                        self.p2 = self.p0 + vec * (2.0 / 3.0)
                elif self.active_handle == self.HANDLE_P3:
                    self.p3 = QPointF(pos)
                    if is_shift:
                        vec = self.p3 - self.p0
                        self.p1 = self.p0 + vec * (1.0 / 3.0)
                        self.p2 = self.p0 + vec * (2.0 / 3.0)
                elif self.active_handle == self.HANDLE_P1:
                    self.p1 = QPointF(pos)
                elif self.active_handle == self.HANDLE_P2:
                    self.p2 = QPointF(pos)

                canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        if self.state == 1:
            self.state = 2
            canvas.update()
        elif self.state == 2:
            self.active_handle = self.HANDLE_NONE
            self.is_rotating = False

    def key_press(self, canvas, event, color_activo=None):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Escape):
            if self.state in (1, 2):
                self.commit_line(canvas)
                return True
        return False

    def _draw_line_stroke(self, painter, canvas):
        color = QColor(canvas.color_primario)
        suavizado = getattr(canvas, 'suavizado_pincel', True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, suavizado)

        stroke_width = max(1, getattr(canvas, 'ancho_pincel', 3))
        estilo_linea = getattr(canvas, 'linea_estilo', 'Recta')
        pen_style = Qt.PenStyle.DashLine if estilo_linea == 'Punteada' else Qt.PenStyle.SolidLine

        cap_inicio = getattr(canvas, 'linea_cap_inicio', 'Plana')
        cap_fin = getattr(canvas, 'linea_cap_fin', 'Plana')

        # Tangente en p0
        v0 = self.p0 - (self.p1 if self.p1 != self.p0 else self.p3)
        # Tangente en p3
        v3 = self.p3 - (self.p2 if self.p2 != self.p3 else self.p0)

        # Recortar ligeramente extremos si la punta es Flecha
        p0_draw = QPointF(self.p0)
        p3_draw = QPointF(self.p3)

        norm0 = math.hypot(v0.x(), v0.y())
        if norm0 > 1e-5 and cap_inicio == "Flecha":
            u0 = QPointF(v0.x() / norm0, v0.y() / norm0)
            len0 = max(8.0, stroke_width * 2.4)
            p0_draw = self.p0 - u0 * (len0 * 0.4)

        norm3 = math.hypot(v3.x(), v3.y())
        if norm3 > 1e-5 and cap_fin == "Flecha":
            u3 = QPointF(v3.x() / norm3, v3.y() / norm3)
            len3 = max(8.0, stroke_width * 2.4)
            p3_draw = self.p3 - u3 * (len3 * 0.4)

        pen = QPen(color, stroke_width, pen_style, Qt.PenCapStyle.FlatCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        path = QPainterPath(p0_draw)
        p1_draw = self.p1 if cap_inicio != "Flecha" else p0_draw + (self.p1 - self.p0)
        p2_draw = self.p2 if cap_fin != "Flecha" else p3_draw + (self.p2 - self.p3)
        path.cubicTo(p1_draw, p2_draw, p3_draw)
        painter.drawPath(path)

        # Dibujar remates
        _draw_cap(painter, self.p0, v0, cap_inicio, color, stroke_width)
        _draw_cap(painter, self.p3, v3, cap_fin, color, stroke_width)

    def commit_line(self, canvas):
        if self.state in (1, 2) and self.p0 and self.p3:
            painter = QPainter(canvas.layer_mgr.buffer)
            canvas.aplicar_clip_seleccion(painter)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            self._draw_line_stroke(painter, canvas)
            painter.end()

            self.reset()
            canvas.push_document_state("Línea")
            canvas.update()
        else:
            self.reset()
            canvas.update()

    def draw_preview(self, painter, canvas):
        if self.state in (1, 2) and self.p0 and self.p3:
            self._draw_line_stroke(painter, canvas)

    def draw_handles(self, painter, canvas):
        if self.state == 2 and self.p0 and self.p3:
            s = self.HANDLE_SIZE
            s2 = s / 2.0
            pts = [self.p0, self.p1, self.p2, self.p3]

            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.setBrush(QBrush(QColor(255, 255, 255)))

            for pt in pts:
                if pt:
                    painter.drawRect(QRectF(pt.x() - s2, pt.y() - s2, s, s))
