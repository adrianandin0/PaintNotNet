"""
menu_ajustes.py — Ajustes de imagen: Tono/Saturación, Brillo/Contraste,
Iluminación y Sombras, Curvas de Color, B&N, Invertir.
"""
import numpy as np
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton,
    QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QSizePolicy, QWidget,
)
from PyQt6.QtGui import (
    QImage, QColor, QIcon, QPainter, QPen, QBrush, QLinearGradient,
    QPainterPath, QConicalGradient,
)
from PyQt6.QtCore import Qt, QEventLoop, QRectF, QPointF, QSize
from core.i18n import t


# ═══════════════════════════════════════════════════════════════════════════════
#  Helpers compartidos
# ═══════════════════════════════════════════════════════════════════════════════

BTN_RESET_SS = """
    QPushButton {
        background: transparent;
        border: none;
        color: #aaaaaa;
        font-size: 14px;
        padding: 0 2px;
    }
    QPushButton:hover { color: #EDEDED; }
"""

SLIDER_BASE_SS = """
    QSlider::groove:horizontal {
        height: 14px;
        border-radius: 7px;
        margin: 0px;
    }
    QSlider::handle:horizontal {
        width: 16px;
        height: 20px;
        margin: -3px 0;
        background: #0078D7;
        border-radius: 4px;
    }
    QSlider::handle:horizontal:hover { background: #1a8fe8; }
"""


def _make_reset_btn(tooltip="Reset"):
    btn = QPushButton("↺")
    btn.setFixedSize(22, 22)
    btn.setToolTip(tooltip)
    btn.setStyleSheet(BTN_RESET_SS)
    return btn


def _apply_to_canvas(canvas, img, is_floating):
    if is_floating:
        canvas.selection_engine.floating_image = img
        if canvas.selection_engine.unscaled_floating_image:
            canvas.selection_engine.unscaled_floating_image = img.copy()
    else:
        canvas.layer_mgr.buffer = img
    canvas.update()


def _get_orig(canvas, is_floating):
    if is_floating:
        return canvas.selection_engine.floating_image.copy()
    return canvas.layer_mgr.buffer.copy()


def _unpremultiply(arr):
    """Des-premultiplica los canales BGRA (ARGB32_Premultiplied) a float32 Straight en el rango 0..255.
    Retorna (b_straight, g_straight, r_straight, a_float, mask).
    Píxeles con A == 0 se fijan rigurosamente a (0, 0, 0).
    """
    b = arr[:, :, 0].astype(np.float32)
    g = arr[:, :, 1].astype(np.float32)
    r = arr[:, :, 2].astype(np.float32)
    a = arr[:, :, 3].astype(np.float32)

    mask = a > 0
    alpha_inv = np.zeros_like(a)
    alpha_inv[mask] = 255.0 / a[mask]

    b_straight = np.zeros_like(b)
    g_straight = np.zeros_like(g)
    r_straight = np.zeros_like(r)

    b_straight[mask] = np.clip(b[mask] * alpha_inv[mask], 0.0, 255.0)
    g_straight[mask] = np.clip(g[mask] * alpha_inv[mask], 0.0, 255.0)
    r_straight[mask] = np.clip(r[mask] * alpha_inv[mask], 0.0, 255.0)

    return b_straight, g_straight, r_straight, a, mask


def _repremultiply(arr, b_straight, g_straight, r_straight, a, mask):
    """Re-premultiplica los colores des-premultiplicados ajustados por el canal Alpha original.
    Garantiza que ningún canal supere su límite de Alfa (0 <= R,G,B <= A) y que los floats
    se recorten antes de convertirse a uint8, evitando desbordamientos y ruido de neón.
    """
    b_straight = np.clip(b_straight, 0.0, 255.0)
    g_straight = np.clip(g_straight, 0.0, 255.0)
    r_straight = np.clip(r_straight, 0.0, 255.0)

    alpha_scale = a / 255.0

    b_final = np.zeros_like(b_straight)
    g_final = np.zeros_like(g_straight)
    r_final = np.zeros_like(r_straight)

    b_final[mask] = np.clip(b_straight[mask] * alpha_scale[mask], 0.0, a[mask])
    g_final[mask] = np.clip(g_straight[mask] * alpha_scale[mask], 0.0, a[mask])
    r_final[mask] = np.clip(r_straight[mask] * alpha_scale[mask], 0.0, a[mask])

    arr[:, :, 0] = np.round(b_final).astype(np.uint8)
    arr[:, :, 1] = np.round(g_final).astype(np.uint8)
    arr[:, :, 2] = np.round(r_final).astype(np.uint8)


# ═══════════════════════════════════════════════════════════════════════════════
#  Slider con gradiente de color
# ═══════════════════════════════════════════════════════════════════════════════

class GradientSlider(QSlider):
    """QSlider horizontal con una barra de gradiente personalizable."""

    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self._gradient_stops: list[tuple[float, QColor]] = []

    def set_gradient_stops(self, stops: list[tuple[float, QColor]]):
        self._gradient_stops = stops
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtWidgets import QStyleOptionSlider, QStyle
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dibujar la barra de gradiente
        groove_rect = QRectF(8, self.height() / 2 - 7, self.width() - 16, 14)
        radius = 7.0

        if self._gradient_stops:
            grad = QLinearGradient(groove_rect.left(), 0, groove_rect.right(), 0)
            for pos, color in self._gradient_stops:
                grad.setColorAt(pos, color)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(groove_rect, radius, radius)
        else:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(80, 80, 80)))
            p.drawRoundedRect(groove_rect, radius, radius)

        # Borde sutil
        p.setPen(QPen(QColor(0, 0, 0, 60), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(groove_rect, radius, radius)

        # Handle
        val_range = self.maximum() - self.minimum()
        ratio = (self.value() - self.minimum()) / val_range if val_range else 0.5
        hx = groove_rect.left() + ratio * groove_rect.width()
        hy = self.height() / 2
        hw, hh = 12, 20

        p.setPen(QPen(QColor(0, 0, 0, 120), 1))
        p.setBrush(QBrush(QColor(0, 120, 215)))
        p.drawRoundedRect(QRectF(hx - hw / 2, hy - hh / 2, hw, hh), 3, 3)
        p.end()


# ═══════════════════════════════════════════════════════════════════════════════
#  Fila de slider con label, valor numérico y botón de reset
# ═══════════════════════════════════════════════════════════════════════════════

class SliderRow(QWidget):
    """Fila completa: label / slider con gradiente / spinbox / botón reset."""

    def __init__(self, label: str, mn: int, mx: int, default: int,
                 suffix: str = "", use_double: bool = False,
                 double_step: float = 0.01,
                 gradient_stops: list = None, parent=None):
        super().__init__(parent)
        self._default = default
        self._suffix = suffix

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(2)

        # Label
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size:11px;")
        layout.addWidget(lbl)

        # Fila de control
        row = QHBoxLayout()
        row.setSpacing(4)

        self.slider = GradientSlider()
        self.slider.setRange(mn, mx)
        self.slider.setValue(default)
        self.slider.setMinimumWidth(160)
        if gradient_stops:
            self.slider.set_gradient_stops(gradient_stops)
        row.addWidget(self.slider, 1)

        if use_double:
            self.spin = QDoubleSpinBox()
            self.spin.setRange(mn, mx)
            self.spin.setSingleStep(double_step)
            self.spin.setDecimals(2)
            self.spin.setValue(default)
        else:
            self.spin = QSpinBox()
            self.spin.setRange(mn, mx)
            self.spin.setValue(default)
        if suffix:
            self.spin.setSuffix(suffix)
        self.spin.setFixedWidth(62)
        self.spin.setStyleSheet("font-size:11px;")
        row.addWidget(self.spin)

        self.btn_reset = _make_reset_btn()
        row.addWidget(self.btn_reset)

        layout.addLayout(row)

        # Conexiones
        self.slider.valueChanged.connect(self._on_slider)
        self.spin.valueChanged.connect(self._on_spin)
        self.btn_reset.clicked.connect(self.reset)

    def _on_slider(self, val):
        self.spin.blockSignals(True)
        self.spin.setValue(val)
        self.spin.blockSignals(False)

    def _on_spin(self, val):
        self.slider.blockSignals(True)
        self.slider.setValue(int(val))
        self.slider.blockSignals(False)

    def value(self):
        return self.spin.value()

    def reset(self):
        self.slider.blockSignals(True)
        self.spin.blockSignals(True)
        self.slider.setValue(self._default)
        self.spin.setValue(self._default)
        self.slider.blockSignals(False)
        self.spin.blockSignals(False)
        # Disparar cambio
        self.slider.valueChanged.emit(self._default)

    def connect_changed(self, fn):
        self.slider.valueChanged.connect(fn)
        self.spin.valueChanged.connect(fn)


def _hue_stops():
    stops = []
    for i in range(361):
        color = QColor.fromHsvF(i / 360, 1.0, 1.0)
        stops.append((i / 360, color))
    return stops


def _sat_stops():
    return [
        (0.0, QColor(128, 128, 128)),
        (0.5, QColor(128, 200, 128)),
        (1.0, QColor(0, 255, 0)),
    ]


def _lightness_stops():
    return [
        (0.0, QColor(0, 0, 0)),
        (0.5, QColor(128, 128, 128)),
        (1.0, QColor(255, 255, 255)),
    ]


# ═══════════════════════════════════════════════════════════════════════════════
#  Base dialog con preview en tiempo real
# ═══════════════════════════════════════════════════════════════════════════════

class _BaseAdjustDialog(QDialog):
    def __init__(self, canvas, title, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setModal(False)

        self.target_is_floating = canvas.asegurar_imagen_flotante()
        self.orig_image = _get_orig(canvas, self.target_is_floating)

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setSpacing(6)
        self._main_layout.setContentsMargins(12, 12, 12, 12)

    def _add_buttons(self):
        l = QHBoxLayout()
        btn_ok = QPushButton(t("Aceptar"))
        btn_cancel = QPushButton(t("Cancelar"))
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        l.addStretch()
        l.addWidget(btn_ok)
        l.addWidget(btn_cancel)
        self._main_layout.addLayout(l)

    def accept(self):
        if self.target_is_floating:
            self.canvas.push_floating_sub_state(self.windowTitle())
        super().accept()

    def reject(self):
        """Cancela: restaura el buffer al estado previo a la apertura del diálogo
        y elimina la entrada del historial que se pushó (sin hacer undo completo,
        para no retroceder al estado anterior a la rotación u otras ops previas)."""
        _apply_to_canvas(self.canvas, self.orig_image.copy(), self.target_is_floating)
        if not self.target_is_floating:
            self.canvas.layer_mgr.buffer = self.orig_image.copy()
            self.canvas.update()
        # Descarta la entrada del historial sin retroceder al estado anterior
        if not self.target_is_floating:
            self.canvas.history_mgr.pop_last_state()
            self.canvas.actualizar_historial_gui()
        super().reject()

    def aplicar_vista_previa(self):
        raise NotImplementedError


# ═══════════════════════════════════════════════════════════════════════════════
#  Diálogo Tono / Saturación / Luminosidad
# ═══════════════════════════════════════════════════════════════════════════════

class DialogoTonoSaturacion(_BaseAdjustDialog):
    def __init__(self, canvas, parent=None):
        super().__init__(canvas, t("Tono / Saturación"), parent)
        self.setFixedWidth(360)

        self.row_tono = SliderRow(
            t("Tono:"), -180, 180, 0, "°",
            gradient_stops=_hue_stops()
        )
        self.row_sat = SliderRow(
            t("Saturación:"), -100, 100, 0,
            gradient_stops=[
                (0.0, QColor(80, 80, 80)),
                (0.5, QColor(120, 120, 200)),
                (1.0, QColor(50, 180, 255)),
            ]
        )
        self.row_lum = SliderRow(
            t("Luminosidad:"), -100, 100, 0,
            gradient_stops=_lightness_stops()
        )

        self._main_layout.addWidget(self.row_tono)
        self._main_layout.addWidget(self.row_sat)
        self._main_layout.addWidget(self.row_lum)
        self._add_buttons()

        self.row_tono.connect_changed(self.aplicar_vista_previa)
        self.row_sat.connect_changed(self.aplicar_vista_previa)
        self.row_lum.connect_changed(self.aplicar_vista_previa)

    def aplicar_vista_previa(self):
        h_shift = self.row_tono.value()
        s_shift = self.row_sat.value()
        l_shift = self.row_lum.value()

        img = self.orig_image.copy()

        if h_shift == 0 and s_shift == 0 and l_shift == 0:
            _apply_to_canvas(self.canvas, img, self.target_is_floating)
            return

        ptr = img.bits()
        ptr.setsize(img.height() * img.bytesPerLine())
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((img.height(), img.width(), 4)).copy()

        b, g, r, a, mask = _unpremultiply(arr)

        if s_shift != 0:
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            sat_factor = max(0.0, 1.0 + s_shift / 100.0 * 1.5)
            r = lum + (r - lum) * sat_factor
            g = lum + (g - lum) * sat_factor
            b = lum + (b - lum) * sat_factor

        if h_shift != 0:
            import math
            rad = math.radians(h_shift)
            cos_a = np.cos(rad)
            sin_a = np.sin(rad)
            sqrt3 = 1.7320508
            r_new = r * (cos_a + (1 - cos_a) / 3) + g * ((1 - cos_a) / 3 - sin_a / sqrt3) + b * ((1 - cos_a) / 3 + sin_a / sqrt3)
            g_new = r * ((1 - cos_a) / 3 + sin_a / sqrt3) + g * (cos_a + (1 - cos_a) / 3) + b * ((1 - cos_a) / 3 - sin_a / sqrt3)
            b_new = r * ((1 - cos_a) / 3 - sin_a / sqrt3) + g * ((1 - cos_a) / 3 + sin_a / sqrt3) + b * (cos_a + (1 - cos_a) / 3)
            r, g, b = r_new, g_new, b_new

        if l_shift != 0:
            factor = l_shift / 100.0 * 255
            r = r + factor
            g = g + factor
            b = b + factor

        _repremultiply(arr, b, g, r, a, mask)

        result = QImage(arr.tobytes(), img.width(), img.height(),
                        img.bytesPerLine(), QImage.Format.Format_ARGB32_Premultiplied)
        _apply_to_canvas(self.canvas, result.copy(), self.target_is_floating)


# ═══════════════════════════════════════════════════════════════════════════════
#  Diálogo Brillo / Contraste
# ═══════════════════════════════════════════════════════════════════════════════

class DialogoBrilloContraste(_BaseAdjustDialog):
    def __init__(self, canvas, parent=None):
        super().__init__(canvas, t("Brillo / Contraste"), parent)
        self.setFixedWidth(360)

        self.row_brillo = SliderRow(
            t("Brillo:"), -100, 100, 0,
            gradient_stops=_lightness_stops()
        )
        self.row_contraste = SliderRow(
            t("Contraste:"), -100, 100, 0,
            gradient_stops=[
                (0.0, QColor(100, 100, 100)),
                (0.5, QColor(128, 128, 128)),
                (1.0, QColor(255, 255, 255)),
            ]
        )

        self._main_layout.addWidget(self.row_brillo)
        self._main_layout.addWidget(self.row_contraste)
        self._add_buttons()

        self.row_brillo.connect_changed(self.aplicar_vista_previa)
        self.row_contraste.connect_changed(self.aplicar_vista_previa)

    def aplicar_vista_previa(self):
        brillo = self.row_brillo.value()
        contraste = self.row_contraste.value()

        img = self.orig_image.copy()

        if brillo == 0 and contraste == 0:
            _apply_to_canvas(self.canvas, img, self.target_is_floating)
            return

        ptr = img.bits()
        ptr.setsize(img.height() * img.bytesPerLine())
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((img.height(), img.width(), 4)).copy()

        b, g, r, a, mask = _unpremultiply(arr)

        if brillo != 0:
            shift = brillo / 100.0 * 128
            r += shift
            g += shift
            b += shift

        if contraste != 0:
            factor = (259 * (contraste + 255)) / (255 * (259 - contraste))
            r = factor * (r - 128) + 128
            g = factor * (g - 128) + 128
            b = factor * (b - 128) + 128

        _repremultiply(arr, b, g, r, a, mask)

        result = QImage(arr.tobytes(), img.width(), img.height(),
                        img.bytesPerLine(), QImage.Format.Format_ARGB32_Premultiplied)
        _apply_to_canvas(self.canvas, result.copy(), self.target_is_floating)


# ═══════════════════════════════════════════════════════════════════════════════
#  Diálogo Iluminación y Sombras
# ═══════════════════════════════════════════════════════════════════════════════

class DialogoIluminacionSombras(_BaseAdjustDialog):
    def __init__(self, canvas, parent=None):
        super().__init__(canvas, t("Iluminación y Sombras"), parent)
        self.setFixedWidth(380)

        self.row_highlights = SliderRow(
            t("Iluminaciones:"), -100, 100, 0,
            gradient_stops=[
                (0.0, QColor(60, 60, 60)),
                (0.5, QColor(180, 180, 180)),
                (1.0, QColor(255, 255, 220)),
            ]
        )
        self.row_shadows = SliderRow(
            t("Sombras:"), -100, 100, 0,
            gradient_stops=[
                (0.0, QColor(0, 0, 30)),
                (0.5, QColor(60, 60, 80)),
                (1.0, QColor(160, 160, 160)),
            ]
        )
        self.row_clarity = SliderRow(
            t("Claridad:"), -100, 100, 0,
            gradient_stops=[
                (0.0, QColor(100, 100, 120)),
                (0.5, QColor(160, 160, 160)),
                (1.0, QColor(220, 220, 255)),
            ]
        )
        self.row_radius = SliderRow(
            t("Radio:"), 1, 200, 30,
            gradient_stops=[
                (0.0, QColor(60, 60, 80)),
                (1.0, QColor(120, 120, 200)),
            ]
        )

        for row in (self.row_highlights, self.row_shadows, self.row_clarity, self.row_radius):
            self._main_layout.addWidget(row)
        self._add_buttons()

        self.row_highlights.connect_changed(self.aplicar_vista_previa)
        self.row_shadows.connect_changed(self.aplicar_vista_previa)
        self.row_clarity.connect_changed(self.aplicar_vista_previa)
        self.row_radius.connect_changed(self.aplicar_vista_previa)

    def aplicar_vista_previa(self):
        highlights = self.row_highlights.value() / 100.0
        shadows = self.row_shadows.value() / 100.0
        clarity = self.row_clarity.value() / 100.0

        img = self.orig_image.copy()

        if highlights == 0 and shadows == 0 and clarity == 0:
            _apply_to_canvas(self.canvas, img, self.target_is_floating)
            return

        ptr = img.bits()
        ptr.setsize(img.height() * img.bytesPerLine())
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((img.height(), img.width(), 4)).copy()

        b, g, r, a, mask = _unpremultiply(arr)

        if highlights != 0 or shadows != 0 or clarity != 0:
            lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0

            if highlights != 0:
                hi_mask = np.clip((lum - 0.5) * 2, 0, 1)
                r += hi_mask * highlights * 80
                g += hi_mask * highlights * 80
                b += hi_mask * highlights * 80

            if shadows != 0:
                sh_mask = np.clip((0.5 - lum) * 2, 0, 1)
                r += sh_mask * shadows * 80
                g += sh_mask * shadows * 80
                b += sh_mask * shadows * 80

            if clarity != 0:
                gray = 0.299 * r + 0.587 * g + 0.114 * b
                factor = 1.0 + clarity * 0.5
                mid = 128.0
                r = mid + (r - mid) * factor
                g = mid + (g - mid) * factor
                b = mid + (b - mid) * factor

        _repremultiply(arr, b, g, r, a, mask)

        result = QImage(arr.tobytes(), img.width(), img.height(),
                        img.bytesPerLine(), QImage.Format.Format_ARGB32_Premultiplied)
        _apply_to_canvas(self.canvas, result.copy(), self.target_is_floating)


# ═══════════════════════════════════════════════════════════════════════════════
#  Widget de curvas de color
# ═══════════════════════════════════════════════════════════════════════════════

CHANNEL_COLORS = {
    "RGB":   QColor(200, 200, 200),
    "R":     QColor(230, 60,  60),
    "G":     QColor(60,  200, 60),
    "B":     QColor(60,  100, 220),
    "Lum":   QColor(200, 200, 200),
}


class CurveWidget(QWidget):
    """Widget interactivo para editar una curva de tonos con puntos de control."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(256, 256)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

        self._points: list[tuple[float, float]] = [(0.0, 0.0), (1.0, 1.0)]
        self._dragging: int | None = None
        self._color = QColor(200, 200, 200)

    def set_color(self, color: QColor):
        self._color = color
        self.update()

    def set_points(self, pts):
        self._points = sorted(pts)
        self.update()

    def get_lut(self) -> np.ndarray:
        """Devuelve una LUT de 256 valores calculada por interpolación monotónica."""
        pts = sorted(self._points)
        if len(pts) < 2:
            return np.arange(256, dtype=np.float32)

        xs = np.array([p[0] * 255 for p in pts], dtype=np.float64)
        ys = np.array([p[1] * 255 for p in pts], dtype=np.float64)
        x_lut = np.arange(256, dtype=np.float64)
        lut = np.interp(x_lut, xs, ys)
        return lut.astype(np.float32)

    def reset(self):
        self._points = [(0.0, 0.0), (1.0, 1.0)]
        self.update()

    # ── painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        W, H = self.width(), self.height()
        margin = 16
        gw = W - 2 * margin
        gh = H - 2 * margin

        from core.theme import ThemeManager
        tm = ThemeManager()
        is_dark = (tm.resolver_nombre_tema(tm.current_theme) == "Oscuro")

        # Fondo
        bg_col = QColor(45, 45, 45) if is_dark else QColor(245, 245, 245)
        p.fillRect(self.rect(), bg_col)

        # Grid
        grid_col = QColor(80, 80, 80) if is_dark else QColor(200, 200, 200)
        p.setPen(QPen(grid_col, 1, Qt.PenStyle.DotLine))
        for i in range(1, 4):
            x = margin + i * gw / 4
            y = margin + i * gh / 4
            p.drawLine(int(x), margin, int(x), margin + gh)
            p.drawLine(margin, int(y), margin + gw, int(y))

        # Diagonal de referencia
        diag_col = QColor(100, 100, 100) if is_dark else QColor(160, 160, 160)
        p.setPen(QPen(diag_col, 1, Qt.PenStyle.DashLine))
        p.drawLine(margin, margin + gh, margin + gw, margin)

        # Curva
        pts_sorted = sorted(self._points)
        if len(pts_sorted) >= 2:
            def to_widget(px, py):
                return QPointF(margin + px * gw, margin + (1 - py) * gh)

            path = QPainterPath()
            first = to_widget(*pts_sorted[0])
            path.moveTo(first)

            if len(pts_sorted) == 2:
                path.lineTo(to_widget(*pts_sorted[1]))
            else:
                for i in range(len(pts_sorted) - 1):
                    p0 = to_widget(*pts_sorted[i])
                    p1 = to_widget(*pts_sorted[i + 1])
                    cx = (p0.x() + p1.x()) / 2
                    path.cubicTo(QPointF(cx, p0.y()), QPointF(cx, p1.y()), p1)

            curve_col = self._color if is_dark else QColor(30, 30, 30)
            p.setPen(QPen(curve_col, 2))
            p.drawPath(path)

            pen = QPen(self._color, 2)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)

        # Puntos de control
        for i, (px, py) in enumerate(pts_sorted):
            wp = to_widget(px, py)
            p.setPen(QPen(QColor(255, 255, 255), 2))
            p.setBrush(QBrush(self._color))
            p.drawEllipse(wp, 5, 5)

        p.end()

    # ── mouse ─────────────────────────────────────────────────────────────────

    def _to_norm(self, pos):
        W, H = self.width(), self.height()
        margin = 16
        gw = W - 2 * margin
        gh = H - 2 * margin
        nx = (pos.x() - margin) / gw
        ny = 1 - (pos.y() - margin) / gh
        return max(0.0, min(1.0, nx)), max(0.0, min(1.0, ny))

    def _find_near(self, pos, threshold=10):
        W, H = self.width(), self.height()
        margin = 16
        gw = W - 2 * margin
        gh = H - 2 * margin
        for i, (px, py) in enumerate(self._points):
            wx = margin + px * gw
            wy = margin + (1 - py) * gh
            if abs(pos.x() - wx) < threshold and abs(pos.y() - wy) < threshold:
                return i
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            idx = self._find_near(event.position())
            if idx is not None:
                self._dragging = idx
            else:
                nx, ny = self._to_norm(event.position())
                self._points.append((nx, ny))
                self._points.sort()
                self._dragging = self._points.index((nx, ny))
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            idx = self._find_near(event.position())
            if idx is not None and len(self._points) > 2:
                # No eliminar los extremos fijos
                if self._points[idx][0] not in (0.0, 1.0):
                    self._points.pop(idx)
                    self.update()

    def mouseMoveEvent(self, event):
        if self._dragging is not None:
            nx, ny = self._to_norm(event.position())
            old_x, old_y = self._points[self._dragging]
            # Mantener extremos en sus límites X
            if old_x == 0.0:
                nx = 0.0
            elif old_x == 1.0:
                nx = 1.0
            self._points[self._dragging] = (nx, ny)
            self._points.sort()
            self.update()
            self.parentWidget().on_curve_changed()

    def mouseReleaseEvent(self, event):
        self._dragging = None


# ═══════════════════════════════════════════════════════════════════════════════
#  Diálogo Curvas de Color
# ═══════════════════════════════════════════════════════════════════════════════

class DialogoCurvas(_BaseAdjustDialog):
    """Editor de curvas de tono con canales RGB individual + Luminosidad."""

    CHANNELS = ["RGB", "R", "G", "B", "Lum"]

    def __init__(self, canvas, parent=None):
        super().__init__(canvas, t("Curvas de Color"), parent)
        self.setMinimumWidth(360)

        # Datos de curva por canal
        self._curves: dict[str, list] = {ch: [(0.0, 0.0), (1.0, 1.0)] for ch in self.CHANNELS}
        self._current_channel = "RGB"

        # Selector de canal
        top_row = QHBoxLayout()
        lbl_ch = QLabel(t("Canal:"))
        lbl_ch.setStyleSheet("font-size:11px; color:#E8E8E8;")
        self.combo_channel = QComboBox()
        ch_labels = {
            "RGB": t("RGB"),
            "R":   t("Rojo"),
            "G":   t("Verde"),
            "B":   t("Azul"),
            "Lum": t("Luminosidad"),
        }
        for ch in self.CHANNELS:
            self.combo_channel.addItem(ch_labels[ch], ch)
        self.combo_channel.currentIndexChanged.connect(self._on_channel_changed)

        btn_reset_curve = QPushButton(t("Restablecer"))
        btn_reset_curve.setFixedHeight(24)
        btn_reset_curve.clicked.connect(self._reset_current_curve)

        top_row.addWidget(lbl_ch)
        top_row.addWidget(self.combo_channel)
        top_row.addStretch()
        top_row.addWidget(btn_reset_curve)
        self._main_layout.addLayout(top_row)

        # Tip
        tip = QLabel(t("Clic derecho para eliminar un punto de control."))
        tip.setStyleSheet("font-size: 10px; color: #888888;")
        self._main_layout.addWidget(tip)

        # Widget de curva
        self.curve_widget = CurveWidget()
        self.curve_widget.set_color(CHANNEL_COLORS["RGB"])
        self._main_layout.addWidget(self.curve_widget)

        self._add_buttons()

    def on_curve_changed(self):
        self._curves[self._current_channel] = list(self.curve_widget._points)
        self.aplicar_vista_previa()

    def _on_channel_changed(self, idx):
        ch = self.combo_channel.itemData(idx)
        # Guardar curva actual
        self._curves[self._current_channel] = list(self.curve_widget._points)
        # Cargar nueva
        self._current_channel = ch
        self.curve_widget.set_color(CHANNEL_COLORS.get(ch, QColor(200, 200, 200)))
        self.curve_widget.set_points(self._curves[ch])

    def _reset_current_curve(self):
        self._curves[self._current_channel] = [(0.0, 0.0), (1.0, 1.0)]
        self.curve_widget.reset()
        self.aplicar_vista_previa()

    def aplicar_vista_previa(self):
        img = self.orig_image.copy()
        ptr = img.bits()
        ptr.setsize(img.height() * img.bytesPerLine())
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((img.height(), img.width(), 4)).copy()

        b, g, r, a, mask = _unpremultiply(arr)

        def lut_for(ch):
            pts = sorted(self._curves[ch])
            xs = np.array([p[0] * 255 for p in pts], dtype=np.float64)
            ys = np.array([p[1] * 255 for p in pts], dtype=np.float64)
            return np.interp(np.arange(256), xs, ys).astype(np.float32)

        lut_rgb = lut_for("RGB")
        b = lut_rgb[np.clip(b, 0, 255).astype(np.uint8)]
        g = lut_rgb[np.clip(g, 0, 255).astype(np.uint8)]
        r = lut_rgb[np.clip(r, 0, 255).astype(np.uint8)]

        lut_b = lut_for("B")
        lut_g = lut_for("G")
        lut_r = lut_for("R")
        b = lut_b[np.clip(b, 0, 255).astype(np.uint8)]
        g = lut_g[np.clip(g, 0, 255).astype(np.uint8)]
        r = lut_r[np.clip(r, 0, 255).astype(np.uint8)]

        lut_lum = lut_for("Lum")
        lum = np.clip(0.114 * b + 0.587 * g + 0.299 * r, 0, 255).astype(np.uint8)
        lum_mapped = lut_lum[lum]
        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = np.where(lum > 0, lum_mapped / np.maximum(lum.astype(np.float32), 1.0), 1.0)
        b = b * ratio
        g = g * ratio
        r = r * ratio

        _repremultiply(arr, b, g, r, a, mask)

        result = QImage(arr.tobytes(), img.width(), img.height(),
                        img.bytesPerLine(), QImage.Format.Format_ARGB32_Premultiplied)
        _apply_to_canvas(self.canvas, result.copy(), self.target_is_floating)


# ═══════════════════════════════════════════════════════════════════════════════
#  MenuAjustes
# ═══════════════════════════════════════════════════════════════════════════════

class MenuAjustes:
    def __init__(self, ventana_principal):
        self.ventana = ventana_principal

    def crear_menu(self, menu_bar):
        self.menu_bar = menu_bar
        self.retraducir_menu()

    def retraducir_menu(self):
        from core.i18n import t
        if hasattr(self, 'menu_ajustes') and self.menu_ajustes:
            self.menu_bar.removeAction(self.menu_ajustes.menuAction())

        self.menu_ajustes = self.menu_bar.addMenu(t("Ajustes"))

        accion_tono_sat = self.menu_ajustes.addAction(
            QIcon("gui/iconos/hue.png"), t("Tono / Saturación..."))
        accion_tono_sat.triggered.connect(self.tono_saturacion)

        accion_brillo_cont = self.menu_ajustes.addAction(
            QIcon("gui/iconos/slidebw.png"), t("Brillo / Contraste..."))
        accion_brillo_cont.triggered.connect(self.brillo_contraste)

        accion_ilum = self.menu_ajustes.addAction(
            QIcon("gui/iconos/light.png"), t("Iluminación y Sombras..."))
        accion_ilum.triggered.connect(self.iluminacion_sombras)

        accion_curvas = self.menu_ajustes.addAction(
            QIcon("gui/iconos/curves.png"), t("Curvas de Color..."))
        accion_curvas.triggered.connect(self.curvas_color)

        self.menu_ajustes.addSeparator()

        accion_bw = self.menu_ajustes.addAction(
            QIcon("gui/iconos/bnw.png"), t("Blanco y Negro"))
        accion_bw.setShortcut("Ctrl+Shift+B")
        accion_bw.triggered.connect(self.blanco_y_negro)

        self.menu_ajustes.addSeparator()

        accion_invertir = self.menu_ajustes.addAction(
            QIcon("gui/iconos/negative.png"), t("Invertir colores"))
        accion_invertir.setShortcut("Ctrl+Shift+I")
        accion_invertir.triggered.connect(self.invertir_colores)

    # ── acciones ──────────────────────────────────────────────────────────────

    def _run_dialog(self, dlg_class, op_name):
        canvas = self.ventana.lienzo
        is_floating = bool(
            canvas.selection_engine.floating_image
            and not canvas.selection_engine.floating_image.isNull()
        )
        if not is_floating:
            canvas.push_document_state(op_name)

        dlg = dlg_class(canvas, self.ventana)
        loop = QEventLoop()
        dlg.accepted.connect(loop.quit)
        dlg.rejected.connect(loop.quit)
        dlg.show()
        loop.exec()
        # Nota: en caso de Cancelar, el propio reject() del diálogo ya restauró
        # el buffer y eliminó la entrada del historial con pop_last_state().
        # No se llama a canvas.undo() aquí para evitar retroceder un paso extra.

    def tono_saturacion(self):
        self._run_dialog(DialogoTonoSaturacion, "Tono / Saturación")

    def brillo_contraste(self):
        self._run_dialog(DialogoBrilloContraste, "Brillo / Contraste")

    def iluminacion_sombras(self):
        self._run_dialog(DialogoIluminacionSombras, "Iluminación y Sombras")

    def curvas_color(self):
        self._run_dialog(DialogoCurvas, "Curvas de Color")

    def blanco_y_negro(self):
        canvas = self.ventana.lienzo
        is_floating = canvas.asegurar_imagen_flotante()
        if not is_floating:
            canvas.push_document_state("Blanco y negro")

        img = canvas.selection_engine.floating_image.copy() if is_floating else canvas.layer_mgr.buffer.copy()
        ptr = img.bits()
        ptr.setsize(img.height() * img.bytesPerLine())
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((img.height(), img.width(), 4)).copy()

        b, g, r, a, mask = _unpremultiply(arr)
        gray = 0.299 * r + 0.587 * g + 0.114 * b
        _repremultiply(arr, gray, gray, gray, a, mask)

        result = QImage(arr.tobytes(), img.width(), img.height(),
                        img.bytesPerLine(), QImage.Format.Format_ARGB32_Premultiplied)
        _apply_to_canvas(canvas, result.copy(), is_floating)
        if not is_floating:
            canvas.actualizar_historial_gui()
        canvas.update()

    def invertir_colores(self):
        canvas = self.ventana.lienzo
        is_floating = canvas.asegurar_imagen_flotante()
        if not is_floating:
            canvas.push_document_state("Invertir colores")

        img = canvas.selection_engine.floating_image.copy() if is_floating else canvas.layer_mgr.buffer.copy()
        ptr = img.bits()
        ptr.setsize(img.height() * img.bytesPerLine())
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((img.height(), img.width(), 4)).copy()

        b, g, r, a, mask = _unpremultiply(arr)
        b_inv = 255.0 - b
        g_inv = 255.0 - g
        r_inv = 255.0 - r
        _repremultiply(arr, b_inv, g_inv, r_inv, a, mask)

        result = QImage(arr.tobytes(), img.width(), img.height(),
                        img.bytesPerLine(), QImage.Format.Format_ARGB32_Premultiplied)
        _apply_to_canvas(canvas, result.copy(), is_floating)
        if not is_floating:
            canvas.actualizar_historial_gui()
        canvas.update()
