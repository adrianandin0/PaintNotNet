from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton,
                             QPushButton, QListWidget, QListWidgetItem, QAbstractItemView,
                             QMessageBox, QMenu, QInputDialog)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QImage, QPainter, QColor


class LayerRowWidget(QWidget):
    """Widget personalizado para cada fila de la lista de capas con icono de Ojo."""
    def __init__(self, capa, panel, parent=None):
        super().__init__(parent)
        self.capa = capa
        self.panel = panel

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        # 1. Miniatura (16x16)
        self.lbl_thumb = QLabel()
        self.lbl_thumb.setFixedSize(16, 16)
        self.actualizar_thumb()
        layout.addWidget(self.lbl_thumb)

        # 2. Nombre de la Capa
        self.lbl_name = QLabel(capa.name)
        self.lbl_name.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.lbl_name)

        layout.addStretch()

        # 3. Botón Ojo de Visibilidad (eye.png)
        self.btn_eye = QToolButton()
        self.btn_eye.setFixedSize(20, 20)
        self.btn_eye.setIcon(QIcon("gui/iconos/eye.png"))
        self.btn_eye.setIconSize(QSize(14, 14))
        self.btn_eye.setAutoRaise(True)
        self.btn_eye.setToolTip("Mostrar / Ocultar capa")
        self.btn_eye.clicked.connect(self.toggle_visibility)
        layout.addWidget(self.btn_eye)

        self.actualizar_estado_visibilidad()

    def actualizar_thumb(self):
        thumb_icon = self.panel.generar_thumbnail(self.capa.image)
        pix = thumb_icon.pixmap(16, 16)
        self.lbl_thumb.setPixmap(pix)

    def toggle_visibility(self):
        self.capa.visible = not self.capa.visible
        self.actualizar_estado_visibilidad()
        canvas = self.panel.obtener_canvas()
        if canvas:
            canvas.update()

    def actualizar_estado_visibilidad(self):
        if self.capa.visible:
            self.btn_eye.setStyleSheet("QToolButton { opacity: 1.0; border: none; }")
            self.lbl_name.setStyleSheet("font-size: 11px;")
        else:
            self.btn_eye.setStyleSheet("QToolButton { opacity: 0.2; background: transparent; border: none; }")
            self.lbl_name.setStyleSheet("font-size: 11px; color: #777777; text-decoration: line-through;")


class LayersPanelWidget(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.layer_counter = 1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.lista_capas = QListWidget()
        self.lista_capas.setStyleSheet("""
            QListWidget { font-size: 11px; }
            QListWidget::item:selected QLabel { color: #FFFFFF !important; }
        """)
        self.lista_capas.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.lista_capas.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.lista_capas.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.lista_capas.setIconSize(QSize(16, 16))
        self.lista_capas.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lista_capas.customContextMenuRequested.connect(self._mostrar_menu_contextual)
        self.lista_capas.itemDoubleClicked.connect(self._renombrar_capa_dialogo)
        self.lista_capas.model().rowsMoved.connect(self._on_rows_moved)
        layout.addWidget(self.lista_capas)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)

        self.btn_add = QPushButton()
        self.btn_add.setIcon(QIcon("gui/iconos/add.png"))
        self.btn_add.setIconSize(QSize(16, 16))
        self.btn_add.setToolTip("Nueva Capa")

        self.btn_up = QPushButton()
        self.btn_up.setIcon(QIcon("gui/iconos/arrow_up.png"))
        self.btn_up.setIconSize(QSize(16, 16))
        self.btn_up.setToolTip("Mover Capa Arriba")

        self.btn_down = QPushButton()
        self.btn_down.setIcon(QIcon("gui/iconos/arrow_down.png"))
        self.btn_down.setIconSize(QSize(16, 16))
        self.btn_down.setToolTip("Mover Capa Abajo")

        self.btn_combine = QPushButton()
        self.btn_combine.setIcon(QIcon("gui/iconos/merge.png"))
        self.btn_combine.setIconSize(QSize(16, 16))
        self.btn_combine.setToolTip("Combinar")

        self.btn_del = QPushButton()
        self.btn_del.setIcon(QIcon("gui/iconos/bin.png"))
        self.btn_del.setIconSize(QSize(16, 16))
        self.btn_del.setToolTip("Eliminar")

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_up)
        btn_layout.addWidget(self.btn_down)
        btn_layout.addWidget(self.btn_combine)
        btn_layout.addWidget(self.btn_del)

        layout.addLayout(btn_layout)

        self.btn_add.clicked.connect(self.agregar_capa)
        self.btn_up.clicked.connect(self.mover_capa_arriba)
        self.btn_down.clicked.connect(self.mover_capa_abajo)
        self.btn_combine.clicked.connect(self.combinar_capas)
        self.btn_del.clicked.connect(self.borrar_capa)
        self.lista_capas.currentRowChanged.connect(self.cambiar_capa_activa)

    def set_canvas(self, canvas):
        self.canvas_override = canvas
        self.reconstruir_lista_capas()

    def obtener_canvas(self):
        if hasattr(self, 'canvas_override') and self.canvas_override is not None:
            return self.canvas_override
        return getattr(self.main_window, 'lienzo', getattr(self.main_window, 'canvas', None))

    def generar_thumbnail(self, layer_image):
        canvas_16 = QImage(16, 16, QImage.Format.Format_ARGB32_Premultiplied)
        canvas_16.fill(QColor(45, 45, 45))

        if layer_image and not layer_image.isNull():
            thumb = layer_image.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            painter = QPainter(canvas_16)
            ox = (16 - thumb.width()) // 2
            oy = (16 - thumb.height()) // 2
            painter.drawImage(ox, oy, thumb)
            painter.setPen(QColor(90, 90, 90))
            painter.drawRect(0, 0, 15, 15)
            painter.end()

        return QIcon(QPixmap.fromImage(canvas_16))

    def actualizar_thumbnails(self):
        for i in range(self.lista_capas.count()):
            item = self.lista_capas.item(i)
            row_widget = self.lista_capas.itemWidget(item)
            if row_widget and hasattr(row_widget, 'actualizar_thumb'):
                row_widget.actualizar_thumb()

    def reconstruir_lista_capas(self):
        self.lista_capas.blockSignals(True)
        self.lista_capas.clear()

        canvas = self.obtener_canvas()
        if not canvas or not hasattr(canvas, 'layer_mgr'):
            self.lista_capas.blockSignals(False)
            return

        mgr = canvas.layer_mgr
        for idx, capa in enumerate(mgr.capas):
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 26))
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.lista_capas.addItem(item)

            row_widget = LayerRowWidget(capa, self)
            self.lista_capas.setItemWidget(item, row_widget)

        idx_activo = max(0, min(mgr.indice_activo, len(mgr.capas) - 1))
        mgr.indice_activo = idx_activo
        self.lista_capas.setCurrentRow(idx_activo)
        self.lista_capas.blockSignals(False)

    def agregar_capa(self):
        canvas = self.obtener_canvas()
        if not canvas:
            return
        mgr = canvas.layer_mgr

        self.layer_counter += 1
        from core.i18n import t as _t
        nombre = _t("Capa %1").replace("%1", str(self.layer_counter))
        mgr.agregar_capa(nombre)

        self.reconstruir_lista_capas()
        canvas.push_document_state("Nueva Capa")
        canvas.update()

    def mover_capa_arriba(self):
        curr_row = self.lista_capas.currentRow()
        if curr_row <= 0:
            return
        canvas = self.obtener_canvas()
        if not canvas or not hasattr(canvas, 'layer_mgr'):
            return
        mgr = canvas.layer_mgr
        target_row = curr_row - 1
        mgr.capas[curr_row], mgr.capas[target_row] = mgr.capas[target_row], mgr.capas[curr_row]
        mgr.indice_activo = target_row
        self.reconstruir_lista_capas()
        canvas.push_document_state("Reordenar Capas")
        canvas.update()

    def mover_capa_abajo(self):
        curr_row = self.lista_capas.currentRow()
        if curr_row < 0 or curr_row >= self.lista_capas.count() - 1:
            return
        canvas = self.obtener_canvas()
        if not canvas or not hasattr(canvas, 'layer_mgr'):
            return
        mgr = canvas.layer_mgr
        target_row = curr_row + 1
        mgr.capas[curr_row], mgr.capas[target_row] = mgr.capas[target_row], mgr.capas[curr_row]
        mgr.indice_activo = target_row
        self.reconstruir_lista_capas()
        canvas.push_document_state("Reordenar Capas")
        canvas.update()

    def duplicar_capa(self):
        selected_items = self.lista_capas.selectedItems()
        if len(selected_items) != 1:
            return
        row = self.lista_capas.row(selected_items[0])
        canvas = self.obtener_canvas()
        if not canvas or not hasattr(canvas, 'layer_mgr') or row < 0 or row >= len(canvas.layer_mgr.capas):
            return

        from core.layers import Layer
        orig_capa = canvas.layer_mgr.capas[row]
        nuevo_nombre = f"{orig_capa.name} Copia"
        dup_capa = Layer(nuevo_nombre, canvas.layer_mgr.width, canvas.layer_mgr.height, transparent=True)
        dup_capa.visible = orig_capa.visible
        dup_capa.image = orig_capa.image.copy()

        canvas.layer_mgr.capas.insert(row, dup_capa)
        canvas.layer_mgr.indice_activo = row

        self.reconstruir_lista_capas()
        canvas.push_document_state("Duplicar Capa")
        canvas.update()

    def combinar_capas(self):
        selected_items = self.lista_capas.selectedItems()
        if len(selected_items) < 2:
            QMessageBox.information(self, "Combinar Capas", "Seleccione al menos 2 capas para combinarlas.")
            return

        indices = sorted([self.lista_capas.row(item) for item in selected_items])
        canvas = self.obtener_canvas()
        canvas.layer_mgr.combinar_capas_indices(indices)
        self.reconstruir_lista_capas()
        if canvas:
            canvas.push_document_state("Combinar Capas")
        canvas.update()

    def borrar_capa(self):
        selected_items = self.lista_capas.selectedItems()
        if not selected_items:
            return

        if len(selected_items) >= self.lista_capas.count():
            QMessageBox.warning(self, "Acción denegada", "Debe quedar al menos una capa en el lienzo.")
            return

        respuesta = QMessageBox.question(
            self,
            "Eliminar Capas",
            f"¿Está seguro que desea borrar las {len(selected_items)} capa(s) seleccionada(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            canvas = self.obtener_canvas()
            indices = sorted([self.lista_capas.row(item) for item in selected_items], reverse=True)
            mgr = canvas.layer_mgr

            for idx in indices:
                mgr.capas.pop(idx)

            self.reconstruir_lista_capas()
            if canvas:
                canvas.push_document_state("Eliminar Capas")
            canvas.update()

    def cambiar_capa_activa(self, idx):
        if idx >= 0 and self.main_window and hasattr(self.main_window, 'canvas'):
            canvas = self.main_window.canvas
            if canvas.selection_engine.floating_image:
                from tools.move_select_pixels import MoveSelectPixelsTool
                MoveSelectPixelsTool.commit_floating_image(canvas)
            canvas.layer_mgr.indice_activo = idx
            canvas.update()

    def _on_rows_moved(self, parent, start, end, destination, row):
        canvas = self.obtener_canvas()
        if not canvas or not hasattr(canvas, 'layer_mgr'):
            return

        original_capas = list(canvas.layer_mgr.capas)
        nuevas_capas = []
        for i in range(self.lista_capas.count()):
            item = self.lista_capas.item(i)
            idx_orig = item.data(Qt.ItemDataRole.UserRole)
            if idx_orig is not None and 0 <= idx_orig < len(original_capas):
                nuevas_capas.append(original_capas[idx_orig])

        if len(nuevas_capas) == len(original_capas):
            canvas.layer_mgr.capas = nuevas_capas
            curr_row = self.lista_capas.currentRow()
            if curr_row >= 0:
                canvas.layer_mgr.indice_activo = curr_row
            self.reconstruir_lista_capas()
            canvas.push_document_state("Reordenar Capas")
            canvas.update()

    def _mostrar_menu_contextual(self, pos):
        item = self.lista_capas.itemAt(pos)
        if not item:
            return

        selected_items = self.lista_capas.selectedItems()
        if not selected_items:
            return

        from core.i18n import t
        menu = QMenu(self)

        if len(selected_items) == 1:
            accion_renombrar = menu.addAction(t("Renombrar capa..."))
            accion_renombrar.triggered.connect(lambda: self._renombrar_capa_dialogo(item))

            accion_duplicar = menu.addAction(t("Duplicar capa"))
            accion_duplicar.triggered.connect(self.duplicar_capa)

        if len(selected_items) >= 2:
            accion_combinar = menu.addAction(t("Combinar capas"))
            accion_combinar.triggered.connect(self.combinar_capas)

        menu.addSeparator()
        accion_eliminar = menu.addAction(t("Eliminar capa"))
        accion_eliminar.triggered.connect(self.borrar_capa)

        menu.exec(self.lista_capas.mapToGlobal(pos))

    def _renombrar_capa_dialogo(self, item):
        idx = self.lista_capas.row(item)
        if idx < 0:
            return

        canvas = self.obtener_canvas()
        if not canvas or idx >= len(canvas.layer_mgr.capas):
            return

        capa = canvas.layer_mgr.capas[idx]
        nuevo_nombre, ok = QInputDialog.getText(
            self,
            "Renombrar Capa",
            "Nuevo nombre para la capa:",
            text=capa.name
        )

        if ok and nuevo_nombre.strip():
            nombre_final = nuevo_nombre.strip()
            capa.name = nombre_final
            self.reconstruir_lista_capas()

    def retraducir_panel(self):
        from core.i18n import t
        if hasattr(self, 'btn_add'):
            self.btn_add.setToolTip(t("Nueva Capa"))
        if hasattr(self, 'btn_up'):
            self.btn_up.setToolTip(t("Mover Capa Arriba"))
        if hasattr(self, 'btn_down'):
            self.btn_down.setToolTip(t("Mover Capa Abajo"))
        if hasattr(self, 'btn_combine'):
            self.btn_combine.setToolTip(t("Combinar"))
        if hasattr(self, 'btn_del'):
            self.btn_del.setToolTip(t("Eliminar"))
