import math
import random
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QImage
from tools.base_tool import BaseTool
from PyQt6.QtWidgets import QApplication


class SprayTool(BaseTool):
    """Herramienta Aerosol / Spray Paint con control de intensidad y chorreado continuo de gotas tras cobertura total."""
    def __init__(self):
        super().__init__("Aerosol", "gui/iconos/spray.png")
        self.is_drawing = False
        self.shift_anchor = None
        self._last_pos = None
        # Registro de gotas activas durante el trazo: (gx, gy) -> { 'start_x': float, 'start_y': float, 'length': float }
        self.active_drips = {}

    def draw_handles(self, painter, canvas):
        if canvas.cursor_pos is None:
            return
        pos = canvas.cursor_pos
        size = max(1, getattr(canvas, 'grosor_pincel', 15))
        r = size / 2.0
        suavizado = getattr(canvas, 'suavizado_pincel', True)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, suavizado)

        # Círculo guía exterior del área de aerosol
        pen_outer = QPen(QColor(0, 0, 0, 180), 1.0, Qt.PenStyle.DashLine)
        painter.setPen(pen_outer)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(pos, r, r)

        # Círculo guía interior
        col_pri = QColor(canvas.color_primario)
        col_rim = QColor(col_pri)
        col_rim.setAlpha(220)
        painter.setPen(QPen(col_rim, 0.8))
        painter.drawEllipse(pos, r - 0.5, r - 0.5)

        painter.restore()

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.is_drawing = True
            pos = event.position()
            self._last_pos = pos
            self.shift_anchor = None
            self.active_drips = {}
            color = color_activo if color_activo else (canvas.color_primario if event.button() == Qt.MouseButton.LeftButton else canvas.color_secundario)
            self._spray_at(canvas, pos, color)
            canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        if self.is_drawing:
            raw_pos = event.position()
            modifiers = QApplication.keyboardModifiers()
            is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

            if is_shift:
                if self.shift_anchor is None:
                    self.shift_anchor = QPointF(self._last_pos) if self._last_pos else raw_pos
                dx = raw_pos.x() - self.shift_anchor.x()
                dy = raw_pos.y() - self.shift_anchor.y()
                if abs(dx) >= abs(dy):
                    pos = QPointF(raw_pos.x(), self.shift_anchor.y())
                else:
                    pos = QPointF(self.shift_anchor.x(), raw_pos.y())
            else:
                self.shift_anchor = None
                pos = raw_pos

            self._last_pos = pos
            color = color_activo if color_activo else (canvas.color_primario if event.buttons() & Qt.MouseButton.LeftButton else canvas.color_secundario)
            self._spray_at(canvas, pos, color)
            canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        if self.is_drawing:
            self.is_drawing = False
            self.shift_anchor = None
            self._last_pos = None
            self.active_drips = {}
            if hasattr(canvas, 'push_document_state'):
                canvas.push_document_state(self.name)
            canvas.update()

    def _is_area_fully_covered(self, qimage: QImage, cx: float, cy: float, radius: float, target_color: QColor) -> bool:
        """
        Verifica si el área circular central bajo el aerosol está totalmente llena de pintura
        (sin huecos, píxeles transparentes o píxeles de otro color sin cubrir).
        """
        w, h = qimage.width(), qimage.height()
        icx, icy = int(cx), int(cy)
        if icx < 0 or icx >= w or icy < 0 or icy >= h:
            return False

        r_sample = max(3, int(radius * 0.35))
        total_pixels = 0
        covered_pixels = 0

        tr, tg, tb = target_color.red(), target_color.green(), target_color.blue()

        step = 1 if r_sample <= 6 else 2
        for dy in range(-r_sample, r_sample + 1, step):
            py = icy + dy
            if py < 0 or py >= h:
                continue
            for dx in range(-r_sample, r_sample + 1, step):
                px = icx + dx
                if px < 0 or px >= w:
                    continue
                if dx * dx + dy * dy <= r_sample * r_sample:
                    total_pixels += 1
                    col = qimage.pixelColor(px, py)
                    if col.alpha() < 120:
                        continue
                    
                    dr = abs(col.red() - tr)
                    dg = abs(col.green() - tg)
                    db = abs(col.blue() - tb)
                    if (dr + dg + db) < 140:
                        covered_pixels += 1

        if total_pixels == 0:
            return False

        return (covered_pixels / total_pixels) >= 0.85

    def _spray_at(self, canvas, point: QPointF, color: QColor):
        active_layer = canvas.layer_mgr.get_active_layer()
        if not active_layer or not active_layer.visible or active_layer.locked:
            return

        grosor = max(2, getattr(canvas, 'grosor_pincel', 15))
        radius = grosor / 2.0
        suavizado = getattr(canvas, 'suavizado_pincel', True)

        # Intensidad del aerosol (1 a 100%, 50% por defecto)
        intensidad = getattr(canvas, 'spray_intensidad', 50)
        intensidad_factor = max(0.1, intensidad / 50.0)

        # Número de partículas proporcional al radio y a la intensidad configurada
        density = max(5, int(radius * 3.5 * intensidad_factor))

        painter = QPainter(active_layer.image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, suavizado)

        base_color = QColor(color)
        pen_dot = QPen(base_color, 1.2)
        painter.setPen(pen_dot)

        # 1. Pulverizar partículas de aerosol sobre la capa
        for _ in range(density):
            r_ratio = math.sqrt(random.random()) * radius
            angle = random.uniform(0, 2 * math.pi)
            px = point.x() + r_ratio * math.cos(angle)
            py = point.y() + r_ratio * math.sin(angle)

            if suavizado:
                falloff = 1.0 - (r_ratio / radius) * 0.5
                c = QColor(base_color)
                c.setAlpha(max(1, int(c.alpha() * falloff)))
                painter.setPen(QPen(c, 1.2))

            painter.drawPoint(QPointF(px, py))

        # 2. Verificar si el goteo está habilitado y la zona está 100% llena (cobertura total sin huecos)
        goteo_enabled = getattr(canvas, 'spray_goteo', True)
        if goteo_enabled and self._is_area_fully_covered(active_layer.image, point.x(), point.y(), radius, base_color):
            grid_size = 14.0
            gx = int(point.x() // grid_size)
            gy = int(point.y() // grid_size)
            cell_key = (gx, gy)

            if cell_key not in self.active_drips:
                self.active_drips[cell_key] = {
                    'start_x': point.x() + random.uniform(-1.0, 1.0),
                    'start_y': point.y() + radius * 0.6,
                    'length': 0.0
                }

            drip_info = self.active_drips[cell_key]
            drip_info['length'] += 0.75 * intensidad_factor

            # Dibujar línea continua sólida y limpia desde la base de la mancha hasta la punta inferior
            drip_x = drip_info['start_x']
            drip_top = drip_info['start_y']
            drip_bottom = drip_top + drip_info['length']

            # Trazado continuo sin interrupciones
            line_pen = QPen(base_color, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(line_pen)
            painter.setBrush(QBrush(base_color))

            # Dibujar el tallo sólido continuo de la gota
            painter.drawLine(QPointF(drip_x, drip_top), QPointF(drip_x, drip_bottom))

            # Dibujar la gota/bulbo redondeado en la punta inferior
            bulb_r = min(3.0, 1.2 + (drip_info['length'] * 0.03))
            painter.drawEllipse(QPointF(drip_x, drip_bottom), bulb_r, bulb_r)

        painter.end()
