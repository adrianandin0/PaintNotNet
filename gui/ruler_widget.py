import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPoint, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
from core.theme import ThemeManager


class RulerCornerWidget(QWidget):
    """Esquina superior izquierda (22x22 px) donde se cruzan las reglas."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(22, 22)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        tm = ThemeManager()
        res_nombre = tm.resolver_nombre_tema(tm.current_theme)
        is_dark = (res_nombre == "Oscuro")

        bg_col = QColor("#2B2B2B" if is_dark else "#F0F0F0")
        line_col = QColor("#555555" if is_dark else "#B0B0B0")
        text_col = QColor("#A0A0A0" if is_dark else "#555555")

        painter.fillRect(self.rect(), bg_col)

        # Bordes derecho e inferior
        pen_border = QPen(line_col, 1.0)
        painter.setPen(pen_border)
        painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height() - 1)
        painter.drawLine(0, self.height() - 1, self.width() - 1, self.height() - 1)

        # Texto "cm"
        font = QFont("sans-serif", 7)
        painter.setFont(font)
        painter.setPen(text_col)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "cm")
        painter.end()


class RulerWidget(QWidget):
    """Regla graduada en centímetros (Horizontal o Vertical) adaptada al tema activo."""
    def __init__(self, orientation=Qt.Orientation.Horizontal, canvas=None, scroll_area=None, parent=None):
        super().__init__(parent)
        self.orientation = orientation
        self.canvas = canvas
        self.scroll_area = scroll_area

        if self.orientation == Qt.Orientation.Horizontal:
            self.setFixedHeight(22)
        else:
            self.setFixedWidth(22)

        # Conectar señales de desplazamiento si el scroll area está presente
        if self.scroll_area:
            hbar = self.scroll_area.horizontalScrollBar()
            vbar = self.scroll_area.verticalScrollBar()
            if hbar:
                hbar.valueChanged.connect(self.update)
            if vbar:
                vbar.valueChanged.connect(self.update)

    def set_canvas(self, canvas, scroll_area=None):
        self.canvas = canvas
        if scroll_area:
            self.scroll_area = scroll_area
            hbar = self.scroll_area.horizontalScrollBar()
            vbar = self.scroll_area.verticalScrollBar()
            if hbar:
                hbar.valueChanged.connect(self.update)
            if vbar:
                vbar.valueChanged.connect(self.update)
        self.update()

    def paintEvent(self, event):
        if not self.canvas or not self.scroll_area:
            return

        viewport = self.scroll_area.viewport()
        if not viewport:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # Determinar colores según el tema (Tema Oscuro: gris oscuro / líneas blancas; Tema Claro: claro / líneas negras)
        tm = ThemeManager()
        res_nombre = tm.resolver_nombre_tema(tm.current_theme)
        is_dark = (res_nombre == "Oscuro")

        bg_col = QColor("#2B2B2B" if is_dark else "#F0F0F0")
        line_col = QColor("#E0E0E0" if is_dark else "#111111")
        subline_col = QColor("#888888" if is_dark else "#777777")
        border_col = QColor("#555555" if is_dark else "#B0B0B0")
        text_col = QColor("#FFFFFF" if is_dark else "#000000")

        painter.fillRect(self.rect(), bg_col)

        # Dibujar línea divisoria de la regla con el lienzo
        pen_border = QPen(border_col, 1.0)
        painter.setPen(pen_border)
        if self.orientation == Qt.Orientation.Horizontal:
            painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        else:
            painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())

        # Calcular origen de coordenadas (0,0) del lienzo mapeado a la regla
        parent_container = self.parentWidget()
        if parent_container:
            pt_canvas_in_parent = self.canvas.mapTo(parent_container, QPoint(0, 0))
            pt_ruler_in_parent = self.mapTo(parent_container, QPoint(0, 0))
            origin_x = pt_canvas_in_parent.x() - pt_ruler_in_parent.x()
            origin_y = pt_canvas_in_parent.y() - pt_ruler_in_parent.y()
        else:
            origin_x = 0
            origin_y = 0

        dpi = float(getattr(self.canvas, 'dpi', 96))
        zoom = float(getattr(self.canvas, 'scale_factor', getattr(self.canvas, 'zoom_factor', 1.0)))
        px_per_cm = (dpi / 2.54) * zoom

        if px_per_cm <= 0:
            painter.end()
            return

        # Seleccionar intervalos según el zoom (en centímetros)
        if px_per_cm >= 100:
            major_step_cm = 1.0
            sub_step_cm = 0.1  # mm
        elif px_per_cm >= 40:
            major_step_cm = 1.0
            sub_step_cm = 0.5
        elif px_per_cm >= 18:
            major_step_cm = 2.0
            sub_step_cm = 1.0
        elif px_per_cm >= 8:
            major_step_cm = 5.0
            sub_step_cm = 1.0
        else:
            major_step_cm = 10.0
            sub_step_cm = 5.0

        font = QFont("sans-serif", 7)
        painter.setFont(font)

        if self.orientation == Qt.Orientation.Horizontal:
            ruler_len = self.width()
            start_cm = math.floor((0 - origin_x) / px_per_cm) - 1
            end_cm = math.ceil((ruler_len - origin_x) / px_per_cm) + 1

            # Dibujar sub-ticks primero
            pen_sub = QPen(subline_col, 1.0)
            painter.setPen(pen_sub)

            curr_cm = start_cm
            while curr_cm <= end_cm:
                rx = origin_x + curr_cm * px_per_cm
                if 0 <= rx <= ruler_len:
                    # Verificar si es tick mayor o sub-tick
                    is_major = (abs(round(curr_cm / major_step_cm) * major_step_cm - curr_cm) < 1e-4)
                    is_half = (abs(round(curr_cm / (major_step_cm / 2.0)) * (major_step_cm / 2.0) - curr_cm) < 1e-4)

                    if not is_major:
                        h_tick = 7 if is_half else 4
                        y_start = self.height() - 1 - h_tick
                        painter.drawLine(int(round(rx)), y_start, int(round(rx)), self.height() - 1)
                curr_cm += sub_step_cm

            # Dibujar ticks mayores y etiquetas
            pen_major = QPen(line_col, 1.0)
            curr_cm = math.floor(start_cm / major_step_cm) * major_step_cm
            while curr_cm <= end_cm:
                rx = origin_x + curr_cm * px_per_cm
                if 0 <= rx <= ruler_len:
                    painter.setPen(pen_major)
                    painter.drawLine(int(round(rx)), self.height() - 11, int(round(rx)), self.height() - 1)

                    val_str = f"{int(round(curr_cm))}"
                    painter.setPen(text_col)
                    txt_rect = QRectF(rx + 2, 1, 35, 12)
                    painter.drawText(txt_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, val_str)
                curr_cm += major_step_cm

        else:
            # Orientación Vertical
            ruler_len = self.height()
            start_cm = math.floor((0 - origin_y) / px_per_cm) - 1
            end_cm = math.ceil((ruler_len - origin_y) / px_per_cm) + 1

            # Dibujar sub-ticks primero
            pen_sub = QPen(subline_col, 1.0)
            painter.setPen(pen_sub)

            curr_cm = start_cm
            while curr_cm <= end_cm:
                ry = origin_y + curr_cm * px_per_cm
                if 0 <= ry <= ruler_len:
                    is_major = (abs(round(curr_cm / major_step_cm) * major_step_cm - curr_cm) < 1e-4)
                    is_half = (abs(round(curr_cm / (major_step_cm / 2.0)) * (major_step_cm / 2.0) - curr_cm) < 1e-4)

                    if not is_major:
                        w_tick = 7 if is_half else 4
                        x_start = self.width() - 1 - w_tick
                        painter.drawLine(x_start, int(round(ry)), self.width() - 1, int(round(ry)))
                curr_cm += sub_step_cm

            # Dibujar ticks mayores y etiquetas (texto rotado -90 grados)
            pen_major = QPen(line_col, 1.0)
            curr_cm = math.floor(start_cm / major_step_cm) * major_step_cm
            while curr_cm <= end_cm:
                ry = origin_y + curr_cm * px_per_cm
                if 0 <= ry <= ruler_len:
                    painter.setPen(pen_major)
                    painter.drawLine(self.width() - 11, int(round(ry)), self.width() - 1, int(round(ry)))

                    val_str = f"{int(round(curr_cm))}"
                    painter.setPen(text_col)

                    painter.save()
                    painter.translate(self.width() - 13, ry + 2)
                    painter.rotate(-90)
                    painter.drawText(QRectF(0, -10, 35, 12), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, val_str)
                    painter.restore()

                curr_cm += major_step_cm

        painter.end()
