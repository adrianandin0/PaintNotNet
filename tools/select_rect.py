from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QPen, QColor
from tools.base_tool import BaseTool

class SelectRectTool(BaseTool):
    def __init__(self):
        super().__init__("Selección Rectangular", "gui/iconos/select_rect.png")
        self.start_point = QPoint()
        self.current_point = QPoint()
        self.is_selecting = False

    def mouse_press(self, canvas, event, color_activo):
        self.start_point = event.position().toPoint()
        self.current_point = self.start_point
        self.is_selecting = True

    def mouse_move(self, canvas, event, color_activo):
        if self.is_selecting:
            self.current_point = event.position().toPoint()
            canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        if self.is_selecting:
            rect = self._get_rect(event.modifiers())
            if rect.width() > 2 and rect.height() > 2:
                canvas.selection_engine.set_rectangle(rect)
            else:
                canvas.selection_engine.clear_selection()
            self.is_selecting = False
            canvas.update()

    def _get_rect(self, modifiers):
        rect = QRect(self.start_point, self.current_point).normalized()
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            side = max(rect.width(), rect.height())
            x = self.start_point.x() if self.current_point.x() >= self.start_point.x() else self.start_point.x() - side
            y = self.start_point.y() if self.current_point.y() >= self.start_point.y() else self.start_point.y() - side
            rect = QRect(x, y, side, side)
        return rect

    def draw_preview(self, painter, canvas):
        if self.is_selecting:
            mods = canvas.keyboardModifiers() if hasattr(canvas, 'keyboardModifiers') else None
            if mods is None:
                mods = Qt.KeyboardModifier.NoModifier

            rect = self._get_rect(mods)
            pen = QPen(QColor(0, 120, 215), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect)
