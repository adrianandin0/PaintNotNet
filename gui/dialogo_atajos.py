from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QKeySequence, QIcon

DEFAULT_SHORTCUTS = {
    "Selección Rectangular": "S",
    "Mover Selección": "M",
    "Selección Libre": "L",
    "Mover Contenido": "Z",
    "Selección Elíptica": "E",
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
        self.setWindowTitle("Atajos de Teclado")
        self.setFixedSize(450, 520)

        layout = QVBoxLayout()

        lbl_info = QLabel("Haz doble clic en una celda o presiona una tecla para cambiar el atajo (un único carácter):")
        lbl_info.setWordWrap(True)
        layout.addWidget(lbl_info)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(2)
        self.tabla.setHorizontalHeaderLabels(["Herramienta", "Tecla de Atajo"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        self.atajos_actuales = cargar_atajos()
        self.cargar_tabla()

        layout.addWidget(self.tabla)

        # Botones inferiores
        btn_layout = QHBoxLayout()
        btn_reset = QPushButton("Restablecer por Defecto")
        btn_reset.clicked.connect(self.restablecer_defecto)
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("Guardar")
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self.guardar_y_cerrar)

        btn_layout.addWidget(btn_reset)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def cargar_tabla(self):
        self.tabla.setRowCount(0)
        for i, (tool_name, key) in enumerate(self.atajos_actuales.items()):
            self.tabla.insertRow(i)

            item_tool = QTableWidgetItem(tool_name)
            item_tool.setFlags(item_tool.flags() & ~Qt.ItemFlag.ItemIsEditable)
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
            tool_name = self.tabla.item(row, 0).text()
            key_text = self.tabla.item(row, 1).text().strip().upper()
            char = key_text[0] if key_text else ""
            nuevos_atajos[tool_name] = char

        guardar_atajos(nuevos_atajos)
        self.accept()
