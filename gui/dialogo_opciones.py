import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDialogButtonBox, QGroupBox, QCheckBox
)
from PyQt6.QtCore import QSettings, QSize, Qt
from PyQt6.QtGui import QIcon
from core.i18n import t


class DialogoOpciones(QDialog):
    """Diálogo de Preferencias de Usuario compacto y con fuentes legibles."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferencias de usuario")
        self.setFixedSize(370, 275)

        self.setStyleSheet("""
            QDialog {
                font-size: 11px;
            }
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
                color: #64B4FF;
                border: 1px solid #686868;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 4px;
                color: #64B4FF;
            }
            QLabel {
                font-size: 11px;
                color: #DDDDDD;
            }
            QComboBox, QLineEdit {
                font-size: 11px;
                padding: 2px 4px;
            }
            QCheckBox {
                font-size: 11px;
                color: #DDDDDD;
            }
        """)

        self.settings = QSettings("PaintNotNet", "PaintNotNet")

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        # 1. Idioma
        group_lang = QGroupBox(t("Idioma / Language"))
        layout_lang = QHBoxLayout()
        layout_lang.setContentsMargins(8, 6, 8, 6)
        layout_lang.setSpacing(8)

        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Español", "English"])
        default_lang = self.settings.value("language", "Español")
        idx_lang = self.combo_lang.findText(str(default_lang))
        if idx_lang >= 0:
            self.combo_lang.setCurrentIndex(idx_lang)

        layout_lang.addWidget(QLabel(t("Idioma:")))
        layout_lang.addWidget(self.combo_lang)
        group_lang.setLayout(layout_lang)
        layout.addWidget(group_lang)

        # 2. Directorio Predeterminado
        group_dir = QGroupBox(t("Directorio predeterminado"))
        layout_dir = QHBoxLayout()
        layout_dir.setContentsMargins(8, 6, 8, 6)
        layout_dir.setSpacing(6)

        self.input_dir = QLineEdit()
        default_path = self.settings.value("default_dir", os.path.expanduser("~"))
        self.input_dir.setText(str(default_path))

        btn_examinar = QPushButton()
        btn_examinar.setIcon(QIcon("gui/iconos/folder.png"))
        btn_examinar.setIconSize(QSize(18, 18))
        btn_examinar.setFixedWidth(34)
        btn_examinar.setToolTip("Examinar directorio...")
        btn_examinar.clicked.connect(self._on_examinar)

        layout_dir.addWidget(self.input_dir)
        layout_dir.addWidget(btn_examinar)
        group_dir.setLayout(layout_dir)
        layout.addWidget(group_dir)

        # 3. Formato Predeterminado
        group_format = QGroupBox(t("Formato predeterminado"))
        layout_format = QHBoxLayout()
        layout_format.setContentsMargins(8, 6, 8, 6)
        layout_format.setSpacing(8)

        self.combo_format = QComboBox()
        self.combo_format.addItems([
            "PNG (*.png)",
            "PaintNotNet (*.pnn)",
            "JPG (*.jpg)",
            "BMP (*.bmp)",
            "GIF (*.gif)"
        ])
        default_fmt = self.settings.value("default_format", "PNG (*.png)")
        idx = self.combo_format.findText(str(default_fmt))
        if idx >= 0:
            self.combo_format.setCurrentIndex(idx)

        layout_format.addWidget(QLabel(t("Formato:")))
        layout_format.addWidget(self.combo_format)
        group_format.setLayout(layout_format)
        layout.addWidget(group_format)

        # 4. Guardar cambios al cerrar
        self.chk_save_on_close = QCheckBox(t("Guardar cambios al cerrar"))
        save_on_close = self.settings.value("save_on_close", True, type=bool)
        self.chk_save_on_close.setChecked(save_on_close)
        layout.addWidget(self.chk_save_on_close)

        # Botones OK / Cancel
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _on_examinar(self):
        from gui.dialogo_archivo import DialogoArchivo
        directorio_actual = self.input_dir.text().strip()
        if not directorio_actual or not os.path.isdir(directorio_actual):
            import os as _os
            directorio_actual = _os.path.expanduser('~')
        dialogo = DialogoArchivo(
            parent=self,
            modo="directorio",
            directorio=directorio_actual,
            titulo="Seleccionar directorio predeterminado"
        )
        if dialogo.exec() and dialogo.ruta_seleccionada():
            self.input_dir.setText(dialogo.ruta_seleccionada())

    def _on_accept(self):
        from core.i18n import I18nManager
        nuevo_idioma = self.combo_lang.currentText()
        self.settings.setValue("language", nuevo_idioma)
        self.settings.setValue("default_dir", self.input_dir.text())
        self.settings.setValue("default_format", self.combo_format.currentText())
        self.settings.setValue("save_on_close", self.chk_save_on_close.isChecked())

        I18nManager().establecer_idioma(nuevo_idioma)

        if self.parent() and hasattr(self.parent(), 'retraducir_ui'):
            self.parent().retraducir_ui()

        self.accept()
