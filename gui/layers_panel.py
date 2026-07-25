from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QListWidget, QAbstractItemView, QMessageBox)
from PyQt6.QtCore import Qt

class LayersPanelWidget(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Lista de capas
        self.lista_capas = QListWidget()
        self.lista_capas.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.lista_capas)

        # Botones de control
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)

        self.btn_add = QPushButton("+")
        self.btn_add.setToolTip("Nueva Capa")

        self.btn_del = QPushButton("-")
        self.btn_del.setToolTip("Eliminar Capa")

        self.btn_up = QPushButton("▲")
        self.btn_up.setToolTip("Subir Capa (Traer al frente)")

        self.btn_down = QPushButton("▼")
        self.btn_down.setToolTip("Bajar Capa (Enviar atrás)")

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_del)
        btn_layout.addWidget(self.btn_up)
        btn_layout.addWidget(self.btn_down)

        layout.addLayout(btn_layout)

        # Capa base por defecto
        self.lista_capas.addItem("Capa 1")
        self.lista_capas.setCurrentRow(0)

        # ==========================================
        # CONEXIONES DE EVENTOS
        # ==========================================
        self.btn_add.clicked.connect(self.agregar_capa)
        self.btn_del.clicked.connect(self.borrar_capa)
        self.btn_up.clicked.connect(self.subir_capa)
        self.btn_down.clicked.connect(self.bajar_capa)
        self.lista_capas.currentRowChanged.connect(self.cambiar_capa_activa)

    def obtener_canvas(self):
        return self.main_window.canvas

    def agregar_capa(self):
        canvas = self.obtener_canvas()
        mgr = canvas.layer_mgr

        # Nombre automático
        nombre = f"Capa {self.lista_capas.count() + 1}"

        # Impactar backend
        mgr.agregar_capa(nombre)

        # Impactar visual
        self.lista_capas.addItem(nombre)
        self.lista_capas.setCurrentRow(self.lista_capas.count() - 1)
        canvas.update()

    def borrar_capa(self):
        if self.lista_capas.count() <= 1:
            QMessageBox.warning(self, "Acción denegada", "Debe quedar al menos una capa en el lienzo.")
            return

        respuesta = QMessageBox.question(
            self,
            "Eliminar Capa",
            "¿Está seguro que desea borrar la capa seleccionada? Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            idx = self.lista_capas.currentRow()
            canvas = self.obtener_canvas()

            # Borrar del backend
            canvas.layer_mgr.capas.pop(idx)

            # Borrar de la lista visual
            self.lista_capas.takeItem(idx)

            # Seleccionar la capa anterior para no perder el foco
            nuevo_idx = max(0, idx - 1)
            self.lista_capas.setCurrentRow(nuevo_idx)
            canvas.update()

    def cambiar_capa_activa(self, idx):
        if idx >= 0 and self.main_window and hasattr(self.main_window, 'canvas'):
            self.main_window.canvas.layer_mgr.indice_activo = idx

    def subir_capa(self):
        idx = self.lista_capas.currentRow()
        canvas = self.obtener_canvas()
        mgr = canvas.layer_mgr

        if idx < self.lista_capas.count() - 1:
            # Intercambiar en el backend
            mgr.capas[idx], mgr.capas[idx+1] = mgr.capas[idx+1], mgr.capas[idx]

            # Intercambiar en la lista visual
            item = self.lista_capas.takeItem(idx)
            self.lista_capas.insertItem(idx + 1, item)

            self.lista_capas.setCurrentRow(idx + 1)
            canvas.update()

    def bajar_capa(self):
        idx = self.lista_capas.currentRow()
        canvas = self.obtener_canvas()
        mgr = canvas.layer_mgr

        if idx > 0:
            # Intercambiar en el backend
            mgr.capas[idx], mgr.capas[idx-1] = mgr.capas[idx-1], mgr.capas[idx]

            # Intercambiar en la lista visual
            item = self.lista_capas.takeItem(idx)
            self.lista_capas.insertItem(idx - 1, item)

            self.lista_capas.setCurrentRow(idx - 1)
            canvas.update()
