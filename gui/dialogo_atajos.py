from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QKeySequence, QIcon

DEFAULT_SHORTCUTS = {
    "Selección Rectangular": "S",
    "Mover Selección": "M",
    "Selección Libre": "L",
    "Mover Contenido": "V",
    "Selección Elíptica": "C",
    "Invertir Selección": "I",
    "Balde de Pintura": "F",
    "Degradado": "G",
    "Pincel": "B",
    "Cuentagotas": "K",
    "Lápiz": "P",
    "Goma de Borrar": "E",
    "Varita Mágica": "W",
    "Línea": "O",
    "Texto": "T",
    "Zoom": "Z",
    "Insertar Formas": "H",
    "Difuminar": "D",
}

TOOL_ICONS = {
    "Selección Rectangular": "gui/iconos/select_rect.png",
    "Mover Selección":       "gui/iconos/move_select_only.png",
    "Selección Libre":       "gui/iconos/select_free.png",
    "Mover Contenido":       "gui/iconos/move_select_pixels.png",
    "Selección Elíptica":    "gui/iconos/select_ellipse.png",
    "Invertir Selección":    "gui/iconos/invert.png",
    "Balde de Pintura":      "gui/iconos/bucket.png",
    "Degradado":             "gui/iconos/gradient.png",
    "Pincel":                "gui/iconos/brush.png",
    "Cuentagotas":           "gui/iconos/eyedropper.png",
    "Lápiz":                 "gui/iconos/pencil.png",
    "Goma de Borrar":        "gui/iconos/eraser.png",
    "Varita Mágica":         "gui/iconos/magic.png",
    "Línea":                 "gui/iconos/line.png",
    "Texto":                 "gui/iconos/text.png",
    "Zoom":                  "gui/iconos/zoom.png",
    "Insertar Formas":       "gui/iconos/shapes.png",
    "Difuminar":             "gui/iconos/blur.png",
}

def cargar_atajos():
    settings = QSettings("PaintNotNet", "PaintNotNet")
    atajos = {}
    for tool_name, default_key in DEFAULT_SHORTCUTS.items():
        val = settings.value(f"shortcut_{tool_name}", default_key)
        atajos[tool_name] = str(val) if val else default_key
    return atajos

def guardar_atajos(atajos_dict):
    settings = QSettings("PaintNotNet", "PaintNotNet")
    for tool_name, key in atajos_dict.items():
        settings.setValue(f"shortcut_{tool_name}", str(key).upper())


class DialogoAtajos(QDialog):
    """Diálogo para configurar atajos de teclado personalizados para las herramientas."""
    def __init__(self, parent=None):
        super().__init__(parent)
        from core.i18n import t
        self.setWindowTitle(t("Atajos de Teclado"))
        self.setFixedSize(450, 520)

        layout = QVBoxLayout()

        lbl_info = QLabel(t("Haz doble clic en una celda o presiona una tecla para cambiar el atajo (un único carácter):"))
        lbl_info.setWordWrap(True)
        layout.addWidget(lbl_info)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(2)
        self.tabla.setHorizontalHeaderLabels([t("Herramienta"), t("Tecla de Atajo")])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        self.atajos_actuales = cargar_atajos()
        self.cargar_tabla()

        layout.addWidget(self.tabla)

        # Botones inferiores
        btn_layout = QHBoxLayout()
        btn_reset = QPushButton(t("Restablecer por Defecto"))
        btn_reset.clicked.connect(self.restablecer_defecto)

        btn_cancel = QPushButton(t("Cancelar"))
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton(t("Guardar"))
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self.guardar_y_cerrar)

        btn_layout.addWidget(btn_reset)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def cargar_tabla(self):
        from core.i18n import t
        self.tabla.setRowCount(0)
        for i, (tool_name, key) in enumerate(self.atajos_actuales.items()):
            self.tabla.insertRow(i)

            item_tool = QTableWidgetItem(t(tool_name))
            item_tool.setData(Qt.ItemDataRole.UserRole, tool_name)
            item_tool.setFlags(item_tool.flags() & ~Qt.ItemFlag.ItemIsEditable)
            icon_path = TOOL_ICONS.get(tool_name, "")
            if icon_path:
                item_tool.setIcon(QIcon(icon_path))
            self.tabla.setItem(i, 0, item_tool)

            item_key = QTableWidgetItem(str(key).upper())
            item_key.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(i, 1, item_key)

    def restablecer_defecto(self):
        self.atajos_actuales = DEFAULT_SHORTCUTS.copy()
        self.cargar_tabla()

    def guardar_y_cerrar(self):
        nuevos_atajos = {}
        for row in range(self.tabla.rowCount()):
            item_tool = self.tabla.item(row, 0)
            tool_name = item_tool.data(Qt.ItemDataRole.UserRole) or item_tool.text()
            key_text = self.tabla.item(row, 1).text().strip().upper()
            char = key_text[0] if key_text else ""
            nuevos_atajos[tool_name] = char

        guardar_atajos(nuevos_atajos)
        self.accept()
