from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QPen, QColor
from PyQt6.QtWidgets import QApplication
from tools.base_tool import BaseTool


class SelectEllipseTool(BaseTool):
    def __init__(self):
        super().__init__("Selección Elíptica", "gui/iconos/select_ellipse.png")
        self.start_point = QPoint()
        self.current_point = QPoint()
        self.is_selecting = False

    def mouse_press(self, canvas, event, color_activo=None):
        pos = event.position().toPoint()
        engine = canvas.selection_engine
        hit = engine.hit_test(event.position()) if engine.has_selection() else engine.HANDLE_NONE

        if hit != engine.HANDLE_NONE:
            engine.begin_transform(event.position(), event.button(), hit)
        else:
            self.start_point = pos
            self.current_point = pos
            self.is_selecting = True

    def mouse_move(self, canvas, event, color_activo=None):
        engine = canvas.selection_engine
        if engine.is_moving or engine.is_rotating:
            is_shift = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier)
            engine.update_transform(event.position(), is_shift=is_shift)
            canvas.update()
        elif self.is_selecting:
            self.current_point = event.position().toPoint()
            canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        engine = canvas.selection_engine
        if engine.is_moving or engine.is_rotating:
            engine.end_transform()
        elif self.is_selecting:
            rect = self._get_rect(event.modifiers())
            if rect.width() > 2 and rect.height() > 2:
                canvas.selection_engine.set_ellipse(rect)
                if hasattr(canvas, 'main_window') and canvas.main_window:
                    canvas.main_window.activar_herramienta_mover()
            else:
                canvas.selection_engine.clear_selection()
            self.is_selecting = False
            canvas.update()

    def _get_rect(self, modifiers=None):
        if modifiers is None:
            modifiers = QApplication.keyboardModifiers()

        dx = self.current_point.x() - self.start_point.x()
        dy = self.current_point.y() - self.start_point.y()

        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            side = max(abs(dx), abs(dy))
            dx = side if dx >= 0 else -side
            dy = side if dy >= 0 else -side

        return QRect(self.start_point.x(), self.start_point.y(), dx, dy).normalized()

    def draw_preview(self, painter, canvas):
        if self.is_selecting:
            rect = self._get_rect()
            pen = QPen(QColor(0, 120, 215), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(rect)
