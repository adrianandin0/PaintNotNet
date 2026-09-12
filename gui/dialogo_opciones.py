import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QSlider,
    QPushButton, QComboBox, QDialogButtonBox, QGroupBox, QCheckBox, QWidget, QSizePolicy
)
from PyQt6.QtCore import QSettings, QSize, Qt, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices
from core.i18n import t


class DialogoOpciones(QDialog):
    """Diálogo de Preferencias de Usuario armonizado y agrupado limpiamente."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("Preferencias de usuario"))
        self.setMinimumSize(580, 550)

        self.setStyleSheet("""
            QDialog {
                font-size: 11px;
            }
            QGroupBox {
                font-size: 11px;
                font-weight: normal;
                border-radius: 4px;
                margin-top: 6px;
                padding-top: 4px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 6px;
                font-weight: normal;
            }
            QLabel {
                font-size: 11px;
                font-weight: normal;
            }
            QComboBox, QLineEdit {
                font-size: 11px;
                padding: 2px 4px;
            }
            QCheckBox {
                font-size: 11px;
                font-weight: normal;
            }
        """)

        self.settings = QSettings("PaintNotNet", "PaintNotNet")

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # ── 1. Grupo 1: Espacio de Trabajo (Tema, Idioma, Reglas, Cuadrícula, Atajos) ──
        from core.theme import ThemeManager
        group_workspace = QGroupBox(t("Espacio de trabajo"))
        group_workspace.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout_ws = QVBoxLayout()
        layout_ws.setContentsMargins(10, 8, 10, 8)
        layout_ws.setSpacing(8)

        # Fila 1: Tema e Idioma lado a lado
        row_theme_lang = QHBoxLayout()
        row_theme_lang.setSpacing(8)

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

        row_theme_lang.addWidget(lbl_icon_theme)
        row_theme_lang.addWidget(QLabel(t("Tema:")))
        row_theme_lang.addWidget(self.combo_theme)

        row_theme_lang.addSpacing(16)

        lbl_icon_lang = QLabel()
        lbl_icon_lang.setPixmap(QIcon("gui/iconos/languages.png").pixmap(QSize(16, 16)))
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Español", "English", "Português", "Français"])
        default_lang = self.settings.value("language", "Español")
        idx_lang = self.combo_lang.findText(str(default_lang))
        if idx_lang >= 0:
            self.combo_lang.setCurrentIndex(idx_lang)

        row_theme_lang.addWidget(lbl_icon_lang)
        row_theme_lang.addWidget(QLabel(t("Idioma:")))
        row_theme_lang.addWidget(self.combo_lang)
        row_theme_lang.addStretch()

        layout_ws.addLayout(row_theme_lang)

        # Fila 2: Casillas de verificación del espacio de trabajo
        row_chks_ws = QHBoxLayout()
        row_chks_ws.setSpacing(12)

        self.chk_show_grid = QCheckBox(t("Mostrar cuadrícula de píxeles"))
        self.chk_show_grid.setChecked(self.settings.value("show_pixel_grid", False, type=bool))

        self.chk_show_rulers = QCheckBox(t("Mostrar reglas graduadas"))
        self.chk_show_rulers.setChecked(self.settings.value("show_rulers", False, type=bool))

        self.chk_show_shortcuts = QCheckBox(t("Mostrar atajos de teclado"))
        self.chk_show_shortcuts.setChecked(self.settings.value("show_shortcuts", True, type=bool))

        row_chks_ws.addWidget(self.chk_show_grid)
        row_chks_ws.addWidget(self.chk_show_rulers)
        row_chks_ws.addWidget(self.chk_show_shortcuts)
        row_chks_ws.addStretch()

        layout_ws.addLayout(row_chks_ws)

        # Fila 3: Unidad de regla
        row_ruler = QHBoxLayout()
        lbl_unit = QLabel(t("Unidad de regla:"))
        self.combo_ruler_unit = QComboBox()
        self.combo_ruler_unit.addItems([
            t("Centímetros (cm)"),
            t("Pulgadas (in)"),
            t("Píxeles (px)")
        ])
        self.ruler_unit_raw = ["cm", "in", "px"]
        default_unit = str(self.settings.value("ruler_unit", "cm"))
        if default_unit in self.ruler_unit_raw:
            self.combo_ruler_unit.setCurrentIndex(self.ruler_unit_raw.index(default_unit))

        row_ruler.addWidget(lbl_unit)
        row_ruler.addWidget(self.combo_ruler_unit)
        row_ruler.addStretch()

        layout_ws.addLayout(row_ruler)
        group_workspace.setLayout(layout_ws)
        layout.addWidget(group_workspace)

        # ── Grupo: Rendimiento y Memoria ──
        group_perf = QGroupBox(t("Rendimiento y memoria"))
        group_perf.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout_perf = QVBoxLayout()
        layout_perf.setContentsMargins(10, 8, 10, 8)
        layout_perf.setSpacing(8)

        row_ram = QHBoxLayout()
        row_ram.setSpacing(8)

        lbl_ram = QLabel(t("Límite de memoria del historial:"))
        self.slider_history_ram = QSlider(Qt.Orientation.Horizontal)
        self.slider_history_ram.setRange(128, 8192)
        self.slider_history_ram.setSingleStep(128)
        self.slider_history_ram.setPageStep(512)
        self.slider_history_ram.setFixedWidth(130)

        self.lbl_ram_val = QLabel("512 MB")
        self.lbl_ram_val.setMinimumWidth(55)
        self.lbl_ram_val.setStyleSheet("font-weight: bold;")

        def _update_ram_label(val):
            snapped = max(128, min(8192, round(val / 128.0) * 128))
            if snapped != val:
                self.slider_history_ram.blockSignals(True)
                self.slider_history_ram.setValue(snapped)
                self.slider_history_ram.blockSignals(False)
            self.lbl_ram_val.setText(f"{snapped} MB")

        self.slider_history_ram.valueChanged.connect(_update_ram_label)

        current_ram = self.settings.value("max_history_ram_mb", 512, type=int)
        current_ram = max(128, min(8192, round(current_ram / 128.0) * 128))
        self.slider_history_ram.setValue(current_ram)
        _update_ram_label(current_ram)

        lbl_ram_hint = QLabel(f"({t('512 MB recomendado')})")
        lbl_ram_hint.setStyleSheet("color: #999999; font-size: 11px;")

        row_ram.addWidget(lbl_ram)
        row_ram.addWidget(self.slider_history_ram)
        row_ram.addWidget(self.lbl_ram_val)
        row_ram.addWidget(lbl_ram_hint)
        row_ram.addStretch()

        self.chk_use_opengl = QCheckBox(t("Usar aceleración por hardware (OpenGL)"))
        use_opengl = self.settings.value("use_opengl", True, type=bool)
        self.chk_use_opengl.setChecked(use_opengl)

        layout_perf.addLayout(row_ram)
        layout_perf.addWidget(self.chk_use_opengl)
        group_perf.setLayout(layout_perf)
        layout.addWidget(group_perf)

        # ── 2. Grupo 2: Archivos y Guardado (Directorio, Formato, Guardar al cerrar) ──
        group_files = QGroupBox(t("Archivos y guardado"))
        group_files.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout_files = QVBoxLayout()
        layout_files.setContentsMargins(10, 8, 10, 8)
        layout_files.setSpacing(8)

        # Fila 1: Directorio predeterminado
        row_dir = QHBoxLayout()
        self.input_dir = QLineEdit()
        default_path = self.settings.value("default_dir", os.path.expanduser("~"))
        self.input_dir.setText(str(default_path))

        btn_examinar = QPushButton()
        btn_examinar.setIcon(QIcon("gui/iconos/folder.png"))
        btn_examinar.setIconSize(QSize(16, 16))
        btn_examinar.setFixedWidth(34)
        btn_examinar.setToolTip(t("Examinar directorio..."))
        btn_examinar.clicked.connect(self._on_examinar)

        row_dir.addWidget(QLabel(t("Directorio predeterminado:")))
        row_dir.addWidget(self.input_dir)
        row_dir.addWidget(btn_examinar)
        layout_files.addLayout(row_dir)

        # Fila 2: Formato predeterminado y Guardar al cerrar
        row_fmt_save = QHBoxLayout()
        row_fmt_save.setSpacing(8)

        lbl_icon_fmt = QLabel()
        lbl_icon_fmt.setPixmap(QIcon("gui/iconos/picture.png").pixmap(QSize(16, 16)))

        self.combo_format = QComboBox()
        self.combo_format.addItems([
            "PNG (*.png)",
            "PaintNotNet (*.pnn)",
            "JPG (*.jpg)",
            "WEBP (*.webp)",
            "GIF (*.gif)",
            "TIFF (*.tiff)",
            "BMP (*.bmp)",
            "ICO (*.ico)",
            "TGA (*.tga)",
        ])
        default_fmt = self.settings.value("default_format", "PNG (*.png)")
        idx = self.combo_format.findText(str(default_fmt))
        if idx >= 0:
            self.combo_format.setCurrentIndex(idx)

        self.chk_save_on_close = QCheckBox(t("Guardar cambios al cerrar"))
        self.chk_save_on_close.setChecked(self.settings.value("save_on_close", True, type=bool))

        row_fmt_save.addWidget(lbl_icon_fmt)
        row_fmt_save.addWidget(QLabel(t("Formato:")))
        row_fmt_save.addWidget(self.combo_format)
        row_fmt_save.addSpacing(24)
        row_fmt_save.addWidget(self.chk_save_on_close)
        row_fmt_save.addStretch()

        layout_files.addLayout(row_fmt_save)
        group_files.setLayout(layout_files)
        layout.addWidget(group_files)

        # ── 3. Grupo 3: Búsqueda de Imágenes Online ──
        group_online = QGroupBox(t("Búsqueda de imágenes online"))
        group_online.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout_online = QVBoxLayout()
        layout_online.setContentsMargins(10, 8, 10, 8)
        layout_online.setSpacing(8)

        self.chk_online_enabled = QCheckBox(t("Activar búsqueda de imágenes desde internet"))
        online_enabled = self.settings.value("online_search_enabled", False, type=bool)
        self.chk_online_enabled.setChecked(online_enabled)
        self.chk_online_enabled.toggled.connect(self._on_online_search_toggled)

        self.chk_online_free_only = QCheckBox(t("Usar solo fuentes sin clave (Wikimedia Commons)"))
        online_free_only = self.settings.value("online_search_free_only", False, type=bool)
        self.chk_online_free_only.setChecked(online_free_only)
        self.chk_online_free_only.toggled.connect(self._on_online_free_toggled)

        layout_online.addWidget(self.chk_online_enabled)
        layout_online.addWidget(self.chk_online_free_only)

        # Campos para API Keys
        self.widget_keys = QWidget()
        layout_keys = QVBoxLayout(self.widget_keys)
        layout_keys.setContentsMargins(0, 2, 0, 2)
        layout_keys.setSpacing(8)

        # Serper.dev Google Images API
        row_serper = QHBoxLayout()
        lbl_serper = QLabel("Serper API Key:")
        lbl_serper.setFixedWidth(120)
        self.input_api_serper = QLineEdit()
        self.input_api_serper.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_api_serper.setPlaceholderText(t("Clave de API Serper (Google)..."))
        self.input_api_serper.setText(str(self.settings.value("api_key_serper", "")))

        self.btn_show_serper = QPushButton()
        self.btn_show_serper.setIcon(QIcon("gui/iconos/eye.png"))
        self.btn_show_serper.setIconSize(QSize(14, 14))
        self.btn_show_serper.setFixedWidth(28)
        self.btn_show_serper.setCheckable(True)
        self.btn_show_serper.setToolTip(t("Mostrar/Ocultar clave"))
        self.btn_show_serper.toggled.connect(lambda checked, w=self.input_api_serper: w.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password))

        self.btn_link_serper = QPushButton(t("Obtener key gratis"))
        self.btn_link_serper.setFixedWidth(135)
        self.btn_link_serper.clicked.connect(lambda: self._abrir_url_externa("https://serper.dev/"))
        row_serper.addWidget(lbl_serper)
        row_serper.addWidget(self.input_api_serper)
        row_serper.addWidget(self.btn_show_serper)
        row_serper.addWidget(self.btn_link_serper)
        layout_keys.addLayout(row_serper)

        # Pexels
        row_pexels = QHBoxLayout()
        lbl_pexels = QLabel("Pexels API Key:")
        lbl_pexels.setFixedWidth(120)
        self.input_api_pexels = QLineEdit()
        self.input_api_pexels.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_api_pexels.setPlaceholderText(t("Clave de API Pexels..."))
        self.input_api_pexels.setText(str(self.settings.value("api_key_pexels", "")))

        self.btn_show_pexels = QPushButton()
        self.btn_show_pexels.setIcon(QIcon("gui/iconos/eye.png"))
        self.btn_show_pexels.setIconSize(QSize(14, 14))
        self.btn_show_pexels.setFixedWidth(28)
        self.btn_show_pexels.setCheckable(True)
        self.btn_show_pexels.setToolTip(t("Mostrar/Ocultar clave"))
        self.btn_show_pexels.toggled.connect(lambda checked, w=self.input_api_pexels: w.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password))

        self.btn_link_pexels = QPushButton(t("Obtener key gratis"))
        self.btn_link_pexels.setFixedWidth(135)
        self.btn_link_pexels.clicked.connect(lambda: self._abrir_url_externa("https://www.pexels.com/api/"))
        row_pexels.addWidget(lbl_pexels)
        row_pexels.addWidget(self.input_api_pexels)
        row_pexels.addWidget(self.btn_show_pexels)
        row_pexels.addWidget(self.btn_link_pexels)
        layout_keys.addLayout(row_pexels)

        # Unsplash
        row_unsplash = QHBoxLayout()
        lbl_unsplash = QLabel("Unsplash API Key:")
        lbl_unsplash.setFixedWidth(120)
        self.input_api_unsplash = QLineEdit()
        self.input_api_unsplash.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_api_unsplash.setPlaceholderText(t("Clave de API Unsplash..."))
        self.input_api_unsplash.setText(str(self.settings.value("api_key_unsplash", "")))

        self.btn_show_unsplash = QPushButton()
        self.btn_show_unsplash.setIcon(QIcon("gui/iconos/eye.png"))
        self.btn_show_unsplash.setIconSize(QSize(14, 14))
        self.btn_show_unsplash.setFixedWidth(28)
        self.btn_show_unsplash.setCheckable(True)
        self.btn_show_unsplash.setToolTip(t("Mostrar/Ocultar clave"))
        self.btn_show_unsplash.toggled.connect(lambda checked, w=self.input_api_unsplash: w.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password))

        self.btn_link_unsplash = QPushButton(t("Obtener key gratis"))
        self.btn_link_unsplash.setFixedWidth(135)
        self.btn_link_unsplash.clicked.connect(lambda: self._abrir_url_externa("https://unsplash.com/developers"))
        row_unsplash.addWidget(lbl_unsplash)
        row_unsplash.addWidget(self.input_api_unsplash)
        row_unsplash.addWidget(self.btn_show_unsplash)
        row_unsplash.addWidget(self.btn_link_unsplash)
        layout_keys.addLayout(row_unsplash)

        # Pixabay
        row_pixabay = QHBoxLayout()
        lbl_pixabay = QLabel("Pixabay API Key:")
        lbl_pixabay.setFixedWidth(120)
        self.input_api_pixabay = QLineEdit()
        self.input_api_pixabay.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_api_pixabay.setPlaceholderText(t("Clave de API Pixabay..."))
        self.input_api_pixabay.setText(str(self.settings.value("api_key_pixabay", "")))

        self.btn_show_pixabay = QPushButton()
        self.btn_show_pixabay.setIcon(QIcon("gui/iconos/eye.png"))
        self.btn_show_pixabay.setIconSize(QSize(14, 14))
        self.btn_show_pixabay.setFixedWidth(28)
        self.btn_show_pixabay.setCheckable(True)
        self.btn_show_pixabay.setToolTip(t("Mostrar/Ocultar clave"))
        self.btn_show_pixabay.toggled.connect(lambda checked, w=self.input_api_pixabay: w.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password))

        self.btn_link_pixabay = QPushButton(t("Obtener key gratis"))
        self.btn_link_pixabay.setFixedWidth(135)
        self.btn_link_pixabay.clicked.connect(lambda: self._abrir_url_externa("https://pixabay.com/api/docs/"))
        row_pixabay.addWidget(lbl_pixabay)
        row_pixabay.addWidget(self.input_api_pixabay)
        row_pixabay.addWidget(self.btn_show_pixabay)
        row_pixabay.addWidget(self.btn_link_pixabay)
        layout_keys.addLayout(row_pixabay)

        layout_online.addWidget(self.widget_keys)
        group_online.setLayout(layout_online)
        layout.addWidget(group_online)

        self._update_online_controls_state()

        # ── 4. Barra Inferior (Eliminar preferencias | Aceptar / Cancelar) ──
        layout_bottom = QHBoxLayout()
        layout_bottom.setContentsMargins(4, 4, 4, 2)

        self.btn_reset_prefs = QPushButton(t("Eliminar preferencias"))
        self.btn_reset_prefs.setIcon(QIcon("gui/iconos/bin.png"))
        self.btn_reset_prefs.setIconSize(QSize(14, 14))
        self.btn_reset_prefs.setToolTip(t("Eliminar todas las preferencias y restablecer a valores de fábrica"))
        self.btn_reset_prefs.clicked.connect(self._on_reset_preferences)
        layout_bottom.addWidget(self.btn_reset_prefs)

        layout_bottom.addStretch()

        btn_ok = QPushButton(t("Aceptar"))
        btn_cancel = QPushButton(t("Cancelar"))
        btn_ok.setFixedWidth(80)
        btn_cancel.setFixedWidth(80)
        btn_ok.clicked.connect(self._on_accept)
        btn_cancel.clicked.connect(self.reject)
        layout_bottom.addWidget(btn_ok)
        layout_bottom.addWidget(btn_cancel)

        layout.addLayout(layout_bottom)

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

    def _abrir_url_externa(self, url: str):
        import webbrowser
        try:
            if not QDesktopServices.openUrl(QUrl(url)):
                webbrowser.open(url)
        except Exception:
            webbrowser.open(url)

    def _on_online_search_toggled(self, checked: bool):
        self._update_online_controls_state()

    def _on_online_free_toggled(self, checked: bool):
        self._update_online_controls_state()

    def _update_online_controls_state(self):
        enabled = self.chk_online_enabled.isChecked()
        self.chk_online_free_only.setEnabled(enabled)
        free_only = self.chk_online_free_only.isChecked()

        keys_editable = enabled and not free_only
        self.input_api_serper.setEnabled(keys_editable)
        self.input_api_pexels.setEnabled(keys_editable)
        self.input_api_unsplash.setEnabled(keys_editable)
        self.input_api_pixabay.setEnabled(keys_editable)

        self.btn_show_serper.setEnabled(keys_editable)
        self.btn_show_pexels.setEnabled(keys_editable)
        self.btn_show_unsplash.setEnabled(keys_editable)
        self.btn_show_pixabay.setEnabled(keys_editable)

        # Mantener los botones de obtener key habilitados siempre que la búsqueda online esté activa
        self.btn_link_serper.setEnabled(enabled)
        self.btn_link_pexels.setEnabled(enabled)
        self.btn_link_unsplash.setEnabled(enabled)
        self.btn_link_pixabay.setEnabled(enabled)

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
        self.settings.setValue("show_shortcuts", self.chk_show_shortcuts.isChecked())

        self.settings.setValue("show_pixel_grid", self.chk_show_grid.isChecked())
        self.settings.setValue("show_rulers", self.chk_show_rulers.isChecked())

        # Guardar límite de memoria del historial y aceleración GPU
        max_ram_mb = self.slider_history_ram.value()
        max_ram_mb = max(128, min(8192, round(max_ram_mb / 128.0) * 128))
        self.settings.setValue("max_history_ram_mb", max_ram_mb)
        self.settings.setValue("use_opengl", self.chk_use_opengl.isChecked())

        # Guardar Opciones de Búsqueda de Imágenes Online
        self.settings.setValue("online_search_enabled", self.chk_online_enabled.isChecked())
        self.settings.setValue("online_search_free_only", self.chk_online_free_only.isChecked())
        self.settings.setValue("api_key_serper", self.input_api_serper.text().strip())
        self.settings.setValue("api_key_pexels", self.input_api_pexels.text().strip())
        self.settings.setValue("api_key_unsplash", self.input_api_unsplash.text().strip())
        self.settings.setValue("api_key_pixabay", self.input_api_pixabay.text().strip())

        unit_idx = self.combo_ruler_unit.currentIndex()
        if 0 <= unit_idx < len(self.ruler_unit_raw):
            ruler_unit = self.ruler_unit_raw[unit_idx]
            self.settings.setValue("ruler_unit", ruler_unit)
        else:
            ruler_unit = "cm"

        I18nManager().establecer_idioma(nuevo_idioma)

        parent = self.parent()
        if parent:
            if hasattr(parent, 'bottom_bar') and parent.bottom_bar:
                parent.bottom_bar.chk_grid.setChecked(self.chk_show_grid.isChecked())
                parent.bottom_bar.chk_rulers.setChecked(self.chk_show_rulers.isChecked())
            if hasattr(parent, 'tab_widget') and parent.tab_widget:
                for i in range(parent.tab_widget.count()):
                    container = parent.tab_widget.widget(i)
                    if container:
                        if hasattr(container, 'canvas') and container.canvas and hasattr(container.canvas, 'history_mgr'):
                            container.canvas.history_mgr.set_max_memory_mb(max_ram_mb)
                        if hasattr(container, 'corner'):
                            container.corner.set_unit(ruler_unit)
                        if hasattr(container, 'top_ruler'):
                            container.top_ruler.set_unit(ruler_unit)
                        if hasattr(container, 'left_ruler'):
                            container.left_ruler.set_unit(ruler_unit)

            if hasattr(parent, 'tool_panel') and parent.tool_panel:
                parent.tool_panel.actualizar_insignias_atajos()
            if hasattr(parent, 'retraducir_ui'):
                parent.retraducir_ui()

        self.accept()
