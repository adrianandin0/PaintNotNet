from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QLinearGradient, QBrush, QImage
from tools.base_tool import BaseTool


class GradientTool(BaseTool):
    def __init__(self):
        super().__init__("Degradado", "gui/iconos/gradient.png")
        self.p_start = None
        self.p_end = None
        self.is_dragging = False
        self.active_button = Qt.MouseButton.LeftButton

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.active_button = event.button()
            pos = event.position()
            self.p_start = QPointF(pos)
            self.p_end = QPointF(pos)
            self.is_dragging = True
            canvas.update()

    def mouse_move(self, canvas, event, color_activo=None):
        if self.is_dragging:
            self.p_end = QPointF(event.position())
            canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        if self.is_dragging and event.button() == self.active_button:
            self.p_end = QPointF(event.position())
            self.is_dragging = False
            self.commit_gradient(canvas)
            if hasattr(canvas, 'push_document_state'):
                canvas.push_document_state(self.name)
            canvas.update()

    def commit_gradient(self, canvas):
        if not self.p_start or not self.p_end:
            return

        if self.p_start == self.p_end:
            self.p_start = QPointF(0, 0)
            self.p_end = QPointF(canvas.layer_mgr.width, 0)

        modo = getattr(canvas, 'modo_degradado', 'Color')
        active_layer = canvas.layer_mgr.get_active_layer()
        if not active_layer or not active_layer.visible or active_layer.locked:
            return

        target_img = active_layer.image
        w, h = canvas.layer_mgr.width, canvas.layer_mgr.height

        if modo == 'Transparencia':
            # --- MODO TRANSPARENCIA: Reducir alfa de sólido (1.0) a transparente (0.0) ---
            mask = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
            mask.fill(Qt.GlobalColor.transparent)

            p_mask = QPainter(mask)
            p_mask.setRenderHint(QPainter.RenderHint.Antialiasing)

            grad = QLinearGradient(self.p_start, self.p_end)
            if self.active_button == Qt.MouseButton.RightButton:
                # Clic derecho: de transparente (0) a opaco (255)
                grad.setColorAt(0.0, QColor(0, 0, 0, 0))
                grad.setColorAt(1.0, QColor(0, 0, 0, 255))
            else:
                # Clic izquierdo: de opaco (255) a transparente (0)
                grad.setColorAt(0.0, QColor(0, 0, 0, 255))
                grad.setColorAt(1.0, QColor(0, 0, 0, 0))

            p_mask.fillRect(0, 0, w, h, QBrush(grad))
            p_mask.end()

            # Multiplicar el alfa de la capa activa con la máscara mediante CompositionMode_DestinationIn
            painter = QPainter(target_img)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            if canvas.selection_engine.has_selection():
                painter.setClipPath(canvas.selection_engine.active_path)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
            painter.drawImage(0, 0, mask)
            painter.end()

        else:
            # --- MODO COLOR: Rellenar con degradado entre color primario y secundario ---
            painter = QPainter(target_img)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            if canvas.selection_engine.has_selection():
                painter.setClipPath(canvas.selection_engine.active_path)

            grad = QLinearGradient(self.p_start, self.p_end)
            if self.active_button == Qt.MouseButton.RightButton:
                grad.setColorAt(0.0, canvas.color_secundario)
                grad.setColorAt(1.0, canvas.color_primario)
            else:
                grad.setColorAt(0.0, canvas.color_primario)
                grad.setColorAt(1.0, canvas.color_secundario)

            brush = QBrush(grad)
            painter.fillRect(0, 0, w, h, brush)
            painter.end()

        self.p_start = None
        self.p_end = None

    def draw_preview(self, painter, canvas):
        if self.is_dragging and self.p_start and self.p_end:
            modo = getattr(canvas, 'modo_degradado', 'Color')
            w, h = canvas.layer_mgr.width, canvas.layer_mgr.height

            if modo == 'Transparencia':
                active_layer = canvas.layer_mgr.get_active_layer()
                if active_layer:
                    # Previsualización directa en vivo recortando alfa de la capa activa
                    preview_img = active_layer.image.copy()
                    mask = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
                    mask.fill(Qt.GlobalColor.transparent)

                    p_mask = QPainter(mask)
                    p_mask.setRenderHint(QPainter.RenderHint.Antialiasing)

                    grad = QLinearGradient(self.p_start, self.p_end)
                    if self.active_button == Qt.MouseButton.RightButton:
                        grad.setColorAt(0.0, QColor(0, 0, 0, 0))
                        grad.setColorAt(1.0, QColor(0, 0, 0, 255))
                    else:
                        grad.setColorAt(0.0, QColor(0, 0, 0, 255))
                        grad.setColorAt(1.0, QColor(0, 0, 0, 0))

                    p_mask.fillRect(0, 0, w, h, QBrush(grad))
                    p_mask.end()

                    p_prev = QPainter(preview_img)
                    p_prev.setRenderHint(QPainter.RenderHint.Antialiasing)
                    if canvas.selection_engine.has_selection():
                        p_prev.setClipPath(canvas.selection_engine.active_path)
                    p_prev.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
                    p_prev.drawImage(0, 0, mask)
                    p_prev.end()

                    painter.save()
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    painter.drawImage(0, 0, preview_img)
                    painter.restore()
            else:
                painter.save()
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

                if canvas.selection_engine.has_selection():
                    painter.setClipPath(canvas.selection_engine.active_path)

                grad = QLinearGradient(self.p_start, self.p_end)
                if self.active_button == Qt.MouseButton.RightButton:
                    grad.setColorAt(0.0, canvas.color_secundario)
                    grad.setColorAt(1.0, canvas.color_primario)
                else:
                    grad.setColorAt(0.0, canvas.color_primario)
                    grad.setColorAt(1.0, canvas.color_secundario)

                brush = QBrush(grad)
                painter.fillRect(0, 0, w, h, brush)
                painter.restore()

            # Línea guía y nodos
            pen = QPen(QColor(255, 255, 255), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawLine(self.p_start, self.p_end)

            s = 8
            s2 = s / 2.0
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            col1 = canvas.color_secundario if self.active_button == Qt.MouseButton.RightButton else canvas.color_primario
            col2 = canvas.color_primario if self.active_button == Qt.MouseButton.RightButton else canvas.color_secundario

            if modo == 'Transparencia':
                col1 = QColor(0, 120, 215)
                col2 = QColor(255, 255, 255)

            painter.setBrush(QBrush(col1))
            painter.drawEllipse(QRectF(self.p_start.x() - s2, self.p_start.y() - s2, s, s))

            painter.setBrush(QBrush(col2))
            painter.drawEllipse(QRectF(self.p_end.x() - s2, self.p_end.y() - s2, s, s))
