"""
effects_panel.py — Panel lateral de Efectos (Borde, Resplandor, Sombra).

Cada efecto tiene:
  - Checkbox de activación
  - SpinBox de Ancho
  - 1 slot de color guardable (igual estética que panel de colores)

El color de cada slot se persiste en QSettings("PaintNotNet", "EffectsPanel").
"""
import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QGroupBox, QCheckBox, QSizePolicy, QAbstractSpinBox
)
from PyQt6.QtGui import QPainter, QBrush, QPen, QColor, QPainterPath
from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QSettings
from core.i18n import t


# Clase auxiliar: botón de slot de color (1 slot por efecto)

class _EffectColorSlot(QPushButton):
    """
    Botón slot de color para el panel de efectos.
    Igual estética que CustomSlotButton del panel de colores:
    muestra cuadrícula de transparencia cuando hay alpha < 255.
    """
    color_changed = pyqtSignal(QColor)

    def __init__(self, parent_panel, settings_key: str):
        super().__init__()
        self._panel = parent_panel
        self._key   = settings_key
        self.settings = QSettings("PaintNotNet", "EffectsPanel")
        self._color: QColor | None = None
        self.setFixedSize(20, 20)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self._cargar()
        self._refresh_tooltip()

    def contextMenuEvent(self, event):
        event.ignore()

    # ---- persistencia --------------------------------------------------

    def _cargar(self):
        val = self.settings.value(self._key, None)
        if val:
            c = QColor(val)
            if c.isValid():
                self._color = c

    def _guardar(self):
        if self._color and self._color.isValid():
            self.settings.setValue(self._key, self._color.name(QColor.NameFormat.HexArgb))
        else:
            self.settings.remove(self._key)

    def mousePressEvent(self, event):
        if event.button() not in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            return

        # Si el usuario presiona Ctrl + Clic en el recuadro de color de efectos
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.set_color_external(None)
            self.color_changed.emit(QColor(0, 0, 0, 0))
            return

        initial = self.get_color()
        from gui.dialogo_color import SingleColorPickerDialog
        dialog = SingleColorPickerDialog(initial_color=initial, parent=self, show_saved=False)
        dialog.color_preview_changed.connect(self._on_preview_color)

        from PyQt6.QtWidgets import QDialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._color = dialog.get_color()
            self._guardar()
            self.update()
            self._refresh_tooltip()
            self.color_changed.emit(QColor(self._color))
        else:
            self._color = QColor(initial)
            self._guardar()
            self.update()
            self._refresh_tooltip()
            self.color_changed.emit(QColor(initial))
        super().mousePressEvent(event)

    def _on_preview_color(self, color):
        self._color = QColor(color)
        self.update()
        self._refresh_tooltip()
        self.color_changed.emit(QColor(color))

    # ---- propiedades ---------------------------------------------------

    def get_color(self) -> QColor:
        return QColor(self._color) if self._color else QColor(255, 255, 255)

    def set_color_external(self, color: QColor | None):
        self._color = QColor(color) if color else None
        self._guardar()
        self.update()
        self._refresh_tooltip()

    # ---- pintura con ajedrez de alpha ----------------------------------

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QPen
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        w, h = self.width(), self.height()

        if self._color is not None and self._color.isValid():
            # 1. Cuadrícula de transparencia (4×4 px)
            sq = 4
            c1 = QColor(255, 255, 255)
            c2 = QColor(200, 200, 200)
            for y in range(0, h, sq):
                for x in range(0, w, sq):
                    c = c1 if ((x // sq) + (y // sq)) % 2 == 0 else c2
                    painter.fillRect(x, y, sq, sq, c)
            # 2. Color con alpha real encima
            painter.fillRect(0, 0, w, h, self._color)
            # 3. Borde
            painter.setPen(QPen(QColor(160, 160, 160), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(0, 0, w - 1, h - 1)
        else:
            # Slot vacío: adaptable al tema (igual que panel de colores)
            from core.theme import ThemeManager
            tm = ThemeManager()
            if tm.resolver_nombre_tema(tm.current_theme) == "Claro":
                painter.fillRect(0, 0, w, h, QColor(225, 225, 225))
                pen = QPen(QColor(120, 120, 120), 1, Qt.PenStyle.SolidLine)
            else:
                painter.fillRect(0, 0, w, h, QColor(35, 35, 35))
                pen = QPen(QColor(100, 100, 100), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(0, 0, w - 1, h - 1)

    def _refresh_tooltip(self):
        if self._color is None or not self._color.isValid():
            self.setToolTip(t("Slot vacío: Clic para Guardar | Slot lleno: Clic para Usar (Shift+Clic Reemplazar, Ctrl+Clic Eliminar)"))
        else:
            self.setToolTip(t("Color guardado (Shift+Clic Reemplazar, Ctrl+Clic Eliminar)"))

    # compatibilidad con código antiguo
    def _refresh_ui(self):
        self._refresh_tooltip()
        self.update()


# Clase auxiliar: rueda de dirección de luz (igual a la del antiguo text_panel)

class _LightDirectionWidget(QWidget):
    """Control circular 2D compacto para la dirección de la sombra."""
    lightVectorChanged = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(32, 32)
        self.light_x = 0.0
        self.light_y = 0.0

    def mouseDoubleClickEvent(self, event):
        self.light_x = 0.0
        self.light_y = 0.0
        self.lightVectorChanged.emit(self.light_x, self.light_y)
        self.update()

    def paintEvent(self, event):
        from core.theme import ThemeManager
        tm = ThemeManager()
        is_light = (tm.resolver_nombre_tema(tm.current_theme) == "Claro")

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        radius = (self.width() - 4) / 2.0
        center = QPointF(self.width() / 2.0, self.height() / 2.0)

        bg_col     = QColor("#E0E0E0") if is_light else QColor("#3C3C3C")
        border_col = QColor("#A0A0A0") if is_light else QColor("#686868")
        cross_col  = QColor("#B0B0B0") if is_light else QColor("#5C5C5C")

        painter.setBrush(QBrush(bg_col))
        painter.setPen(QPen(border_col, 1))
        painter.drawEllipse(center, radius, radius)

        painter.setPen(QPen(cross_col, 1, Qt.PenStyle.DashLine))
        painter.drawLine(int(center.x()), 2, int(center.x()), self.height() - 2)
        painter.drawLine(2, int(center.y()), self.width() - 2, int(center.y()))

        ix = center.x() + (self.light_x * radius)
        iy = center.y() + (self.light_y * radius)
        painter.setBrush(QBrush(QColor("#0078D7")))
        painter.setPen(QPen(QColor(40, 40, 40) if is_light else Qt.GlobalColor.white, 1))
        painter.drawEllipse(QPointF(ix, iy), 4.0, 4.0)

    def mousePressEvent(self, event):
        self._update_from_pos(event.position().toPoint())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._update_from_pos(event.position().toPoint())

    def _update_from_pos(self, pos):
        cx, cy = self.width() / 2.0, self.height() / 2.0
        radius  = (self.width() - 4) / 2.0
        dx = (pos.x() - cx) / radius
        dy = (pos.y() - cy) / radius
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 1.0:
            dx /= dist
            dy /= dist
        self.light_x = dx
        self.light_y = dy
        self.lightVectorChanged.emit(self.light_x, self.light_y)
        self.update()


# Panel principal

class EffectsPanelWidget(QWidget):
    """Panel lateral de Efectos: Borde, Resplandor, Sombra."""
    effects_changed = pyqtSignal(dict)

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window

        lbl_style   = "color: #E8E8E8; font-size: 11px; font-weight: normal;"
        group_style = (
            "QGroupBox { font-size: 11px; color: #E8E8E8; font-weight: normal; "
            "margin-top: 10px; padding: 4px 4px 4px 4px; "
            "border: 1px solid #3A3A3A; border-radius: 3px; } "
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; "
            "padding: 0 4px; color: #E8E8E8; background-color: #5C5C5C; }"
        )
        spin_style = "font-size: 11px; color: #EDEDED;"
        chk_style  = "color: #E8E8E8; font-size: 11px;"

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── BORDE ─────────────────────────────────────────────────────────
        self.group_borde = QGroupBox(t("Borde"))
        self.group_borde.setStyleSheet(group_style)
        borde_l = QVBoxLayout()
        borde_l.setContentsMargins(2, 6, 2, 4)
        borde_l.setSpacing(3)

        borde_row = QHBoxLayout()
        borde_row.setSpacing(4)
        self.chk_borde = QCheckBox(t("Ancho:"))
        self.chk_borde.setStyleSheet(chk_style)
        self.chk_borde.toggled.connect(self._emit)
        self.spin_borde = QSpinBox()
        self.spin_borde.setRange(1, 200)
        self.spin_borde.setValue(4)
        self.spin_borde.setFixedHeight(20)
        self.spin_borde.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_borde.setStyleSheet(spin_style)
        self.spin_borde.valueChanged.connect(self._emit)
        self.slot_borde = _EffectColorSlot(self, "borde_color")
        self.slot_borde.color_changed.connect(self._emit)
        borde_row.addWidget(self.chk_borde)
        borde_row.addWidget(self.spin_borde)
        borde_row.addWidget(self.slot_borde)
        borde_l.addLayout(borde_row)
        self.group_borde.setLayout(borde_l)
        layout.addWidget(self.group_borde)

        # ── RESPLANDOR ────────────────────────────────────────────────────
        self.group_glow = QGroupBox(t("Resplandor"))
        self.group_glow.setStyleSheet(group_style)
        glow_l = QVBoxLayout()
        glow_l.setContentsMargins(2, 6, 2, 4)
        glow_l.setSpacing(3)

        glow_row = QHBoxLayout()
        glow_row.setSpacing(4)
        self.chk_glow = QCheckBox(t("Ancho:"))
        self.chk_glow.setStyleSheet(chk_style)
        self.chk_glow.toggled.connect(self._emit)
        self.spin_glow = QSpinBox()
        self.spin_glow.setRange(1, 200)
        self.spin_glow.setValue(10)
        self.spin_glow.setFixedHeight(20)
        self.spin_glow.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_glow.setStyleSheet(spin_style)
        self.spin_glow.valueChanged.connect(self._emit)
        self.slot_glow = _EffectColorSlot(self, "glow_color")
        self.slot_glow.color_changed.connect(self._emit)
        glow_row.addWidget(self.chk_glow)
        glow_row.addWidget(self.spin_glow)
        glow_row.addWidget(self.slot_glow)
        glow_l.addLayout(glow_row)
        self.group_glow.setLayout(glow_l)
        layout.addWidget(self.group_glow)

        # ── SOMBRA ────────────────────────────────────────────────────────
        self.group_shadow = QGroupBox(t("Sombra"))
        self.group_shadow.setStyleSheet(group_style)
        shadow_l = QVBoxLayout()
        shadow_l.setContentsMargins(2, 6, 2, 4)
        shadow_l.setSpacing(3)

        # Rueda de dirección de luz (centrada)
        light_row = QHBoxLayout()
        light_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.light_widget = _LightDirectionWidget()
        self.light_widget.lightVectorChanged.connect(self._emit)
        light_row.addWidget(self.light_widget)
        shadow_l.addLayout(light_row)

        shadow_row = QHBoxLayout()
        shadow_row.setSpacing(4)
        self.chk_shadow = QCheckBox(t("Ancho:"))
        self.chk_shadow.setStyleSheet(chk_style)
        self.chk_shadow.toggled.connect(self._emit)
        self.spin_shadow = QSpinBox()
        self.spin_shadow.setRange(1, 200)
        self.spin_shadow.setValue(10)
        self.spin_shadow.setFixedHeight(20)
        self.spin_shadow.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_shadow.setStyleSheet(spin_style)
        self.spin_shadow.valueChanged.connect(self._emit)
        self.slot_shadow = _EffectColorSlot(self, "shadow_color")
        self.slot_shadow.color_changed.connect(self._emit)
        shadow_row.addWidget(self.chk_shadow)
        shadow_row.addWidget(self.spin_shadow)
        shadow_row.addWidget(self.slot_shadow)
        shadow_l.addLayout(shadow_row)
        self.group_shadow.setLayout(shadow_l)
        layout.addWidget(self.group_shadow)

        layout.addStretch()
        self.setLayout(layout)
        self.setFixedWidth(155)

        self.actualizar_estilo_tema()

    def actualizar_estilo_tema(self):
        from core.theme import ThemeManager
        tm = ThemeManager()
        is_dark = (tm.resolver_nombre_tema(tm.current_theme) == "Oscuro")

        txt_col  = "#EDEDED" if is_dark else "#222222"
        brd_col  = "#3A3A3A" if is_dark else "#B0B0B0"
        title_bg = "#5C5C5C" if is_dark else "#D0D0D0"
        title_fg = "#E8E8E8" if is_dark else "#222222"

        group_style = f"""
            QGroupBox {{
                font-size: 11px;
                color: {txt_col};
                font-weight: normal;
                margin-top: 10px;
                padding: 4px 4px 4px 4px;
                border: 1px solid {brd_col};
                border-radius: 3px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 4px;
                color: {title_fg};
                background-color: {title_bg};
            }}
        """
        for g in (self.group_borde, self.group_glow, self.group_shadow):
            g.setStyleSheet(group_style)

        chk_style = f"color: {txt_col}; font-size: 11px;"
        for chk in (self.chk_borde, self.chk_glow, self.chk_shadow):
            chk.setStyleSheet(chk_style)

        spin_style = f"font-size: 11px;"
        for spin in (self.spin_borde, self.spin_glow, self.spin_shadow):
            spin.setStyleSheet(spin_style)

        self.light_widget.update()

    # Config

    def obtener_config(self) -> dict:
        """Devuelve la configuración actual de todos los efectos."""
        return {
            "borde_enabled":  self.chk_borde.isChecked(),
            "borde_width":    self.spin_borde.value(),
            "borde_color":    self.slot_borde.get_color(),

            "glow_enabled":   self.chk_glow.isChecked(),
            "glow_width":     self.spin_glow.value(),
            "glow_color":     self.slot_glow.get_color(),

            "shadow_enabled": self.chk_shadow.isChecked(),
            "shadow_width":   self.spin_shadow.value(),
            "shadow_color":   self.slot_shadow.get_color(),
            "shadow_dx":      self.light_widget.light_x,
            "shadow_dy":      self.light_widget.light_y,
        }

    def _emit(self, *_):
        self.effects_changed.emit(self.obtener_config())

    # I18n

    def retraducir_panel(self):
        if hasattr(self, 'group_borde'):
            self.group_borde.setTitle(t("Borde"))
        if hasattr(self, 'group_glow'):
            self.group_glow.setTitle(t("Resplandor"))
        if hasattr(self, 'group_shadow'):
            self.group_shadow.setTitle(t("Sombra"))
        for chk in (self.chk_borde, self.chk_glow, self.chk_shadow):
            chk.setText(t("Ancho:"))
        for slot in (self.slot_borde, self.slot_glow, self.slot_shadow):
            slot._refresh_ui()

    def reset_to_defaults(self):
        settings = QSettings("PaintNotNet", "EffectsPanel")
        settings.clear()

        self.slot_borde.set_color_external(None)
        self.slot_glow.set_color_external(None)
        self.slot_shadow.set_color_external(None)

        self.chk_borde.setChecked(False)
        self.chk_glow.setChecked(False)
        self.chk_shadow.setChecked(False)

        self.spin_borde.setValue(4)
        self.spin_glow.setValue(10)
        self.spin_shadow.setValue(10)

        self.light_widget.light_x = 0.5
        self.light_widget.light_y = 0.5
        self.light_widget.update()

        self._emit()
