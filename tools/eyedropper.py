from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF
from PyQt6.QtGui import QPen, QColor, QBrush, QTransform, QPainter
from tools.base_tool import BaseTool


class EyedropperTool(BaseTool):
    def __init__(self):
        super().__init__("Cuentagotas", "gui/iconos/eyedropper.png")
        self.is_picking = False
        self.current_pos = QPoint()
        self.current_color = None
        self.button_pressed = Qt.MouseButton.LeftButton

    def mouse_press(self, canvas, event, color_activo=None):
        pos = event.position().toPoint()
        self.is_picking = True
        self.button_pressed = event.button()
        self.current_pos = pos
        self.update_color(canvas, pos)
        canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        pos = event.position().toPoint()
        self.current_pos = pos
        self.update_color(canvas, pos)
        canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        if self.is_picking:
            pos = event.position().toPoint()
            self.update_color(canvas, pos)
            self.is_picking = False
            canvas.update()

    def update_color(self, canvas, pos):
        x, y = pos.x(), pos.y()
        if hasattr(canvas, 'layer_mgr') and canvas.layer_mgr:
            qimg = canvas.layer_mgr.get_qimage()
            if 0 <= x < qimg.width() and 0 <= y < qimg.height():
                pixel_color = qimg.pixelColor(x, y)
                self.current_color = pixel_color

                main_win = getattr(canvas, 'main_window', None)
                if not main_win and hasattr(canvas, 'parent'):
                    p = canvas.parent()
                    while p:
                        if hasattr(p, 'color_panel'):
                            main_win = p
                            break
                        p = p.parent() if hasattr(p, 'parent') else None

                if self.is_picking:
                    if self.button_pressed == Qt.MouseButton.LeftButton:
                        canvas.color_primario = pixel_color
                        if main_win and hasattr(main_win, 'color_panel'):
                            main_win.color_panel.modo_color = "primario"
                            main_win.color_panel.set_color_activo(pixel_color)
                    elif self.button_pressed == Qt.MouseButton.RightButton:
                        canvas.color_secundario = pixel_color
                        if main_win and hasattr(main_win, 'color_panel'):
                            main_win.color_panel.modo_color = "secundario"
                            main_win.color_panel.set_color_activo(pixel_color)

    def draw_handles(self, painter, canvas):
        if self.current_color and self.current_color.isValid():
            painter.save()
            # Resetear la transformación para dibujar en coordenadas fijas de pantalla (widget)
            painter.setWorldTransform(QTransform())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

            off_x, off_y = canvas.obtener_offset_canvas()
            sf = canvas.scale_factor
            # Centro exacto en coordenadas del widget
            cx = float(off_x) + (float(self.current_pos.x()) + 0.5) * float(sf)
            cy = float(off_y) + (float(self.current_pos.y()) + 0.5) * float(sf)

            # Círculo de 25px de diámetro exacto (radio = 12.5px)
            radius = 12.5
            circle_rect = QRectF(cx - radius, cy - radius, 25.0, 25.0)

            # Si el color es semitransparente, dibujar fondo de damero
            if self.current_color.alpha() < 255:
                painter.setBrush(QBrush(QColor(200, 200, 200)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(circle_rect)

            # 1. Relleno del color que se está seleccionando
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(self.current_color))
            painter.drawEllipse(circle_rect)

            # 2. Anillo de contorno de alto contraste (negro exterior de 2px, blanco interior de 1px)
            pen_outer = QPen(QColor(0, 0, 0, 220), 2.0)
            painter.setPen(pen_outer)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(circle_rect)

            pen_inner = QPen(QColor(255, 255, 255, 220), 1.0)
            painter.setPen(pen_inner)
            painter.drawEllipse(QRectF(cx - 11.5, cy - 11.5, 23.0, 23.0))

            # 3. Retícula / punto central para indicar el píxel exacto muestreado
            pen_dot_dark = QPen(QColor(0, 0, 0, 255), 2.0)
            painter.setPen(pen_dot_dark)
            painter.drawPoint(QPointF(cx, cy))

            pen_dot_light = QPen(QColor(255, 255, 255, 255), 1.0)
            painter.setPen(pen_dot_light)
            painter.drawPoint(QPointF(cx, cy))

            painter.restore()

