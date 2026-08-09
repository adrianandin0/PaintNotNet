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
        self.setWindowTitle(t("Preferencias de usuario"))
        self.setFixedSize(460, 335)

        self.setStyleSheet("""
            QDialog {
                font-size: 11px;
            }
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 4px;
            }
            QLabel {
                font-size: 11px;
            }
            QComboBox, QLineEdit {
                font-size: 11px;
                padding: 2px 4px;
            }
            QCheckBox {
                font-size: 11px;
            }
        """)

        self.settings = QSettings("PaintNotNet", "PaintNotNet")

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        # 1. Tema de la interfaz
        from core.theme import ThemeManager
        group_theme = QGroupBox(t("Tema de la interfaz"))
        layout_theme = QHBoxLayout()
        layout_theme.setContentsMargins(8, 6, 8, 6)
        layout_theme.setSpacing(6)

        lbl_icon_theme = QLabel()
        lbl_icon_theme.setPixmap(QIcon("gui/iconos/dark-mode.png").pixmap(QSize(16, 16)))

        self.combo_theme = QComboBox()
        temas_disponibles = ThemeManager().obtener_temas_disponibles()
        self.combo_theme.addItems([t(item) for item in temas_disponibles])
        self.combo_theme_raw = temas_disponibles

        default_theme = self.settings.value("theme", "Definido por el sistema")
        idx_theme = -1
        for i, raw_t in enumerate(temas_disponibles):
            if raw_t.lower() == str(default_theme).lower():
                idx_theme = i
                break
        if idx_theme >= 0:
            self.combo_theme.setCurrentIndex(idx_theme)

        layout_theme.addWidget(lbl_icon_theme)
        layout_theme.addWidget(QLabel(t("Tema:")))
        layout_theme.addStretch()
        layout_theme.addWidget(self.combo_theme)
        group_theme.setLayout(layout_theme)
        layout.addWidget(group_theme)

        # 2. Idioma
        group_lang = QGroupBox(t("Idioma / Language"))
        layout_lang = QHBoxLayout()
        layout_lang.setContentsMargins(8, 6, 8, 6)
        layout_lang.setSpacing(6)

        lbl_icon_lang = QLabel()
        lbl_icon_lang.setPixmap(QIcon("gui/iconos/languages.png").pixmap(QSize(16, 16)))

        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Español", "English"])
        default_lang = self.settings.value("language", "Español")
        idx_lang = self.combo_lang.findText(str(default_lang))
        if idx_lang >= 0:
            self.combo_lang.setCurrentIndex(idx_lang)

        layout_lang.addWidget(lbl_icon_lang)
        layout_lang.addWidget(QLabel(t("Idioma:")))
        layout_lang.addStretch()
        layout_lang.addWidget(self.combo_lang)
        group_lang.setLayout(layout_lang)
        layout.addWidget(group_lang)

        # 3. Directorio Predeterminado
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

        layout_dir.addWidget(btn_examinar)
        layout_dir.addWidget(self.input_dir)
        group_dir.setLayout(layout_dir)
        layout.addWidget(group_dir)

        # 4. Formato Predeterminado
        group_format = QGroupBox(t("Formato predeterminado"))
        layout_format = QHBoxLayout()
        layout_format.setContentsMargins(8, 6, 8, 6)
        layout_format.setSpacing(6)

        lbl_icon_fmt = QLabel()
        lbl_icon_fmt.setPixmap(QIcon("gui/iconos/picture.png").pixmap(QSize(16, 16)))

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

        layout_format.addWidget(lbl_icon_fmt)
        layout_format.addWidget(QLabel(t("Formato:")))
        layout_format.addStretch()
        layout_format.addWidget(self.combo_format)
        group_format.setLayout(layout_format)
        layout.addWidget(group_format)

        # 5. Guardar cambios al cerrar y Eliminar preferencias
        layout_chk = QHBoxLayout()
        layout_chk.setContentsMargins(0, 0, 0, 0)

        self.chk_save_on_close = QCheckBox(t("Guardar cambios al cerrar"))
        save_on_close = self.settings.value("save_on_close", True, type=bool)
        self.chk_save_on_close.setChecked(save_on_close)
        layout_chk.addWidget(self.chk_save_on_close)

        layout_chk.addStretch()

        self.btn_reset_prefs = QPushButton(t("Eliminar preferencias de usuario"))
        self.btn_reset_prefs.setIcon(QIcon("gui/iconos/bin.png"))
        self.btn_reset_prefs.setIconSize(QSize(14, 14))
        self.btn_reset_prefs.setToolTip(t("Eliminar todas las preferencias y restablecer a valores de fábrica"))
        self.btn_reset_prefs.clicked.connect(self._on_reset_preferences)
        layout_chk.addWidget(self.btn_reset_prefs)

        layout.addLayout(layout_chk)

        # Botones Aceptar / Cancelar
        layout_buttons = QHBoxLayout()
        layout_buttons.addStretch()
        btn_ok = QPushButton(t("Aceptar"))
        btn_cancel = QPushButton(t("Cancelar"))
        btn_ok.setFixedWidth(80)
        btn_cancel.setFixedWidth(80)
        btn_ok.clicked.connect(self._on_accept)
        btn_cancel.clicked.connect(self.reject)
        layout_buttons.addWidget(btn_ok)
        layout_buttons.addWidget(btn_cancel)
        layout.addLayout(layout_buttons)

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

    def _on_reset_preferences(self):
        from PyQt6.QtWidgets import QMessageBox

        confirm = QMessageBox.question(
            self,
            t("Eliminar preferencias"),
            t("¿Estás seguro de que deseas eliminar todas las preferencias de usuario y restablecer el programa a los valores predeterminados de fábrica?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            parent = self.parent()
            if parent and hasattr(parent, 'reset_panel_layout_and_preferences'):
                parent.reset_panel_layout_and_preferences()
            else:
                QSettings("PaintNotNet", "PaintNotNet").clear()
                QSettings("PaintNotNet", "EffectsPanel").clear()
                QSettings("PaintNotNet", "RecentFiles").clear()

            QMessageBox.information(
                self,
                t("Preferencias eliminadas"),
                t("Las preferencias se han eliminado. El programa se restablecerá completamente al reiniciar la aplicación.")
            )
            self.accept()

    def _on_accept(self):
        from core.i18n import I18nManager
        from core.theme import ThemeManager

        nuevo_tema_idx = self.combo_theme.currentIndex()
        if 0 <= nuevo_tema_idx < len(self.combo_theme_raw):
            nuevo_tema = self.combo_theme_raw[nuevo_tema_idx]
            self.settings.setValue("theme", nuevo_tema)
            ThemeManager().establecer_tema(nuevo_tema, self.parent())

        nuevo_idioma = self.combo_lang.currentText()
        self.settings.setValue("language", nuevo_idioma)
        self.settings.setValue("default_dir", self.input_dir.text())
        self.settings.setValue("default_format", self.combo_format.currentText())
        self.settings.setValue("save_on_close", self.chk_save_on_close.isChecked())

        I18nManager().establecer_idioma(nuevo_idioma)

        if self.parent() and hasattr(self.parent(), 'retraducir_ui'):
            self.parent().retraducir_ui()

        self.accept()

