import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QFontComboBox, QCheckBox, QGroupBox, QColorDialog
)
from PyQt6.QtGui import QFont, QPainter, QBrush, QPen, QColor
from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QSettings
from core.i18n import t


class ShadowColorButton(QPushButton):
    """Botón inteligente para casilleros de sombra con soporte para clic izq, der, Shift y Ctrl."""
    color_interacted = pyqtSignal(Qt.MouseButton, bool, bool)

    def mousePressEvent(self, event):
        is_shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        is_ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        self.color_interacted.emit(event.button(), is_shift, is_ctrl)
        super().mousePressEvent(event)


class LightDirectionWidget(QWidget):
    """Control circular 2D compacto para la dirección de la luz."""
    lightVectorChanged = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(22, 22)
        self.light_x = 0.0
        self.light_y = 0.0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        radius = (self.width() - 4) / 2.0
        center = QPointF(self.width() / 2.0, self.height() / 2.0)

        painter.setBrush(QBrush(QColor("#2B2B2B")))
        painter.setPen(QPen(QColor("#555555"), 1))
        painter.drawEllipse(center, radius, radius)

        painter.setPen(QPen(QColor("#444444"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(int(center.x()), 2, int(center.x()), self.height() - 2)
        painter.drawLine(2, int(center.y()), self.width() - 2, int(center.y()))

        ix = center.x() + (self.light_x * radius)
        iy = center.y() + (self.light_y * radius)

        painter.setBrush(QBrush(QColor("#00AAFF")))
        painter.setPen(QPen(Qt.GlobalColor.white, 1))
        painter.drawEllipse(QPointF(ix, iy), 3.0, 3.0)

    def mousePressEvent(self, event):
        self.update_vector_from_pos(event.position().toPoint())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.update_vector_from_pos(event.position().toPoint())

    def update_vector_from_pos(self, pos):
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        radius = (self.width() - 4) / 2.0

        dx = (pos.x() - center_x) / radius
        dy = (pos.y() - center_y) / radius

        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 1.0:
            dx /= dist
            dy /= dist

        self.light_x = dx
        self.light_y = dy

        self.lightVectorChanged.emit(self.light_x, self.light_y)
        self.update()


class TextPanelWidget(QWidget):
    """Panel de configuración de texto con esfera de sombra elevada."""
    text_config_changed = pyqtSignal(dict)

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window

        lbl_style = "color: #CCCCCC; font-size: 9px; font-weight: normal;"

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- 1. Fuente y Tamaño ---
        self.lbl_fuente = QLabel("Fuente:")
        self.lbl_fuente.setStyleSheet(lbl_style)
        layout.addWidget(self.lbl_fuente)

        self.font_combo = QFontComboBox()
        self.font_combo.setFixedHeight(20)
        self.font_combo.setStyleSheet("font-size: 9px; color: #FFFFFF;")
        self.font_combo.currentFontChanged.connect(self.emitir_configuracion)
        layout.addWidget(self.font_combo)

        tam_layout = QHBoxLayout()
        tam_layout.setSpacing(2)
        self.lbl_tam = QLabel("Tamaño:")
        self.lbl_tam.setStyleSheet(lbl_style)

        self.spin_size = QSpinBox()
        self.spin_size.setRange(1, 9999)
        self.spin_size.setValue(24)
        self.spin_size.setFixedHeight(20)
        self.spin_size.setStyleSheet("font-size: 9px; color: #FFFFFF;")
        self.spin_size.valueChanged.connect(self.emitir_configuracion)

        tam_layout.addWidget(self.lbl_tam)
        tam_layout.addWidget(self.spin_size)
        layout.addLayout(tam_layout)

        # --- 2. Estilos (B, I, U, S) ---
        styles_layout = QHBoxLayout()
        styles_layout.setSpacing(2)
        styles_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_bold = QPushButton("B")
        self.btn_bold.setCheckable(True)
        self.btn_bold.setFixedSize(25, 21)
        self.btn_bold.setStyleSheet("font-weight: bold; font-size: 11px; color: #FFFFFF;")
        self.btn_bold.toggled.connect(self.emitir_configuracion)

        self.btn_italic = QPushButton("I")
        self.btn_italic.setCheckable(True)
        self.btn_italic.setFixedSize(25, 21)
        self.btn_italic.setStyleSheet("font-style: italic; font-size: 11px; color: #FFFFFF;")
        self.btn_italic.toggled.connect(self.emitir_configuracion)

        self.btn_underline = QPushButton("U")
        self.btn_underline.setCheckable(True)
        self.btn_underline.setFixedSize(25, 21)
        self.btn_underline.setStyleSheet("text-decoration: underline; font-size: 11px; color: #FFFFFF;")
        self.btn_underline.toggled.connect(self.emitir_configuracion)

        self.btn_strike = QPushButton("S")
        self.btn_strike.setCheckable(True)
        self.btn_strike.setFixedSize(25, 21)
        self.btn_strike.setStyleSheet("text-decoration: line-through; font-size: 11px; color: #FFFFFF;")
        self.btn_strike.toggled.connect(self.emitir_configuracion)

        styles_layout.addWidget(self.btn_bold)
        styles_layout.addWidget(self.btn_italic)
        styles_layout.addWidget(self.btn_underline)
        styles_layout.addWidget(self.btn_strike)
        layout.addLayout(styles_layout)

        group_style = (
            "QGroupBox { font-size: 9px; color: #CCCCCC; font-weight: normal; "
            "margin-top: 10px; padding: 4px 4px 4px 4px; "
            "border: 1px solid #383838; border-radius: 3px; } "
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; "
            "padding: 0 4px; color: #CCCCCC; background-color: #2b2b2b; }"
        )

        # --- 3. Borde ---
        self.group_borde = QGroupBox("Borde")
        self.group_borde.setStyleSheet(group_style)
        borde_layout = QVBoxLayout()
        borde_layout.setContentsMargins(2, 2, 2, 2)
        borde_layout.setSpacing(2)

        self.chk_borde = QCheckBox("Mostrar")
        self.chk_borde.setStyleSheet(lbl_style)
        self.chk_borde.toggled.connect(self.emitir_configuracion)
        borde_layout.addWidget(self.chk_borde)

        b_size_layout = QHBoxLayout()
        b_size_layout.setSpacing(2)
        self.lbl_b_size = QLabel("Grosor:")
        self.lbl_b_size.setStyleSheet(lbl_style)
        self.spin_borde_size = QSpinBox()
        self.spin_borde_size.setRange(1, 100)
        self.spin_borde_size.setValue(3)
        self.spin_borde_size.setFixedHeight(20)
        self.spin_borde_size.setStyleSheet("font-size: 9px; color: #FFFFFF;")
        self.spin_borde_size.valueChanged.connect(self.emitir_configuracion)
        b_size_layout.addWidget(self.lbl_b_size)
        b_size_layout.addWidget(self.spin_borde_size)
        borde_layout.addLayout(b_size_layout)

        self.group_borde.setLayout(borde_layout)
        layout.addWidget(self.group_borde)

        # --- 4. Sombra ---
        self.group_sombra = QGroupBox("Sombra")
        self.group_sombra.setStyleSheet(group_style)
        sombra_layout = QVBoxLayout()
        sombra_layout.setContentsMargins(2, 2, 2, 4)
        sombra_layout.setSpacing(3)

        top_sombra_row = QHBoxLayout()
        top_sombra_row.setContentsMargins(0, 0, 0, 0)
        top_sombra_row.setSpacing(2)

        self.chk_sombra = QCheckBox("Mostrar")
        self.chk_sombra.setStyleSheet(lbl_style)
        self.chk_sombra.toggled.connect(self.emitir_configuracion)

        lbl_luz = QLabel("")
        lbl_luz.setStyleSheet(lbl_style)
        self.light_widget = LightDirectionWidget()
        self.light_widget.lightVectorChanged.connect(self.emitir_configuracion)

        top_sombra_row.addWidget(self.chk_sombra)
        top_sombra_row.addStretch()
        top_sombra_row.addWidget(lbl_luz)
        top_sombra_row.addWidget(self.light_widget, alignment=Qt.AlignmentFlag.AlignTop)
        sombra_layout.addLayout(top_sombra_row)

        s_dist_layout = QHBoxLayout()
        s_dist_layout.setContentsMargins(0, 2, 0, 0)
        s_dist_layout.setSpacing(2)
        self.lbl_dist = QLabel("Tamaño:")
        self.lbl_dist.setStyleSheet(lbl_style)
        self.spin_sombra_dist = QSpinBox()
        self.spin_sombra_dist.setRange(1, 9999)
        self.spin_sombra_dist.setValue(5)
        self.spin_sombra_dist.setFixedHeight(20)
        self.spin_sombra_dist.setStyleSheet("font-size: 9px; color: #FFFFFF;")
        self.spin_sombra_dist.valueChanged.connect(self.emitir_configuracion)
        s_dist_layout.addWidget(self.lbl_dist)
        s_dist_layout.addWidget(self.spin_sombra_dist)
        sombra_layout.addLayout(s_dist_layout)

        # 3ra fila: Color de Sombra con 5 casilleros
        s_color_layout = QHBoxLayout()
        s_color_layout.setContentsMargins(0, 4, 0, 0)
        s_color_layout.setSpacing(2)

        self.lbl_s_col = QLabel("Color:")
        self.lbl_s_col.setStyleSheet(lbl_style)
        s_color_layout.addWidget(self.lbl_s_col)

        self.sombra_custom_color = self.cargar_sombra_custom_settings()
        self.sombra_color = QColor("#FFFFFF")
        self.sombra_color_btns = []

        colores_predeterminados = [
            (QColor("#FFFFFF"), "Blanco"),
            (QColor("#000000"), "Negro"),
            (QColor("#1A1423"), "Sombra natural oscura"),
            (QColor("#FFF3D1"), "Luz solar"),
            (None, "Slot personalizado")
        ]

        def _make_shadow_color_handler(slot_idx):
            return lambda button_type, is_shift, is_ctrl: self._seleccionar_color_sombra(slot_idx, button_type, is_shift, is_ctrl)

        for idx, (col, nombre) in enumerate(colores_predeterminados):
            btn = ShadowColorButton()
            btn.setFixedSize(16, 16)
            if col:
                btn.setProperty("color_val", col)
                btn.setToolTip(f"{nombre} ({col.name().upper()})")
            btn.color_interacted.connect(_make_shadow_color_handler(idx))
            self.sombra_color_btns.append(btn)
            s_color_layout.addWidget(btn)

        sombra_layout.addLayout(s_color_layout)

        self.group_sombra.setLayout(sombra_layout)
        layout.addWidget(self.group_sombra)

        self.setLayout(layout)
        self.setFixedWidth(140)

        self.actualizar_ui_colores_sombra(active_idx=0)

    def cargar_sombra_custom_settings(self):
        settings = QSettings("PaintNotNet", "TextShadow")
        val = settings.value("custom_shadow_color", None)
        if val:
            c = QColor(val)
            if c.isValid():
                return c
        return None

    def guardar_sombra_custom_settings(self, color):
        settings = QSettings("PaintNotNet", "TextShadow")
        if color and color.isValid():
            settings.setValue("custom_shadow_color", color.name(QColor.NameFormat.HexArgb))
        else:
            settings.remove("custom_shadow_color")

    def _seleccionar_color_sombra(self, idx, button_type, is_shift, is_ctrl):
        if idx == 4:
            if is_ctrl:
                # Ctrl + Clic: ELIMINAR COLOR ALMACENADO
                self.sombra_custom_color = None
                self.guardar_sombra_custom_settings(None)
                self.sombra_color = self.sombra_color_btns[0].property("color_val")
                self.actualizar_ui_colores_sombra(active_idx=0)
                self.emitir_configuracion()
                return

            if self.sombra_custom_color is None or is_shift:
                # Slot vacío o Shift+Clic: GUARDAR / REEMPLAZAR
                canvas = getattr(self.main_window, 'lienzo', None) or getattr(self.main_window, 'canvas', None) if self.main_window else None
                col_pri = getattr(canvas, 'color_primario', QColor(0, 0, 0)) if canvas else QColor(0, 0, 0)
                col_sec = getattr(canvas, 'color_secundario', QColor(255, 255, 255)) if canvas else QColor(255, 255, 255)
                color_panel = col_pri if button_type == Qt.MouseButton.LeftButton else col_sec

                self.sombra_custom_color = QColor(color_panel)
                self.guardar_sombra_custom_settings(self.sombra_custom_color)

            self.sombra_color = QColor(self.sombra_custom_color)
        else:
            btn = self.sombra_color_btns[idx]
            self.sombra_color = btn.property("color_val")

        self.actualizar_ui_colores_sombra(active_idx=idx)
        self.emitir_configuracion()

    def actualizar_ui_colores_sombra(self, active_idx=0):
        for i in range(4):
            btn = self.sombra_color_btns[i]
            c_val = btn.property("color_val")
            is_active = (i == active_idx)
            border_color = "#0078D7" if is_active else "#555555"
            border_w = "2px" if is_active else "1px"
            btn.setStyleSheet(f"background-color: {c_val.name()}; border: {border_w} solid {border_color}; border-radius: 2px;")

        btn5 = self.sombra_color_btns[4]
        is_active5 = (active_idx == 4)
        if self.sombra_custom_color is None:
            border_color = "#0078D7" if is_active5 else "#777777"
            border_w = "2px" if is_active5 else "1px"
            btn5.setStyleSheet(f"background-color: #2D2D2D; border: {border_w} dashed {border_color}; border-radius: 2px;")
            btn5.setToolTip(t("Slot vacío: Clic para Guardar color activo del panel"))
        else:
            border_color = "#0078D7" if is_active5 else "#555555"
            border_w = "2px" if is_active5 else "1px"
            rgba_str = f"rgba({self.sombra_custom_color.red()}, {self.sombra_custom_color.green()}, {self.sombra_custom_color.blue()}, {self.sombra_custom_color.alpha()/255.0})"
            btn5.setStyleSheet(f"background-color: {rgba_str}; border: {border_w} solid {border_color}; border-radius: 2px;")
            btn5.setToolTip(t("Color guardado (Shift+Clic Reemplazar, Ctrl+Clic Eliminar)"))

    def obtener_configuracion(self):
        font_obj = self.font_combo.currentFont()
        font_family = font_obj.family() if isinstance(font_obj, QFont) else str(font_obj)
        dist = self.spin_sombra_dist.value()
        return {
            "font": font_obj,
            "font_family": font_family,
            "size": self.spin_size.value(),
            "font_size": self.spin_size.value(),
            "bold": self.btn_bold.isChecked(),
            "italic": self.btn_italic.isChecked(),
            "underline": self.btn_underline.isChecked(),
            "strike": self.btn_strike.isChecked(),
            "has_borde": self.chk_borde.isChecked(),
            "borde_enabled": self.chk_borde.isChecked(),
            "borde_size": self.spin_borde_size.value(),
            "has_sombra": self.chk_sombra.isChecked(),
            "sombra_enabled": self.chk_sombra.isChecked(),
            "sombra_dist": dist,
            "sombra_color": self.sombra_color,
            "sombra_offset_x": self.light_widget.light_x * dist,
            "sombra_offset_y": self.light_widget.light_y * dist,
            "sombra_dx": self.light_widget.light_x,
            "sombra_dy": self.light_widget.light_y
        }

    def emitir_configuracion(self):
        self.text_config_changed.emit(self.obtener_configuracion())

    def retraducir_panel(self):
        from core.i18n import t
        if hasattr(self, 'lbl_fuente'):
            self.lbl_fuente.setText(t("Fuente:"))
        if hasattr(self, 'lbl_tam'):
            self.lbl_tam.setText(t("Tamaño:"))
        if hasattr(self, 'group_borde'):
            self.group_borde.setTitle(t("Borde"))
        if hasattr(self, 'chk_borde'):
            self.chk_borde.setText(t("Mostrar"))
        if hasattr(self, 'lbl_b_size'):
            self.lbl_b_size.setText(t("Grosor:"))
        if hasattr(self, 'group_sombra'):
            self.group_sombra.setTitle(t("Sombra"))
        if hasattr(self, 'chk_sombra'):
            self.chk_sombra.setText(t("Mostrar"))
        if hasattr(self, 'lbl_dist'):
            self.lbl_dist.setText(t("Tamaño:"))
        if hasattr(self, 'lbl_s_col'):
            self.lbl_s_col.setText(t("Color:"))
        # Refresca los tooltips de los slots de color de sombra (usan t() internamente)
        if hasattr(self, 'actualizar_ui_colores_sombra'):
            self.actualizar_ui_colores_sombra()
