"""
TransformTool: Herramienta de deformación 2D plana ultrarrápida (Fast 2D Mesh Warp).

Levanta los píxeles de la capa activa dentro de la selección y permite
deformar la imagen mediante 16 tiradores interconectados en un plano 2D puro.
Toda la deformación se realiza en 2D sin proyecciones 3D ni planos que se oculten por detrás,
optimizada para máxima velocidad y respuesta instantánea a 60+ FPS.

Controles:
  - Activar herramienta con selección activa → la grilla aparece automáticamente.
  - Arrastrar esquinas o bordes: deforma la selección en 2D.
  - Clic fuera de la grilla / Enter: confirma y aplica al lienzo.
  - Escape: cancela y restaura la imagen original.
"""

import math
from PyQt6.QtCore import Qt, QPointF, QRectF, QRect
from PyQt6.QtGui import (
    QPainter, QImage, QTransform, QPen, QColor, QBrush, QPolygonF,
    QPainterPath
)
from tools.base_tool import BaseTool


def _lerp(a: QPointF, b: QPointF, t: float) -> QPointF:
    return QPointF(a.x() + (b.x() - a.x()) * t,
                   a.y() + (b.y() - a.y()) * t)


def _bilerp(p0: QPointF, p1: QPointF, p2: QPointF, p3: QPointF, u: float, v: float) -> QPointF:
    top = _lerp(p0, p1, u)
    bot = _lerp(p3, p2, u)
    return _lerp(top, bot, v)


def _b3_0(t: float) -> float: return (1.0 - t)**3
def _b3_1(t: float) -> float: return 3.0 * ((1.0 - t)**2) * t
def _b3_2(t: float) -> float: return 3.0 * (1.0 - t) * (t**2)
def _b3_3(t: float) -> float: return t**3


def _evaluate_bicubic_surface(ctrl_points: list[list[QPointF]], u: float, v: float) -> QPointF:
    """Evalúa una superficie curva bicúbica suave de Bezier sobre la matriz de 4x4 puntos de control."""
    bu = [_b3_0(u), _b3_1(u), _b3_2(u), _b3_3(u)]
    bv = [_b3_0(v), _b3_1(v), _b3_2(v), _b3_3(v)]
    x, y = 0.0, 0.0
    for r in range(4):
        wr = bv[r]
        for c in range(4):
            w = wr * bu[c]
            pt = ctrl_points[r][c]
            x += pt.x() * w
            y += pt.y() * w
    return QPointF(x, y)


def _get_triangle_transform_2d(s0: QPointF, s1: QPointF, s2: QPointF,
                               d0: QPointF, d1: QPointF, d2: QPointF) -> QTransform | None:
    x0, y0 = s0.x(), s0.y()
    x1, y1 = s1.x(), s1.y()
    x2, y2 = s2.x(), s2.y()

    u0, v0 = d0.x(), d0.y()
    u1, v1 = d1.x(), d1.y()
    u2, v2 = d2.x(), d2.y()

    det = x0 * (y1 - y2) + x1 * (y2 - y0) + x2 * (y0 - y1)
    if abs(det) < 1e-6:
        return None

    m11 = (u0 * (y1 - y2) + u1 * (y2 - y0) + u2 * (y0 - y1)) / det
    m21 = (u0 * (x2 - x1) + u1 * (x0 - x2) + u2 * (x1 - x0)) / det
    dx  = (u0 * (x1 * y2 - x2 * y1) + u1 * (x2 * y0 - x0 * y2) + u2 * (x0 * y1 - x1 * y0)) / det

    m12 = (v0 * (y1 - y2) + v1 * (y2 - y0) + v2 * (y0 - y1)) / det
    m22 = (v0 * (x2 - x1) + v1 * (x0 - x2) + v2 * (x1 - x0)) / det
    dy  = (v0 * (x1 * y2 - x2 * y1) + v1 * (x2 * y0 - x0 * y2) + v2 * (x0 * y1 - x1 * y0)) / det

    return QTransform(m11, m12, m21, m22, dx, dy)


def _expand_triangle(d0: QPointF, d1: QPointF, d2: QPointF, amount: float = 0.5) -> tuple[QPointF, QPointF, QPointF]:
    """Expande ligeramente los vértices del triángulo hacia afuera para eliminar huecos de escaneo de píxeles (pinholes)."""
    cx = (d0.x() + d1.x() + d2.x()) / 3.0
    cy = (d0.y() + d1.y() + d2.y()) / 3.0
    def expand_pt(pt: QPointF) -> QPointF:
        vx = pt.x() - cx
        vy = pt.y() - cy
        length = math.hypot(vx, vy)
        if length < 1e-5:
            return pt
        return QPointF(pt.x() + (vx / length) * amount, pt.y() + (vy / length) * amount)
    return expand_pt(d0), expand_pt(d1), expand_pt(d2)


class TransformTool(BaseTool):

    HANDLE_NONE = (-1, -1)
    HANDLE_MOVE = (-2, -2)
    HANDLE_SIZE = 7   # píxeles de pantalla idénticos a los tiradores de selección
    GRID_SUBDIVISIONS = 32  # Subdivisión ultra-fina 32x32 para curvas matemáticas continuas sin segmentos rectos visibles

    def __init__(self):
        super().__init__("Transformar", "gui/iconos/transform.png")
        self._corners: list[QPointF] = []        # [TL, TR, BR, BL]
        self._offsets: list[list[QPointF]] = []  # Matriz 4x4 de curvas locales
        self._src_slices: list[list[tuple[QImage, float, float]]] = [] # Recortes optimizados 3x3
        self._active_handle = self.HANDLE_NONE
        self._last_doc_pos: QPointF | None = None
        self._is_active = False
        self._original_image: QImage | None = None  # backup para Escape
        self._original_pos: QPointF | None = None
        self._layer_backup: QImage | None = None
        self._path_backup: QPainterPath | None = None
        self._undo_stack: list[tuple[list[QPointF], list[list[QPointF]]]] = []
        self._redo_stack: list[tuple[list[QPointF], list[list[QPointF]]]] = []

    def _get_move_handle_info(self, scale_factor: float = 1.0) -> tuple[QPointF, QPointF, QRectF]:
        """Calcula la posición del punto de anclaje de movimiento (top center exterior), la línea conectora y su QRectF."""
        if not self._corners or len(self._corners) < 4:
            return QPointF(), QPointF(), QRectF()

        ctrl_grid = self._get_control_grid()
        top_center = _evaluate_bicubic_surface(ctrl_grid, 0.5, 0.0)

        tl = ctrl_grid[0][0]
        tr = ctrl_grid[0][3]
        vx = tr.x() - tl.x()
        vy = tr.y() - tl.y()
        length = math.hypot(vx, vy)

        sf = max(0.001, scale_factor)
        offset_dist = 18.0 / sf

        if length > 1e-5:
            nx = vy / length
            ny = -vx / length
            move_pt = QPointF(top_center.x() + nx * offset_dist, top_center.y() + ny * offset_dist)
        else:
            move_pt = QPointF(top_center.x(), top_center.y() - offset_dist)

        move_sz = 10.0 / sf
        half_sz = move_sz / 2.0
        move_rect = QRectF(move_pt.x() - half_sz, move_pt.y() - half_sz, move_sz, move_sz)

        return top_center, move_pt, move_rect

    def _reset_state(self):
        self._corners = []
        self._offsets = [[QPointF(0, 0) for _ in range(4)] for _ in range(4)]
        self._src_slices = []
        self._is_active = False
        self._original_image = None
        self._original_pos = None
        self._layer_backup = None
        self._path_backup = None
        self._active_handle = self.HANDLE_NONE
        self._last_doc_pos = None
        self._undo_stack.clear()
        self._redo_stack.clear()

    def _save_undo_step(self):
        c_copy = [QPointF(p) for p in self._corners]
        o_copy = [[QPointF(p) for p in row] for row in self._offsets]
        self._undo_stack.append((c_copy, o_copy))
        self._redo_stack.clear()

    def undo_step(self, canvas) -> bool:
        """Deshace el último movimiento de tiradores durante la sesión de transformación interactiva."""
        if not self._is_active:
            return False

        if len(self._undo_stack) > 1:
            curr = self._undo_stack.pop()
            self._redo_stack.append(curr)

            prev_corners, prev_offsets = self._undo_stack[-1]
            self._corners = [QPointF(p) for p in prev_corners]
            self._offsets = [[QPointF(p) for p in row] for row in prev_offsets]

            self._apply_warp(canvas)
            canvas.update()
            return True
        elif len(self._undo_stack) == 1:
            self._cancel(canvas)
            return True

        return False

    def redo_step(self, canvas) -> bool:
        """Rehace el movimiento de tiradores deshecho durante la sesión de transformación interactiva."""
        if not self._is_active or not self._redo_stack:
            return False

        next_state = self._redo_stack.pop()
        self._undo_stack.append(next_state)

        next_corners, next_offsets = next_state
        self._corners = [QPointF(p) for p in next_corners]
        self._offsets = [[QPointF(p) for p in row] for row in next_offsets]

        self._apply_warp(canvas)
        canvas.update()
        return True

    def _get_control_grid(self) -> list[list[QPointF]]:
        """Devuelve la matriz 4x4 de puntos de control de la superficie curva."""
        if not self._corners or len(self._corners) < 4:
            return [[QPointF() for _ in range(4)] for _ in range(4)]
        grid = []
        for r in range(4):
            row = []
            for c in range(4):
                u = c / 3.0
                v = r / 3.0
                base = _bilerp(self._corners[0], self._corners[1], self._corners[2], self._corners[3], u, v)
                row.append(base + self._offsets[r][c])
            grid.append(row)
        return grid

    def _get_mesh_point(self, r: int, c: int) -> QPointF:
        grid = self._get_control_grid()
        return grid[r][c]

    def _evaluate_fine_grid(self, n: int) -> list[list[QPointF]]:
        """Genera una malla fina de NxN puntos evaluados sobre la superficie bicúbica suave."""
        ctrl = self._get_control_grid()
        grid = []
        for r in range(n + 1):
            v = r / float(n)
            row = []
            for c in range(n + 1):
                u = c / float(n)
                row.append(_evaluate_bicubic_surface(ctrl, u, v))
            grid.append(row)
        return grid

    def on_activate(self, canvas):
        self._reset_state()
        canvas.actualizar_cursor_herramienta(self)
        has_floating = bool(canvas.selection_engine.floating_image and not canvas.selection_engine.floating_image.isNull())
        if canvas.selection_engine.has_selection() or has_floating:
            self._lift_selection(canvas)
            canvas.update()

    def _lift_selection(self, canvas) -> bool:
        engine = canvas.selection_engine
        self._is_new_content = getattr(engine, 'is_new_content', False)
        has_floating = bool(engine.floating_image and not engine.floating_image.isNull())
        if not engine.has_selection() and not has_floating:
            return False

        layer = canvas.layer_mgr.get_active_layer()
        if layer and layer.image:
            self._layer_backup = layer.image.copy()
        if not engine.active_path.isEmpty():
            self._path_backup = QPainterPath(engine.active_path)
        else:
            self._path_backup = None

        if not getattr(self, '_is_new_content', False):
            canvas.floating_initial_canvas = None
        if hasattr(canvas, 'floating_sub_history'):
            canvas.floating_sub_history.clear()

        raw = getattr(engine, 'original_raw_image', None) or engine.unscaled_floating_image or engine.floating_image
        if raw and not raw.isNull():
            src = raw.copy()
            W = float(src.width())
            H = float(src.height())
            rot = getattr(engine, 'total_rotation', 0.0)
            sx = getattr(engine, 'scale_x', 1.0)
            sy = getattr(engine, 'scale_y', 1.0)

            if getattr(engine, 'rotation_center', None) and not engine.rotation_center.isNull():
                cx, cy = engine.rotation_center.x(), engine.rotation_center.y()
            elif engine.active_rect and not engine.active_rect.isEmpty():
                cx, cy = engine.active_rect.center().x(), engine.active_rect.center().y()
            else:
                pos = getattr(engine, 'original_image_pos', QPointF(0, 0))
                cx, cy = pos.x() + W / 2.0, pos.y() + H / 2.0

            rad = math.radians(rot)
            cos_a, sin_a = math.cos(rad), math.sin(rad)
            w_half = (W * sx) / 2.0
            h_half = (H * sy) / 2.0

            local_pts = [
                (-w_half, -h_half),
                ( w_half, -h_half),
                ( w_half,  h_half),
                (-w_half,  h_half)
            ]

            corners = []
            for lx, ly in local_pts:
                px = cx + (lx * cos_a - ly * sin_a)
                py = cy + (lx * sin_a + ly * cos_a)
                corners.append(QPointF(px, py))

            self._corners = corners
            self._initial_corners = [QPointF(p) for p in corners]
            self._offsets = [[QPointF(0, 0) for _ in range(4)] for _ in range(4)]
            self._original_image = src.copy()
            self._original_pos = QPointF(corners[0])

            engine.unscaled_floating_image = src.copy()
            self._is_new_content = getattr(engine, 'is_new_content', False)

            self._undo_stack.clear()
            self._redo_stack.clear()
            self._save_undo_step()

            self._is_active = True
            self._apply_warp(canvas)
            return True

        active_rect = engine.active_rect.intersected(
            QRectF(0, 0, canvas.layer_mgr.width, canvas.layer_mgr.height)
        )
        if active_rect.width() < 1 or active_rect.height() < 1:
            return False

        r = active_rect.toRect()
        buffer = canvas.layer_mgr.buffer
        if not hasattr(canvas, 'floating_initial_canvas') or canvas.floating_initial_canvas is None:
            canvas.floating_initial_canvas = buffer.copy()
        lifted = buffer.copy(r)

        if not engine.active_path.isEmpty():
            masked = QImage(r.size(), QImage.Format.Format_ARGB32_Premultiplied)
            masked.fill(Qt.GlobalColor.transparent)
            mp = QPainter(masked)
            local_path = QPainterPath(engine.active_path)
            local_path.translate(-QPointF(r.topLeft()))
            mp.setClipPath(local_path)
            mp.drawImage(0, 0, lifted)
            mp.end()
            lifted = masked

        pos = QPointF(r.topLeft())
        src = lifted

        if not getattr(self, '_is_new_content', False):
            layer = canvas.layer_mgr.get_active_layer()
            is_layer_trans = getattr(layer, 'transparent', True) if layer else True
            p = QPainter(buffer)
            if is_layer_trans:
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                if not engine.active_path.isEmpty():
                    p.setClipPath(engine.active_path)
                p.fillRect(r, Qt.GlobalColor.transparent)
            else:
                bg_col = getattr(canvas, 'color_secundario', QColor(255, 255, 255))
                if not isinstance(bg_col, QColor) or not bg_col.isValid():
                    bg_col = QColor(255, 255, 255)
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
                if not engine.active_path.isEmpty():
                    p.setClipPath(engine.active_path)
                p.fillRect(r, bg_col)
            p.end()

        engine.floating_image = src.copy()
        engine.unscaled_floating_image = src.copy()
        engine.original_image_pos = QPointF(pos)
        if not engine.has_selection():
            engine.is_new_content = False

        self._original_image = src.copy()
        self._original_pos = QPointF(pos)

        w = float(src.width())
        h = float(src.height())
        x0, y0 = pos.x(), pos.y()

        self._corners = [
            QPointF(x0,     y0    ),   # 0 TL
            QPointF(x0 + w, y0    ),   # 1 TR
            QPointF(x0 + w, y0 + h),   # 2 BR
            QPointF(x0,     y0 + h),   # 3 BL
        ]
        self._offsets = [[QPointF(0, 0) for _ in range(4)] for _ in range(4)]
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._save_undo_step()

        self._is_active = True
        self._apply_warp(canvas)
        return True

    def on_deactivate(self, canvas):
        if self._is_active:
            self._commit(canvas)

    def _hit_test(self, doc_pos: QPointF, scale_factor: float) -> tuple[int, int]:
        if not self._corners:
            return self.HANDLE_NONE

        sf = max(0.001, scale_factor)

        # 1. Probar primero el punto de anclaje de movimiento (Move Anchor Handle)
        top_center, move_pt, move_rect = self._get_move_handle_info(scale_factor)
        tol_move = 4.0 / sf
        if move_rect.adjusted(-tol_move, -tol_move, tol_move, tol_move).contains(doc_pos):
            return self.HANDLE_MOVE

        # 2. Probar los 16 tiradores de la malla 4x4
        tol = 14.0 / sf
        for r in range(4):
            for c in range(4):
                pt = self._get_mesh_point(r, c)
                if abs(doc_pos.x() - pt.x()) <= tol and abs(doc_pos.y() - pt.y()) <= tol:
                    return (r, c)
        return self.HANDLE_NONE

    def _apply_warp(self, canvas):
        engine = canvas.selection_engine
        src = engine.unscaled_floating_image
        if not src or src.isNull() or not self._corners:
            return

        w_src = float(src.width())
        h_src = float(src.height())

        # Adaptar subdivisiones durante el arrastre activo para respuesta instantánea (120+ FPS)
        n = 12 if getattr(self, '_active_handle', self.HANDLE_NONE) != self.HANDLE_NONE else self.GRID_SUBDIVISIONS
        fine_grid = self._evaluate_fine_grid(n)

        all_xs = [pt.x() for row in fine_grid for pt in row]
        all_ys = [pt.y() for row in fine_grid for pt in row]
        out_x = min(all_xs)
        out_y = min(all_ys)
        out_w = max(int(max(all_xs) - out_x) + 2, 1)
        out_h = max(int(max(all_ys) - out_y) + 2, 1)

        max_dim = max(16384, max(canvas.layer_mgr.width, canvas.layer_mgr.height) * 4)
        if out_w > max_dim or out_h > max_dim:
            return

        result = QImage(out_w, out_h, QImage.Format.Format_ARGB32_Premultiplied)
        result.fill(Qt.GlobalColor.transparent)

        p = QPainter(result)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        origin = QPointF(out_x, out_y)
        eps = 0.05

        for r in range(n):
            v0, v1 = r / float(n), (r + 1) / float(n)
            for c in range(n):
                u0, u1 = c / float(n), (c + 1) / float(n)

                s0 = QPointF(u0 * w_src + eps, v0 * h_src + eps)
                s1 = QPointF(u1 * w_src - eps, v0 * h_src + eps)
                s2 = QPointF(u1 * w_src - eps, v1 * h_src - eps)
                s3 = QPointF(u0 * w_src + eps, v1 * h_src - eps)

                d0 = fine_grid[r][c] - origin
                d1 = fine_grid[r][c+1] - origin
                d2 = fine_grid[r+1][c+1] - origin
                d3 = fine_grid[r+1][c] - origin

                t_a = _get_triangle_transform_2d(s0, s1, s2, d0, d1, d2)
                if t_a:
                    p.save()
                    clip_a = QPainterPath()
                    clip_a.addPolygon(QPolygonF([d0, d1, d2]))
                    p.setClipPath(clip_a)
                    p.setTransform(t_a)
                    p.drawImage(0, 0, src)
                    p.restore()

                t_b = _get_triangle_transform_2d(s0, s2, s3, d0, d2, d3)
                if t_b:
                    p.save()
                    clip_b = QPainterPath()
                    clip_b.addPolygon(QPolygonF([d0, d2, d3]))
                    p.setClipPath(clip_b)
                    p.setTransform(t_b)
                    p.drawImage(0, 0, src)
                    p.restore()

        p.end()

        # Aplicar máscara con suave suavizado de bordes (antialiasing) únicamente en el contorno exterior
        outer_pts = []
        for c in range(n): outer_pts.append(fine_grid[0][c] - origin)
        for r in range(n): outer_pts.append(fine_grid[r][n] - origin)
        for c in range(n, 0, -1): outer_pts.append(fine_grid[n][c] - origin)
        for r in range(n, 0, -1): outer_pts.append(fine_grid[r][0] - origin)

        outer_polygon = QPolygonF(outer_pts)
        outer_path = QPainterPath()
        outer_path.addPolygon(outer_polygon)

        mask = QImage(out_w, out_h, QImage.Format.Format_ARGB32_Premultiplied)
        mask.fill(Qt.GlobalColor.transparent)
        pm = QPainter(mask)
        pm.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pm.fillPath(outer_path, QColor(255, 255, 255, 255))
        pm.end()

        p_final = QPainter(result)
        p_final.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        p_final.drawImage(0, 0, mask)
        p_final.end()

        engine.floating_image = result
        engine.original_image_pos = QPointF(out_x, out_y)

        c0, c1, c2, c3 = fine_grid[0][0], fine_grid[0][n], fine_grid[n][n], fine_grid[n][0]

        poly_path = QPainterPath()
        poly_path.addPolygon(QPolygonF([c0, c1, c2, c3, c0]))
        engine.active_path = poly_path
        engine.active_rect = poly_path.boundingRect()

        cx = (c0.x() + c1.x() + c2.x() + c3.x()) / 4.0
        cy = (c0.y() + c1.y() + c2.y() + c3.y()) / 4.0
        engine.rotation_center = QPointF(cx, cy)

        dx = c1.x() - c0.x()
        dy = c1.y() - c0.y()
        rot_deg = math.degrees(math.atan2(dy, dx)) % 360.0
        engine.total_rotation = rot_deg
        engine.rotation_angle = rot_deg

        w_curr = math.hypot(c1.x() - c0.x(), c1.y() - c0.y())
        h_curr = math.hypot(c3.x() - c0.x(), c3.y() - c0.y())

        raw = engine.original_raw_image or engine.unscaled_floating_image
        if raw and not raw.isNull():
            raw_w = max(1.0, float(raw.width()))
            raw_h = max(1.0, float(raw.height()))
            engine.scale_x = w_curr / raw_w
            engine.scale_y = h_curr / raw_h

        engine.initial_unrotated_rect = QRectF(cx - w_curr / 2.0, cy - h_curr / 2.0, w_curr, h_curr)
        p_unr = QPainterPath()
        p_unr.addRect(engine.initial_unrotated_rect)
        engine.initial_unrotated_path = p_unr

    def draw_preview(self, painter: QPainter, canvas):
        """Renderizado en tiempo real a 200+ FPS directamente con contornos curvos suaves."""
        if not self._is_active or not self._corners or not canvas.selection_engine.unscaled_floating_image:
            return

        src = canvas.selection_engine.unscaled_floating_image
        w_src = float(src.width())
        h_src = float(src.height())

        n = 12 if getattr(self, '_active_handle', self.HANDLE_NONE) != self.HANDLE_NONE else self.GRID_SUBDIVISIONS
        fine_grid = self._evaluate_fine_grid(n)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        eps = 0.05
        for r in range(n):
            v0, v1 = r / float(n), (r + 1) / float(n)
            for c in range(n):
                u0, u1 = c / float(n), (c + 1) / float(n)

                s0 = QPointF(u0 * w_src + eps, v0 * h_src + eps)
                s1 = QPointF(u1 * w_src - eps, v0 * h_src + eps)
                s2 = QPointF(u1 * w_src - eps, v1 * h_src - eps)
                s3 = QPointF(u0 * w_src + eps, v1 * h_src - eps)

                d0 = fine_grid[r][c]
                d1 = fine_grid[r][c+1]
                d2 = fine_grid[r+1][c+1]
                d3 = fine_grid[r+1][c]

                t_a = _get_triangle_transform_2d(s0, s1, s2, d0, d1, d2)
                if t_a:
                    painter.save()
                    clip_a = QPainterPath()
                    clip_a.addPolygon(QPolygonF([d0, d1, d2]))
                    painter.setClipPath(clip_a)
                    painter.setTransform(t_a, True)
                    painter.drawImage(0, 0, src)
                    painter.restore()

                t_b = _get_triangle_transform_2d(s0, s2, s3, d0, d2, d3)
                if t_b:
                    painter.save()
                    clip_b = QPainterPath()
                    clip_b.addPolygon(QPolygonF([d0, d2, d3]))
                    painter.setClipPath(clip_b)
                    painter.setTransform(t_b, True)
                    painter.drawImage(0, 0, src)
                    painter.restore()

        painter.restore()

    def mouse_press(self, canvas, event, color_activo=None):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        doc_pos = event.position()

        if not self._is_active:
            has_floating = bool(canvas.selection_engine.floating_image and not canvas.selection_engine.floating_image.isNull())
            if canvas.selection_engine.has_selection() or has_floating:
                if self._lift_selection(canvas):
                    canvas.update()
            return

        h = self._hit_test(doc_pos, canvas.scale_factor)
        if h != self.HANDLE_NONE:
            self._active_handle = h
            self._last_doc_pos = QPointF(doc_pos)
        else:
            self._commit(canvas)

    def mouse_move(self, canvas, event, color_activo=None):
        canvas.actualizar_cursor_herramienta(self)
        if not self._is_active or self._active_handle == self.HANDLE_NONE or self._last_doc_pos is None:
            return

        doc_pos = event.position()
        delta = doc_pos - self._last_doc_pos
        self._last_doc_pos = QPointF(doc_pos)

        if self._active_handle == self.HANDLE_MOVE:
            # Arrastre del punto de anclaje: desplaza todo el objeto sin modificar su forma ni curvas
            for i in range(len(self._corners)):
                self._corners[i] += delta
        else:
            r0, c0 = self._active_handle
            corner_idx = None
            if (r0, c0) == (0, 0): corner_idx = 0
            elif (r0, c0) == (0, 3): corner_idx = 1
            elif (r0, c0) == (3, 3): corner_idx = 2
            elif (r0, c0) == (3, 0): corner_idx = 3

            if corner_idx is not None:
                # Arrastre de Esquina: Deforma la envolvente 2D global de la imagen
                self._corners[corner_idx] += delta
            else:
                # Arrastre de Borde o Interior: Curva suavemente la malla 2D local
                for r in range(4):
                    dr = abs(r - r0) / 3.0
                    wr = 0.5 * (1.0 + math.cos(math.pi * dr))
                    for c in range(4):
                        dc = abs(c - c0) / 3.0
                        wc = 0.5 * (1.0 + math.cos(math.pi * dc))
                        w = wr * wc
                        self._offsets[r][c] += delta * w

        canvas.update()

    def mouse_release(self, canvas, event, color_activo=None):
        if self._active_handle != self.HANDLE_NONE:
            self._save_undo_step()
            self._apply_warp(canvas)
        self._active_handle = self.HANDLE_NONE
        self._last_doc_pos = None
        canvas.actualizar_cursor_herramienta(self)
        canvas.update()

    def key_press(self, canvas, event, color_activo=None):
        if not self._is_active:
            return False
        key = event.key()
        mods = event.modifiers()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._commit(canvas)
            return True
        if key == Qt.Key.Key_Escape:
            self._cancel(canvas)
            return True
        if key == Qt.Key.Key_Z and (mods & Qt.KeyboardModifier.ControlModifier):
            if mods & Qt.KeyboardModifier.ShiftModifier:
                return self.redo_step(canvas)
            else:
                return self.undo_step(canvas)
        if key == Qt.Key.Key_Y and (mods & Qt.KeyboardModifier.ControlModifier):
            return self.redo_step(canvas)
        return False

    def _commit(self, canvas):
        if not self._is_active:
            return

        engine = canvas.selection_engine
        self._apply_warp(canvas)

        layer = canvas.layer_mgr.get_active_layer()
        if layer and layer.image:
            is_new = getattr(self, '_is_new_content', False) or getattr(engine, 'is_new_content', False)
            if is_new and hasattr(canvas, 'floating_initial_canvas') and canvas.floating_initial_canvas:
                layer.image = canvas.floating_initial_canvas.copy()
            elif self._layer_backup:
                layer.image = self._layer_backup.copy()

            if not is_new:
                use_trans = getattr(layer, 'transparent', True) if layer else True

                bg_col = getattr(canvas, 'color_secundario', QColor(255, 255, 255))
                if not isinstance(bg_col, QColor) or not bg_col.isValid():
                    bg_col = QColor(255, 255, 255)

                p_clear = QPainter(layer.image)
                if use_trans:
                    p_clear.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                    if self._path_backup and not self._path_backup.isEmpty():
                        p_clear.setClipPath(self._path_backup)
                        p_clear.fillRect(self._path_backup.boundingRect(), Qt.GlobalColor.transparent)
                    elif hasattr(self, '_initial_corners') and self._initial_corners and len(self._initial_corners) >= 4:
                        poly_clear = QPainterPath()
                        poly_clear.addPolygon(QPolygonF(self._initial_corners))
                        p_clear.setClipPath(poly_clear)
                        p_clear.fillRect(poly_clear.boundingRect(), Qt.GlobalColor.transparent)
                    elif self._original_pos and self._original_image:
                        r_orig = QRectF(self._original_pos.x(), self._original_pos.y(),
                                        float(self._original_image.width()),
                                        float(self._original_image.height()))
                        p_clear.fillRect(r_orig, Qt.GlobalColor.transparent)
                else:
                    p_clear.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
                    if self._path_backup and not self._path_backup.isEmpty():
                        p_clear.setClipPath(self._path_backup)
                        p_clear.fillRect(self._path_backup.boundingRect(), bg_col)
                    elif hasattr(self, '_initial_corners') and self._initial_corners and len(self._initial_corners) >= 4:
                        poly_clear = QPainterPath()
                        poly_clear.addPolygon(QPolygonF(self._initial_corners))
                        p_clear.setClipPath(poly_clear)
                        p_clear.fillRect(poly_clear.boundingRect(), bg_col)
                    elif self._original_pos and self._original_image:
                        r_orig = QRectF(self._original_pos.x(), self._original_pos.y(),
                                        float(self._original_image.width()),
                                        float(self._original_image.height()))
                        p_clear.fillRect(r_orig, bg_col)
                p_clear.end()

            if engine.floating_image and not engine.floating_image.isNull():
                p = QPainter(layer.image)
                p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
                p.drawImage(engine.original_image_pos, engine.floating_image)
                p.end()

        engine.floating_image = None
        engine.unscaled_floating_image = None
        engine.clear_selection()
        self._reset_state()
        if hasattr(canvas.layer_mgr, 'invalidate_cache'):
            canvas.layer_mgr.invalidate_cache()
        canvas.push_document_state("Transformar", force=True)
        canvas.update()

    def cancel_transform(self, canvas) -> bool:
        if self._is_active:
            self._cancel(canvas)
            return True
        return False

    def _cancel(self, canvas):
        layer = canvas.layer_mgr.get_active_layer()
        if layer and layer.image and self._layer_backup:
            layer.image = self._layer_backup.copy()
        elif layer and layer.image and self._original_image:
            p = QPainter(layer.image)
            p.drawImage(self._original_pos, self._original_image)
            p.end()

        engine = canvas.selection_engine
        engine.floating_image = None
        engine.unscaled_floating_image = None
        engine.clear_selection()
        if self._path_backup:
            engine.set_path(QPainterPath(self._path_backup))

        self._reset_state()
        if hasattr(canvas.layer_mgr, 'invalidate_cache'):
            canvas.layer_mgr.invalidate_cache()
        from core.i18n import t
        canvas.push_document_state(t("Cancelar transformación"), force=True)
        canvas.update()

    def draw_handles(self, painter, canvas):
        if not self._is_active or not self._corners:
            return

        sf = max(0.001, canvas.scale_factor)
        handle_size = 7.0 / sf
        half_h = handle_size / 2.0

        n = self.GRID_SUBDIVISIONS
        fine_grid = self._evaluate_fine_grid(n)
        ctrl_grid = self._get_control_grid()

        pen_cage = QPen(QColor(0, 120, 215), 1.0, Qt.PenStyle.SolidLine)
        pen_cage.setCosmetic(True)

        pen_grid = QPen(QColor(0, 120, 215, 180), 1.0, Qt.PenStyle.DashLine)
        pen_grid.setCosmetic(True)

        # Dibujar líneas guía curvadas suaves siguiendo la superficie bicúbica
        for r in range(4):
            sub_r = int(round(r * n / 3.0))
            painter.setPen(pen_cage if r in (0, 3) else pen_grid)
            for c in range(n):
                painter.drawLine(fine_grid[sub_r][c], fine_grid[sub_r][c+1])

        for c in range(4):
            sub_c = int(round(c * n / 3.0))
            painter.setPen(pen_cage if c in (0, 3) else pen_grid)
            for r in range(n):
                painter.drawLine(fine_grid[r][sub_c], fine_grid[r+1][sub_c])

        # 1. Dibujar el punto de anclaje de movimiento (Move Anchor Handle)
        top_center, move_pt, move_rect = self._get_move_handle_info(canvas.scale_factor)
        if not move_rect.isEmpty():
            pen_stem = QPen(QColor(0, 120, 215), 1.0, Qt.PenStyle.DashLine)
            pen_stem.setCosmetic(True)
            painter.setPen(pen_stem)
            painter.drawLine(top_center, move_pt)

            pen_move_border = QPen(QColor(0, 50, 160), 1.0, Qt.PenStyle.SolidLine)
            pen_move_border.setCosmetic(True)
            painter.setPen(pen_move_border)
            painter.setBrush(QBrush(QColor(0, 120, 215)))
            painter.drawRect(move_rect)

        # 2. Dibujar los 16 tiradores de la malla 4x4
        pen_border = QPen(QColor(0, 120, 215), 1.0, Qt.PenStyle.SolidLine)
        pen_border.setCosmetic(True)

        for r in range(4):
            for c in range(4):
                pt = ctrl_grid[r][c]
                r_rect = QRectF(pt.x() - half_h, pt.y() - half_h, handle_size, handle_size)

                painter.setPen(pen_border)
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.drawRect(r_rect)
