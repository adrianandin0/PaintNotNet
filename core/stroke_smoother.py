"""
core/stroke_smoother.py — Motor central de suavizado Bézier y densificación adaptativa por resolución.
Proporciona interpolación continua C^1/C^2 y filtrado de eventos de mouse para eliminar trazos angulosos
en imágenes de alta resolución (4K, 8K, 3805x5707 px).
"""
import math
from PyQt6.QtCore import QPointF, QPoint


def smooth_mouse_input(prev_pos, raw_pos, weight=0.15):
    """
    Aplica filtrado suavizado exponencial (Exponential Moving Average) sobre la coordenada bruta del mouse.
    Elimina micro-variaciones de sensor en ratones de alta frecuencia / pantallas de alta resolución.
    """
    if prev_pos is None:
        return QPointF(raw_pos)
    rx, ry = raw_pos.x(), raw_pos.y()
    px, py = prev_pos.x(), prev_pos.y()
    nx = rx * (1.0 - weight) + px * weight
    ny = ry * (1.0 - weight) + py * weight
    return QPointF(nx, ny)


def generate_smooth_stroke_points(pts, start_idx=0, is_final=False, step_px=1.0, alpha=0.5):
    """
    Genera puntos interpolados a lo largo del trazo utilizando ajuste de curva B-Spline por Puntos Medios
    (Quadratic/Cubic Bezier Midpoint Interpolation), garantizando trazos 100% fluidos, redondos y sin esquinas
    angulosas ni poligonales incluso al dibujar a alta velocidad o en lienzos de alta resolución (4K/8K).

    - pts: Lista de QPointF/QPoint acumulados en el trazo.
    - start_idx: Índice del último segmento procesado.
    - is_final: True si el mouse se soltó (mouse_release), forzando el dibujado del último tramo.
    - step_px: Distancia entre puntos de muestra en píxeles.

    Devuelve: (lista_de_tuples, nuevo_start_idx) donde cada tupla es (QPointF(x,y), dist_segmento)
    """
    n = len(pts)
    if n < 2:
        return [], start_idx

    end_segment = n if is_final else (n - 1)
    if end_segment <= start_idx:
        return [], start_idx

    interpolated_points = []

    for i in range(start_idx, end_segment):
        if i == 0:
            p_start = QPointF(pts[0])
            p_ctrl = QPointF(pts[0])
            p_end = QPointF((pts[0].x() + pts[1].x()) / 2.0, (pts[0].y() + pts[1].y()) / 2.0)
        elif i == n - 1:
            p_start = QPointF((pts[-2].x() + pts[-1].x()) / 2.0, (pts[-2].y() + pts[-1].y()) / 2.0)
            p_ctrl = QPointF(pts[-1])
            p_end = QPointF(pts[-1])
        else:
            p_prev = pts[i - 1]
            p_curr = pts[i]
            p_next = pts[i + 1]

            p_start = QPointF((p_prev.x() + p_curr.x()) / 2.0, (p_prev.y() + p_curr.y()) / 2.0)
            p_ctrl = QPointF(p_curr.x(), p_curr.y())
            p_end = QPointF((p_curr.x() + p_next.x()) / 2.0, (p_curr.y() + p_next.y()) / 2.0)

        # Distancia aproximada del segmento de curva
        d1 = math.hypot(p_ctrl.x() - p_start.x(), p_ctrl.y() - p_start.y())
        d2 = math.hypot(p_end.x() - p_ctrl.x(), p_end.y() - p_ctrl.y())
        dist = max(0.5, d1 + d2)

        steps = max(2, int(math.ceil(dist / max(0.2, step_px))))

        for s in range(steps):
            t = (s + 1.0) / float(steps)
            om = 1.0 - t
            # Fórmula Bézier cuadrática: (1-t)^2 * P_start + 2(1-t)t * P_ctrl + t^2 * P_end
            bx = om * om * p_start.x() + 2.0 * om * t * p_ctrl.x() + t * t * p_end.x()
            by = om * om * p_start.y() + 2.0 * om * t * p_ctrl.y() + t * t * p_end.y()

            interpolated_points.append((QPointF(bx, by), dist))

    new_start_idx = end_segment
    return interpolated_points, new_start_idx
