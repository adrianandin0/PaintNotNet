from PyQt6.QtWidgets import QToolBar, QWidget, QHBoxLayout, QLabel, QSpinBox, QSlider, QComboBox, QCheckBox, QStyle, QAbstractSpinBox, QFontComboBox, QPushButton, QToolButton, QButtonGroup
from PyQt6.QtGui import QIcon, QAction, QFont
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QSettings
from gui.effects_panel import _EffectColorSlot, _LightDirectionWidget
from core.i18n import t


class TopToolBarWidget(QToolBar):
    grosor_changed = pyqtSignal(int)
    tolerancia_changed = pyqtSignal(int)

    def __init__(self, main_window=None):
        super().__init__("Barra de Herramientas General", main_window)
        self.main_window = main_window
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(QSize(24, 24))
        self.setStyleSheet("QToolBar { spacing: 4px; padding: 2px; }")

        # 0. Nueva Pestaña (+)
        self.action_nueva_pestana = QAction(QIcon("gui/iconos/new.png"), "Nueva Pestaña", self)
        self.action_nueva_pestana.setToolTip("Nueva Pestaña (Ctrl+N)")
        self.addAction(self.action_nueva_pestana)

        # 1. Abrir
        self.action_abrir = QAction(QIcon("gui/iconos/open.png"), "Abrir", self)
        self.action_abrir.setToolTip("Abrir imagen (Ctrl+O)")
        self.addAction(self.action_abrir)

        # 2. Guardar
        self.action_guardar = QAction(QIcon("gui/iconos/save.png"), "Guardar", self)
        self.action_guardar.setToolTip("Guardar imagen (Ctrl+S)")
        self.addAction(self.action_guardar)

        self.addSeparator()

        # 3. Cortar
        self.action_cortar = QAction(QIcon("gui/iconos/cut.png"), "Cortar", self)
        self.action_cortar.setToolTip("Cortar selección (Ctrl+X)")
        self.addAction(self.action_cortar)

        # 4. Copiar
        self.action_copiar = QAction(QIcon("gui/iconos/copy.png"), "Copiar", self)
        self.action_copiar.setToolTip("Copiar selección (Ctrl+C)")
        self.addAction(self.action_copiar)

        # 5. Pegar
        self.action_pegar = QAction(QIcon("gui/iconos/paste.png"), "Pegar", self)
        self.action_pegar.setToolTip("Pegar contenido (Ctrl+V)")
        self.addAction(self.action_pegar)

        # 6. Recortar a selección
        self.action_crop = QAction(QIcon("gui/iconos/crop.png"), "Recortar", self)
        self.action_crop.setToolTip("Recortar a selección")
        self.action_crop.triggered.connect(self._on_crop_clicked)
        self.addAction(self.action_crop)

        # 6. Selector de Grosor / Ancho Global
        self.lbl_grosor = QLabel(" Grosor: ")
        self.lbl_grosor.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.act_lbl_grosor = self.addWidget(self.lbl_grosor)

        self.spin_grosor = QSpinBox()
        self.spin_grosor.setRange(1, 9999)
        self.spin_grosor.setValue(3)
        self.spin_grosor.setSuffix(" px")
        self.spin_grosor.setFixedWidth(65)
        self.spin_grosor.setFixedHeight(22)
        self.spin_grosor.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_grosor.setStyleSheet("font-size: 11px; padding: 1px 4px;")
        self.spin_grosor.valueChanged.connect(self._on_grosor_changed)
        self.act_spin_grosor = self.addWidget(self.spin_grosor)

        self.sep_grosor = self.addSeparator()

        # Selector de Forma de Pincel (Circular vs Cuadrada)
        self.lbl_forma_pincel = QLabel(t("Forma:"))
        self.lbl_forma_pincel.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.act_lbl_forma_pincel = self.addWidget(self.lbl_forma_pincel)

        self.btn_group_forma = QButtonGroup(self)
        self.btn_group_forma.setExclusive(True)

        self.btn_forma_circular = QToolButton()
        self.btn_forma_circular.setIcon(QIcon("gui/iconos/shape_circle.png"))
        self.btn_forma_circular.setIconSize(QSize(18, 18))
        self.btn_forma_circular.setCheckable(True)
        self.btn_forma_circular.setChecked(True)
        self.btn_forma_circular.setToolTip(t("Circular"))
        self.btn_forma_circular.setFixedSize(24, 22)
        self.btn_forma_circular.clicked.connect(lambda: self._on_forma_pincel_changed("Redondo"))
        self.btn_group_forma.addButton(self.btn_forma_circular)
        self.act_btn_forma_circular = self.addWidget(self.btn_forma_circular)

        self.btn_forma_cuadrada = QToolButton()
        self.btn_forma_cuadrada.setIcon(QIcon("gui/iconos/shape_square.png"))
        self.btn_forma_cuadrada.setIconSize(QSize(18, 18))
        self.btn_forma_cuadrada.setCheckable(True)
        self.btn_forma_cuadrada.setToolTip(t("Cuadrado"))
        self.btn_forma_cuadrada.setFixedSize(24, 22)
        self.btn_forma_cuadrada.clicked.connect(lambda: self._on_forma_pincel_changed("Cuadrado"))
        self.btn_group_forma.addButton(self.btn_forma_cuadrada)
        self.act_btn_forma_cuadrada = self.addWidget(self.btn_forma_cuadrada)

        self.sep_forma_pincel = self.addSeparator()

        # Selector de Modo de Degradado (Color vs Transparencia)
        self.lbl_modo_degradado = QLabel(t("Modo:"))
        self.lbl_modo_degradado.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.act_lbl_modo_degradado = self.addWidget(self.lbl_modo_degradado)

        self.btn_group_degradado_modo = QButtonGroup(self)
        self.btn_group_degradado_modo.setExclusive(True)

        self.btn_degradado_color = QToolButton()
        self.btn_degradado_color.setIcon(QIcon("gui/iconos/gradient.png"))
        self.btn_degradado_color.setIconSize(QSize(18, 18))
        self.btn_degradado_color.setCheckable(True)
        self.btn_degradado_color.setChecked(True)
        self.btn_degradado_color.setToolTip(t("Color"))
        self.btn_degradado_color.setFixedSize(24, 22)
        self.btn_degradado_color.clicked.connect(lambda: self._on_modo_degradado_changed("Color"))
        self.btn_group_degradado_modo.addButton(self.btn_degradado_color)
        self.act_btn_degradado_color = self.addWidget(self.btn_degradado_color)

        self.btn_degradado_transparencia = QToolButton()
        self.btn_degradado_transparencia.setIcon(QIcon("gui/iconos/transparency.png"))
        self.btn_degradado_transparencia.setIconSize(QSize(18, 18))
        self.btn_degradado_transparencia.setCheckable(True)
        self.btn_degradado_transparencia.setToolTip(t("Transparencia"))
        self.btn_degradado_transparencia.setFixedSize(24, 22)
        self.btn_degradado_transparencia.clicked.connect(lambda: self._on_modo_degradado_changed("Transparencia"))
        self.btn_group_degradado_modo.addButton(self.btn_degradado_transparencia)
        self.act_btn_degradado_transparencia = self.addWidget(self.btn_degradado_transparencia)

        self.sep_modo_degradado = self.addSeparator()

        # 7. Selector de Tolerancia Global
        self.lbl_tol = QLabel(" Tolerancia: ")
        self.lbl_tol.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.act_lbl_tol = self.addWidget(self.lbl_tol)

        self.slider_tol = QSlider(Qt.Orientation.Horizontal)
        self.slider_tol.setRange(0, 100)
        self.slider_tol.setValue(32)
        self.slider_tol.setFixedWidth(65)
        self.slider_tol.valueChanged.connect(self._on_tolerancia_changed)
        self.act_slider_tol = self.addWidget(self.slider_tol)

        self.lbl_tol_val = QLabel("50%")
        self.lbl_tol_val.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.lbl_tol_val.setFixedWidth(36)
        self.lbl_tol_val.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.act_lbl_tol_val = self.addWidget(self.lbl_tol_val)

        self.sep_tol = self.addSeparator()

        # 8. Selector de Suavizado Global
        self.lbl_suav = QLabel(" Suavizado: ")
        self.lbl_suav.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.act_lbl_suav = self.addWidget(self.lbl_suav)

        self.slider_suav = QSlider(Qt.Orientation.Horizontal)
        self.slider_suav.setRange(0, 100)
        self.slider_suav.setValue(100)
        self.slider_suav.setFixedWidth(65)
        self.slider_suav.valueChanged.connect(self._on_suavizado_changed)
        self.act_slider_suav = self.addWidget(self.slider_suav)

        self.lbl_suav_val = QLabel("100%")
        self.lbl_suav_val.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.lbl_suav_val.setFixedWidth(36)
        self.lbl_suav_val.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.act_lbl_suav_val = self.addWidget(self.lbl_suav_val)

        self.sep_suav = self.addSeparator()

        # 9. Selector de Zoom
        self.lbl_zoom = QLabel()
        self.lbl_zoom.setPixmap(QIcon("gui/iconos/zoom.png").pixmap(QSize(24, 24)))
        self.lbl_zoom.setToolTip("Zoom")
        self.lbl_zoom.setContentsMargins(4, 0, 2, 0)
        self.act_lbl_zoom = self.addWidget(self.lbl_zoom)

        self.combo_zoom = QComboBox()
        self.combo_zoom.setEditable(True)
        self.combo_zoom.setFixedWidth(80)
        self.combo_zoom.setFixedHeight(22)
        self.combo_zoom.addItems([
            "10%", "25%", "50%", "75%",
            "100%", "200%", "300%", "400%", "500%",
            "750%", "1000%", "1250%", "1500%",
            "2000%", "2500%", "3000%"
        ])
        self.combo_zoom.setCurrentText("100%")
        self.combo_zoom.setStyleSheet("font-size: 11px; padding: 1px;")
        self.combo_zoom.activated.connect(self._on_zoom_changed)
        if self.combo_zoom.lineEdit():
            self.combo_zoom.lineEdit().editingFinished.connect(self._on_zoom_changed)
        self.act_combo_zoom = self.addWidget(self.combo_zoom)

        self.sep_zoom = self.addSeparator()

        # 10. Opciones de Línea
        self.lbl_linea = QLabel()
        self.lbl_linea.setPixmap(QIcon("gui/iconos/line.png").pixmap(QSize(24, 24)))
        self.lbl_linea.setToolTip("Línea")
        self.lbl_linea.setContentsMargins(4, 0, 2, 0)
        self.act_lbl_linea = self.addWidget(self.lbl_linea)

        combo_style = """
            QComboBox {
                padding: 1px 2px;
                font-size: 11px;
                outline: 0;
            }
            QComboBox:focus {
                outline: 0;
            }
            QComboBox::drop-down {
                width: 0px;
                border: none;
                image: none;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
            }
            QComboBox QAbstractItemView {
                min-width: 34px;
                outline: 0;
                border: 1px solid #555555;
            }
            QComboBox QAbstractItemView::item {
                border: none;
                outline: 0;
                padding: 3px 4px;
            }
            QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover {
                border: none;
                outline: 0;
                background-color: #0066CC;
                color: #FFFFFF;
            }
        """

        self.combo_linea_inicio = QComboBox()
        self.combo_linea_inicio.setStyleSheet(combo_style)
        self.combo_linea_inicio.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_linea_inicio.setIconSize(QSize(18, 18))
        self.combo_linea_inicio.setFixedWidth(24)
        self.combo_linea_inicio.addItem(QIcon("gui/iconos/plain_point_left.png"), "", "Plana")
        self.combo_linea_inicio.addItem(QIcon("gui/iconos/round_point_left.png"), "", "Redonda")
        self.combo_linea_inicio.addItem(QIcon("gui/iconos/arrow_point_left.png"), "", "Flecha")
        self.combo_linea_inicio.addItem(QIcon("gui/iconos/circle_point_left.png"), "", "Circulo")
        self.combo_linea_inicio.setToolTip("Punta Inicial: Plana")
        self.combo_linea_inicio.currentIndexChanged.connect(self._on_linea_inicio_changed)
        self.act_combo_linea_ini = self.addWidget(self.combo_linea_inicio)

        self.combo_linea_estilo = QComboBox()
        self.combo_linea_estilo.setStyleSheet(combo_style)
        self.combo_linea_estilo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_linea_estilo.setIconSize(QSize(18, 18))
        self.combo_linea_estilo.setFixedWidth(24)
        self.combo_linea_estilo.addItem(QIcon("gui/iconos/flat.png"), "", "Recta")
        self.combo_linea_estilo.addItem(QIcon("gui/iconos/pointed.png"), "", "Punteada")
        self.combo_linea_estilo.setToolTip("Estilo de Trazo: Recta")
        self.combo_linea_estilo.currentIndexChanged.connect(self._on_linea_estilo_changed)
        self.act_combo_linea_est = self.addWidget(self.combo_linea_estilo)

        self.combo_linea_fin = QComboBox()
        self.combo_linea_fin.setStyleSheet(combo_style)
        self.combo_linea_fin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_linea_fin.setIconSize(QSize(18, 18))
        self.combo_linea_fin.setFixedWidth(24)
        self.combo_linea_fin.addItem(QIcon("gui/iconos/plain_point_right.png"), "", "Plana")
        self.combo_linea_fin.addItem(QIcon("gui/iconos/round_point_right.png"), "", "Redonda")
        self.combo_linea_fin.addItem(QIcon("gui/iconos/arrow_point_right.png"), "", "Flecha")
        self.combo_linea_fin.addItem(QIcon("gui/iconos/circle_point_right.png"), "", "Circulo")
        self.combo_linea_fin.setToolTip("Punta Final: Plana")
        self.combo_linea_fin.currentIndexChanged.connect(self._on_linea_fin_changed)
        self.act_combo_linea_fin = self.addWidget(self.combo_linea_fin)

        self.sep_linea = self.addSeparator()

        # 11. Opciones de Formas Geométrica
        self.lbl_formas = QLabel()
        self.lbl_formas.setPixmap(QIcon("gui/iconos/shapes.png").pixmap(QSize(24, 24)))
        self.lbl_formas.setToolTip("Formas")
        self.lbl_formas.setContentsMargins(4, 0, 2, 0)
        self.act_lbl_formas = self.addWidget(self.lbl_formas)

        self.chk_formas_redondeado = QCheckBox("Redondeado")
        self.chk_formas_redondeado.setStyleSheet("font-size: 11px;")
        self.chk_formas_redondeado.setToolTip("Esquinas redondeadas para Rectángulos y Triángulos")
        self.act_chk_formas_red = self.addWidget(self.chk_formas_redondeado)

        self.combo_forma_estilo = QComboBox()
        self.combo_forma_estilo.setStyleSheet(combo_style)
        self.combo_forma_estilo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_forma_estilo.setIconSize(QSize(18, 18))
        self.combo_forma_estilo.setFixedWidth(24)
        self.combo_forma_estilo.addItem(QIcon("gui/iconos/shape.png"), "", "Solo Borde")
        self.combo_forma_estilo.addItem(QIcon("gui/iconos/shapes_solid.png"), "", "Forma Sólida")
        self.combo_forma_estilo.addItem(QIcon("gui/iconos/shapes_colored.png"), "", "Borde y Relleno")
        self.combo_forma_estilo.setToolTip("Estilo de Forma: Solo Borde")
        self.combo_forma_estilo.currentIndexChanged.connect(self._on_forma_estilo_changed)
        self.act_combo_forma_est = self.addWidget(self.combo_forma_estilo)

        self.combo_forma_tipo = QComboBox()
        self.combo_forma_tipo.setStyleSheet(combo_style)
        self.combo_forma_tipo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_forma_tipo.setIconSize(QSize(18, 18))
        self.combo_forma_tipo.setFixedWidth(24)
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_rectangle.png"), "", "Rectángulo")
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_triangle.png"), "", "Triángulo")
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_circle.png"), "", "Elipse")
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_cloud.png"), "", "Nube")
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_heart.png"), "", "Corazón")
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_chat.png"), "", "Chat")
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_star.png"), "", "Estrella")
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/shape_flower.png"), "", "Flor")
        self.combo_forma_tipo.addItem(QIcon("gui/iconos/hand.png"), "", "Mano")
        self.combo_forma_tipo.setToolTip("Tipo de Forma: Rectángulo")
        self.combo_forma_tipo.currentIndexChanged.connect(self._on_forma_tipo_changed)
        self.act_combo_forma_tipo = self.addWidget(self.combo_forma_tipo)

        self.sep_formas = self.addSeparator()

        # 12. Opciones de Difuminar / Blur
        self.lbl_blur = QLabel()
        self.lbl_blur.setPixmap(QIcon("gui/iconos/blur.png").pixmap(QSize(24, 24)))
        self.lbl_blur.setToolTip("Difuminar")
        self.lbl_blur.setContentsMargins(4, 0, 2, 0)
        self.act_lbl_blur = self.addWidget(self.lbl_blur)

        settings = QSettings("PaintNotNet", "PaintNotNet")
        saved_mode = settings.value("blur_modo", "Pixelado")
        if saved_mode == "Gausiano":
            saved_mode = "Gaussiano"
        saved_val = int(settings.value("blur_val", 0))

        self.combo_blur_modo = QComboBox()
        self.combo_blur_modo.setStyleSheet("font-size: 11px; padding: 1px;")
        self.combo_blur_modo.setFixedWidth(100)
        self.combo_blur_modo.setFixedHeight(22)
        self.combo_blur_modo.addItem("Pixelado", "Pixelado")
        self.combo_blur_modo.addItem("Gaussiano", "Gaussiano")
        idx_mode = self.combo_blur_modo.findData(saved_mode)
        if idx_mode >= 0:
            self.combo_blur_modo.setCurrentIndex(idx_mode)
        self.combo_blur_modo.currentIndexChanged.connect(self._on_blur_changed)
        self.act_combo_blur_modo = self.addWidget(self.combo_blur_modo)

        self.slider_blur = QSlider(Qt.Orientation.Horizontal)
        self.slider_blur.setRange(0, 100)
        self.slider_blur.setValue(saved_val)
        self.slider_blur.setFixedWidth(65)
        self.slider_blur.valueChanged.connect(self._on_blur_changed)
        self.act_slider_blur = self.addWidget(self.slider_blur)

        self.lbl_blur_val = QLabel(f"{saved_val}%")
        self.lbl_blur_val.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.lbl_blur_val.setFixedWidth(36)
        self.lbl_blur_val.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.act_lbl_blur_val = self.addWidget(self.lbl_blur_val)

        # ==========================================================
        # CONTROL DE INTENSIDAD DE DIFUMINADO (DEDO)
        # ==========================================================
        saved_smudge = settings.value("smudge_intensidad", 50, type=int)

        self.lbl_smudge_intensidad = QLabel(t("Intensidad:"))
        self.lbl_smudge_intensidad.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.act_lbl_smudge_intensidad = self.addWidget(self.lbl_smudge_intensidad)

        self.slider_smudge_intensidad = QSlider(Qt.Orientation.Horizontal)
        self.slider_smudge_intensidad.setRange(1, 100)
        self.slider_smudge_intensidad.setValue(saved_smudge)
        self.slider_smudge_intensidad.setFixedWidth(70)
        self.slider_smudge_intensidad.valueChanged.connect(self._on_smudge_intensidad_changed)
        self.act_slider_smudge_intensidad = self.addWidget(self.slider_smudge_intensidad)

        self.lbl_smudge_val = QLabel(f"{saved_smudge}%")
        self.lbl_smudge_val.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.lbl_smudge_val.setFixedWidth(36)
        self.lbl_smudge_val.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.act_lbl_smudge_val = self.addWidget(self.lbl_smudge_val)

        self.sep_smudge = self.addSeparator()

        # ==========================================================
        # CONTEXTO DE TEXTO Y EFECTOS DE TEXTO (1 sola línea)
        # ==========================================================
        self.sep_texto = self.addSeparator()

        # 1. Fuente
        self.lbl_texto_fuente = QLabel(t("Fuente:"))
        self.lbl_texto_fuente.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.act_lbl_texto_fuente = self.addWidget(self.lbl_texto_fuente)

        self.combo_texto_fuente = QFontComboBox()
        self.combo_texto_fuente.setFixedHeight(22)
        self.combo_texto_fuente.setFixedWidth(115)
        self.combo_texto_fuente.setStyleSheet("font-size: 11px;")
        self.combo_texto_fuente.currentFontChanged.connect(
            lambda f: self._emitir_cambio_texto_parcial({"font_family": f.family() if isinstance(f, QFont) else str(f)})
        )
        self.act_combo_texto_fuente = self.addWidget(self.combo_texto_fuente)

        # 2. Tamaño
        self.lbl_texto_tam = QLabel(t("Tamaño:"))
        self.lbl_texto_tam.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.act_lbl_texto_tam = self.addWidget(self.lbl_texto_tam)

        self.spin_texto_tam = QSpinBox()
        self.spin_texto_tam.setRange(1, 9999)
        self.spin_texto_tam.setValue(24)
        self.spin_texto_tam.setSuffix(" px")
        self.spin_texto_tam.setFixedHeight(22)
        self.spin_texto_tam.setFixedWidth(58)
        self.spin_texto_tam.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_texto_tam.setStyleSheet("font-size: 11px;")
        self.spin_texto_tam.valueChanged.connect(
            lambda v: self._emitir_cambio_texto_parcial({"font_size": int(v), "size": int(v)})
        )
        self.act_spin_texto_tam = self.addWidget(self.spin_texto_tam)

        # 3. Estilos (Negrita, Cursiva, Subrayado, Tachado)
        self.btn_texto_bold = QPushButton()
        self.btn_texto_bold.setIcon(QIcon("gui/iconos/bold.png"))
        self.btn_texto_bold.setIconSize(QSize(14, 14))
        self.btn_texto_bold.setCheckable(True)
        self.btn_texto_bold.setFixedSize(22, 22)
        self.btn_texto_bold.setToolTip(t("Negrita"))
        self.btn_texto_bold.toggled.connect(lambda c: self._emitir_cambio_texto_parcial({"bold": c}))
        self.act_btn_texto_bold = self.addWidget(self.btn_texto_bold)

        self.btn_texto_italic = QPushButton()
        self.btn_texto_italic.setIcon(QIcon("gui/iconos/italics.png"))
        self.btn_texto_italic.setIconSize(QSize(14, 14))
        self.btn_texto_italic.setCheckable(True)
        self.btn_texto_italic.setFixedSize(22, 22)
        self.btn_texto_italic.setToolTip(t("Cursiva"))
        self.btn_texto_italic.toggled.connect(lambda c: self._emitir_cambio_texto_parcial({"italic": c}))
        self.act_btn_texto_italic = self.addWidget(self.btn_texto_italic)

        self.btn_texto_underline = QPushButton()
        self.btn_texto_underline.setIcon(QIcon("gui/iconos/underline.png"))
        self.btn_texto_underline.setIconSize(QSize(14, 14))
        self.btn_texto_underline.setCheckable(True)
        self.btn_texto_underline.setFixedSize(22, 22)
        self.btn_texto_underline.setToolTip(t("Subrayado"))
        self.btn_texto_underline.toggled.connect(lambda c: self._emitir_cambio_texto_parcial({"underline": c}))
        self.act_btn_texto_underline = self.addWidget(self.btn_texto_underline)

        self.btn_texto_strike = QPushButton()
        self.btn_texto_strike.setIcon(QIcon("gui/iconos/strikethrough.png"))
        self.btn_texto_strike.setIconSize(QSize(14, 14))
        self.btn_texto_strike.setCheckable(True)
        self.btn_texto_strike.setFixedSize(22, 22)
        self.btn_texto_strike.setToolTip(t("Tachado"))
        self.btn_texto_strike.toggled.connect(lambda c: self._emitir_cambio_texto_parcial({"strike": c}))
        self.act_btn_texto_strike = self.addWidget(self.btn_texto_strike)

        # 4. Alineación (Izquierda, Centro, Derecha, Justificar)
        self._align_group = QButtonGroup(self)
        self._align_group.setExclusive(True)

        self.btn_texto_align_left = QToolButton()
        self.btn_texto_align_left.setCheckable(True)
        self.btn_texto_align_left.setChecked(True)
        self.btn_texto_align_left.setFixedSize(22, 22)
        self.btn_texto_align_left.setToolTip(t("Alinear izquierda"))
        self.btn_texto_align_left.setIcon(QIcon("gui/iconos/left-align.png"))
        self.btn_texto_align_left.toggled.connect(lambda c: self._emitir_cambio_texto_parcial({"alignment": Qt.AlignmentFlag.AlignLeft}) if c else None)
        self._align_group.addButton(self.btn_texto_align_left)
        self.act_btn_texto_align_left = self.addWidget(self.btn_texto_align_left)

        self.btn_texto_align_center = QToolButton()
        self.btn_texto_align_center.setCheckable(True)
        self.btn_texto_align_center.setFixedSize(22, 22)
        self.btn_texto_align_center.setToolTip(t("Alinear centro"))
        self.btn_texto_align_center.setIcon(QIcon("gui/iconos/center-align.png"))
        self.btn_texto_align_center.toggled.connect(lambda c: self._emitir_cambio_texto_parcial({"alignment": Qt.AlignmentFlag.AlignHCenter}) if c else None)
        self._align_group.addButton(self.btn_texto_align_center)
        self.act_btn_texto_align_center = self.addWidget(self.btn_texto_align_center)

        self.btn_texto_align_right = QToolButton()
        self.btn_texto_align_right.setCheckable(True)
        self.btn_texto_align_right.setFixedSize(22, 22)
        self.btn_texto_align_right.setToolTip(t("Alinear derecha"))
        self.btn_texto_align_right.setIcon(QIcon("gui/iconos/right-align.png"))
        self.btn_texto_align_right.toggled.connect(lambda c: self._emitir_cambio_texto_parcial({"alignment": Qt.AlignmentFlag.AlignRight}) if c else None)
        self._align_group.addButton(self.btn_texto_align_right)
        self.act_btn_texto_align_right = self.addWidget(self.btn_texto_align_right)

        self.btn_texto_align_justify = QToolButton()
        self.btn_texto_align_justify.setCheckable(True)
        self.btn_texto_align_justify.setFixedSize(22, 22)
        self.btn_texto_align_justify.setToolTip(t("Justificar texto"))
        self.btn_texto_align_justify.setIcon(QIcon("gui/iconos/justify.png"))
        self.btn_texto_align_justify.toggled.connect(lambda c: self._emitir_cambio_texto_parcial({"alignment": Qt.AlignmentFlag.AlignJustify}) if c else None)
        self._align_group.addButton(self.btn_texto_align_justify)
        self.act_btn_texto_align_justify = self.addWidget(self.btn_texto_align_justify)

        self.sep_texto_efe = self.addSeparator()

        # 5. Efectos: Borde
        self.chk_texto_borde = QCheckBox(t("Borde"))
        self.chk_texto_borde.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.chk_texto_borde.toggled.connect(self._emitir_cambio_efectos)
        self.act_chk_texto_borde = self.addWidget(self.chk_texto_borde)

        self.spin_texto_borde = QSpinBox()
        self.spin_texto_borde.setRange(1, 200)
        self.spin_texto_borde.setValue(4)
        self.spin_texto_borde.setFixedHeight(22)
        self.spin_texto_borde.setFixedWidth(36)
        self.spin_texto_borde.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_texto_borde.setStyleSheet("font-size: 11px;")
        self.spin_texto_borde.valueChanged.connect(self._emitir_cambio_efectos)
        self.act_spin_texto_borde = self.addWidget(self.spin_texto_borde)

        self.slot_texto_borde = _EffectColorSlot(self, "borde_color")
        self.slot_texto_borde.color_changed.connect(self._emitir_cambio_efectos)
        self.act_slot_texto_borde = self.addWidget(self.slot_texto_borde)

        # 6. Efectos: Resplandor
        self.chk_texto_glow = QCheckBox(t("Resplandor"))
        self.chk_texto_glow.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.chk_texto_glow.toggled.connect(self._emitir_cambio_efectos)
        self.act_chk_texto_glow = self.addWidget(self.chk_texto_glow)

        self.spin_texto_glow = QSpinBox()
        self.spin_texto_glow.setRange(1, 200)
        self.spin_texto_glow.setValue(10)
        self.spin_texto_glow.setFixedHeight(22)
        self.spin_texto_glow.setFixedWidth(36)
        self.spin_texto_glow.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_texto_glow.setStyleSheet("font-size: 11px;")
        self.spin_texto_glow.valueChanged.connect(self._emitir_cambio_efectos)
        self.act_spin_texto_glow = self.addWidget(self.spin_texto_glow)

        self.slot_texto_glow = _EffectColorSlot(self, "glow_color")
        self.slot_texto_glow.color_changed.connect(self._emitir_cambio_efectos)
        self.act_slot_texto_glow = self.addWidget(self.slot_texto_glow)

        # 7. Efectos: Sombra con Rueda de Luz en paralelo a slot de color
        self.chk_texto_shadow = QCheckBox(t("Sombra"))
        self.chk_texto_shadow.setStyleSheet("font-size: 11px; font-weight: normal;")
        self.chk_texto_shadow.toggled.connect(self._emitir_cambio_efectos)
        self.act_chk_texto_shadow = self.addWidget(self.chk_texto_shadow)

        self.spin_texto_shadow = QSpinBox()
        self.spin_texto_shadow.setRange(1, 200)
        self.spin_texto_shadow.setValue(10)
        self.spin_texto_shadow.setFixedHeight(22)
        self.spin_texto_shadow.setFixedWidth(36)
        self.spin_texto_shadow.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_texto_shadow.setStyleSheet("font-size: 11px;")
        self.spin_texto_shadow.valueChanged.connect(self._emitir_cambio_efectos)
        self.act_spin_texto_shadow = self.addWidget(self.spin_texto_shadow)

        self.slot_texto_shadow = _EffectColorSlot(self, "shadow_color")
        self.slot_texto_shadow.color_changed.connect(self._emitir_cambio_efectos)
        self.act_slot_texto_shadow = self.addWidget(self.slot_texto_shadow)

        self.light_texto_shadow = _LightDirectionWidget()
        self.light_texto_shadow.setFixedSize(24, 24)
        self.light_texto_shadow.lightVectorChanged.connect(self._emitir_cambio_efectos)
        self.act_light_texto_shadow = self.addWidget(self.light_texto_shadow)

        if main_window:
            self.conectar_acciones()

        self.actualizar_estilo_tema()
        from tools.pencil import PencilTool
        self.update_tool_states(PencilTool())

    def actualizar_estilo_tema(self):
        from core.theme import ThemeManager
        tm = ThemeManager()
        is_dark = (tm.resolver_nombre_tema(tm.current_theme) == "Oscuro")
        suf = "_d.png" if is_dark else "_l.png"

        if hasattr(self, 'combo_linea_inicio'):
            self.combo_linea_inicio.setItemIcon(0, QIcon(f"gui/iconos/plain_point_left{suf}"))
            self.combo_linea_inicio.setItemIcon(1, QIcon(f"gui/iconos/round_point_left{suf}"))
            self.combo_linea_inicio.setItemIcon(2, QIcon(f"gui/iconos/arrow_point_left{suf}"))
            self.combo_linea_inicio.setItemIcon(3, QIcon(f"gui/iconos/circle_point_left{suf}"))

        if hasattr(self, 'combo_linea_estilo'):
            self.combo_linea_estilo.setItemIcon(0, QIcon(f"gui/iconos/flat{suf}"))
            self.combo_linea_estilo.setItemIcon(1, QIcon(f"gui/iconos/pointed{suf}"))

        if hasattr(self, 'combo_linea_fin'):
            self.combo_linea_fin.setItemIcon(0, QIcon(f"gui/iconos/plain_point_right{suf}"))
            self.combo_linea_fin.setItemIcon(1, QIcon(f"gui/iconos/round_point_right{suf}"))
            self.combo_linea_fin.setItemIcon(2, QIcon(f"gui/iconos/arrow_point_right{suf}"))
            self.combo_linea_fin.setItemIcon(3, QIcon(f"gui/iconos/circle_point_right{suf}"))

        if hasattr(self, 'combo_forma_estilo'):
            self.combo_forma_estilo.setItemIcon(0, QIcon(f"gui/iconos/shape{suf}"))

    def _on_blur_changed(self, *args):
        val = self.slider_blur.value()
        modo = self.combo_blur_modo.currentData() or "Pixelado"
        self.lbl_blur_val.setText(f"{val}%")

        settings = QSettings("PaintNotNet", "PaintNotNet")
        settings.setValue("blur_modo", modo)
        settings.setValue("blur_val", val)

        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            canvas = self.main_window.lienzo
            if hasattr(canvas, 'selection_engine') and canvas.selection_engine.has_selection():
                canvas.actualizar_preview_difuminado_seleccion(modo, val)
            else:
                canvas.update()

    def _on_smudge_intensidad_changed(self, val):
        if hasattr(self, 'lbl_smudge_val'):
            self.lbl_smudge_val.setText(f"{val}%")
        settings = QSettings("PaintNotNet", "PaintNotNet")
        settings.setValue("smudge_intensidad", val)

    def _on_forma_pincel_changed(self, forma_name):
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.forma_pincel = forma_name
            self.main_window.lienzo.update()

    def _on_modo_degradado_changed(self, modo_name):
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.modo_degradado = modo_name
            self.main_window.lienzo.update()

    def _set_group_visible(self, group_items, visible: bool):
        for item in group_items:
            if item:
                item.setVisible(visible)

    def update_tool_states(self, tool_obj):
        if not tool_obj:
            return

        from tools.bucket import BucketTool
        from tools.magic_wand import MagicWandTool
        from tools.brush import BrushTool
        from tools.pencil import PencilTool
        from tools.eraser import EraserTool
        from tools.zoom import ZoomTool
        from tools.line import LineTool
        from tools.shapes import ShapesTool
        from tools.blur import BlurTool
        from tools.gradient import GradientTool

        from tools.spray import SprayTool
        from tools.smudge import SmudgeTool
        from tools.stamp import StampTool

        uses_grosor = isinstance(tool_obj, (BrushTool, PencilTool, EraserTool, LineTool, ShapesTool, SprayTool, SmudgeTool, StampTool))
        uses_forma = isinstance(tool_obj, (BrushTool, PencilTool, EraserTool, LineTool, SprayTool, SmudgeTool, StampTool))
        uses_tolerance = isinstance(tool_obj, (BucketTool, MagicWandTool))
        uses_smoothness = isinstance(tool_obj, (BrushTool, LineTool, EraserTool, ShapesTool, SprayTool, StampTool))
        uses_zoom = isinstance(tool_obj, ZoomTool)
        uses_line = isinstance(tool_obj, LineTool)
        uses_shapes = isinstance(tool_obj, ShapesTool)
        uses_blur = isinstance(tool_obj, BlurTool)
        uses_smudge = isinstance(tool_obj, SmudgeTool)
        uses_gradient = isinstance(tool_obj, GradientTool)

        # Modo Degradado (Color vs Transparencia)
        self._set_group_visible([
            getattr(self, 'lbl_modo_degradado', None),
            getattr(self, 'btn_degradado_color', None),
            getattr(self, 'btn_degradado_transparencia', None),
            getattr(self, 'act_lbl_modo_degradado', None),
            getattr(self, 'act_btn_degradado_color', None),
            getattr(self, 'act_btn_degradado_transparencia', None),
            getattr(self, 'sep_modo_degradado', None)
        ], uses_gradient)

        if uses_gradient and self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            modo_actual = getattr(self.main_window.lienzo, 'modo_degradado', 'Color')
            if modo_actual == 'Color':
                self.btn_degradado_color.setChecked(True)
            else:
                self.btn_degradado_transparencia.setChecked(True)

        # Grosor
        self._set_group_visible([
            getattr(self, 'lbl_grosor', None),
            getattr(self, 'spin_grosor', None),
            getattr(self, 'act_lbl_grosor', None),
            getattr(self, 'act_spin_grosor', None),
            getattr(self, 'sep_grosor', None)
        ], uses_grosor)

        # Forma de Pincel (Circular vs Cuadrado)
        self._set_group_visible([
            getattr(self, 'lbl_forma_pincel', None),
            getattr(self, 'btn_forma_circular', None),
            getattr(self, 'btn_forma_cuadrada', None),
            getattr(self, 'act_lbl_forma_pincel', None),
            getattr(self, 'act_btn_forma_circular', None),
            getattr(self, 'act_btn_forma_cuadrada', None),
            getattr(self, 'sep_forma_pincel', None)
        ], uses_forma)

        if uses_forma and self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            forma_actual = getattr(self.main_window.lienzo, 'forma_pincel', 'Redondo')
            if forma_actual in ('Redondo', 'Circular'):
                self.btn_forma_circular.setChecked(True)
            else:
                self.btn_forma_cuadrada.setChecked(True)

        # Tolerancia
        self._set_group_visible([
            getattr(self, 'lbl_tol', None),
            getattr(self, 'slider_tol', None),
            getattr(self, 'lbl_tol_val', None),
            getattr(self, 'act_lbl_tol', None),
            getattr(self, 'act_slider_tol', None),
            getattr(self, 'act_lbl_tol_val', None),
            getattr(self, 'sep_tol', None)
        ], uses_tolerance)

        # Suavizado
        self._set_group_visible([
            getattr(self, 'lbl_suav', None),
            getattr(self, 'slider_suav', None),
            getattr(self, 'lbl_suav_val', None),
            getattr(self, 'act_lbl_suav', None),
            getattr(self, 'act_slider_suav', None),
            getattr(self, 'act_lbl_suav_val', None),
            getattr(self, 'sep_suav', None)
        ], uses_smoothness)

        # Zoom
        self._set_group_visible([
            getattr(self, 'lbl_zoom', None),
            getattr(self, 'combo_zoom', None),
            getattr(self, 'act_lbl_zoom', None),
            getattr(self, 'act_combo_zoom', None),
            getattr(self, 'sep_zoom', None)
        ], uses_zoom)

        # Línea
        self._set_group_visible([
            getattr(self, 'lbl_linea', None),
            getattr(self, 'combo_linea_inicio', None),
            getattr(self, 'combo_linea_estilo', None),
            getattr(self, 'combo_linea_fin', None),
            getattr(self, 'act_lbl_linea', None),
            getattr(self, 'act_combo_linea_ini', None),
            getattr(self, 'act_combo_linea_est', None),
            getattr(self, 'act_combo_linea_fin', None),
            getattr(self, 'sep_linea', None)
        ], uses_line)
        if uses_line and self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.linea_cap_inicio = self.combo_linea_inicio.currentData() or "Plana"
            self.main_window.lienzo.linea_estilo = self.combo_linea_estilo.currentData() or "Recta"
            self.main_window.lienzo.linea_cap_fin = self.combo_linea_fin.currentData() or "Plana"

        # Formas
        self._set_group_visible([
            getattr(self, 'lbl_formas', None),
            getattr(self, 'chk_formas_redondeado', None),
            getattr(self, 'combo_forma_estilo', None),
            getattr(self, 'combo_forma_tipo', None),
            getattr(self, 'act_lbl_formas', None),
            getattr(self, 'act_chk_formas_red', None),
            getattr(self, 'act_combo_forma_est', None),
            getattr(self, 'act_combo_forma_tipo', None),
            getattr(self, 'sep_formas', None)
        ], uses_shapes)

        # Blur
        self._set_group_visible([
            getattr(self, 'lbl_blur', None),
            getattr(self, 'combo_blur_modo', None),
            getattr(self, 'slider_blur', None),
            getattr(self, 'lbl_blur_val', None),
            getattr(self, 'act_lbl_blur', None),
            getattr(self, 'act_combo_blur_modo', None),
            getattr(self, 'act_slider_blur', None),
            getattr(self, 'act_lbl_blur_val', None)
        ], uses_blur)

        # Smudge Intensidad
        self._set_group_visible([
            getattr(self, 'lbl_smudge_intensidad', None),
            getattr(self, 'slider_smudge_intensidad', None),
            getattr(self, 'lbl_smudge_val', None),
            getattr(self, 'act_lbl_smudge_intensidad', None),
            getattr(self, 'act_slider_smudge_intensidad', None),
            getattr(self, 'act_lbl_smudge_val', None),
            getattr(self, 'sep_smudge', None)
        ], uses_smudge)

        from tools.text import TextTool
        uses_text = isinstance(tool_obj, TextTool)

        # Texto y Efectos de Texto
        items_texto = [
            getattr(self, 'lbl_texto_fuente', None), getattr(self, 'act_lbl_texto_fuente', None),
            getattr(self, 'combo_texto_fuente', None), getattr(self, 'act_combo_texto_fuente', None),
            getattr(self, 'lbl_texto_tam', None), getattr(self, 'act_lbl_texto_tam', None),
            getattr(self, 'spin_texto_tam', None), getattr(self, 'act_spin_texto_tam', None),
            getattr(self, 'btn_texto_bold', None), getattr(self, 'act_btn_texto_bold', None),
            getattr(self, 'btn_texto_italic', None), getattr(self, 'act_btn_texto_italic', None),
            getattr(self, 'btn_texto_underline', None), getattr(self, 'act_btn_texto_underline', None),
            getattr(self, 'btn_texto_strike', None), getattr(self, 'act_btn_texto_strike', None),
            getattr(self, 'btn_texto_align_left', None), getattr(self, 'act_btn_texto_align_left', None),
            getattr(self, 'btn_texto_align_center', None), getattr(self, 'act_btn_texto_align_center', None),
            getattr(self, 'btn_texto_align_right', None), getattr(self, 'act_btn_texto_align_right', None),
            getattr(self, 'btn_texto_align_justify', None), getattr(self, 'act_btn_texto_align_justify', None),
            getattr(self, 'chk_texto_borde', None), getattr(self, 'act_chk_texto_borde', None),
            getattr(self, 'spin_texto_borde', None), getattr(self, 'act_spin_texto_borde', None),
            getattr(self, 'slot_texto_borde', None), getattr(self, 'act_slot_texto_borde', None),
            getattr(self, 'chk_texto_glow', None), getattr(self, 'act_chk_texto_glow', None),
            getattr(self, 'spin_texto_glow', None), getattr(self, 'act_spin_texto_glow', None),
            getattr(self, 'slot_texto_glow', None), getattr(self, 'act_slot_texto_glow', None),
            getattr(self, 'chk_texto_shadow', None), getattr(self, 'act_chk_texto_shadow', None),
            getattr(self, 'spin_texto_shadow', None), getattr(self, 'act_spin_texto_shadow', None),
            getattr(self, 'slot_texto_shadow', None), getattr(self, 'act_slot_texto_shadow', None),
            getattr(self, 'light_texto_shadow', None), getattr(self, 'act_light_texto_shadow', None),
            getattr(self, 'sep_texto', None)
        ]
        self._set_group_visible(items_texto, uses_text)
        if hasattr(self, 'sep_texto_efe') and self.sep_texto_efe:
            self.sep_texto_efe.setVisible(uses_text)

    def _emitir_cambio_texto_parcial(self, diff_dict):
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            canvas = self.main_window.lienzo
            from tools.text import TextTool
            if hasattr(canvas, 'active_tool_obj') and isinstance(canvas.active_tool_obj, TextTool):
                canvas.active_tool_obj.on_format_changed(canvas, diff_dict)
            else:
                cfg = getattr(canvas, 'config_texto', {})
                cfg.update(diff_dict)
                canvas.actualizar_config_texto(cfg)

    def _emitir_cambio_efectos(self, *_):
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.update()

    def obtener_config_efectos(self) -> dict:
        from PyQt6.QtGui import QColor
        return {
            "borde_enabled":  getattr(self, 'chk_texto_borde', QCheckBox()).isChecked(),
            "borde_width":    getattr(self, 'spin_texto_borde', QSpinBox()).value(),
            "borde_color":    self.slot_texto_borde.get_color() if hasattr(self, 'slot_texto_borde') else QColor(255, 255, 255),

            "glow_enabled":   getattr(self, 'chk_texto_glow', QCheckBox()).isChecked(),
            "glow_width":     getattr(self, 'spin_texto_glow', QSpinBox()).value(),
            "glow_color":     self.slot_texto_glow.get_color() if hasattr(self, 'slot_texto_glow') else QColor(255, 255, 255),

            "shadow_enabled": getattr(self, 'chk_texto_shadow', QCheckBox()).isChecked(),
            "shadow_width":   getattr(self, 'spin_texto_shadow', QSpinBox()).value(),
            "shadow_color":   self.slot_texto_shadow.get_color() if hasattr(self, 'slot_texto_shadow') else QColor(255, 255, 255),
            "shadow_dx":      self.light_texto_shadow.light_x if hasattr(self, 'light_texto_shadow') else 0.5,
            "shadow_dy":      self.light_texto_shadow.light_y if hasattr(self, 'light_texto_shadow') else 0.5,
        }

    def obtener_config(self) -> dict:
        return self.obtener_config_efectos()

    def actualizar_desde_formato(self, fmt):
        if not hasattr(self, 'btn_texto_bold'):
            return
        self.btn_texto_bold.blockSignals(True)
        self.btn_texto_italic.blockSignals(True)
        self.btn_texto_underline.blockSignals(True)
        self.btn_texto_strike.blockSignals(True)
        self.combo_texto_fuente.blockSignals(True)
        self.spin_texto_tam.blockSignals(True)
        self._align_group.blockSignals(True)

        self.btn_texto_bold.setChecked(fmt.bold)
        self.btn_texto_italic.setChecked(fmt.italic)
        self.btn_texto_underline.setChecked(fmt.underline)
        self.btn_texto_strike.setChecked(fmt.strike)
        self.spin_texto_tam.setValue(fmt.font_size)

        font = QFont(fmt.font_family)
        self.combo_texto_fuente.setCurrentFont(font)

        if fmt.alignment == Qt.AlignmentFlag.AlignHCenter:
            self.btn_texto_align_center.setChecked(True)
        elif fmt.alignment == Qt.AlignmentFlag.AlignRight:
            self.btn_texto_align_right.setChecked(True)
        else:
            self.btn_texto_align_left.setChecked(True)

        self.btn_texto_bold.blockSignals(False)
        self.btn_texto_italic.blockSignals(False)
        self.btn_texto_underline.blockSignals(False)
        self.btn_texto_strike.blockSignals(False)
        self.combo_texto_fuente.blockSignals(False)
        self.spin_texto_tam.blockSignals(False)
        self._align_group.blockSignals(False)

    def retraducir_panel(self):
        pass

    def conectar_acciones(self):
        if self.main_window:
            if hasattr(self.main_window, 'nuevo_archivo'):
                self.action_nueva_pestana.triggered.connect(self.main_window.nuevo_archivo)
            if hasattr(self.main_window, 'menu_archivo'):
                self.action_abrir.triggered.connect(self.main_window.menu_archivo.abrir_archivo)
                self.action_guardar.triggered.connect(self.main_window.menu_archivo.guardar_archivo)
            if hasattr(self.main_window, 'menu_editar'):
                self.action_cortar.triggered.connect(self.main_window.menu_editar.cortar)
                self.action_copiar.triggered.connect(self.main_window.menu_editar.copiar)
                self.action_pegar.triggered.connect(self.main_window.menu_editar.pegar)

    def _on_crop_clicked(self):
        from core.i18n import t
        canvas = None
        if self.main_window and hasattr(self.main_window, 'lienzo'):
            canvas = self.main_window.lienzo
        if canvas and hasattr(canvas, 'recortar_a_seleccion'):
            ok = canvas.recortar_a_seleccion()
            if not ok:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self.main_window,
                    t("Sin selección"),
                    t("No hay selección activa para recortar.")
                )

    def _on_grosor_changed(self, val):
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.ancho_pincel = val
            self.main_window.lienzo.grosor_pincel = val
            self.main_window.lienzo.update()
        self.grosor_changed.emit(val)

    def _on_tolerancia_changed(self, val):
        self.lbl_tol_val.setText(f"{val}%")
        canvas = None
        if self.main_window:
            canvas = getattr(self.main_window, 'lienzo', getattr(self.main_window, 'canvas', None))
        if canvas:
            canvas.tolerancia = val
            if hasattr(canvas, 'active_tool_obj') and hasattr(canvas.active_tool_obj, 'update_tolerance'):
                canvas.active_tool_obj.update_tolerance(canvas, val)

    def _on_suavizado_changed(self, val):
        self.lbl_suav_val.setText(f"{val}%")
        # suavizado_pincel es bool: cualquier valor > 0 activa antialiasing
        suav_bool = val > 0
        if self.main_window and hasattr(self.main_window, 'tab_widget'):
            for i in range(self.main_window.tab_widget.count()):
                area = self.main_window.tab_widget.widget(i)
                canvas = area.widget() if (area and hasattr(area, 'widget')) else area
                if canvas and hasattr(canvas, 'suavizado_pincel'):
                    canvas.suavizado_pincel = suav_bool
        elif self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.suavizado_pincel = suav_bool

    def _on_zoom_changed(self):
        txt = self.combo_zoom.currentText().replace("%", "").strip()
        try:
            val = int(txt)
            val = max(1, min(3000, val))
            if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
                self.main_window.lienzo.set_zoom(val / 100.0)
        except ValueError:
            pass

    def sync_zoom_from_canvas(self, scale_factor):
        """Sincroniza el combo de zoom con el valor actual del canvas."""
        pct = int(round(scale_factor * 100))
        txt = f"{pct}%"
        if hasattr(self, 'combo_zoom') and self.combo_zoom.currentText() != txt:
            self.combo_zoom.blockSignals(True)
            self.combo_zoom.setCurrentText(txt)
            self.combo_zoom.blockSignals(False)

    def _on_linea_inicio_changed(self, idx):
        from core.i18n import t
        val = self.combo_linea_inicio.itemData(idx) or "Plana"
        self.combo_linea_inicio.setToolTip(f"{t('Punta Inicial:')} {t(val)}")
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.linea_cap_inicio = val
            self.main_window.lienzo.update()

    def _on_linea_estilo_changed(self, idx):
        from core.i18n import t
        val = self.combo_linea_estilo.itemData(idx) or "Recta"
        self.combo_linea_estilo.setToolTip(f"{t('Estilo de Trazo:')} {t(val)}")
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.linea_estilo = val
            self.main_window.lienzo.update()

    def _on_linea_fin_changed(self, idx):
        from core.i18n import t
        val = self.combo_linea_fin.itemData(idx) or "Plana"
        self.combo_linea_fin.setToolTip(f"{t('Punta Final:')} {t(val)}")
        if self.main_window and hasattr(self.main_window, 'lienzo') and self.main_window.lienzo:
            self.main_window.lienzo.linea_cap_fin = val
            self.main_window.lienzo.update()

    def _on_forma_tipo_changed(self, idx):
        from core.i18n import t
        val = self.combo_forma_tipo.itemData(idx) or "Rectángulo"
        self.combo_forma_tipo.setToolTip(f"{t('Tipo de Forma:')} {t(val)}")

    def _on_forma_estilo_changed(self, idx):
        from core.i18n import t
        val = self.combo_forma_estilo.itemData(idx) or "Solo Borde"
        self.combo_forma_estilo.setToolTip(f"{t('Estilo de Forma:')} {t(val)}")

    def retraducir_toolbar(self):
        from core.i18n import t
        self.action_nueva_pestana.setToolTip(f"{t('Nuevo')} (Ctrl+N)")
        self.action_abrir.setToolTip(f"{t('Abrir...')} (Ctrl+O)")
        self.action_guardar.setToolTip(f"{t('Guardar')} (Ctrl+S)")
        self.action_cortar.setToolTip(f"{t('Cortar')} (Ctrl+X)")
        self.action_copiar.setToolTip(f"{t('Copiar')} (Ctrl+C)")
        self.action_pegar.setToolTip(f"{t('Pegar')} (Ctrl+V)")
        if hasattr(self, 'action_crop'):
            self.action_crop.setToolTip(t('Recortar a selección'))
        if hasattr(self, 'lbl_grosor'):
            self.lbl_grosor.setText(f" {t('Grosor:')} ")
        if hasattr(self, 'lbl_forma_pincel'):
            self.lbl_forma_pincel.setText(f" {t('Forma:')} ")
        if hasattr(self, 'btn_forma_circular'):
            self.btn_forma_circular.setToolTip(t("Circular"))
        if hasattr(self, 'btn_forma_cuadrada'):
            self.btn_forma_cuadrada.setToolTip(t("Cuadrado"))
        if hasattr(self, 'lbl_modo_degradado'):
            self.lbl_modo_degradado.setText(f" {t('Modo:')} ")
        if hasattr(self, 'btn_degradado_color'):
            self.btn_degradado_color.setToolTip(t("Color"))
        if hasattr(self, 'btn_degradado_transparencia'):
            self.btn_degradado_transparencia.setToolTip(t("Transparencia"))
        if hasattr(self, 'lbl_tol'):
            self.lbl_tol.setText(f" {t('Tolerancia:')} ")
        if hasattr(self, 'lbl_suav'):
            self.lbl_suav.setText(f" {t('Suavizado:')} ")
        if hasattr(self, 'lbl_zoom'):
            self.lbl_zoom.setToolTip(t("Zoom"))
        if hasattr(self, 'lbl_linea'):
            self.lbl_linea.setToolTip(t("Línea"))
        if hasattr(self, 'lbl_formas'):
            self.lbl_formas.setToolTip(t("Formas"))
        if hasattr(self, 'lbl_blur'):
            self.lbl_blur.setToolTip(t("Difuminar"))
        if hasattr(self, 'chk_formas_redondeado'):
            self.chk_formas_redondeado.setText(t("Redondeado"))

        # Actualizar tooltips traducidos de los combos
        val_ini = self.combo_linea_inicio.currentData() or "Plana"
        self.combo_linea_inicio.setToolTip(f"{t('Punta Inicial:')} {t(val_ini)}")
        val_est = self.combo_linea_estilo.currentData() or "Recta"
        self.combo_linea_estilo.setToolTip(f"{t('Estilo de Trazo:')} {t(val_est)}")
        val_fin = self.combo_linea_fin.currentData() or "Plana"
        self.combo_linea_fin.setToolTip(f"{t('Punta Final:')} {t(val_fin)}")

        val_f_est = self.combo_forma_estilo.currentData() or "Solo Borde"
        self.combo_forma_estilo.setToolTip(f"{t('Estilo de Forma:')} {t(val_f_est)}")
        val_f_tipo = self.combo_forma_tipo.currentData() or "Rectángulo"
        self.combo_forma_tipo.setToolTip(f"{t('Tipo de Forma:')} {t(val_f_tipo)}")

        if hasattr(self, 'combo_blur_modo'):
            self.combo_blur_modo.blockSignals(True)
            self.combo_blur_modo.setItemText(0, t("Pixelado"))
            self.combo_blur_modo.setItemText(1, t("Gaussiano"))
            self.combo_blur_modo.blockSignals(False)

