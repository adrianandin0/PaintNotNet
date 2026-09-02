import math
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QBrush, QImage, QPainterPath, QPolygonF, QColor
from tools.base_tool import BaseTool


HANDLE_NONE = 0
HANDLE_MOVE = 1
HANDLE_TOP_LEFT = 2
HANDLE_TOP_CENTER = 3
HANDLE_TOP_RIGHT = 4
HANDLE_MIDDLE_LEFT = 5
HANDLE_MIDDLE_RIGHT = 6
HANDLE_BOTTOM_LEFT = 7
HANDLE_BOTTOM_CENTER = 8
HANDLE_BOTTOM_RIGHT = 9


class ShapesTool(BaseTool):
    """Herramienta para insertar formas geométricas ajustables con soporte para Shift (relación 1:1 simétrica)."""
    def __init__(self):
        super().__init__("Insertar Formas", "gui/iconos/shapes.png")
        self.start_point = None
        self.current_point = None
        self.is_drawing = False
        self.is_moving = False
        self.is_resizing = False
        self.active_shape_rect = None
        self.active_handle = HANDLE_NONE
        self.drag_start_pos = None
        self.orig_rect = None

    def get_icon_path(self, canvas):
        tipo = "Rectángulo"
        if hasattr(canvas, 'main_window') and canvas.main_window and hasattr(canvas.main_window, 'top_toolbar'):
            tb = canvas.main_window.top_toolbar
            if hasattr(tb, 'combo_forma_tipo'):
                tipo = tb.combo_forma_tipo.currentData() or "Rectángulo"

        mapa_iconos = {
            "Rectángulo": "gui/iconos/shape_rectangle.png",
            "Triángulo": "gui/iconos/shape_triangle.png",
            "Elipse": "gui/iconos/shape_circle.png",
            "Chispa": "gui/iconos/shape_sparkle.png",
            "Sol": "gui/iconos/shape_sun.png",
            "Rombo": "gui/iconos/shape_diamond.png",
            "Nube": "gui/iconos/shape_cloud.png",
            "Corazón": "gui/iconos/shape_heart.png",
            "Chat": "gui/iconos/shape_chat.png",
            "Estrella": "gui/iconos/shape_star.png",
            "Flor": "gui/iconos/shape_flower.png",
            "Mano": "gui/iconos/hand.png",
        }
        return mapa_iconos.get(tipo, "gui/iconos/shapes.png")

    def _get_tight_rect(self, canvas, rect=None):
        if rect is None:
            rect = self.active_shape_rect
        if not rect or rect.width() < 1 or rect.height() < 1:
            return QRectF()
        tipo, estilo, redondeado, grosor, col_prim, col_sec = self._get_shape_config(canvas)
        full_path = self._get_full_shape_path(rect, tipo, redondeado)
        tight = full_path.boundingRect()
        if tight.width() < 1 or tight.height() < 1:
            return rect
        return tight

    def _get_handle_at(self, pt, canvas):
        if not self.active_shape_rect:
            return HANDLE_NONE
        tight = self._get_tight_rect(canvas)
        if not tight or tight.width() < 1 or tight.height() < 1:
            return HANDLE_NONE

        handle_size = 12.0
        half_h = handle_size / 2.0

        pts = {
            HANDLE_TOP_LEFT: QPointF(tight.left(), tight.top()),
            HANDLE_TOP_CENTER: QPointF(tight.center().x(), tight.top()),
            HANDLE_TOP_RIGHT: QPointF(tight.right(), tight.top()),
            HANDLE_MIDDLE_LEFT: QPointF(tight.left(), tight.center().y()),
            HANDLE_MIDDLE_RIGHT: QPointF(tight.right(), tight.center().y()),
            HANDLE_BOTTOM_LEFT: QPointF(tight.left(), tight.bottom()),
            HANDLE_BOTTOM_CENTER: QPointF(tight.center().x(), tight.bottom()),
            HANDLE_BOTTOM_RIGHT: QPointF(tight.right(), tight.bottom()),
        }

        for h_type, p in pts.items():
            h_rect = QRectF(p.x() - half_h, p.y() - half_h, handle_size, handle_size)
            if h_rect.contains(pt):
                return h_type

        if tight.contains(pt) or self.active_shape_rect.contains(pt):
            return HANDLE_MOVE

        return HANDLE_NONE

    def _update_cursor(self, canvas, pos):
        canvas.actualizar_cursor_herramienta(self)

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()

            if self.active_shape_rect:
                handle = self._get_handle_at(pos, canvas)
                if handle != HANDLE_NONE:
                    self.active_handle = handle
                    self.drag_start_pos = pos
                    self.orig_rect = QRectF(self.active_shape_rect)
                    self.orig_tight = self._get_tight_rect(canvas)
                    if handle == HANDLE_MOVE:
                        self.is_moving = True
                    else:
                        self.is_resizing = True
                    return
                else:
                    self.commit_shape(canvas)

            self.is_drawing = True
            self.start_point = pos
            self.current_point = pos
            self.active_shape_rect = QRectF(pos, pos)
            canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        pos = event.position()

        if self.is_drawing:
            self.current_point = pos
            self.active_shape_rect = self._calc_rect(canvas, event)
            canvas.update()
        elif self.is_moving and self.orig_rect and self.drag_start_pos:
            dx = pos.x() - self.drag_start_pos.x()
            dy = pos.y() - self.drag_start_pos.y()
            self.active_shape_rect = self.orig_rect.translated(dx, dy)
            canvas.update()
        elif self.is_resizing and self.orig_rect and self.drag_start_pos and getattr(self, 'orig_tight', None):
            dx = pos.x() - self.drag_start_pos.x()
            dy = pos.y() - self.drag_start_pos.y()

            left = self.orig_tight.left()
            top = self.orig_tight.top()
            right = self.orig_tight.right()
            bottom = self.orig_tight.bottom()

            if self.active_handle in (HANDLE_TOP_LEFT, HANDLE_MIDDLE_LEFT, HANDLE_BOTTOM_LEFT):
                left += dx
            if self.active_handle in (HANDLE_TOP_RIGHT, HANDLE_MIDDLE_RIGHT, HANDLE_BOTTOM_RIGHT):
                right += dx
            if self.active_handle in (HANDLE_TOP_LEFT, HANDLE_TOP_CENTER, HANDLE_TOP_RIGHT):
                top += dy
            if self.active_handle in (HANDLE_BOTTOM_LEFT, HANDLE_BOTTOM_CENTER, HANDLE_BOTTOM_RIGHT):
                bottom += dy

            modifiers = event.modifiers() if hasattr(event, 'modifiers') else Qt.KeyboardModifier.NoModifier
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                w = abs(right - left)
                h = abs(bottom - top)
                side = max(w, h)
                if self.active_handle in (HANDLE_TOP_LEFT, HANDLE_MIDDLE_LEFT, HANDLE_BOTTOM_LEFT):
                    left = right - side
                else:
                    right = left + side
                if self.active_handle in (HANDLE_TOP_LEFT, HANDLE_TOP_CENTER, HANDLE_TOP_RIGHT):
                    top = bottom - side
                else:
                    bottom = top + side

            new_tight = QRectF(QPointF(left, top), QPointF(right, bottom)).normalized()
            if new_tight.width() >= 2 and new_tight.height() >= 2 and self.orig_tight.width() > 0 and self.orig_tight.height() > 0:
                scale_x = new_tight.width() / self.orig_tight.width()
                scale_y = new_tight.height() / self.orig_tight.height()

                new_rect_left = new_tight.left() + (self.orig_rect.left() - self.orig_tight.left()) * scale_x
                new_rect_top = new_tight.top() + (self.orig_rect.top() - self.orig_tight.top()) * scale_y
                new_rect_w = self.orig_rect.width() * scale_x
                new_rect_h = self.orig_rect.height() * scale_y

                self.active_shape_rect = QRectF(new_rect_left, new_rect_top, new_rect_w, new_rect_h)
            canvas.update()
        else:
            self._update_cursor(canvas, pos)

    def mouse_release(self, canvas, event, color_activo=None):
        if self.is_drawing:
            self.is_drawing = False
            self.current_point = event.position()
            rect = self._calc_rect(canvas, event)
            if rect.width() < 3 or rect.height() < 3:
                self.active_shape_rect = None
            else:
                self.active_shape_rect = rect
            canvas.update()
        elif self.is_moving or self.is_resizing:
            self.is_moving = False
            self.is_resizing = False
            self.active_handle = HANDLE_NONE
            canvas.update()

    def _get_shape_config(self, canvas):
        tipo = "Rectángulo"
        estilo = "Solo Borde"
        redondeado = False
        grosor = getattr(canvas, 'grosor_pincel', 3)
        col_prim = getattr(canvas, 'color_primario', QColor(0, 0, 0))
        col_sec = getattr(canvas, 'color_secundario', QColor(255, 255, 255))

        if hasattr(canvas, 'main_window') and canvas.main_window and hasattr(canvas.main_window, 'top_toolbar'):
            tb = canvas.main_window.top_toolbar
            if hasattr(tb, 'combo_forma_tipo'):
                tipo = tb.combo_forma_tipo.currentData() or "Rectángulo"
            if hasattr(tb, 'combo_forma_estilo'):
                estilo = tb.combo_forma_estilo.currentData() or "Solo Borde"
            if hasattr(tb, 'chk_formas_redondeado'):
                redondeado = tb.chk_formas_redondeado.isChecked()

        return tipo, estilo, redondeado, grosor, col_prim, col_sec

    def _build_shape_path(self, rect, tipo, redondeado):
        path = QPainterPath()
        if rect.width() <= 0 or rect.height() <= 0:
            return path

        if tipo == "Elipse":
            path.addEllipse(rect)
        elif tipo == "Triángulo":
            x1, y1 = rect.left(), rect.top()
            x2, y2 = rect.right(), rect.bottom()

            if redondeado:
                r = max(4.0, min(rect.width(), rect.height()) * 0.2)

                p_top = QPointF((x1 + x2) / 2.0, y1)
                p_br = QPointF(x2, y2)
                p_bl = QPointF(x1, y2)

                def get_corner(p_prev, p_curr, p_next, radius):
                    v1 = QPointF(p_prev.x() - p_curr.x(), p_prev.y() - p_curr.y())
                    v2 = QPointF(p_next.x() - p_curr.x(), p_next.y() - p_curr.y())
                    len1 = math.hypot(v1.x(), v1.y())
                    len2 = math.hypot(v2.x(), v2.y())
                    if len1 == 0 or len2 == 0:
                        return p_curr, p_curr
                    d = min(radius, len1 * 0.45, len2 * 0.45)
                    start = QPointF(p_curr.x() + (v1.x() / len1) * d, p_curr.y() + (v1.y() / len1) * d)
                    end = QPointF(p_curr.x() + (v2.x() / len2) * d, p_curr.y() + (v2.y() / len2) * d)
                    return start, end

                s_top, e_top = get_corner(p_bl, p_top, p_br, r)
                s_br, e_br = get_corner(p_top, p_br, p_bl, r)
                s_bl, e_bl = get_corner(p_br, p_bl, p_top, r)

                path.moveTo(s_top)
                path.quadTo(p_top, e_top)
                path.lineTo(s_br)
                path.quadTo(p_br, e_br)
                path.lineTo(s_bl)
                path.quadTo(p_bl, e_bl)
                path.closeSubpath()
            else:
                p_top = QPointF((x1 + x2) / 2.0, y1)
                p_br = QPointF(x2, y2)
                p_bl = QPointF(x1, y2)

                poly = QPolygonF([p_top, p_br, p_bl])
                path.addPolygon(poly)
                path.closeSubpath()
        elif tipo == "Nube":
            x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
            path.moveTo(x + w * 0.15, y + h * 0.8)
            path.lineTo(x + w * 0.85, y + h * 0.8)
            path.cubicTo(x + w * 1.05, y + h * 0.8, x + w * 1.05, y + h * 0.45, x + w * 0.8, y + h * 0.45)
            path.cubicTo(x + w * 0.85, y + h * 0.15, x + w * 0.55, y + h * 0.1, x + w * 0.5, y + h * 0.3)
            path.cubicTo(x + w * 0.4, y + h * 0.15, x + w * 0.15, y + h * 0.15, x + w * 0.12, y + h * 0.45)
            path.cubicTo(x - w * 0.05, y + h * 0.5, x - w * 0.05, y + h * 0.8, x + w * 0.15, y + h * 0.8)
            path.closeSubpath()
        elif tipo == "Corazón":
            x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
            path.moveTo(x + w * 0.5, y + h * 0.18)
            path.cubicTo(x + w * 0.22, y - h * 0.05, x, y + h * 0.18, x, y + h * 0.40)
            path.cubicTo(x, y + h * 0.60, x + w * 0.20, y + h * 0.80, x + w * 0.5, y + h * 0.98)
            path.cubicTo(x + w * 0.80, y + h * 0.80, x + w, y + h * 0.60, x + w, y + h * 0.40)
            path.cubicTo(x + w, y + h * 0.18, x + w * 0.78, y - h * 0.05, x + w * 0.5, y + h * 0.18)
            path.closeSubpath()
        elif tipo == "Chat":
            x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
            body_h = h * 0.78
            body_path = QPainterPath()
            if redondeado:
                rx = max(2.0, min(w, body_h) * 0.18)
                body_path.addRoundedRect(QRectF(x, y, w, body_h), rx, rx)
            else:
                body_path.addRect(QRectF(x, y, w, body_h))

            tail_path = QPainterPath()
            poly_pts = [
                QPointF(x + w * 0.18, y + body_h - 1.0),
                QPointF(x + w * 0.08, y + h),
                QPointF(x + w * 0.34, y + body_h - 1.0)
            ]
            tail_path.addPolygon(QPolygonF(poly_pts))
            tail_path.closeSubpath()
            path = body_path.united(tail_path)
        elif tipo == "Estrella":
            cx, cy = rect.center().x(), rect.center().y()
            rx, ry = rect.width() / 2.0, rect.height() / 2.0
            r_outer_x, r_outer_y = rx, ry
            r_inner_x, r_inner_y = rx * 0.382, ry * 0.382

            pts = []
            for i in range(10):
                angle = -math.pi / 2.0 + i * (math.pi / 5.0)
                curr_rx = r_outer_x if i % 2 == 0 else r_inner_x
                curr_ry = r_outer_y if i % 2 == 0 else r_inner_y
                pts.append(QPointF(cx + curr_rx * math.cos(angle), cy + curr_ry * math.sin(angle)))

            if redondeado:
                r = min(rx, ry) * 0.08
                for i in range(10):
                    p_prev = pts[(i - 1) % 10]
                    p_curr = pts[i]
                    p_next = pts[(i + 1) % 10]

                    v1 = QPointF(p_prev.x() - p_curr.x(), p_prev.y() - p_curr.y())
                    v2 = QPointF(p_next.x() - p_curr.x(), p_next.y() - p_curr.y())
                    len1 = math.hypot(v1.x(), v1.y())
                    len2 = math.hypot(v2.x(), v2.y())
                    d = min(r, len1 * 0.4, len2 * 0.4) if (len1 > 0 and len2 > 0) else 0
                    s_pt = QPointF(p_curr.x() + (v1.x() / (len1 or 1)) * d, p_curr.y() + (v1.y() / (len1 or 1)) * d)
                    e_pt = QPointF(p_curr.x() + (v2.x() / (len2 or 1)) * d, p_curr.y() + (v2.y() / (len2 or 1)) * d)

                    if i == 0:
                        path.moveTo(s_pt)
                    else:
                        path.lineTo(s_pt)
                    path.quadTo(p_curr, e_pt)
                path.closeSubpath()
            else:
                path.addPolygon(QPolygonF(pts))
                path.closeSubpath()
        elif tipo == "Chispa":
            cx, cy = rect.center().x(), rect.center().y()
            rx, ry = rect.width() / 2.0, rect.height() / 2.0
            p_top = QPointF(cx, rect.top())
            p_right = QPointF(rect.right(), cy)
            p_bottom = QPointF(cx, rect.bottom())
            p_left = QPointF(rect.left(), cy)

            k = 0.18
            cp_tr = QPointF(cx + rx * k, cy - ry * k)
            cp_rb = QPointF(cx + rx * k, cy + ry * k)
            cp_bl = QPointF(cx - rx * k, cy + ry * k)
            cp_lt = QPointF(cx - rx * k, cy - ry * k)

            if redondeado:
                r = min(rx, ry) * 0.14
                def get_corner(p_prev, p_curr, p_next, radius):
                    v1 = QPointF(p_prev.x() - p_curr.x(), p_prev.y() - p_curr.y())
                    v2 = QPointF(p_next.x() - p_curr.x(), p_next.y() - p_curr.y())
                    len1 = math.hypot(v1.x(), v1.y())
                    len2 = math.hypot(v2.x(), v2.y())
                    if len1 == 0 or len2 == 0:
                        return p_curr, p_curr
                    d = min(radius, len1 * 0.45, len2 * 0.45)
                    start = QPointF(p_curr.x() + (v1.x() / len1) * d, p_curr.y() + (v1.y() / len1) * d)
                    end = QPointF(p_curr.x() + (v2.x() / len2) * d, p_curr.y() + (v2.y() / len2) * d)
                    return start, end

                s_top, e_top = get_corner(cp_lt, p_top, cp_tr, r)
                s_right, e_right = get_corner(cp_tr, p_right, cp_rb, r)
                s_bottom, e_bottom = get_corner(cp_rb, p_bottom, cp_bl, r)
                s_left, e_left = get_corner(cp_bl, p_left, cp_lt, r)

                path.moveTo(s_top)
                path.quadTo(p_top, e_top)
                path.quadTo(cp_tr, s_right)
                path.quadTo(p_right, e_right)
                path.quadTo(cp_rb, s_bottom)
                path.quadTo(p_bottom, e_bottom)
                path.quadTo(cp_bl, s_left)
                path.quadTo(p_left, e_left)
                path.quadTo(cp_lt, s_top)
                path.closeSubpath()
            else:
                path.moveTo(p_top)
                path.quadTo(cp_tr, p_right)
                path.quadTo(cp_rb, p_bottom)
                path.quadTo(cp_bl, p_left)
                path.quadTo(cp_lt, p_top)
                path.closeSubpath()
        elif tipo == "Rombo":
            cx, cy = rect.center().x(), rect.center().y()
            p_top = QPointF(cx, rect.top())
            p_right = QPointF(rect.right(), cy)
            p_bottom = QPointF(cx, rect.bottom())
            p_left = QPointF(rect.left(), cy)

            if redondeado:
                r = max(4.0, min(rect.width(), rect.height()) * 0.15)
                def get_corner(p_prev, p_curr, p_next, radius):
                    v1 = QPointF(p_prev.x() - p_curr.x(), p_prev.y() - p_curr.y())
                    v2 = QPointF(p_next.x() - p_curr.x(), p_next.y() - p_curr.y())
                    len1 = math.hypot(v1.x(), v1.y())
                    len2 = math.hypot(v2.x(), v2.y())
                    if len1 == 0 or len2 == 0:
                        return p_curr, p_curr
                    d = min(radius, len1 * 0.45, len2 * 0.45)
                    start = QPointF(p_curr.x() + (v1.x() / len1) * d, p_curr.y() + (v1.y() / len1) * d)
                    end = QPointF(p_curr.x() + (v2.x() / len2) * d, p_curr.y() + (v2.y() / len2) * d)
                    return start, end

                s_top, e_top = get_corner(p_left, p_top, p_right, r)
                s_right, e_right = get_corner(p_top, p_right, p_bottom, r)
                s_bottom, e_bottom = get_corner(p_right, p_bottom, p_left, r)
                s_left, e_left = get_corner(p_bottom, p_left, p_top, r)

                path.moveTo(s_top)
                path.quadTo(p_top, e_top)
                path.lineTo(s_right)
                path.quadTo(p_right, e_right)
                path.lineTo(s_bottom)
                path.quadTo(p_bottom, e_bottom)
                path.lineTo(s_left)
                path.quadTo(p_left, e_left)
                path.closeSubpath()
            else:
                poly = QPolygonF([p_top, p_right, p_bottom, p_left])
                path.addPolygon(poly)
                path.closeSubpath()
        elif tipo == "Sol":
            rays_path, center_path = self._build_sun_components(rect, redondeado)
            path = rays_path.united(center_path)
        elif tipo == "Flor":
            petals_path, center_path = self._build_flower_components(rect)
            path = petals_path.united(center_path)
        elif tipo == "Mano":
            outer_path, inner_path = self._build_hand_components(rect)
            path = outer_path.united(inner_path)
        else: # Rectángulo
            if redondeado:
                rx = max(2.0, min(rect.width(), rect.height()) * 0.15)
                path.addRoundedRect(rect, rx, rx)
            else:
                path.addRect(rect)
        return path

    def _build_hand_components(self, rect):
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()

        outer_path = QPainterPath()

        # Base izquierda del índice
        outer_path.moveTo(x + w * 0.28, y + h * 0.35)

        # Dedo índice hacia arriba (lado izquierdo)
        outer_path.lineTo(x + w * 0.28, y + h * 0.10)
        # Punta del índice redondeada
        outer_path.cubicTo(x + w * 0.28, y + h * 0.03, x + w * 0.42, y + h * 0.03, x + w * 0.42, y + h * 0.10)
        # Bajada del dedo índice (lado derecho)
        outer_path.lineTo(x + w * 0.42, y + h * 0.35)

        # Dedo Medio (bucle redondeado saliendo vertical desde x + w * 0.42)
        outer_path.cubicTo(x + w * 0.42, y + h * 0.26, x + w * 0.58, y + h * 0.26, x + w * 0.60, y + h * 0.38)

        # Dedo Anular (bucle redondeado)
        outer_path.cubicTo(x + w * 0.60, y + h * 0.31, x + w * 0.74, y + h * 0.31, x + w * 0.76, y + h * 0.43)

        # Dedo Meñique (bucle redondeado y caída lateral derecha)
        outer_path.cubicTo(x + w * 0.76, y + h * 0.38, x + w * 0.88, y + h * 0.40, x + w * 0.88, y + h * 0.52)

        # Curva redondeada de la palma inferior
        outer_path.cubicTo(x + w * 0.88, y + h * 0.75, x + w * 0.70, y + h * 0.88, x + w * 0.48, y + h * 0.88)

        # Pulgar doblado a la izquierda (llegando horizontalmente al punto x + w * 0.28, y + h * 0.35)
        outer_path.cubicTo(x + w * 0.30, y + h * 0.88, x + w * 0.12, y + h * 0.72, x + w * 0.12, y + h * 0.50)
        outer_path.cubicTo(x + w * 0.12, y + h * 0.40, x + w * 0.20, y + h * 0.35, x + w * 0.28, y + h * 0.35)
        outer_path.closeSubpath()

        # Líneas interiores (separaciones de dedos)
        inner_path = QPainterPath()

        # Separación 1: lado izquierdo del índice bajando hacia la palma
        inner_path.moveTo(x + w * 0.28, y + h * 0.35)
        inner_path.lineTo(x + w * 0.28, y + h * 0.50)

        # Separación 2: índice / medio
        inner_path.moveTo(x + w * 0.42, y + h * 0.35)
        inner_path.lineTo(x + w * 0.42, y + h * 0.50)

        # Separación 3: medio / anular
        inner_path.moveTo(x + w * 0.60, y + h * 0.38)
        inner_path.lineTo(x + w * 0.60, y + h * 0.50)

        # Separación 4: anular / meñique
        inner_path.moveTo(x + w * 0.76, y + h * 0.43)
        inner_path.lineTo(x + w * 0.76, y + h * 0.50)

        return outer_path, inner_path

    def _build_flower_components(self, rect):
        cx, cy = rect.center().x(), rect.center().y()
        rx, ry = rect.width() / 2.0, rect.height() / 2.0

        r_outer_x, r_outer_y = rx, ry
        r_center_x, r_center_y = rx * 0.28, ry * 0.28
        r_valley_x, r_valley_y = r_center_x, r_center_y

        center_rect = QRectF(cx - r_center_x, cy - r_center_y, r_center_x * 2, r_center_y * 2)
        center_path = QPainterPath()
        center_path.addEllipse(center_rect)

        flower_outer = QPainterPath()
        n = 6
        for i in range(n):
            a_peak = i * (2.0 * math.pi / n) - math.pi / 2.0
            a_v1 = (i - 0.5) * (2.0 * math.pi / n) - math.pi / 2.0
            a_v2 = (i + 0.5) * (2.0 * math.pi / n) - math.pi / 2.0

            p_v1 = QPointF(cx + r_valley_x * math.cos(a_v1), cy + r_valley_y * math.sin(a_v1))
            p_peak = QPointF(cx + r_outer_x * math.cos(a_peak), cy + r_outer_y * math.sin(a_peak))

            cp1 = QPointF(cx + r_outer_x * 0.72 * math.cos(a_peak - math.radians(22)), cy + r_outer_y * 0.72 * math.sin(a_peak - math.radians(22)))
            cp2 = QPointF(cx + r_outer_x * 1.00 * math.cos(a_peak - math.radians(10)), cy + r_outer_y * 1.00 * math.sin(a_peak - math.radians(10)))

            cp3 = QPointF(cx + r_outer_x * 1.00 * math.cos(a_peak + math.radians(10)), cy + r_outer_y * 1.00 * math.sin(a_peak + math.radians(10)))
            cp4 = QPointF(cx + r_outer_x * 0.72 * math.cos(a_peak + math.radians(22)), cy + r_outer_y * 0.72 * math.sin(a_peak + math.radians(22)))

            p_v2 = QPointF(cx + r_valley_x * math.cos(a_v2), cy + r_valley_y * math.sin(a_v2))

            if i == 0:
                flower_outer.moveTo(p_v1)

            flower_outer.cubicTo(cp1, cp2, p_peak)
            flower_outer.cubicTo(cp3, cp4, p_v2)

        flower_outer.closeSubpath()
        return flower_outer, center_path

    def _build_sun_components(self, rect, redondeado=False):
        cx, cy = rect.center().x(), rect.center().y()
        rx, ry = rect.width() / 2.0, rect.height() / 2.0

        # circulo central del sol
        r_center_x, r_center_y = rx * 0.46, ry * 0.46
        center_rect = QRectF(cx - r_center_x, cy - r_center_y, r_center_x * 2, r_center_y * 2)
        center_path = QPainterPath()
        center_path.addEllipse(center_rect)

        # rayos del sol
        rays_path = QPainterPath()
        n = 11
        r_inner_x, r_inner_y = rx * 0.50, ry * 0.50
        r_outer_x, r_outer_y = rx * 0.70, ry * 0.70
        delta_a = math.pi / 16.0

        def get_corner(p_prev, p_curr, p_next, radius):
            v1 = QPointF(p_prev.x() - p_curr.x(), p_prev.y() - p_curr.y())
            v2 = QPointF(p_next.x() - p_curr.x(), p_next.y() - p_curr.y())
            len1 = math.hypot(v1.x(), v1.y())
            len2 = math.hypot(v2.x(), v2.y())
            if len1 == 0 or len2 == 0:
                return p_curr, p_curr
            d = min(radius, len1 * 0.35, len2 * 0.35)
            start = QPointF(p_curr.x() + (v1.x() / len1) * d, p_curr.y() + (v1.y() / len1) * d)
            end = QPointF(p_curr.x() + (v2.x() / len2) * d, p_curr.y() + (v2.y() / len2) * d)
            return start, end

        for i in range(n):
            angle = i * (2.0 * math.pi / n) - math.pi / 2.0
            p_base1 = QPointF(cx + r_inner_x * math.cos(angle - delta_a), cy + r_inner_y * math.sin(angle - delta_a))
            p_tip   = QPointF(cx + r_outer_x * math.cos(angle), cy + r_outer_y * math.sin(angle))
            p_base2 = QPointF(cx + r_inner_x * math.cos(angle + delta_a), cy + r_inner_y * math.sin(angle + delta_a))

            if redondeado:
                r = min(rx, ry) * 0.08
                s_tip, e_tip = get_corner(p_base1, p_tip, p_base2, r)
                s_b2, e_b2   = get_corner(p_tip, p_base2, p_base1, r)
                s_b1, e_b1   = get_corner(p_base2, p_base1, p_tip, r)

                ray = QPainterPath()
                ray.moveTo(s_tip)
                ray.quadTo(p_tip, e_tip)
                ray.lineTo(s_b2)
                ray.quadTo(p_base2, e_b2)
                ray.lineTo(s_b1)
                ray.quadTo(p_base1, e_b1)
                ray.closeSubpath()
                rays_path.addPath(ray)
            else:
                ray = QPainterPath()
                ray.addPolygon(QPolygonF([p_base1, p_tip, p_base2]))
                ray.closeSubpath()
                rays_path.addPath(ray)

        return rays_path, center_path

    def _draw_shape_to_painter(self, painter, rect, tipo, estilo, redondeado, grosor, col_prim, col_sec):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        join_cap = Qt.PenJoinStyle.RoundJoin if redondeado else Qt.PenJoinStyle.MiterJoin
        end_cap = Qt.PenCapStyle.RoundCap if redondeado else Qt.PenCapStyle.SquareCap

        pen_inner = QPen(col_prim, grosor * 2, Qt.PenStyle.SolidLine, end_cap, join_cap)
        pen_single = QPen(col_prim, grosor, Qt.PenStyle.SolidLine, end_cap, join_cap)
        pen_black_inner = QPen(QColor(0, 0, 0), grosor * 2, Qt.PenStyle.SolidLine, end_cap, join_cap)
        pen_black_single = QPen(QColor(0, 0, 0), grosor, Qt.PenStyle.SolidLine, end_cap, join_cap)
        brush_fill = QBrush(col_sec)
        brush_solid = QBrush(col_prim)

        if tipo == "Mano":
            outer_path, inner_path = self._build_hand_components(rect)
            if estilo == "Solo Borde":
                painter.save()
                painter.setPen(pen_single)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(outer_path)
                painter.drawPath(inner_path)
                painter.restore()
            elif estilo == "Forma Sólida":
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(brush_solid)
                painter.drawPath(outer_path)
            else:  # Borde y Relleno
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(brush_fill)
                painter.drawPath(outer_path)
                painter.save()
                painter.setPen(pen_single)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(outer_path)
                painter.drawPath(inner_path)
                painter.restore()
            return
        elif tipo == "Sol":
            rays_path, center_path = self._build_sun_components(rect, redondeado)

            if estilo == "Solo Borde":
                painter.save()
                painter.setPen(pen_single)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(rays_path)
                painter.drawPath(center_path)
                painter.restore()
            elif estilo == "Forma Sólida":
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(col_prim))
                painter.drawPath(center_path)
                painter.setBrush(QBrush(col_sec))
                painter.drawPath(rays_path)
            else: # borde y relleno
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(col_prim))
                painter.drawPath(center_path)
                painter.setBrush(QBrush(col_sec))
                painter.drawPath(rays_path)

                painter.save()
                painter.setPen(pen_black_single)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(rays_path)
                painter.drawPath(center_path)
                painter.restore()
            return
        elif tipo == "Flor":
            flower_outer, center_path = self._build_flower_components(rect)

            if estilo == "Solo Borde":
                # Dibujar contorno de pétalos sin invadir el interior del círculo central
                painter.save()
                clip_petals = flower_outer.subtracted(center_path)
                painter.setClipPath(clip_petals)
                painter.setPen(pen_inner)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(flower_outer)
                painter.restore()

                # Dibujar círculo central exacto
                painter.save()
                painter.setPen(pen_single)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(center_path)
                painter.restore()
            elif estilo == "Forma Sólida":
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(col_sec))
                painter.drawPath(flower_outer)
                painter.setBrush(QBrush(col_prim))
                painter.drawPath(center_path)
            else: # borde y relleno (centro primario, petalos secundario, borde negro)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(col_sec))
                painter.drawPath(flower_outer)
                painter.setBrush(QBrush(col_prim))
                painter.drawPath(center_path)

                painter.save()
                clip_petals = flower_outer.subtracted(center_path)
                painter.setClipPath(clip_petals)
                painter.setPen(pen_black_inner)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(flower_outer)
                painter.restore()

                painter.save()
                painter.setPen(pen_black_single)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(center_path)
                painter.restore()
            return

        shape_path = self._build_shape_path(rect, tipo, redondeado)

        if estilo == "Forma Sólida":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(brush_solid)
            painter.drawPath(shape_path)
        elif estilo == "Borde y Relleno":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(brush_fill)
            painter.drawPath(shape_path)

            painter.save()
            painter.setClipPath(shape_path)
            painter.setPen(pen_inner)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(shape_path)
            painter.restore()
        else: # Solo Borde
            painter.save()
            painter.setClipPath(shape_path)
            painter.setPen(pen_inner)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(shape_path)
            painter.restore()

    def _calc_rect(self, canvas, event=None):
        if not self.start_point or not self.current_point:
            return QRectF()

        dx = self.current_point.x() - self.start_point.x()
        dy = self.current_point.y() - self.start_point.y()

        from PyQt6.QtWidgets import QApplication
        modifiers = QApplication.keyboardModifiers()
        if event and hasattr(event, 'modifiers'):
            modifiers = event.modifiers()

        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            side = max(abs(dx), abs(dy))
            sx = 1 if dx >= 0 else -1
            sy = 1 if dy >= 0 else -1
            rect = QRectF(QPointF(self.start_point), QPointF(self.start_point.x() + side * sx, self.start_point.y() + side * sy)).normalized()
        else:
            rect = QRectF(QPointF(self.start_point), QPointF(self.current_point)).normalized()
        return rect

    def _get_full_shape_path(self, rect, tipo, redondeado):
        if not rect or rect.width() < 1 or rect.height() < 1:
            return QPainterPath()
        if tipo == "Mano":
            outer_path, inner_path = self._build_hand_components(rect)
            return outer_path.united(inner_path)
        elif tipo == "Sol":
            rays_path, center_path = self._build_sun_components(rect, redondeado)
            return rays_path.united(center_path)
        elif tipo == "Flor":
            flower_outer, center_path = self._build_flower_components(rect)
            return flower_outer.united(center_path)
        else:
            return self._build_shape_path(rect, tipo, redondeado)

    def draw_preview(self, painter, canvas):
        if not self.active_shape_rect or self.active_shape_rect.width() < 1 or self.active_shape_rect.height() < 1:
            return

        rect = self.active_shape_rect
        tipo, estilo, redondeado, grosor, col_prim, col_sec = self._get_shape_config(canvas)

        painter.save()
        canvas.aplicar_clip_seleccion(painter)

        # Dibujar la forma activa calculada en tiempo real
        self._draw_shape_to_painter(painter, rect, tipo, estilo, redondeado, grosor, col_prim, col_sec)

        # Marco delimitador exacto encajado al alto/ancho del trazado (tight bounding rect)
        full_path = self._get_full_shape_path(rect, tipo, redondeado)
        tight_rect = full_path.boundingRect()
        if tight_rect.width() < 1 or tight_rect.height() < 1:
            tight_rect = rect

        # Dibujar marco delimitador (bounding box) azul guionzado encajado exactamente
        pen_box = QPen(QColor(0, 120, 215), 1.0, Qt.PenStyle.DashLine)
        pen_box.setCosmetic(True)
        painter.setPen(pen_box)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(tight_rect)

        # Tiradores de redimensionado en las esquinas y bordes exactos de la figura
        handle_size = 7.0
        half_h = handle_size / 2.0

        pts = [
            QPointF(tight_rect.left(), tight_rect.top()),
            QPointF(tight_rect.center().x(), tight_rect.top()),
            QPointF(tight_rect.right(), tight_rect.top()),
            QPointF(tight_rect.left(), tight_rect.center().y()),
            QPointF(tight_rect.right(), tight_rect.center().y()),
            QPointF(tight_rect.left(), tight_rect.bottom()),
            QPointF(tight_rect.center().x(), tight_rect.bottom()),
            QPointF(tight_rect.right(), tight_rect.bottom()),
        ]

        pen_handle = QPen(QColor(0, 120, 215), 1.0)
        pen_handle.setCosmetic(True)
        brush_handle = QBrush(QColor(255, 255, 255))
        painter.setPen(pen_handle)
        painter.setBrush(brush_handle)

        for pt in pts:
            h_rect = QRectF(pt.x() - half_h, pt.y() - half_h, handle_size, handle_size)
            painter.drawRect(h_rect)

        painter.restore()

    def clear_active_shape(self, canvas):
        self.active_shape_rect = None
        self.is_drawing = False
        self.is_moving = False
        self.is_resizing = False
        self.active_handle = HANDLE_NONE
        if canvas:
            canvas.update()

    def commit_shape(self, canvas):
        if not self.active_shape_rect or self.active_shape_rect.width() < 1 or self.active_shape_rect.height() < 1:
            self.clear_active_shape(canvas)
            return

        rect = self.active_shape_rect
        tipo, estilo, redondeado, grosor, col_prim, col_sec = self._get_shape_config(canvas)

        layer = canvas.layer_mgr.get_active_layer()
        if layer and layer.image:
            p = QPainter(layer.image)
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            canvas.aplicar_clip_seleccion(p)
            self._draw_shape_to_painter(p, rect, tipo, estilo, redondeado, grosor, col_prim, col_sec)
            p.end()
            canvas.push_document_state("Insertar Forma")

        self.clear_active_shape(canvas)

    def copy_shape_to_clipboard(self, canvas):
        if not self.active_shape_rect or self.active_shape_rect.width() < 1 or self.active_shape_rect.height() < 1:
            return False

        rect = self.active_shape_rect
        tipo, estilo, redondeado, grosor, col_prim, col_sec = self._get_shape_config(canvas)

        margin = grosor + 4
        img_w = int(rect.width()) + margin * 2
        img_h = int(rect.height()) + margin * 2

        shape_img = QImage(img_w, img_h, QImage.Format.Format_ARGB32_Premultiplied)
        shape_img.fill(Qt.GlobalColor.transparent)

        p = QPainter(shape_img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect_local = QRectF(margin, margin, rect.width(), rect.height())
        self._draw_shape_to_painter(p, rect_local, tipo, estilo, redondeado, grosor, col_prim, col_sec)
        p.end()

        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setImage(shape_img)
        return True

    def convert_to_selection(self, canvas):
        if not self.active_shape_rect or self.active_shape_rect.width() < 1 or self.active_shape_rect.height() < 1:
            return False

        rect = self.active_shape_rect
        tipo, estilo, redondeado, grosor, col_prim, col_sec = self._get_shape_config(canvas)

        margin = grosor + 4
        img_w = int(rect.width()) + margin * 2
        img_h = int(rect.height()) + margin * 2

        shape_img = QImage(img_w, img_h, QImage.Format.Format_ARGB32_Premultiplied)
        shape_img.fill(Qt.GlobalColor.transparent)

        p = QPainter(shape_img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect_local = QRectF(margin, margin, rect.width(), rect.height())
        self._draw_shape_to_painter(p, rect_local, tipo, estilo, redondeado, grosor, col_prim, col_sec)
        p.end()

        shape_path_global = self._get_full_shape_path(rect, tipo, redondeado)
        pos_global = QPointF(rect.x() - margin, rect.y() - margin)

        canvas.selection_engine.floating_image = shape_img
        canvas.selection_engine.unscaled_floating_image = shape_img.copy()
        canvas.selection_engine.original_image_pos = pos_global
        canvas.selection_engine.active_path = shape_path_global
        canvas.selection_engine.active_rect = shape_path_global.boundingRect()
        canvas.selection_engine.is_transforming = True
        canvas.selection_engine.is_new_content = True

        self.clear_active_shape(canvas)

        from tools.move_select_pixels import MoveSelectPixelsTool
        if hasattr(canvas, 'main_window') and canvas.main_window and hasattr(canvas.main_window, 'tool_panel'):
            for btn in canvas.main_window.tool_panel.button_group.buttons():
                t = btn.property("tool_obj")
                if isinstance(t, MoveSelectPixelsTool):
                    btn.setChecked(True)
                    canvas.set_active_tool(t)
                    break
        return True
