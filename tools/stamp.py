import math
from PyQt6.QtCore import Qt, QPointF, QRectF, QRect, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QImage, QBrush, QBitmap, QPainterPath
from tools.base_tool import BaseTool
from core.i18n import t


class StampTool(BaseTool):
    """Herramienta Estampa (Stamp / Texture Rubber Tool)."""
    def __init__(self):
        super().__init__("Estampa", "gui/iconos/stamp.png")
        self.captured_texture: QImage | None = None

    def draw_handles(self, painter, canvas):
        if canvas.cursor_pos is None:
            return
        pos = canvas.cursor_pos
        size = max(1, getattr(canvas, 'grosor_pincel', 30))
        r = size / 2.0
        suavizado = getattr(canvas, 'suavizado_pincel', True)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, suavizado)

        # Vista previa semi-transparente de la estampa capturada
        if self.captured_texture and not self.captured_texture.isNull():
            scaled_img = self.captured_texture.scaled(
                int(size), int(size),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            preview_rect = QRectF(pos.x() - r, pos.y() - r, size, size)
            painter.setOpacity(0.55)
            
            path = QPainterPath()
            path.addEllipse(preview_rect)
            painter.setClipPath(path)
            painter.drawImage(preview_rect, scaled_img)
            painter.setClipping(False)
            painter.setOpacity(1.0)

        # Borde exterior del cursor
        pen_outer = QPen(QColor(0, 0, 0, 180), 1.5)
        painter.setPen(pen_outer)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(pos, r, r)

        painter.setPen(QPen(QColor(0, 120, 215, 220), 1.0, Qt.PenStyle.DashLine))
        painter.drawEllipse(pos, r - 0.5, r - 0.5)

        painter.restore()

    def mouse_press(self, canvas, event, color_activo=None):
        pos = event.position()
        active_layer = canvas.layer_mgr.get_active_layer()
        if not active_layer or not active_layer.visible or active_layer.locked:
            return

        grosor = max(2, getattr(canvas, 'grosor_pincel', 30))
        radius = int(grosor / 2.0)

        if event.button() == Qt.MouseButton.RightButton:
            # --- CLIC DERECHO: Copiar estampa/textura debajo del cursor ---
            self._capture_stamp(canvas, active_layer, pos, radius)
        elif event.button() == Qt.MouseButton.LeftButton:
            # --- CLIC IZQUIERDO: Aplicar sello/estampa ---
            if self.captured_texture is None or self.captured_texture.isNull():
                if hasattr(canvas, 'main_window') and hasattr(canvas.main_window, 'bottom_bar'):
                    canvas.main_window.bottom_bar.mostrar_mensaje(t("Haz clic derecho para copiar una estampa primero"), 2500)
                return

            self._apply_stamp(canvas, active_layer, pos, radius)
            if hasattr(canvas, 'push_document_state'):
                canvas.push_document_state(self.name)
            canvas.update()

    def _capture_stamp(self, canvas, active_layer, pos: QPointF, radius: int):
        img = active_layer.image
        w, h = img.width(), img.height()
        cx, cy = int(pos.x()), int(pos.y())
        diameter = radius * 2

        stamp_img = QImage(diameter, diameter, QImage.Format.Format_ARGB32_Premultiplied)
        stamp_img.fill(Qt.GlobalColor.transparent)

        painter = QPainter(stamp_img)
        suavizado = getattr(canvas, 'suavizado_pincel', True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, suavizado)

        src_rect = QRect(cx - radius, cy - radius, diameter, diameter)
        target_rect = QRectF(0, 0, diameter, diameter)

        path = QPainterPath()
        path.addEllipse(target_rect)
        painter.setClipPath(path)
        painter.drawImage(target_rect, img, QRectF(src_rect))
        painter.end()

        self.captured_texture = stamp_img
        if hasattr(canvas, 'main_window') and hasattr(canvas.main_window, 'bottom_bar'):
            canvas.main_window.bottom_bar.mostrar_mensaje(t("Estampa copiada"), 2000)

    def _apply_stamp(self, canvas, active_layer, pos: QPointF, radius: int):
        if not self.captured_texture:
            return
        img = active_layer.image
        diameter = radius * 2
        cx, cy = int(pos.x()), int(pos.y())

        scaled_stamp = self.captured_texture.scaled(
            diameter, diameter,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        painter = QPainter(img)
        suavizado = getattr(canvas, 'suavizado_pincel', True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, suavizado)

        target_rect = QRect(cx - radius, cy - radius, diameter, diameter)
        painter.drawImage(target_rect, scaled_stamp)
        painter.end()
