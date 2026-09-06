import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPoint, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QCursor
from core.theme import ThemeManager

# Ciclo de unidades: cm → pulgadas → px → cm ...
UNITS = ["cm", "in", "px"]
UNIT_LABELS = {"cm": "cm", "in": "in", "px": "px"}


class RulerCornerWidget(QWidget):
    """Esquina superior izquierda (22x22 px) donde se cruzan las reglas.
    Clic izquierdo: avanza unidad (cm → in → px → cm).
    Clic derecho: retrocede unidad.
    """
    unit_changed = pyqtSignal(str)   # emite la nueva unidad

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(22, 22)
        from PyQt6.QtCore import QSettings
        settings = QSettings("PaintNotNet", "PaintNotNet")
        saved_unit = str(settings.value("ruler_unit", "cm"))
        self._unit_index = UNITS.index(saved_unit) if saved_unit in UNITS else 0
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.retraducir()

    def set_unit(self, unit: str):
        if unit in UNITS:
            idx = UNITS.index(unit)
            if self._unit_index != idx:
                self._unit_index = idx
                self.update()

    def retraducir(self):
        from core.i18n import t
        self.setToolTip(t("Clic izq: siguiente unidad | Clic der: unidad anterior"))

    @property
    def unit(self) -> str:
        return UNITS[self._unit_index]

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._unit_index = (self._unit_index + 1) % len(UNITS)
        elif event.button() == Qt.MouseButton.RightButton:
            self._unit_index = (self._unit_index - 1) % len(UNITS)
        else:
            return
        self.update()
        from PyQt6.QtCore import QSettings
        QSettings("PaintNotNet", "PaintNotNet").setValue("ruler_unit", self.unit)
        self.unit_changed.emit(self.unit)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        tm = ThemeManager()
        res_nombre = tm.resolver_nombre_tema(tm.current_theme)
        is_dark = (res_nombre == "Oscuro")

        bg_col   = QColor("#2B2B2B" if is_dark else "#F0F0F0")
        line_col = QColor("#555555" if is_dark else "#B0B0B0")
        text_col = QColor("#A0A0A0" if is_dark else "#555555")

        painter.fillRect(self.rect(), bg_col)

        # Bordes derecho e inferior
        pen_border = QPen(line_col, 1.0)
        painter.setPen(pen_border)
        painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height() - 1)
        painter.drawLine(0, self.height() - 1, self.width() - 1, self.height() - 1)

        # Texto con la unidad actual
        font = QFont("sans-serif", 7)
        painter.setFont(font)
        painter.setPen(text_col)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, UNIT_LABELS[self.unit])
        painter.end()


class RulerWidget(QWidget):
    """Regla graduada adaptada al tema activo.
    Soporta unidades: 'cm', 'in', 'px'.
    """
    def __init__(self, orientation=Qt.Orientation.Horizontal, canvas=None, scroll_area=None, parent=None):
        super().__init__(parent)
        self.orientation = orientation
        self.canvas = canvas
        self.scroll_area = scroll_area
        self._unit = "cm"   # unidad activa por defecto

        if self.orientation == Qt.Orientation.Horizontal:
            self.setFixedHeight(22)
        else:
            self.setFixedWidth(22)

        if self.scroll_area:
            hbar = self.scroll_area.horizontalScrollBar()
            vbar = self.scroll_area.verticalScrollBar()
            if hbar:
                hbar.valueChanged.connect(self.update)
            if vbar:
                vbar.valueChanged.connect(self.update)

    def set_unit(self, unit: str):
        """Cambia la unidad activa y repinta."""
        if unit in UNITS:
            self._unit = unit
            self.update()

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

    # ------------------------------------------------------------------
    # Helpers: convertir píxeles de pantalla a la unidad activa
    # ------------------------------------------------------------------
    def _px_per_unit(self, dpi: float, zoom: float) -> float:
        """Devuelve cuántos píxeles de pantalla equivalen a 1 unidad."""
        if self._unit == "cm":
            return (dpi / 2.54) * zoom
        elif self._unit == "in":
            return dpi * zoom
        else:  # px
            return zoom  # 1 px de documento = zoom px de pantalla

    def _nice_steps(self, px_per_unit: float):
        """Elige major_step y sub_step en la unidad activa según el zoom."""
        if self._unit == "px":
            # Para píxeles usamos potencias de 10 y mitades
            if px_per_unit >= 40:
                return 10.0, 1.0
            elif px_per_unit >= 8:
                return 50.0, 10.0
            elif px_per_unit >= 2:
                return 100.0, 50.0
            else:
                return 500.0, 100.0
        elif self._unit == "in":
            if px_per_unit >= 200:
                return 1.0, 0.125
            elif px_per_unit >= 80:
                return 1.0, 0.25
            elif px_per_unit >= 30:
                return 2.0, 0.5
            elif px_per_unit >= 12:
                return 5.0, 1.0
            else:
                return 10.0, 5.0
        else:  # cm
            if px_per_unit >= 100:
                return 1.0, 0.1
            elif px_per_unit >= 40:
                return 1.0, 0.5
            elif px_per_unit >= 18:
                return 2.0, 1.0
            elif px_per_unit >= 8:
                return 5.0, 1.0
            else:
                return 10.0, 5.0

    def _format_label(self, val: float) -> str:
        if self._unit == "px":
            # Píxeles son 1-indexados: el borde izquierdo del lienzo = px 1
            return f"{int(round(val)) + 1}"
        elif self._unit == "in":
            if abs(val - round(val)) < 1e-4:
                return f"{int(round(val))}"
            return f"{val:.1f}"
        else:
            return f"{int(round(val))}"

    # ------------------------------------------------------------------
    def paintEvent(self, event):
        if not self.canvas or not self.scroll_area:
            return

        viewport = self.scroll_area.viewport()
        if not viewport:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        tm = ThemeManager()
        res_nombre = tm.resolver_nombre_tema(tm.current_theme)
        is_dark = (res_nombre == "Oscuro")

        bg_col      = QColor("#2B2B2B" if is_dark else "#F0F0F0")
        line_col    = QColor("#E0E0E0" if is_dark else "#111111")
        subline_col = QColor("#888888" if is_dark else "#777777")
        border_col  = QColor("#555555" if is_dark else "#B0B0B0")
        text_col    = QColor("#FFFFFF" if is_dark else "#000000")

        painter.fillRect(self.rect(), bg_col)

        pen_border = QPen(border_col, 1.0)
        painter.setPen(pen_border)
        if self.orientation == Qt.Orientation.Horizontal:
            painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        else:
            painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())

        # Calcular origen del lienzo mapeado a la regla
        parent_container = self.parentWidget()
        if parent_container:
            pt_canvas_in_parent = self.canvas.mapTo(parent_container, QPoint(0, 0))
            pt_ruler_in_parent  = self.mapTo(parent_container, QPoint(0, 0))
            # El lienzo puede tener un offset interno de centrado dentro del widget
            doc_off_x, doc_off_y = (self.canvas.obtener_offset_canvas()
                                    if hasattr(self.canvas, 'obtener_offset_canvas') else (0, 0))
            origin_x = pt_canvas_in_parent.x() - pt_ruler_in_parent.x() + doc_off_x
            origin_y = pt_canvas_in_parent.y() - pt_ruler_in_parent.y() + doc_off_y
        else:
            origin_x = origin_y = 0

        dpi  = float(getattr(self.canvas, 'dpi', 96))
        zoom = float(getattr(self.canvas, 'scale_factor', getattr(self.canvas, 'zoom_factor', 1.0)))

        px_per_unit = self._px_per_unit(dpi, zoom)
        if px_per_unit <= 0:
            painter.end()
            return

        major_step, sub_step = self._nice_steps(px_per_unit)

        font = QFont("sans-serif", 7)
        painter.setFont(font)

        if self.orientation == Qt.Orientation.Horizontal:
            ruler_len = self.width()
            start_u = math.floor((0 - origin_x) / px_per_unit) - 1
            end_u   = math.ceil((ruler_len - origin_x) / px_per_unit) + 1

            # Sub-ticks
            pen_sub = QPen(subline_col, 1.0)
            painter.setPen(pen_sub)
            curr = start_u
            while curr <= end_u:
                rx = origin_x + curr * px_per_unit
                if 0 <= rx <= ruler_len:
                    is_major = (abs(round(curr / major_step) * major_step - curr) < 1e-4)
                    is_half  = (abs(round(curr / (major_step / 2.0)) * (major_step / 2.0) - curr) < 1e-4)
                    if not is_major:
                        h_tick  = 7 if is_half else 4
                        y_start = self.height() - 1 - h_tick
                        painter.drawLine(int(round(rx)), y_start, int(round(rx)), self.height() - 1)
                curr += sub_step

            # Major ticks + etiquetas
            pen_major = QPen(line_col, 1.0)
            curr = math.floor(start_u / major_step) * major_step
            while curr <= end_u:
                rx = origin_x + curr * px_per_unit
                if 0 <= rx <= ruler_len:
                    painter.setPen(pen_major)
                    painter.drawLine(int(round(rx)), self.height() - 11, int(round(rx)), self.height() - 1)
                    painter.setPen(text_col)
                    painter.drawText(QRectF(rx + 2, 1, 35, 12),
                                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                                     self._format_label(curr))
                curr += major_step

        else:
            ruler_len = self.height()
            start_u = math.floor((0 - origin_y) / px_per_unit) - 1
            end_u   = math.ceil((ruler_len - origin_y) / px_per_unit) + 1

            # Sub-ticks
            pen_sub = QPen(subline_col, 1.0)
            painter.setPen(pen_sub)
            curr = start_u
            while curr <= end_u:
                ry = origin_y + curr * px_per_unit
                if 0 <= ry <= ruler_len:
                    is_major = (abs(round(curr / major_step) * major_step - curr) < 1e-4)
                    is_half  = (abs(round(curr / (major_step / 2.0)) * (major_step / 2.0) - curr) < 1e-4)
                    if not is_major:
                        w_tick  = 7 if is_half else 4
                        x_start = self.width() - 1 - w_tick
                        painter.drawLine(x_start, int(round(ry)), self.width() - 1, int(round(ry)))
                curr += sub_step

            # Major ticks + etiquetas rotadas
            pen_major = QPen(line_col, 1.0)
            curr = math.floor(start_u / major_step) * major_step
            while curr <= end_u:
                ry = origin_y + curr * px_per_unit
                if 0 <= ry <= ruler_len:
                    painter.setPen(pen_major)
                    painter.drawLine(self.width() - 11, int(round(ry)), self.width() - 1, int(round(ry)))
                    painter.setPen(text_col)
                    painter.save()
                    painter.translate(self.width() - 13, ry + 2)
                    painter.rotate(-90)
                    painter.drawText(QRectF(0, -10, 35, 12),
                                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                                     self._format_label(curr))
                    painter.restore()
                curr += major_step

        painter.end()
