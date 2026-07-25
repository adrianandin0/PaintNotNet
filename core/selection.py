from PyQt6.QtCore import QRect, QRectF, QPointF, Qt
from PyQt6.QtGui import QPainterPath, QTransform, QImage

class SelectionEngine:
    # Identificadores de tiradores
    HANDLE_NONE = 0
    HANDLE_TOP_LEFT = 1
    HANDLE_TOP_RIGHT = 2
    HANDLE_BOTTOM_LEFT = 3
    HANDLE_BOTTOM_RIGHT = 4
    HANDLE_TOP_CENTER = 5
    HANDLE_BOTTOM_CENTER = 6
    HANDLE_MIDDLE_LEFT = 7
    HANDLE_MIDDLE_RIGHT = 8
    HANDLE_MOVE = 9

    HANDLE_SIZE = 8  # Tamaño en píxeles de los cuadritos de control

    def __init__(self):
        self.active_rect = QRectF()
        self.active_path = QPainterPath()
        self.floating_image = None  # Almacena el contenido cortado/copiado al mover
        self.original_image_pos = QPointF()
        self.is_transforming = False

    def has_selection(self):
        return not self.active_path.isEmpty() or (self.active_rect.isValid() and not self.active_rect.isEmpty())

    def set_rectangle(self, rect):
        rect_f = QRectF(rect.normalized())
        self.active_rect = rect_f
        self.active_path = QPainterPath()
        self.active_path.addRect(rect_f)

    def set_ellipse(self, rect):
        rect_f = QRectF(rect.normalized())
        self.active_rect = rect_f
        self.active_path = QPainterPath()
        self.active_path.addEllipse(rect_f)

    def set_path(self, path):
        self.active_path = path
        self.active_rect = path.boundingRect()

    def clear_selection(self):
        self.active_rect = QRectF()
        self.active_path = QPainterPath()
        self.floating_image = None
        self.is_transforming = False

    def get_handles(self):
        """Devuelve los rectángulos de los 8 tiradores alrededor de la selección."""
        if not self.has_selection():
            return {}

        r = self.active_rect
        s = self.HANDLE_SIZE
        s2 = s / 2.0

        return {
            self.HANDLE_TOP_LEFT: QRectF(r.left() - s2, r.top() - s2, s, s),
            self.HANDLE_TOP_RIGHT: QRectF(r.right() - s2, r.top() - s2, s, s),
            self.HANDLE_BOTTOM_LEFT: QRectF(r.left() - s2, r.bottom() - s2, s, s),
            self.HANDLE_BOTTOM_RIGHT: QRectF(r.right() - s2, r.bottom() - s2, s, s),
            self.HANDLE_TOP_CENTER: QRectF(r.center().x() - s2, r.top() - s2, s, s),
            self.HANDLE_BOTTOM_CENTER: QRectF(r.center().x() - s2, r.bottom() - s2, s, s),
            self.HANDLE_MIDDLE_LEFT: QRectF(r.left() - s2, r.center().y() - s2, s, s),
            self.HANDLE_MIDDLE_RIGHT: QRectF(r.right() - s2, r.center().y() - s2, s, s),
        }

    def hit_test(self, point_f):
        """Determina sobre qué parte de la selección se hizo clic."""
        handles = self.get_handles()
        for handle_id, handle_rect in handles.items():
            if handle_rect.contains(point_f):
                return handle_id

        if self.active_rect.contains(point_f):
            return self.HANDLE_MOVE

        return self.HANDLE_NONE
