"""
gui/dialogo_pexels.py — Diálogo de búsqueda e inserción de imágenes desde Internet con paginación (40 por página).
Manejo seguro de hilos QThread para evitar bloqueos y cierres inesperados.
"""
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QScrollArea, QWidget, QGridLayout,
    QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QRect
from PyQt6.QtGui import QIcon, QPixmap, QImage, QPainter, QColor, QPen
from core.i18n import t
from core.pexels import PexelsAPIClient


# ---------------------------------------------------------------------------
# Workers asíncronos para búsquedas y descargas con cancelación segura
# ---------------------------------------------------------------------------

class _SearchWorker(QThread):
    results_ready = pyqtSignal(list, str)

    def __init__(self, query: str, is_transparent: bool, page: int = 1):
        super().__init__()
        self.query = query
        self.is_transparent = is_transparent
        self.page = page
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            photos = PexelsAPIClient.search_photos(self.query, "DuckDuckGo", self.is_transparent, page=self.page, per_page=40)
            if not self._is_cancelled:
                self.results_ready.emit(photos, "")
        except Exception as e:
            if not self._is_cancelled:
                self.results_ready.emit([], str(e))


class _DownloadWorker(QThread):
    download_finished = pyqtSignal(bytes, str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            data = PexelsAPIClient.download_bytes(self.url)
            if self._is_cancelled:
                return
            if data:
                self.download_finished.emit(data, "")
            else:
                self.download_finished.emit(b"", "Error al descargar la imagen.")
        except Exception as e:
            if not self._is_cancelled:
                self.download_finished.emit(b"", str(e))


# ---------------------------------------------------------------------------
# Tarjeta de Imagen limpia con cancelación de hilo
# ---------------------------------------------------------------------------

class _ImageCardWidget(QPushButton):
    selected_changed = pyqtSignal(object)
    double_clicked   = pyqtSignal(object)

    def __init__(self, photo_data: dict, parent_dialog=None):
        super().__init__(parent_dialog)
        self.photo_data = photo_data
        self.parent_dialog = parent_dialog
        self.is_selected = False
        self.pixmap: QPixmap | None = None
        self.worker: _DownloadWorker | None = None
        self.setFixedSize(140, 105)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._start_preview_download()
        self._update_style()

    def _start_preview_download(self):
        url = self.photo_data.get("preview_url")
        if not url:
            return
        self.worker = _DownloadWorker(url)
        self.worker.download_finished.connect(self._on_preview_loaded)
        if self.parent_dialog and hasattr(self.parent_dialog, '_track_worker'):
            self.parent_dialog._track_worker(self.worker)
        self.worker.start()

    def cancel_download(self):
        if self.worker:
            try:
                self.worker.download_finished.disconnect()
            except Exception:
                pass
            self.worker.cancel()
            if self.worker.isRunning():
                self.worker.quit()
                self.worker.wait(50)
            self.worker = None

    def _on_preview_loaded(self, data: bytes, err: str):
        if data:
            qimg = QImage.fromData(data)
            if not qimg.isNull():
                self.pixmap = QPixmap.fromImage(qimg)
                self.update()

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self._update_style()

    def _update_style(self):
        if self.is_selected:
            self.setStyleSheet("""
                _ImageCardWidget {
                    border: 3px solid #0078D7;
                    border-radius: 5px;
                    background-color: #0078D7;
                }
            """)
        else:
            self.setStyleSheet("""
                _ImageCardWidget {
                    border: 2px solid transparent;
                    border-radius: 5px;
                    background-color: #2B2B2B;
                }
                _ImageCardWidget:hover {
                    border: 2px solid #64B4FF;
                }
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected_changed.emit(self)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self)
        super().mouseDoubleClickEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()

        # 1. Fondo de cuadrícula de transparencia
        sq = 6
        c1 = QColor(240, 240, 240)
        c2 = QColor(190, 190, 190)
        for y in range(4, h - 4, sq):
            for x in range(4, w - 4, sq):
                c = c1 if ((x // sq) + (y // sq)) % 2 == 0 else c2
                painter.fillRect(x, y, sq, sq, c)

        # 2. Dibujar imagen escalada manteniendo relación de aspecto
        if self.pixmap and not self.pixmap.isNull():
            scaled = self.pixmap.scaled(
                w - 8, h - 8,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            dx = (w - scaled.width()) // 2
            dy = (h - scaled.height()) // 2
            painter.drawPixmap(dx, dy, scaled)
        else:
            painter.setPen(QPen(QColor(150, 150, 150), 1))
            painter.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "...")


# ---------------------------------------------------------------------------
# Diálogo Principal
# ---------------------------------------------------------------------------

class DialogoBusquedaPexels(QDialog):
    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.selected_card: _ImageCardWidget | None = None
        self.cards = []
        self.current_page = 1
        self.search_worker: _SearchWorker | None = None
        self.download_worker: _DownloadWorker | None = None
        self._active_workers = set()

        self.setWindowTitle(t("Insertar desde Internet"))
        self.resize(720, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # ── Barra Superior de Búsqueda ───────────────────────────────────
        top_layout = QHBoxLayout()
        top_layout.setSpacing(6)

        lbl_icon = QLabel()
        lbl_icon.setPixmap(QIcon("gui/iconos/internet.png").pixmap(QSize(20, 20)))
        top_layout.addWidget(lbl_icon)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText(t("Buscar fotos en HD..."))
        self.input_search.returnPressed.connect(self._on_new_search)
        top_layout.addWidget(self.input_search)

        self.chk_transparent = QCheckBox(t("Transparente (PNG)"))
        self.chk_transparent.stateChanged.connect(self._on_new_search)
        top_layout.addWidget(self.chk_transparent)

        self.btn_search = QPushButton(t("Buscar"))
        self.btn_search.setIcon(QIcon("gui/iconos/zoom.png"))
        self.btn_search.setIconSize(QSize(16, 16))
        self.btn_search.clicked.connect(self._on_new_search)
        top_layout.addWidget(self.btn_search)

        layout.addLayout(top_layout)

        # ── Área Central: Galería de Miniaturas ─────────────────────────
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #3C3C3C;
                border-radius: 4px;
                background-color: #1E1E1E;
            }
        """)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(8, 8, 8, 8)
        self.grid_layout.setSpacing(8)

        self.scroll_area.setWidget(self.grid_container)
        layout.addWidget(self.scroll_area)

        # ── Barra de Paginación y Estado ─────────────────────────────────
        page_layout = QHBoxLayout()
        page_layout.setSpacing(8)

        self.lbl_status = QLabel(t("Realiza una búsqueda para ver imágenes."))
        self.lbl_status.setStyleSheet("color: #AAAAAA; font-size: 11px;")
        page_layout.addWidget(self.lbl_status)
        page_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedWidth(100)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setVisible(False)
        page_layout.addWidget(self.progress_bar)

        # Botones de Paginación (< Anterior | Página X | Siguiente >)
        self.btn_prev = QPushButton(t("< Anterior"))
        self.btn_prev.setMinimumWidth(80)
        self.btn_prev.setEnabled(False)
        self.btn_prev.clicked.connect(self._on_prev_page)
        page_layout.addWidget(self.btn_prev)

        self.lbl_page = QLabel(t("Página 1"))
        self.lbl_page.setStyleSheet("font-weight: bold; font-size: 11px; padding: 0 4px;")
        page_layout.addWidget(self.lbl_page)

        self.btn_next = QPushButton(t("Siguiente >"))
        self.btn_next.setMinimumWidth(80)
        self.btn_next.setEnabled(False)
        self.btn_next.clicked.connect(self._on_next_page)
        page_layout.addWidget(self.btn_next)

        layout.addLayout(page_layout)

        # ── Botones Aceptar / Cancelar ───────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_insert = QPushButton(t("Insertar"))
        self.btn_insert.setIcon(QIcon("gui/iconos/picture.png"))
        self.btn_insert.setIconSize(QSize(16, 16))
        self.btn_insert.setMinimumWidth(85)
        self.btn_insert.setMinimumHeight(26)
        self.btn_insert.setEnabled(False)
        self.btn_insert.clicked.connect(self._on_insert)
        btn_layout.addWidget(self.btn_insert)

        self.btn_cancel = QPushButton(t("Cancelar"))
        self.btn_cancel.setIcon(QIcon("gui/iconos/cancel.png"))
        self.btn_cancel.setIconSize(QSize(16, 16))
        self.btn_cancel.setMinimumWidth(85)
        self.btn_cancel.setMinimumHeight(26)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

        # Cargar búsqueda predeterminada
        self.input_search.setText("paisaje")
        self._on_new_search()

    def _track_worker(self, worker):
        if not worker:
            return
        self._active_workers.add(worker)
        worker.finished.connect(lambda: self._active_workers.discard(worker))

    def _stop_all_workers(self):
        for w in list(self._active_workers):
            try:
                if hasattr(w, 'cancel'):
                    w.cancel()
                if w.isRunning():
                    w.quit()
                    w.wait(50)
            except Exception:
                pass
        self._active_workers.clear()

    def closeEvent(self, event):
        self._stop_all_workers()
        super().closeEvent(event)

    def reject(self):
        self._stop_all_workers()
        super().reject()

    def _on_new_search(self):
        self.current_page = 1
        self._fetch_page()

    def _on_prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._fetch_page()

    def _on_next_page(self):
        self.current_page += 1
        self._fetch_page()

    def _fetch_page(self):
        query = self.input_search.text().strip()
        if not query:
            return

        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.cancel()
            try:
                self.search_worker.results_ready.disconnect()
            except Exception:
                pass
            self.search_worker.quit()
            self.search_worker.wait(50)

        self._clear_grid()
        msg_loading = t("Cargando página %1...").replace("%1", str(self.current_page))
        self.lbl_status.setText(msg_loading)
        self.lbl_page.setText(t("Página %1").replace("%1", str(self.current_page)))

        self.progress_bar.setVisible(True)
        self.btn_search.setEnabled(False)
        self.btn_insert.setEnabled(False)
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)

        is_trans = self.chk_transparent.isChecked()
        self.search_worker = _SearchWorker(query, is_trans, page=self.current_page)
        self.search_worker.results_ready.connect(self._on_results_ready)
        self._track_worker(self.search_worker)
        self.search_worker.start()

    def _clear_grid(self):
        self.selected_card = None
        for card in self.cards:
            card.cancel_download()
            self.grid_layout.removeWidget(card)
            card.deleteLater()
        self.cards.clear()

    def _on_results_ready(self, photos: list, err_msg: str):
        self.progress_bar.setVisible(False)
        self.btn_search.setEnabled(True)
        self.btn_prev.setEnabled(self.current_page > 1)

        if err_msg or not photos:
            self.lbl_status.setText(t("No se encontraron imágenes para la búsqueda."))
            self.btn_next.setEnabled(False)
            return

        # 4 columnas (entran de a 4 por fila)
        cols = 4
        for idx, photo in enumerate(photos):
            card = _ImageCardWidget(photo, self)
            card.selected_changed.connect(self._on_card_selected)
            card.double_clicked.connect(self._on_card_double_clicked)
            r = idx // cols
            c = idx % cols
            self.grid_layout.addWidget(card, r, c)
            self.cards.append(card)

        self.btn_next.setEnabled(len(photos) >= 10)
        msg = t("Cargadas %1 imágenes (Página %2).").replace("%1", str(len(photos))).replace("%2", str(self.current_page))
        self.lbl_status.setText(msg)

    def _on_card_selected(self, card: _ImageCardWidget):
        for c in self.cards:
            c.set_selected(c == card)
        self.selected_card = card
        self.btn_insert.setEnabled(True)

    def _on_card_double_clicked(self, card: _ImageCardWidget):
        self._on_card_selected(card)
        self._on_insert()

    def _on_insert(self):
        if not self.selected_card:
            return

        download_url = self.selected_card.photo_data.get("download_url")
        if not download_url:
            return

        self.lbl_status.setText(t("Descargando imagen..."))
        self.progress_bar.setVisible(True)
        self.btn_insert.setEnabled(False)
        self.btn_cancel.setEnabled(False)

        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.cancel()
            try:
                self.download_worker.download_finished.disconnect()
            except Exception:
                pass
            self.download_worker.quit()
            self.download_worker.wait(50)

        self.download_worker = _DownloadWorker(download_url)
        self.download_worker.download_finished.connect(self._on_full_image_downloaded)
        self._track_worker(self.download_worker)
        self.download_worker.start()

    def _on_full_image_downloaded(self, data: bytes, err: str):
        self.progress_bar.setVisible(False)
        self.btn_cancel.setEnabled(True)

        if err or not data:
            self.lbl_status.setText(t("No se pudo descargar la imagen seleccionada."))
            self.btn_insert.setEnabled(True)
            return

        qimg = QImage.fromData(data)
        if qimg.isNull():
            self.lbl_status.setText(t("No se pudo descargar la imagen seleccionada."))
            self.btn_insert.setEnabled(True)
            return

        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.insertar_qimage(qimg)

        self.accept()
