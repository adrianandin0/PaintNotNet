"""
core/canvas_input_handler.py — Manejador de eventos de entrada y despacho de herramientas del lienzo.
"""
import math
from PyQt6.QtCore import QObject, QPoint, QPointF, Qt
from PyQt6.QtGui import QMouseEvent, QCursor, QPixmap, QPainter, QPen, QColor


class CanvasInputHandler(QObject):
    """Manejador especializado de eventos de entrada del usuario (ratón, cursor y navegación)."""

    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas

    def map_canvas_event(self, event) -> QMouseEvent:
        """Traduce las coordenadas físicas del widget a coordenadas lógicas del lienzo (tomando en cuenta offset y zoom)."""
        off_x, off_y = self.canvas.obtener_offset_canvas()
        raw = event.position() - QPointF(float(off_x), float(off_y))
        sf = self.canvas.scale_factor if self.canvas.scale_factor > 0 else 1.0
        pos_mapped = QPointF(raw.x() / sf, raw.y() / sf)
        return QMouseEvent(
            event.type(),
            pos_mapped,
            event.button(),
            event.buttons(),
            event.modifiers()
        )



    def notify_cursor_position(self):
        main_win = getattr(self.canvas, 'main_window', None)
        if main_win and hasattr(main_win, 'bottom_bar') and main_win.bottom_bar:
            pos = getattr(self.canvas, 'cursor_pos', None)
            if pos is not None and hasattr(self.canvas, 'layer_mgr') and self.canvas.layer_mgr:
                cx, cy = int(pos.x()), int(pos.y())
                if 0 <= cx <= self.canvas.layer_mgr.width and 0 <= cy <= self.canvas.layer_mgr.height:
                    main_win.bottom_bar.actualizar_posicion_cursor(cx, cy)
                    return
            main_win.bottom_bar.actualizar_posicion_cursor(None, None)
