from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QTransform
from PyQt6.QtWidgets import QApplication
from tools.base_tool import BaseTool


class MoveSelectOnlyTool(BaseTool):
    def __init__(self):
        super().__init__("Mover Selección", "gui/iconos/move_select_only.png")

    def mouse_press(self, canvas, event, color_activo=None):
        from tools.move_select_pixels import MoveSelectPixelsTool
        if canvas.selection_engine.floating_image is not None:
            MoveSelectPixelsTool.commit_floating_image(canvas)

        engine = canvas.selection_engine
        if not engine.has_selection():
            return

        pos = event.position()
        hit = engine.hit_test(pos)
        if hit == engine.HANDLE_NONE:
            canvas.cancelar_o_deseleccionar()
            return

        engine.begin_transform(pos, event.button(), hit)

    def mouse_move(self, canvas, event, color_activo=None):
        engine = canvas.selection_engine
        if not engine.is_moving and not engine.is_rotating:
            return

        is_shift = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier)
        engine.update_transform(event.position(), is_shift=is_shift)
        canvas._ajustar_tamano_widget()

        canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        engine = canvas.selection_engine
        if engine.is_moving or engine.is_rotating:
            engine.end_transform()
            canvas.push_document_state("Mover Selección")
        else:
            engine.end_transform()
