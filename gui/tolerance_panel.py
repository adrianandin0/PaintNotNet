from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider
from PyQt6.QtCore import Qt, pyqtSignal


class TolerancePanelWidget(QWidget):
    tolerance_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        l_hdr = QHBoxLayout()
        lbl_title = QLabel("Tolerancia:")
        lbl_title.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.lbl_val = QLabel("32%")
        self.lbl_val.setStyleSheet("font-size: 9px; font-weight: bold; color: #64B4FF;")

        l_hdr.addWidget(lbl_title)
        l_hdr.addStretch()
        l_hdr.addWidget(self.lbl_val)
        layout.addLayout(l_hdr)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(32)
        self.slider.setStyleSheet("QSlider { height: 16px; }")

        layout.addWidget(self.slider)

        self.slider.valueChanged.connect(self._on_value_changed)

    def _on_value_changed(self, val):
        self.lbl_val.setText(f"{val}%")
        self.tolerance_changed.emit(val)

    def obtener_tolerancia(self):
        return self.slider.value()
