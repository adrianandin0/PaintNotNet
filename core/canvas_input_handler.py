"""
core/canvas_input_handler.py — Manejador de eventos de entrada y despacho de herramientas del lienzo.
"""
import math
from PyQt6.QtCore import QObject, QPoint, QPointF, Qt, QEvent
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

    def handle_leave_event(self, event):
        self.canvas.cursor_pos = None
        self.canvas.widget_cursor_pos = None
        self.notify_cursor_position()
        self.canvas.update()

    def handle_mouse_press(self, event):
        self.canvas.setFocus()
        self.canvas.widget_cursor_pos = event.position()
        ev = self.map_canvas_event(event)
        self.canvas.cursor_pos = ev.position()
        self.notify_cursor_position()

        if hasattr(self.canvas.selection_engine, 'original_selection_region'):
            self.canvas.selection_engine.original_selection_region = None

        if ev.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.canvas.drawing = True
            color_activo = self.canvas.color_primario if ev.button() == Qt.MouseButton.LeftButton else self.canvas.color_secundario

            tool_name = self.canvas.active_tool_obj.__class__.__name__ if self.canvas.active_tool_obj else ""
            es_herramienta_lectura = tool_name in (
                'ZoomTool', 'EyedropperTool', 'SelectRectTool', 'SelectEllipseTool',
                'SelectFreeTool', 'MagicWandTool', 'MoveSelectOnlyTool'
            )

            if not es_herramienta_lectura and hasattr(self.canvas, 'layer_mgr') and hasattr(self.canvas.layer_mgr, 'preparar_para_modificacion'):
                self.canvas.layer_mgr.preparar_para_modificacion()

            tool = getattr(self.canvas, 'active_tool_obj', None)
            if tool and hasattr(tool, 'mouse_press'):
                try:
                    tool.mouse_press(self.canvas, ev, color_activo)
                except TypeError:
                    tool.mouse_press(self.canvas, ev)
            self.canvas.update()

    def handle_mouse_move(self, event):
        self.canvas.widget_cursor_pos = event.position()
        ev = self.map_canvas_event(event)
        self.canvas.cursor_pos = ev.position()
        self.notify_cursor_position()
        color_activo = self.canvas.color_primario if (ev.buttons() & Qt.MouseButton.LeftButton) else self.canvas.color_secundario

        tool = getattr(self.canvas, 'active_tool_obj', None)
        if tool and hasattr(tool, 'mouse_move'):
            try:
                tool.mouse_move(self.canvas, ev, color_activo)
            except TypeError:
                tool.mouse_move(self.canvas, ev)

        if self.canvas.drawing and self.canvas.callback_modificado:
            self.canvas.callback_modificado()

        tool_name = getattr(self.canvas.active_tool_obj, 'name', getattr(self.canvas.active_tool_obj, 'nombre', ''))
        es_herramienta_trazo = tool_name in ("Pincel", "Lápiz", "Goma de Borrar", "Spray", "Tampón de Clonado", "Acuarela")

        if self.canvas.drawing and es_herramienta_trazo and getattr(self.canvas, 'cursor_pos', None):
            grosor = max(30, int(getattr(self.canvas, 'grosor_pincel', 5) * 4))
            cx, cy = self.canvas.cursor_pos.x(), self.canvas.cursor_pos.y()
            sf = self.canvas.scale_factor
            off_x, off_y = self.canvas.obtener_offset_canvas()

            vx = int(off_x + (cx - grosor) * sf)
            vy = int(off_y + (cy - grosor) * sf)
            vw = int((grosor * 2) * sf)
            vh = int((grosor * 2) * sf)
            self.canvas.update(vx, vy, vw, vh)
        else:
            self.canvas.update()

    def handle_mouse_release(self, event):
        ev = self.map_canvas_event(event)
        self.notify_cursor_position()
        if self.canvas.drawing:
            color_activo = self.canvas.color_primario if ev.button() == Qt.MouseButton.LeftButton else self.canvas.color_secundario

            tool = getattr(self.canvas, 'active_tool_obj', None)
            if tool and hasattr(tool, 'mouse_release'):
                try:
                    tool.mouse_release(self.canvas, ev, color_activo)
                except TypeError:
                    tool.mouse_release(self.canvas, ev)

            self.canvas.drawing = False
            tool_name = self.canvas.active_tool_obj.__class__.__name__ if self.canvas.active_tool_obj else ""
            read_only_or_special = (
                'BucketTool', 'EyedropperTool', 'ZoomTool', 'TransformTool',
                'MoveSelectPixelsTool', 'MoveSelectOnlyTool', 'SelectRectTool',
                'SelectEllipseTool', 'SelectFreeTool', 'MagicWandTool', 'TextTool', 'GradientTool'
            )
            if tool_name not in read_only_or_special:
                self.canvas.push_document_state(getattr(self.canvas.active_tool_obj, 'name', "Trazo"))
        self.canvas.update()

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
