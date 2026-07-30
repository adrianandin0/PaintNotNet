import numpy as np
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton)
from PyQt6.QtGui import QImage, QColor
from PyQt6.QtCore import Qt, QEventLoop


class DialogoTonoSaturacion(QDialog):
    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.setWindowTitle("Tono / Saturación")
        self.setFixedWidth(300)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setModal(False)

        self.target_is_floating = canvas.asegurar_imagen_flotante()
        if self.target_is_floating:
            self.orig_image = canvas.selection_engine.floating_image.copy()
        else:
            self.orig_image = canvas.layer_mgr.buffer.copy()

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Tono (-180 a 180)
        lbl_tono = QLabel("Tono:")
        self.slider_tono = QSlider(Qt.Orientation.Horizontal)
        self.slider_tono.setRange(-180, 180)
        self.slider_tono.setValue(0)
        self.lbl_tono_val = QLabel("0°")

        l_tono = QHBoxLayout()
        l_tono.addWidget(lbl_tono)
        l_tono.addWidget(self.slider_tono)
        l_tono.addWidget(self.lbl_tono_val)
        layout.addLayout(l_tono)

        # Saturación (-100 a 100)
        lbl_sat = QLabel("Saturación:")
        self.slider_sat = QSlider(Qt.Orientation.Horizontal)
        self.slider_sat.setRange(-100, 100)
        self.slider_sat.setValue(0)
        self.lbl_sat_val = QLabel("0")

        l_sat = QHBoxLayout()
        l_sat.addWidget(lbl_sat)
        l_sat.addWidget(self.slider_sat)
        l_sat.addWidget(self.lbl_sat_val)
        layout.addLayout(l_sat)

        # Botones (Aceptar, Restablecer, Cancelar)
        l_btns = QHBoxLayout()
        btn_ok = QPushButton("Aceptar")
        btn_reset = QPushButton("Restablecer")
        btn_cancel = QPushButton("Cancelar")

        btn_ok.clicked.connect(self.accept)
        btn_reset.clicked.connect(self.restablecer)
        btn_cancel.clicked.connect(self.reject)

        l_btns.addWidget(btn_ok)
        l_btns.addWidget(btn_reset)
        l_btns.addWidget(btn_cancel)
        layout.addLayout(l_btns)

        self.slider_tono.valueChanged.connect(self.aplicar_vista_previa)
        self.slider_sat.valueChanged.connect(self.aplicar_vista_previa)

    def accept(self):
        if self.target_is_floating:
            self.canvas.push_floating_sub_state("Tono / Saturación")
        super().accept()

    def restablecer(self):
        self.slider_tono.blockSignals(True)
        self.slider_sat.blockSignals(True)
        self.slider_tono.setValue(0)
        self.slider_sat.setValue(0)
        self.lbl_tono_val.setText("0°")
        self.lbl_sat_val.setText("0")
        self.slider_tono.blockSignals(False)
        self.slider_sat.blockSignals(False)

        if self.target_is_floating:
            self.canvas.selection_engine.floating_image = self.orig_image.copy()
            if self.canvas.selection_engine.unscaled_floating_image:
                self.canvas.selection_engine.unscaled_floating_image = self.orig_image.copy()
        else:
            self.canvas.layer_mgr.buffer = self.orig_image.copy()
        self.canvas.update()

    def aplicar_vista_previa(self):
        h_shift = self.slider_tono.value()
        s_shift = self.slider_sat.value()

        self.lbl_tono_val.setText(f"{h_shift}°")
        self.lbl_sat_val.setText(f"{s_shift}")

        img = self.orig_image.copy()
        if h_shift == 0 and s_shift == 0:
            if self.target_is_floating:
                self.canvas.selection_engine.floating_image = img
            else:
                self.canvas.layer_mgr.buffer = img
            self.canvas.update()
            return

        ptr = img.bits()
        ptr.setsize(img.height() * img.bytesPerLine())
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((img.height(), img.width(), 4))

        b = arr[:, :, 0].astype(np.float32)
        g = arr[:, :, 1].astype(np.float32)
        r = arr[:, :, 2].astype(np.float32)

        if s_shift != 0:
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            sat_factor = max(0.0, 1.0 + s_shift / 100.0 * 1.5)
            r = lum + (r - lum) * sat_factor
            g = lum + (g - lum) * sat_factor
            b = lum + (b - lum) * sat_factor

        if h_shift != 0:
            rad = np.radians(h_shift)
            cos_a = np.cos(rad)
            sin_a = np.sin(rad)
            sqrt3 = 1.7320508
            r_new = r * (cos_a + (1 - cos_a)/3) + g * ((1 - cos_a)/3 - sin_a/sqrt3) + b * ((1 - cos_a)/3 + sin_a/sqrt3)
            g_new = r * ((1 - cos_a)/3 + sin_a/sqrt3) + g * (cos_a + (1 - cos_a)/3) + b * ((1 - cos_a)/3 - sin_a/sqrt3)
            b_new = r * ((1 - cos_a)/3 - sin_a/sqrt3) + g * ((1 - cos_a)/3 + sin_a/sqrt3) + b * (cos_a + (1 - cos_a)/3)
            r, g, b = r_new, g_new, b_new

        arr[:, :, 0] = np.clip(b, 0, 255).astype(np.uint8)
        arr[:, :, 1] = np.clip(g, 0, 255).astype(np.uint8)
        arr[:, :, 2] = np.clip(r, 0, 255).astype(np.uint8)

        if self.target_is_floating:
            self.canvas.selection_engine.floating_image = img
            if self.canvas.selection_engine.unscaled_floating_image:
                self.canvas.selection_engine.unscaled_floating_image = img.copy()
        else:
            self.canvas.layer_mgr.buffer = img
        self.canvas.update()

    def reject(self):
        if self.target_is_floating:
            self.canvas.selection_engine.floating_image = self.orig_image.copy()
            if self.canvas.selection_engine.unscaled_floating_image:
                self.canvas.selection_engine.unscaled_floating_image = self.orig_image.copy()
        else:
            self.canvas.layer_mgr.buffer = self.orig_image.copy()
        self.canvas.update()
        super().reject()


class DialogoBrilloContraste(QDialog):
    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.setWindowTitle("Brillo / Contraste")
        self.setFixedWidth(300)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setModal(False)

        self.target_is_floating = canvas.asegurar_imagen_flotante()
        if self.target_is_floating:
            self.orig_image = canvas.selection_engine.floating_image.copy()
        else:
            self.orig_image = canvas.layer_mgr.buffer.copy()

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Brillo (-100 a 100)
        lbl_brillo = QLabel("Brillo:")
        self.slider_brillo = QSlider(Qt.Orientation.Horizontal)
        self.slider_brillo.setRange(-100, 100)
        self.slider_brillo.setValue(0)
        self.lbl_brillo_val = QLabel("0")

        l_brillo = QHBoxLayout()
        l_brillo.addWidget(lbl_brillo)
        l_brillo.addWidget(self.slider_brillo)
        l_brillo.addWidget(self.lbl_brillo_val)
        layout.addLayout(l_brillo)

        # Contraste (-100 a 100)
        lbl_contraste = QLabel("Contraste:")
        self.slider_contraste = QSlider(Qt.Orientation.Horizontal)
        self.slider_contraste.setRange(-100, 100)
        self.slider_contraste.setValue(0)
        self.lbl_contraste_val = QLabel("0")

        l_contraste = QHBoxLayout()
        l_contraste.addWidget(lbl_contraste)
        l_contraste.addWidget(self.slider_contraste)
        l_contraste.addWidget(self.lbl_contraste_val)
        layout.addLayout(l_contraste)

        # Botones (Aceptar, Restablecer, Cancelar)
        l_btns = QHBoxLayout()
        btn_ok = QPushButton("Aceptar")
        btn_reset = QPushButton("Restablecer")
        btn_cancel = QPushButton("Cancelar")

        btn_ok.clicked.connect(self.accept)
        btn_reset.clicked.connect(self.restablecer)
        btn_cancel.clicked.connect(self.reject)

        l_btns.addWidget(btn_ok)
        l_btns.addWidget(btn_reset)
        l_btns.addWidget(btn_cancel)
        layout.addLayout(l_btns)

        self.slider_brillo.valueChanged.connect(self.aplicar_vista_previa)
        self.slider_contraste.valueChanged.connect(self.aplicar_vista_previa)

    def accept(self):
        if self.target_is_floating:
            self.canvas.push_floating_sub_state("Brillo / Contraste")
        super().accept()

    def restablecer(self):
        self.slider_brillo.blockSignals(True)
        self.slider_contraste.blockSignals(True)
        self.slider_brillo.setValue(0)
        self.slider_contraste.setValue(0)
        self.lbl_brillo_val.setText("0")
        self.lbl_contraste_val.setText("0")
        self.slider_brillo.blockSignals(False)
        self.slider_contraste.blockSignals(False)

        if self.target_is_floating:
            self.canvas.selection_engine.floating_image = self.orig_image.copy()
            if self.canvas.selection_engine.unscaled_floating_image:
                self.canvas.selection_engine.unscaled_floating_image = self.orig_image.copy()
        else:
            self.canvas.layer_mgr.buffer = self.orig_image.copy()
        self.canvas.update()

    def aplicar_vista_previa(self):
        b_shift = self.slider_brillo.value()
        c_shift = self.slider_contraste.value()

        self.lbl_brillo_val.setText(f"{b_shift}")
        self.lbl_contraste_val.setText(f"{c_shift}")

        img = self.orig_image.copy()
        if b_shift == 0 and c_shift == 0:
            if self.target_is_floating:
                self.canvas.selection_engine.floating_image = img
            else:
                self.canvas.layer_mgr.buffer = img
            self.canvas.update()
            return

        ptr = img.bits()
        ptr.setsize(img.height() * img.bytesPerLine())
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((img.height(), img.width(), 4))

        factor = (259.0 * (c_shift + 255.0)) / (255.0 * (259.0 - c_shift))
        lut = np.clip(factor * (np.arange(256, dtype=np.float32) - 128.0) + 128.0 + b_shift, 0, 255).astype(np.uint8)

        arr[:, :, :3] = lut[arr[:, :, :3]]

        if self.target_is_floating:
            self.canvas.selection_engine.floating_image = img
            if self.canvas.selection_engine.unscaled_floating_image:
                self.canvas.selection_engine.unscaled_floating_image = img.copy()
        else:
            self.canvas.layer_mgr.buffer = img
        self.canvas.update()

    def reject(self):
        if self.target_is_floating:
            self.canvas.selection_engine.floating_image = self.orig_image.copy()
            if self.canvas.selection_engine.unscaled_floating_image:
                self.canvas.selection_engine.unscaled_floating_image = self.orig_image.copy()
        else:
            self.canvas.layer_mgr.buffer = self.orig_image.copy()
        self.canvas.update()
        super().reject()


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

        accion_tono_sat = self.menu_ajustes.addAction(t("Tono / Saturación..."))
        accion_tono_sat.triggered.connect(self.tono_saturacion)

        accion_brillo_cont = self.menu_ajustes.addAction(t("Brillo / Contraste..."))
        accion_brillo_cont.triggered.connect(self.brillo_contraste)

        accion_bw = self.menu_ajustes.addAction(t("Blanco y Negro"))
        accion_bw.setShortcut("Ctrl+Shift+B")
        accion_bw.triggered.connect(self.blanco_y_negro)

        self.menu_ajustes.addSeparator()

        accion_invertir = self.menu_ajustes.addAction(t("Invertir colores"))
        accion_invertir.setShortcut("Ctrl+Shift+I")
        accion_invertir.triggered.connect(self.invertir_colores)

    def tono_saturacion(self):
        canvas = self.ventana.lienzo
        is_floating = bool(canvas.selection_engine.floating_image and not canvas.selection_engine.floating_image.isNull())
        if not is_floating:
            canvas.push_document_state("Tono / Saturación")

        dlg = DialogoTonoSaturacion(canvas, self.ventana)

        loop = QEventLoop()
        dlg.accepted.connect(loop.quit)
        dlg.rejected.connect(loop.quit)
        dlg.show()
        loop.exec()

        if dlg.result() != QDialog.DialogCode.Accepted:
            if not is_floating:
                canvas.undo()

    def brillo_contraste(self):
        canvas = self.ventana.lienzo
        is_floating = bool(canvas.selection_engine.floating_image and not canvas.selection_engine.floating_image.isNull())
        if not is_floating:
            canvas.push_document_state("Brillo / Contraste")

        dlg = DialogoBrilloContraste(canvas, self.ventana)

        loop = QEventLoop()
        dlg.accepted.connect(loop.quit)
        dlg.rejected.connect(loop.quit)
        dlg.show()
        loop.exec()

        if dlg.result() != QDialog.DialogCode.Accepted:
            if not is_floating:
                canvas.undo()

    def blanco_y_negro(self):
        canvas = self.ventana.lienzo
        is_floating = canvas.asegurar_imagen_flotante()
        if not is_floating:
            canvas.push_document_state("Blanco y negro")

        img = canvas.selection_engine.floating_image.copy() if is_floating else canvas.layer_mgr.buffer.copy()

        ptr = img.bits()
        ptr.setsize(img.height() * img.bytesPerLine())
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((img.height(), img.width(), 4))

        b = arr[:, :, 0].astype(np.float32)
        g = arr[:, :, 1].astype(np.float32)
        r = arr[:, :, 2].astype(np.float32)

        gray = (0.299 * r + 0.587 * g + 0.114 * b).astype(np.uint8)

        arr[:, :, 0] = gray
        arr[:, :, 1] = gray
        arr[:, :, 2] = gray

        if is_floating:
            canvas.selection_engine.floating_image = img
            if canvas.selection_engine.unscaled_floating_image:
                canvas.selection_engine.unscaled_floating_image = img.copy()
            canvas.push_floating_sub_state("Blanco y negro")
        else:
            canvas.layer_mgr.buffer = img
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
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((img.height(), img.width(), 4))

        arr[:, :, :3] = 255 - arr[:, :, :3]

        if is_floating:
            canvas.selection_engine.floating_image = img
            if canvas.selection_engine.unscaled_floating_image:
                canvas.selection_engine.unscaled_floating_image = img.copy()
            canvas.push_floating_sub_state("Invertir colores")
        else:
            canvas.layer_mgr.buffer = img
            canvas.actualizar_historial_gui()
        canvas.update()
