"""
text_panel.py — Panel de texto simplificado.
Contiene: fuente, tamaño, estilos (B/I/U/S), alineación.
Las opciones de Borde/Resplandor/Sombra viven en effects_panel.py.
"""
import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QFontComboBox, QToolButton, QButtonGroup, QSizePolicy
)
from PyQt6.QtGui import QFont, QColor, QIcon
from PyQt6.QtCore import Qt, pyqtSignal
from core.i18n import t


class TextPanelWidget(QWidget):
    """Panel lateral de configuración de texto (fuente, tamaño, estilos, alineación)."""
    text_config_changed = pyqtSignal(dict)

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window

        lbl_style = "color: #E8E8E8; font-size: 9px; font-weight: normal;"

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Fuente ---
        self.lbl_fuente = QLabel(t("Fuente:"))
        self.lbl_fuente.setStyleSheet(lbl_style)
        layout.addWidget(self.lbl_fuente)

        self.font_combo = QFontComboBox()
        self.font_combo.setFixedHeight(20)
        self.font_combo.setStyleSheet("font-size: 9px; color: #EDEDED;")
        self.font_combo.currentFontChanged.connect(self.emitir_configuracion)
        layout.addWidget(self.font_combo)

        # --- Tamaño ---
        tam_layout = QHBoxLayout()
        tam_layout.setSpacing(2)
        self.lbl_tam = QLabel(t("Tamaño:"))
        self.lbl_tam.setStyleSheet(lbl_style)

        self.spin_size = QSpinBox()
        self.spin_size.setRange(1, 9999)
        self.spin_size.setValue(24)
        self.spin_size.setFixedHeight(20)
        self.spin_size.setStyleSheet("font-size: 9px; color: #EDEDED;")
        self.spin_size.valueChanged.connect(self.emitir_configuracion)

        tam_layout.addWidget(self.lbl_tam)
        tam_layout.addWidget(self.spin_size)
        layout.addLayout(tam_layout)

        # --- Estilos (B / I / U / S) ---
        styles_layout = QHBoxLayout()
        styles_layout.setSpacing(2)
        styles_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_bold = QPushButton("B")
        self.btn_bold.setCheckable(True)
        self.btn_bold.setFixedSize(25, 21)
        self.btn_bold.setStyleSheet("font-weight: bold; font-size: 11px; color: #EDEDED;")
        self.btn_bold.toggled.connect(self.emitir_configuracion)

        self.btn_italic = QPushButton("I")
        self.btn_italic.setCheckable(True)
        self.btn_italic.setFixedSize(25, 21)
        self.btn_italic.setStyleSheet("font-style: italic; font-size: 11px; color: #EDEDED;")
        self.btn_italic.toggled.connect(self.emitir_configuracion)

        self.btn_underline = QPushButton("U")
        self.btn_underline.setCheckable(True)
        self.btn_underline.setFixedSize(25, 21)
        self.btn_underline.setStyleSheet("text-decoration: underline; font-size: 11px; color: #EDEDED;")
        self.btn_underline.toggled.connect(self.emitir_configuracion)

        self.btn_strike = QPushButton("S")
        self.btn_strike.setCheckable(True)
        self.btn_strike.setFixedSize(25, 21)
        self.btn_strike.setStyleSheet("text-decoration: line-through; font-size: 11px; color: #EDEDED;")
        self.btn_strike.toggled.connect(self.emitir_configuracion)

        styles_layout.addWidget(self.btn_bold)
        styles_layout.addWidget(self.btn_italic)
        styles_layout.addWidget(self.btn_underline)
        styles_layout.addWidget(self.btn_strike)
        layout.addLayout(styles_layout)

        # --- Alineación ---
        align_layout = QHBoxLayout()
        align_layout.setSpacing(2)
        align_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._align_group = QButtonGroup(self)
        self._align_group.setExclusive(True)

        btn_align_style = """
            QToolButton {
                background: #2D2D2D;
                border: 1px solid #686868;
                border-radius: 3px;
                font-size: 13px;
                color: #EDEDED;
            }
            QToolButton:hover { background: #5C5C5C; }
            QToolButton:checked {
                background: #1a5fa8;
                border-color: #3d8ef0;
            }
        """

        self.btn_align_left = QToolButton()
        self.btn_align_left.setCheckable(True)
        self.btn_align_left.setChecked(True)
        self.btn_align_left.setFixedSize(34, 24)
        self.btn_align_left.setToolTip(t("Alinear izquierda"))
        self.btn_align_left.setStyleSheet(btn_align_style)
        self.btn_align_left.setIcon(QIcon("gui/iconos/left-align.png"))
        self.btn_align_left.setIconSize(QIcon("gui/iconos/left-align.png").actualSize(
            self.btn_align_left.sizeHint()))

        self.btn_align_center = QToolButton()
        self.btn_align_center.setCheckable(True)
        self.btn_align_center.setFixedSize(34, 24)
        self.btn_align_center.setToolTip(t("Alinear centro"))
        self.btn_align_center.setStyleSheet(btn_align_style)
        self.btn_align_center.setIcon(QIcon("gui/iconos/center-align.png"))

        self.btn_align_right = QToolButton()
        self.btn_align_right.setCheckable(True)
        self.btn_align_right.setFixedSize(34, 24)
        self.btn_align_right.setToolTip(t("Alinear derecha"))
        self.btn_align_right.setStyleSheet(btn_align_style)
        self.btn_align_right.setIcon(QIcon("gui/iconos/right-align.png"))

        self.btn_align_justify = QToolButton()
        self.btn_align_justify.setCheckable(True)
        self.btn_align_justify.setFixedSize(34, 24)
        self.btn_align_justify.setToolTip(t("Justificar"))
        self.btn_align_justify.setStyleSheet(btn_align_style)
        self.btn_align_justify.setIcon(QIcon("gui/iconos/justify.png"))

        self._align_group.addButton(self.btn_align_left)
        self._align_group.addButton(self.btn_align_center)
        self._align_group.addButton(self.btn_align_right)
        self._align_group.addButton(self.btn_align_justify)
        self._align_group.buttonToggled.connect(lambda btn, checked: self.emitir_configuracion() if checked else None)

        align_layout.addWidget(self.btn_align_left)
        align_layout.addWidget(self.btn_align_center)
        align_layout.addWidget(self.btn_align_right)
        align_layout.addWidget(self.btn_align_justify)
        layout.addLayout(align_layout)

        layout.addStretch()
        self.setLayout(layout)
        self.setFixedWidth(155)

    def get_alignment(self) -> Qt.AlignmentFlag:
        if self.btn_align_center.isChecked():
            return Qt.AlignmentFlag.AlignHCenter
        if self.btn_align_right.isChecked():
            return Qt.AlignmentFlag.AlignRight
        if self.btn_align_justify.isChecked():
            return Qt.AlignmentFlag.AlignJustify
        return Qt.AlignmentFlag.AlignLeft

    def obtener_configuracion(self) -> dict:
        font_obj = self.font_combo.currentFont()
        font_family = font_obj.family() if isinstance(font_obj, QFont) else str(font_obj)
        return {
            "font":        font_obj,
            "font_family": font_family,
            "size":        self.spin_size.value(),
            "font_size":   self.spin_size.value(),
            "bold":        self.btn_bold.isChecked(),
            "italic":      self.btn_italic.isChecked(),
            "underline":   self.btn_underline.isChecked(),
            "strike":      self.btn_strike.isChecked(),
            "alignment":   self.get_alignment(),
        }

    def emitir_configuracion(self):
        cfg = self.obtener_configuracion()
        self.text_config_changed.emit(cfg)
        # Si hay una herramienta de texto activa, aplicar formato a la selección
        if self.main_window:
            canvas = getattr(self.main_window, 'lienzo',
                             getattr(self.main_window, 'canvas', None))
            if canvas:
                from tools.text import TextTool
                tool = getattr(canvas, 'active_tool_obj', None)
                if isinstance(tool, TextTool) and tool.is_editing:
                    font_obj = cfg.get("font", None)
                    fmt_dict = {
                        "font_family": cfg.get("font_family",
                                               font_obj.family() if font_obj else "Arial"),
                        "font_size":   cfg.get("size", 24),
                        "bold":        cfg.get("bold",      False),
                        "italic":      cfg.get("italic",    False),
                        "underline":   cfg.get("underline", False),
                        "strike":      cfg.get("strike",    False),
                        "alignment":   cfg.get("alignment", Qt.AlignmentFlag.AlignLeft),
                    }
                    tool.apply_format_to_selection(fmt_dict)

    def retraducir_panel(self):
        if hasattr(self, 'lbl_fuente'):
            self.lbl_fuente.setText(t("Fuente:"))
        if hasattr(self, 'lbl_tam'):
            self.lbl_tam.setText(t("Tamaño:"))
        if hasattr(self, 'btn_align_left'):
            self.btn_align_left.setToolTip(t("Alinear izquierda"))
        if hasattr(self, 'btn_align_center'):
            self.btn_align_center.setToolTip(t("Alinear centro"))
        if hasattr(self, 'btn_align_right'):
            self.btn_align_right.setToolTip(t("Alinear derecha"))
        if hasattr(self, 'btn_align_justify'):
            self.btn_align_justify.setToolTip(t("Justificar"))
