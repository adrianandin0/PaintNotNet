from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize


class HistoryPanelWidget(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("QListWidget { font-size: 10px; color: #FFFFFF; }")
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.btn_undo = QPushButton()
        self.btn_undo.setIcon(QIcon("gui/iconos/back.png"))
        self.btn_undo.setIconSize(QSize(16, 16))
        self.btn_undo.setToolTip("Deshacer (Ctrl+Z)")

        self.btn_redo = QPushButton()
        self.btn_redo.setIcon(QIcon("gui/iconos/forward.png"))
        self.btn_redo.setIconSize(QSize(16, 16))
        self.btn_redo.setToolTip("Rehacer (Ctrl+Y)")

        self.btn_undo.clicked.connect(self._on_undo_clicked)
        self.btn_redo.clicked.connect(self._on_redo_clicked)

        btn_layout.addWidget(self.btn_undo)
        btn_layout.addWidget(self.btn_redo)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def set_canvas(self, canvas):
        self.canvas_override = canvas
        if hasattr(canvas, 'history_mgr'):
            canvas.history_mgr.on_change = self.actualizar_historial
            if not canvas.history_mgr.history_stack:
                canvas.history_mgr.push_state(canvas.obtener_snapshot_documento(), "Lienzo inicial")
            else:
                self.actualizar_historial()

    def _obtener_canvas(self):
        if hasattr(self, 'canvas_override') and self.canvas_override is not None:
            return self.canvas_override
        return getattr(self.main_window, 'lienzo', getattr(self.main_window, 'canvas', None))

    def actualizar_historial(self):
        self.list_widget.blockSignals(True)
        self.list_widget.clear()

        canvas = self._obtener_canvas()
        if not canvas:
            self.list_widget.blockSignals(False)
            return

        history_mgr = canvas.history_mgr

        for idx, (st, action_name) in enumerate(history_mgr.history_stack):
            item = QListWidgetItem(f"{idx}. {action_name}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            if idx > history_mgr.current_index:
                item.setForeground(Qt.GlobalColor.gray)

            self.list_widget.addItem(item)

        base_count = len(history_mgr.history_stack)

        has_sub = bool(
            hasattr(canvas, 'floating_sub_history') and
            canvas.floating_sub_history and
            canvas.selection_engine.floating_image and
            not canvas.selection_engine.floating_image.isNull()
        )

        if has_sub:
            from PyQt6.QtGui import QFont, QColor
            sub_index = getattr(canvas, 'floating_sub_index', len(canvas.floating_sub_history) - 1)
            for sub_i, snapshot in enumerate(canvas.floating_sub_history):
                if sub_i == 0:
                    continue
                display_idx = base_count + sub_i - 1
                action_label = snapshot.get('label', 'Transformar')
                item = QListWidgetItem(f"{display_idx}. {action_label}")
                font = item.font()
                font.setItalic(True)
                item.setFont(font)
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

                if sub_i <= sub_index:
                    item.setForeground(QColor(100, 180, 255))
                else:
                    item.setForeground(Qt.GlobalColor.gray)

                self.list_widget.addItem(item)

        curr_row = history_mgr.current_index
        if has_sub and hasattr(canvas, 'floating_sub_index') and canvas.floating_sub_index > 0:
            curr_row = base_count + canvas.floating_sub_index - 1

        if 0 <= curr_row < self.list_widget.count():
            self.list_widget.setCurrentRow(curr_row)

        can_undo = (history_mgr.current_index > 0) or (has_sub and getattr(canvas, 'floating_sub_index', 0) > 0)
        can_redo = (history_mgr.current_index < len(history_mgr.history_stack) - 1) or (has_sub and getattr(canvas, 'floating_sub_index', 0) < len(canvas.floating_sub_history) - 1)

        self.btn_undo.setEnabled(can_undo)
        self.btn_redo.setEnabled(can_redo)

        self.list_widget.blockSignals(False)

    def _on_item_clicked(self, item):
        row = self.list_widget.row(item)
        canvas = self._obtener_canvas()
        if canvas:
            canvas.jump_to_history_index(row)

    def _on_undo_clicked(self):
        canvas = self._obtener_canvas()
        if canvas:
            canvas.undo()

    def _on_redo_clicked(self):
        canvas = self._obtener_canvas()
        if canvas:
            canvas.redo()
