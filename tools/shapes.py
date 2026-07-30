import math
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QBrush, QImage, QPainterPath, QPolygonF, QColor
from tools.base_tool import BaseTool


class ShapesTool(BaseTool):
    """Herramienta para insertar formas geométricas ajustables con soporte para Shift (relación 1:1 simétrica)."""
    def __init__(self):
        super().__init__("Insertar Formas", "gui/iconos/shapes.png")
        self.start_point = None
        self.current_point = None
        self.is_drawing = False

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_drawing = True
            self.start_point = event.position()
            self.current_point = event.position()
            canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        if self.is_drawing:
            self.current_point = event.position()
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
        else: # Rectángulo
            if redondeado:
                rx = max(2.0, min(rect.width(), rect.height()) * 0.15)
                path.addRoundedRect(rect, rx, rx)
            else:
                path.addRect(rect)
        return path

    def _draw_shape_to_painter(self, painter, rect, tipo, estilo, redondeado, grosor, col_prim, col_sec):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        join_cap = Qt.PenJoinStyle.RoundJoin if redondeado else Qt.PenJoinStyle.MiterJoin
        end_cap = Qt.PenCapStyle.RoundCap if redondeado else Qt.PenCapStyle.SquareCap

        pen_border = QPen(col_prim, grosor, Qt.PenStyle.SolidLine, end_cap, join_cap)
        brush_fill = QBrush(col_sec)
        brush_solid = QBrush(col_prim)

        if estilo == "Forma Sólida":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(brush_solid)
        elif estilo == "Borde y Relleno":
            painter.setPen(pen_border)
            painter.setBrush(brush_fill)
        else: # Solo Borde
            painter.setPen(pen_border)
            painter.setBrush(Qt.BrushStyle.NoBrush)

        shape_path = self._build_shape_path(rect, tipo, redondeado)
        painter.drawPath(shape_path)

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

    def draw_preview(self, painter, canvas):
        if not self.is_drawing or not self.start_point or not self.current_point:
            return

        rect = self._calc_rect(canvas)
        if rect.width() < 1 or rect.height() < 1:
            return

        tipo, estilo, redondeado, grosor, col_prim, col_sec = self._get_shape_config(canvas)

        painter.save()
        canvas.aplicar_clip_seleccion(painter)
        self._draw_shape_to_painter(painter, rect, tipo, estilo, redondeado, grosor, col_prim, col_sec)
        painter.restore()

    def mouse_release(self, canvas, event, color_activo=None):
        if not self.is_drawing:
            return

        self.is_drawing = False
        if not self.start_point or not self.current_point:
            return

        rect = self._calc_rect(canvas, event)
        if rect.width() < 2 or rect.height() < 2:
            canvas.update()
            return

        tipo, estilo, redondeado, grosor, col_prim, col_sec = self._get_shape_config(canvas)

        margin = grosor + 4
        img_w = int(rect.width()) + margin * 2
        img_h = int(rect.height()) + margin * 2

        shape_img = QImage(img_w, img_h, QImage.Format.Format_ARGB32_Premultiplied)
        shape_img.fill(Qt.GlobalColor.transparent)

        p = QPainter(shape_img)
        rect_local = QRectF(margin, margin, rect.width(), rect.height())
        self._draw_shape_to_painter(p, rect_local, tipo, estilo, redondeado, grosor, col_prim, col_sec)
        p.end()

        # Construir path de la forma ajustado
        shape_path_global = self._build_shape_path(rect, tipo, redondeado)

        pos_global = QPointF(rect.x() - margin, rect.y() - margin)
        canvas.selection_engine.floating_image = shape_img
        canvas.selection_engine.unscaled_floating_image = shape_img.copy()
        canvas.selection_engine.original_image_pos = pos_global
        canvas.selection_engine.active_path = shape_path_global
        canvas.selection_engine.active_rect = shape_path_global.boundingRect()
        canvas.selection_engine.is_transforming = True

        canvas.previous_tool_obj = self

        # Cambiar a la herramienta de mover píxeles (Mover píxeles de selección)
        if hasattr(canvas, 'main_window') and canvas.main_window and hasattr(canvas.main_window, 'tool_panel'):
            from tools.move_select_pixels import MoveSelectPixelsTool
            for btn in canvas.main_window.tool_panel.button_group.buttons():
                t = btn.property("tool_obj")
                if isinstance(t, MoveSelectPixelsTool):
                    btn.setChecked(True)
                    canvas.set_active_tool(t)
                    break

        canvas.push_document_state("Insertar Forma")
        canvas.update()
