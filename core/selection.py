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
        self.original_image_pos = QPointF()
        self.is_transforming = False

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
        self.is_transforming = False
        self._reset_transform_state()

    def _reset_transform_state(self):
        self.rotation_angle = 0.0
        self.base_rotation_angle = 0.0
        self.initial_mouse_angle = 0.0
        self.rotation_center = QPointF()
        self.initial_unrotated_path = None
        self.initial_unrotated_rect = None
        self.is_moving = False
        self.is_rotating = False

    def get_handles(self):
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
        handles = self.get_handles()
        for handle_id, handle_rect in handles.items():
            if handle_rect.contains(point_f):
                return handle_id

        if self.active_rect.contains(point_f):
            return self.HANDLE_MOVE

    def rotate_floating_image(self, degrees):
        if not self.has_selection():
            return

        cx, cy = self.active_rect.center().x(), self.active_rect.center().y()
        self.rotation_angle += degrees
        total_angle = self.rotation_angle

        t_path = QTransform().translate(cx, cy).rotate(degrees).translate(-cx, -cy)
        if not self.active_path.isEmpty():
            self.active_path = t_path.map(self.active_path)
            self.active_rect = self.active_path.boundingRect()

        if self.unscaled_floating_image and not self.unscaled_floating_image.isNull():
            t_img = QTransform().rotate(total_angle)
            rotated = self.unscaled_floating_image.transformed(t_img, Qt.TransformationMode.SmoothTransformation)
            self.floating_image = rotated

            new_w = rotated.width()
            new_h = rotated.height()

            new_left = cx - new_w / 2.0
            new_top = cy - new_h / 2.0

            self.active_rect = QRectF(new_left, new_top, new_w, new_h)
            self.original_image_pos = QPointF(new_left, new_top)

    def begin_transform(self, pos, button, hit):
        self.active_handle = hit
        self.last_mouse_pos = pos

        if button == Qt.MouseButton.RightButton and hit in (
            self.HANDLE_TOP_LEFT, self.HANDLE_TOP_RIGHT,
            self.HANDLE_BOTTOM_LEFT, self.HANDLE_BOTTOM_RIGHT
        ):
            self.is_rotating = True
            self.is_moving = False
            self.rotation_center = QPointF(self.active_rect.center())
            self.initial_mouse_angle = math.atan2(pos.y() - self.rotation_center.y(), pos.x() - self.rotation_center.x())
            self.base_rotation_angle = self.rotation_angle
            self.initial_unrotated_path = QPainterPath(self.active_path)
            self.initial_unrotated_rect = QRectF(self.active_rect)
        else:
            self.is_moving = True
            self.is_rotating = False

    def update_transform(self, pos, is_shift=False):
        if self.is_rotating:
            curr_angle = math.atan2(pos.y() - self.rotation_center.y(), pos.x() - self.rotation_center.x())
            delta_rad = curr_angle - self.initial_mouse_angle
            delta_deg = math.degrees(delta_rad)

            total_angle = self.base_rotation_angle + delta_deg
            self.rotation_angle = total_angle

            cx, cy = self.rotation_center.x(), self.rotation_center.y()

            if self.initial_unrotated_path and not self.initial_unrotated_path.isEmpty():
                t = QTransform().translate(cx, cy).rotate(delta_deg).translate(-cx, -cy)
                self.active_path = t.map(self.initial_unrotated_path)
                self.active_rect = self.active_path.boundingRect()

            if self.unscaled_floating_image and not self.unscaled_floating_image.isNull():
                t_img = QTransform().rotate(total_angle)
                rotated = self.unscaled_floating_image.transformed(t_img, Qt.TransformationMode.SmoothTransformation)
                self.floating_image = rotated

                new_w = rotated.width()
                new_h = rotated.height()

                new_left = cx - new_w / 2.0
                new_top = cy - new_h / 2.0

                self.active_rect = QRectF(new_left, new_top, new_w, new_h)
                self.original_image_pos = QPointF(new_left, new_top)

        elif self.is_moving:
            if self.active_handle not in (self.HANDLE_NONE, self.HANDLE_MOVE):
                self.resize_selection(self.active_handle, pos, lock_aspect_ratio=is_shift)
            elif self.active_handle == self.HANDLE_MOVE:
                delta = pos - self.last_mouse_pos
                dx, dy = delta.x(), delta.y()

                self.original_image_pos += QPointF(dx, dy)
                self.active_rect.translate(dx, dy)

                if not self.active_path.isEmpty():
                    transform = QTransform()
                    transform.translate(dx, dy)
                    self.active_path = transform.map(self.active_path)

        self.last_mouse_pos = pos

    def end_transform(self):
        self.is_moving = False
        self.is_rotating = False
        self.active_handle = self.HANDLE_NONE

    def resize_selection(self, handle_id, current_pos, lock_aspect_ratio=False):
        if not self.has_selection() or handle_id in (self.HANDLE_NONE, self.HANDLE_MOVE):
            return

        old_rect = QRectF(self.active_rect)
        if old_rect.width() <= 1 or old_rect.height() <= 1:
            return

        l, r, t, b = old_rect.left(), old_rect.right(), old_rect.top(), old_rect.bottom()
        px, py = current_pos.x(), current_pos.y()

        if handle_id in (self.HANDLE_TOP_LEFT, self.HANDLE_MIDDLE_LEFT, self.HANDLE_BOTTOM_LEFT):
            l = px
        if handle_id in (self.HANDLE_TOP_RIGHT, self.HANDLE_MIDDLE_RIGHT, self.HANDLE_BOTTOM_RIGHT):
            r = px
        if handle_id in (self.HANDLE_TOP_LEFT, self.HANDLE_TOP_CENTER, self.HANDLE_TOP_RIGHT):
            t = py
        if handle_id in (self.HANDLE_BOTTOM_LEFT, self.HANDLE_BOTTOM_CENTER, self.HANDLE_BOTTOM_RIGHT):
            b = py

        new_rect = QRectF(QPointF(l, t), QPointF(r, b)).normalized()

        if lock_aspect_ratio:
            if self.unscaled_floating_image and not self.unscaled_floating_image.isNull():
                orig_aspect = float(self.unscaled_floating_image.width()) / max(1.0, float(self.unscaled_floating_image.height()))
            else:
                orig_aspect = old_rect.width() / max(1.0, old_rect.height())

            curr_w = new_rect.width()
            curr_h = new_rect.height()

            if curr_w / max(1.0, curr_h) > orig_aspect:
                new_rect.setWidth(curr_h * orig_aspect)
            else:
                new_rect.setHeight(curr_w / orig_aspect)

        if new_rect.width() > 2 and new_rect.height() > 2:
            sx = new_rect.width() / max(1.0, old_rect.width())
            sy = new_rect.height() / max(1.0, old_rect.height())

            transform = QTransform()
            transform.translate(new_rect.left(), new_rect.top())
            transform.scale(sx, sy)
            transform.translate(-old_rect.left(), -old_rect.top())

            if not self.active_path.isEmpty():
                self.active_path = transform.map(self.active_path)
            self.active_rect = new_rect

            if self.unscaled_floating_image and not self.unscaled_floating_image.isNull():
                new_w = max(1, int(new_rect.width()))
                new_h = max(1, int(new_rect.height()))
                self.floating_image = self.unscaled_floating_image.scaled(
                    new_w, new_h,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                # Actualizar la base de rotación al tamaño nuevo.
                # Si no se hace esto, rotar luego del resize usa la imagen
                # original ignorando el nuevo tamaño.
                self.unscaled_floating_image = self.floating_image.copy()
                self.rotation_angle = 0.0
                self.base_rotation_angle = 0.0
                self.original_image_pos = new_rect.topLeft()
