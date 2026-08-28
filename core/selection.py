import math
from PyQt6.QtCore import QRect, QRectF, QPointF, Qt
from PyQt6.QtGui import QPainterPath, QTransform, QImage


class SelectionEngine:
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

    HANDLE_SIZE = 8

    def __init__(self):
        self.active_rect = QRectF()
        self.active_path = QPainterPath()
        self.floating_image = None
        self.unscaled_floating_image = None
        self.original_raw_image = None  # Copia intacta de máxima resolución al iniciar la selección
        self.original_image_pos = QPointF()
        self.is_transforming = False

        self.scale_x = 1.0
        self.scale_y = 1.0
        self.total_rotation = 0.0
        self.rotation_angle = 0.0
        self.base_rotation_angle = 0.0
        self.initial_mouse_angle = 0.0
        self.rotation_center = QPointF()

        self.initial_unrotated_path = None
        self.initial_unrotated_rect = None
        self.active_handle = 0
        self.is_moving = False
        self.is_rotating = False
        self.last_mouse_pos = QPointF()

    def has_selection(self):
        return not self.active_path.isEmpty() or (self.active_rect.isValid() and not self.active_rect.isEmpty())

    def is_empty(self):
        return not self.has_selection()

    def set_rectangle(self, rect):
        rect_f = QRectF(rect.normalized())
        self.active_rect = rect_f
        self.active_path = QPainterPath()
        self.active_path.addRect(rect_f)
        self._reset_transform_state()

    def set_ellipse(self, rect):
        rect_f = QRectF(rect.normalized())
        self.active_rect = rect_f
        self.active_path = QPainterPath()
        self.active_path.addEllipse(rect_f)
        self._reset_transform_state()

    def set_path(self, path):
        self.active_path = path
        self.active_rect = path.boundingRect()
        self._reset_transform_state()

    def clear_selection(self):
        self.active_rect = QRectF()
        self.active_path = QPainterPath()
        self.floating_image = None
        self.unscaled_floating_image = None
        self.original_raw_image = None
        self.is_transforming = False
        self._reset_transform_state()

    def _reset_transform_state(self):
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.total_rotation = 0.0
        self.rotation_angle = 0.0
        self.base_rotation_angle = 0.0
        self.initial_mouse_angle = 0.0
        self.rotation_center = QPointF()
        self.initial_unrotated_path = None
        self.initial_unrotated_rect = None
        self.is_moving = False
        self.is_rotating = False

    def init_raw_image(self, img):
        """Inicializa la imagen original sin degradación para transformaciones compuestas."""
        if img and not img.isNull():
            self.original_raw_image = img.copy()
            self.unscaled_floating_image = img.copy()
            self.floating_image = img.copy()
            self.scale_x = 1.0
            self.scale_y = 1.0
            self.total_rotation = 0.0
            self.rotation_center = QPointF(self.active_rect.center())
            self.initial_unrotated_path = QPainterPath(self.active_path)
            self.initial_unrotated_rect = QRectF(self.active_rect)

    def _apply_compound_transform(self):
        """
        Aplica la matriz de transformación compuesta (escalado + rotación) en un solo paso
        directamente desde la imagen original pura sin ninguna pérdida acumulada de calidad.
        """
        raw = self.original_raw_image or self.unscaled_floating_image
        if not raw or raw.isNull():
            return

        t_img = QTransform()
        t_img.scale(self.scale_x, self.scale_y)
        t_img.rotate(self.total_rotation)

        # Renderizado suavizado directo desde el original de alta calidad
        self.floating_image = raw.transformed(t_img, Qt.TransformationMode.SmoothTransformation)
        self.unscaled_floating_image = raw.copy()

        new_w = float(self.floating_image.width())
        new_h = float(self.floating_image.height())

        cx, cy = self.rotation_center.x(), self.rotation_center.y()
        top_left = QPointF(cx - new_w / 2.0, cy - new_h / 2.0)
        self.original_image_pos = top_left
        self.active_rect = QRectF(top_left.x(), top_left.y(), new_w, new_h)

        # Mapeo del path de selección
        if self.initial_unrotated_path and not self.initial_unrotated_path.isEmpty() and self.initial_unrotated_rect:
            orig_cx = self.initial_unrotated_rect.center().x()
            orig_cy = self.initial_unrotated_rect.center().y()

            t_path = (
                QTransform()
                .translate(cx, cy)
                .rotate(self.total_rotation)
                .scale(self.scale_x, self.scale_y)
                .translate(-orig_cx, -orig_cy)
            )
            self.active_path = t_path.map(self.initial_unrotated_path)

    def get_handles(self):
        if not self.has_selection():
            return {}

        raw = self.original_raw_image or self.unscaled_floating_image
        if raw and not raw.isNull():
            W = float(raw.width()) * self.scale_x
            H = float(raw.height()) * self.scale_y
        else:
            r = self.active_rect
            W = r.width()
            H = r.height()

        cx = self.rotation_center.x() if (self.rotation_center and not self.rotation_center.isNull()) else self.active_rect.center().x()
        cy = self.rotation_center.y() if (self.rotation_center and not self.rotation_center.isNull()) else self.active_rect.center().y()

        rad = math.radians(self.total_rotation)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        s = self.HANDLE_SIZE
        s2 = s / 2.0

        local_positions = {
            self.HANDLE_TOP_LEFT: (-W / 2.0, -H / 2.0),
            self.HANDLE_TOP_RIGHT: (W / 2.0, -H / 2.0),
            self.HANDLE_BOTTOM_LEFT: (-W / 2.0, H / 2.0),
            self.HANDLE_BOTTOM_RIGHT: (W / 2.0, H / 2.0),
            self.HANDLE_TOP_CENTER: (0.0, -H / 2.0),
            self.HANDLE_BOTTOM_CENTER: (0.0, H / 2.0),
            self.HANDLE_MIDDLE_LEFT: (-W / 2.0, 0.0),
            self.HANDLE_MIDDLE_RIGHT: (W / 2.0, 0.0),
        }

        handles = {}
        for handle_id, (lx, ly) in local_positions.items():
            canvas_x = cx + (lx * cos_a - ly * sin_a)
            canvas_y = cy + (lx * sin_a + ly * cos_a)
            handles[handle_id] = QRectF(canvas_x - s2, canvas_y - s2, s, s)

        return handles

    def hit_test(self, point_f):
        handles = self.get_handles()
        for handle_id, handle_rect in handles.items():
            if handle_rect.contains(point_f):
                return handle_id

        if self.active_rect.contains(point_f):
            return self.HANDLE_MOVE

    def rotate_floating_image(self, degrees):
        if not self.has_selection():
            return

        if not self.original_raw_image and self.floating_image:
            self.init_raw_image(self.floating_image)

        self.total_rotation = (self.total_rotation + degrees) % 360.0
        self._apply_compound_transform()

    def begin_transform(self, pos, button, hit):
        self.active_handle = hit
        self.last_mouse_pos = pos

        if not self.original_raw_image and self.floating_image and not self.floating_image.isNull():
            self.init_raw_image(self.floating_image)

        if not self.rotation_center or self.rotation_center.isNull():
            self.rotation_center = QPointF(self.active_rect.center())

        if not self.initial_unrotated_rect or self.initial_unrotated_rect.isEmpty():
            self.initial_unrotated_rect = QRectF(self.active_rect)
            self.initial_unrotated_path = QPainterPath(self.active_path)

        if button == Qt.MouseButton.RightButton and hit in (
            self.HANDLE_TOP_LEFT, self.HANDLE_TOP_RIGHT,
            self.HANDLE_BOTTOM_LEFT, self.HANDLE_BOTTOM_RIGHT
        ):
            self.is_rotating = True
            self.is_moving = False
            self.initial_mouse_angle = math.atan2(pos.y() - self.rotation_center.y(), pos.x() - self.rotation_center.x())
            self.base_rotation_angle = self.total_rotation
        else:
            self.is_moving = True
            self.is_rotating = False
            self.initial_scale_x_drag = self.scale_x
            self.initial_scale_y_drag = self.scale_y
            self.initial_center_drag = QPointF(self.rotation_center)

    def update_transform(self, pos, is_shift=False):
        if self.is_rotating:
            curr_angle = math.atan2(pos.y() - self.rotation_center.y(), pos.x() - self.rotation_center.x())
            delta_rad = curr_angle - self.initial_mouse_angle
            delta_deg = math.degrees(delta_rad)

            self.total_rotation = (self.base_rotation_angle + delta_deg) % 360.0
            self._apply_compound_transform()

        elif self.is_moving:
            if self.active_handle not in (self.HANDLE_NONE, self.HANDLE_MOVE):
                self.resize_selection(self.active_handle, pos, lock_aspect_ratio=is_shift)
            elif self.active_handle == self.HANDLE_MOVE:
                delta = pos - self.last_mouse_pos
                self.rotation_center += delta
                self.original_image_pos += delta
                self.active_rect.translate(delta.x(), delta.y())

                if not self.active_path.isEmpty():
                    transform = QTransform()
                    transform.translate(delta.x(), delta.y())
                    self.active_path = transform.map(self.active_path)
                if self.initial_unrotated_path and not self.initial_unrotated_path.isEmpty():
                    self.initial_unrotated_path = QTransform().translate(delta.x(), delta.y()).map(self.initial_unrotated_path)
                if self.initial_unrotated_rect:
                    self.initial_unrotated_rect.translate(delta.x(), delta.y())

        self.last_mouse_pos = pos

    def end_transform(self):
        self.is_moving = False
        self.is_rotating = False
        self.active_handle = self.HANDLE_NONE

    def resize_selection(self, handle_id, current_pos, lock_aspect_ratio=False):
        if not self.has_selection() or handle_id in (self.HANDLE_NONE, self.HANDLE_MOVE):
            return

        if not self.original_raw_image and self.floating_image and not self.floating_image.isNull():
            self.init_raw_image(self.floating_image)

        raw = self.original_raw_image or self.unscaled_floating_image
        if not raw or raw.isNull():
            return

        raw_w = float(raw.width())
        raw_h = float(raw.height())

        # Dimensiones en espacio local des-rotado al inicio del arrastre
        W0 = raw_w * getattr(self, 'initial_scale_x_drag', self.scale_x)
        H0 = raw_h * getattr(self, 'initial_scale_y_drag', self.scale_y)
        center0 = getattr(self, 'initial_center_drag', self.rotation_center)

        # Proyectar current_pos al sistema de coordenadas local sin rotación
        rad = math.radians(-self.total_rotation)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        dx = current_pos.x() - center0.x()
        dy = current_pos.y() - center0.y()

        local_x = dx * cos_a - dy * sin_a
        local_y = dx * sin_a + dy * cos_a

        l0, r0 = -W0 / 2.0, W0 / 2.0
        t0, b0 = -H0 / 2.0, H0 / 2.0

        l1, r1, t1, b1 = l0, r0, t0, b0

        if handle_id in (self.HANDLE_TOP_LEFT, self.HANDLE_MIDDLE_LEFT, self.HANDLE_BOTTOM_LEFT):
            l1 = min(r0 - 2.0, local_x)
        if handle_id in (self.HANDLE_TOP_RIGHT, self.HANDLE_MIDDLE_RIGHT, self.HANDLE_BOTTOM_RIGHT):
            r1 = max(l0 + 2.0, local_x)
        if handle_id in (self.HANDLE_TOP_LEFT, self.HANDLE_TOP_CENTER, self.HANDLE_TOP_RIGHT):
            t1 = min(b0 - 2.0, local_y)
        if handle_id in (self.HANDLE_BOTTOM_LEFT, self.HANDLE_BOTTOM_CENTER, self.HANDLE_BOTTOM_RIGHT):
            b1 = max(t0 + 2.0, local_y)

        new_w = r1 - l1
        new_h = b1 - t1

        if lock_aspect_ratio:
            orig_aspect = raw_w / max(1.0, raw_h)
            if new_w / max(1.0, new_h) > orig_aspect:
                new_w = new_h * orig_aspect
                if handle_id in (self.HANDLE_TOP_LEFT, self.HANDLE_MIDDLE_LEFT, self.HANDLE_BOTTOM_LEFT):
                    l1 = r1 - new_w
                else:
                    r1 = l1 + new_w
            else:
                new_h = new_w / orig_aspect
                if handle_id in (self.HANDLE_TOP_LEFT, self.HANDLE_TOP_CENTER, self.HANDLE_TOP_RIGHT):
                    t1 = b1 - new_h
                else:
                    b1 = t1 + new_h

        if new_w > 2 and new_h > 2:
            self.scale_x = max(0.001, new_w / raw_w)
            self.scale_y = max(0.001, new_h / raw_h)

            local_cx = (l1 + r1) / 2.0
            local_cy = (t1 + b1) / 2.0

            rad_back = math.radians(self.total_rotation)
            cos_b = math.cos(rad_back)
            sin_b = math.sin(rad_back)

            new_cx = center0.x() + (local_cx * cos_b - local_cy * sin_b)
            new_cy = center0.y() + (local_cx * sin_b + local_cy * cos_b)
            self.rotation_center = QPointF(new_cx, new_cy)

            self._apply_compound_transform()
