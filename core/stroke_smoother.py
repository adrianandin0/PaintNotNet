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
    Genera puntos interpolados a lo largo del trazo con continuidad C^1 centrípeda sin esquinas angulosas ni sobre-impulsos (overshoot).
    Usa la formulación de Catmull-Rom Centrípeda (alpha=0.5) adaptativa para trayectorias de alta velocidad.

    - pts: Lista de QPointF/QPoint acumulados en el trazo.
    - start_idx: Índice del último segmento procesado.
    - is_final: True si el mouse se soltó (mouse_release), forzando el dibujado del último tramo.
    - step_px: Distancia entre puntos de muestra en píxeles.

    Devuelve: (lista_de_tuples, nuevo_start_idx) donde cada tupla es (QPointF(x,y), dist_segmento)
    """
    n = len(pts)
    if n < 2:
        return [], start_idx

    end_idx = (n - 1) if is_final else (n - 2)
    if end_idx <= start_idx:
        return [], start_idx

    interpolated_points = []

    for i in range(start_idx, end_idx):
        p0 = pts[max(0, i - 1)]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[min(n - 1, i + 2)]

        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        dist = math.hypot(dx, dy)
        if dist < 0.0001:
            continue

        steps = max(1, int(math.ceil(dist / max(0.2, step_px))))

        # Parámetros de knot intervals para Catmull-Rom centrípeda (alpha=0.5)
        d01 = max(1e-4, math.hypot(p1.x() - p0.x(), p1.y() - p0.y())) ** alpha
        d12 = max(1e-4, math.hypot(p2.x() - p1.x(), p2.y() - p1.y())) ** alpha
        d23 = max(1e-4, math.hypot(p3.x() - p2.x(), p3.y() - p2.y())) ** alpha

        t0 = 0.0
        t1 = t0 + d01
        t2 = t1 + d12
        t3 = t2 + d23

        dt10 = t1 - t0
        dt21 = t2 - t1
        dt32 = t3 - t2
        dt20 = t2 - t0
        dt31 = t3 - t1

        for s in range(steps):
            t_norm = (s + 1.0) / float(steps)
            t = t1 + dt21 * t_norm

            # Pirámide de Barry and Goldman para evaluación de Catmull-Rom Centrípeda
            a1_x = (t1 - t) / dt10 * p0.x() + (t - t0) / dt10 * p1.x()
            a1_y = (t1 - t) / dt10 * p0.y() + (t - t0) / dt10 * p1.y()

            a2_x = (t2 - t) / dt21 * p1.x() + (t - t1) / dt21 * p2.x()
            a2_y = (t2 - t) / dt21 * p1.y() + (t - t1) / dt21 * p2.y()

            a3_x = (t3 - t) / dt32 * p2.x() + (t - t2) / dt32 * p3.x()
            a3_y = (t3 - t) / dt32 * p2.y() + (t - t2) / dt32 * p3.y()

            b1_x = (t2 - t) / dt20 * a1_x + (t - t0) / dt20 * a2_x
            b1_y = (t2 - t) / dt20 * a1_y + (t - t0) / dt20 * a2_y

            b2_x = (t3 - t) / dt31 * a2_x + (t - t1) / dt31 * a3_x
            b2_y = (t3 - t) / dt31 * a2_y + (t - t1) / dt31 * a3_y

            cx = (t2 - t) / dt21 * b1_x + (t - t1) / dt21 * b2_x
            cy = (t2 - t) / dt21 * b1_y + (t - t1) / dt21 * b2_y

            interpolated_points.append((QPointF(cx, cy), dist))

    new_start_idx = end_idx
    return interpolated_points, new_start_idx
