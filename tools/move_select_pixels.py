from PyQt6.QtCore import Qt, QPointF, QRectF, QRect
from PyQt6.QtGui import QImage, QPainter, QTransform, QColor, QPainterPath
from PyQt6.QtWidgets import QApplication
from tools.base_tool import BaseTool


class MoveSelectPixelsTool(BaseTool):
    def __init__(self):
        super().__init__("Mover Contenido", "gui/iconos/move_select_pixels.png")

    def mouse_press(self, canvas, event, color_activo=None):
        engine = canvas.selection_engine
        if not engine.has_selection():
            return

        pos = event.position()
        hit = engine.hit_test(pos)
        if hit == engine.HANDLE_NONE:
            return

        if engine.floating_image is None:
            rect = engine.active_rect.toRect().intersected(QRect(0, 0, canvas.layer_mgr.width, canvas.layer_mgr.height))
            if rect.width() > 0 and rect.height() > 0:
                buffer = canvas.layer_mgr.buffer

                canvas.floating_initial_canvas = buffer.copy()

                engine.floating_image = buffer.copy(rect)

                if not engine.active_path.isEmpty():
                    masked = QImage(rect.size(), QImage.Format.Format_ARGB32_Premultiplied)
                    masked.fill(Qt.GlobalColor.transparent)
                    mpainter = QPainter(masked)
                    local_path = QPainterPath(engine.active_path)
                    local_path.translate(-QPointF(rect.topLeft()))
                    mpainter.setClipPath(local_path)
                    mpainter.drawImage(0, 0, engine.floating_image)
                    mpainter.end()
                    engine.floating_image = masked

                engine.unscaled_floating_image = engine.floating_image.copy()
                engine.init_raw_image(engine.floating_image)
                engine.original_image_pos = QPointF(rect.topLeft())
                engine.is_new_content = False
                canvas.floating_history = [engine.floating_image.copy()]

                painter = QPainter(buffer)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                if not engine.active_path.isEmpty():
                    painter.setClipPath(engine.active_path)
                painter.fillRect(rect, Qt.GlobalColor.transparent)
                painter.end()

        engine.begin_transform(pos, event.button(), hit)

    def mouse_move(self, canvas, event, color_activo=None):
        engine = canvas.selection_engine
        if not engine.is_moving and not engine.is_rotating:
            return

        is_shift = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier)
        engine.update_transform(event.position(), is_shift=is_shift)
        canvas._ajustar_tamano_widget()

        if canvas.callback_modificado:
            canvas.callback_modificado()
        canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        engine = canvas.selection_engine
        if engine.is_moving or engine.is_rotating:
            engine.end_transform()
            canvas.push_document_state("Mover Contenido")

    @staticmethod
    def commit_floating_image(canvas):
        engine = canvas.selection_engine
        if engine.floating_image and not engine.floating_image.isNull():
            buffer = canvas.layer_mgr.buffer
            painter = QPainter(buffer)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.drawImage(engine.original_image_pos, engine.floating_image)
            painter.end()
            engine.floating_image = None
            engine.unscaled_floating_image = None
            engine.is_new_content = False
            if hasattr(engine, 'original_selection_region'):
                engine.original_selection_region = None
            canvas.update()
