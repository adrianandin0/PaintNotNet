import math
import cv2
import numpy as np
from PyQt6.QtCore import Qt, QRect, QRectF, QPoint, QPointF
from PyQt6.QtGui import QPainter, QImage, QPen, QColor, QBrush, QPainterPath
from tools.base_tool import BaseTool
from tools.move_select_pixels import MoveSelectPixelsTool


class BlurTool(BaseTool):
    def __init__(self):
        super().__init__("Difuminar", "gui/iconos/blur.png")
        self.is_selecting_area = False
        self.tipo_area = "Rectangulo"
        self.start_pos = None
        self.current_pos = None
        self.area_points = []

    def _get_pixel_pos(self, event):
        return QPoint(int(math.floor(event.position().x())), int(math.floor(event.position().y())))

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() not in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            return

        top_bar = getattr(canvas.main_window, 'top_toolbar', None) if (hasattr(canvas, 'main_window') and canvas.main_window) else None
        tipo = top_bar.get_blur_tipo() if (top_bar and hasattr(top_bar, 'get_blur_tipo')) else "Rectangulo"

        pos = QPointF(event.position())

        # Si hay una previsualización difuminada viva activa en una selección
        if canvas.selection_engine.floating_image and not canvas.selection_engine.floating_image.isNull():
            # Si el clic ocurre fuera de la región seleccionada activa o inicia nuevo trazo, confirmar efecto flotante y deseleccionar
            MoveSelectPixelsTool.commit_floating_image(canvas)
            canvas.selection_engine.clear_selection()
            canvas.push_document_state("Difuminar área")
            canvas.update()

        self.is_selecting_area = True
        self.tipo_area = tipo
        self.start_pos = pos
        self.current_pos = pos
        self.area_points = [pos]
        canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        raw_pos = QPointF(event.position())

        if self.is_selecting_area:
            self.current_pos = raw_pos
            self.area_points.append(raw_pos)
            canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        if self.is_selecting_area:
            self.is_selecting_area = False
            path = QPainterPath()

            if self.tipo_area == "Rectangulo":
                if self.start_pos and self.current_pos:
                    rect = QRectF(self.start_pos, self.current_pos).normalized()
                    if rect.width() >= 3 and rect.height() >= 3:
                        path.addRect(rect)
            elif self.tipo_area == "Elipse":
                if self.start_pos and self.current_pos:
                    rect = QRectF(self.start_pos, self.current_pos).normalized()
                    if rect.width() >= 3 and rect.height() >= 3:
                        path.addEllipse(rect)
            else:  # "Lazo"
                if len(self.area_points) >= 3:
                    path.moveTo(self.area_points[0])
                    for pt in self.area_points[1:]:
                        path.lineTo(pt)
                    path.closeSubpath()

            self.start_pos = None
            self.current_pos = None
            self.area_points = []

            if not path.isEmpty():
                canvas.selection_engine.set_path(path)
                canvas.actualizar_preview_difuminado_seleccion()
            canvas.update()

    def draw_handles(self, painter, canvas):
        if self.is_selecting_area:
            painter.save()
            pen = QPen(QColor(0, 120, 215), 1, Qt.PenStyle.DashLine)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            if self.tipo_area == "Rectangulo" and self.start_pos and self.current_pos:
                rect = QRectF(self.start_pos, self.current_pos).normalized()
                painter.drawRect(rect)
            elif self.tipo_area == "Elipse" and self.start_pos and self.current_pos:
                rect = QRectF(self.start_pos, self.current_pos).normalized()
                painter.drawEllipse(rect)
            elif self.tipo_area == "Lazo" and len(self.area_points) >= 2:
                path = QPainterPath()
                path.moveTo(self.area_points[0])
                for pt in self.area_points[1:]:
                    path.lineTo(pt)
                painter.drawPath(path)

            painter.restore()
