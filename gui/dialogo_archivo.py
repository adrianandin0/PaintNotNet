"""
dialogo_archivo.py – Gestor de archivos propio de PaintNotNet.
Reemplaza QFileDialog para evitar dependencias del entorno de escritorio.
Incluye múltiples vistas (Íconos/Mosaico, Lista, Detalle), tamaños de miniatura
variables, vista previa de imágenes, ordenación por diversos criterios,
lista personalizable de carpetas Favoritas y barra de búsqueda de archivos.
"""

import os
import sys
import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QLineEdit, QComboBox,
    QPushButton, QLabel, QSizePolicy, QAbstractItemView,
    QFileIconProvider, QMessageBox, QWidget, QToolButton, QFrame,
    QStackedWidget, QTreeWidget, QTreeWidgetItem, QHeaderView, QButtonGroup,
    QMenu
)
from PyQt6.QtCore import Qt, QSize, QFileInfo, QDir, QSettings, QTimer
from PyQt6.QtGui import QPixmap, QIcon, QFont, QColor
from core.i18n import t


# Rutas de iconos

_BASE = "gui/iconos"

def _ico(nombre):
    path = os.path.join(_BASE, nombre)
    if os.path.exists(path):
        return QIcon(path)
    return QIcon()


# Helpers

def _lugares_rapidos():
    """Devuelve lista de (etiqueta, ruta, icono_nombre) para el panel izquierdo."""
    lugares = []

    usuario_real = (
        os.environ.get('SUDO_USER') or
        os.environ.get('LOGNAME') or
        os.environ.get('USER') or
        os.environ.get('USERNAME')
    )
    if usuario_real and usuario_real != 'root':
        home = os.path.join('/home', usuario_real)
        if not os.path.exists(home):
            home = os.path.expanduser('~')
    else:
        home = os.path.expanduser('~')

    lugares.append((t('Inicio'), home, 'home.png'))

    for nombre in ('Desktop', 'Escritorio'):
        p = os.path.join(home, nombre)
        if os.path.isdir(p):
            lugares.append((t('Escritorio'), p, 'desktop.png'))
            break

    for nombre in ('Pictures', 'Imágenes', 'Imagenes', 'Images'):
        p = os.path.join(home, nombre)
        if os.path.isdir(p):
            lugares.append((t('Imágenes'), p, 'gallery.png'))
            break

    for nombre in ('Documents', 'Documentos'):
        p = os.path.join(home, nombre)
        if os.path.isdir(p):
            lugares.append((t('Documentos'), p, 'documents.png'))
            break

    for nombre in ('Downloads', 'Descargas'):
        p = os.path.join(home, nombre)
        if os.path.isdir(p):
            lugares.append((t('Descargas'), p, 'download.png'))
            break

    if sys.platform == 'win32':
        import string
        for letra in string.ascii_uppercase:
            raiz = f'{letra}:\\'
            if os.path.exists(raiz):
                lugares.append((f'{raiz}', raiz, 'disk.png'))
    else:
        lugares.append((t('Sistema (/)'), '/', 'disk.png'))
        media = '/media'
        if os.path.isdir(media):
            try:
                for sub in sorted(os.listdir(media)):
                    p = os.path.join(media, sub)
                    if os.path.isdir(p):
                        lugares.append((sub, p, 'disk.png'))
            except PermissionError:
                pass

    return lugares


def _icono_archivo(ruta, size=24):
    info = QFileInfo(ruta)
    provider = QFileIconProvider()
    return provider.icon(info)


_CACHE_MINIATURAS = {}

def _obtener_thumbnail_o_icono(ruta, size):
    """Devuelve un QIcon con la vista previa de la imagen o el icono del sistema."""
    ext = os.path.splitext(ruta)[1].lower()
    es_imagen = ext in ('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.pnn', '.gif', '.ico', '.tiff')
    
    if es_imagen:
        try:
            mtime = os.path.getmtime(ruta)
        except OSError:
            mtime = 0
        key = (ruta, size, mtime)
        if key in _CACHE_MINIATURAS:
            return _CACHE_MINIATURAS[key]
        
        pm = QPixmap(ruta)
        if not pm.isNull():
            icon_pm = pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon = QIcon(icon_pm)
            _CACHE_MINIATURAS[key] = icon
            return icon

    return _icono_archivo(ruta, size)


def _formato_tamano(bytes_):
    if bytes_ < 1024:
        return f"{bytes_} B"
    elif bytes_ < 1024 * 1024:
        return f"{bytes_ / 1024:.1f} KB"
    elif bytes_ < 1024 * 1024 * 1024:
        return f"{bytes_ / (1024*1024):.1f} MB"
    else:
        return f"{bytes_ / (1024*1024*1024):.1f} GB"


def _formato_fecha(timestamp):
    try:
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ""


def _descripcion_tipo(nombre, es_dir):
    if es_dir:
        return t("Carpeta de archivos")
    ext = os.path.splitext(nombre)[1].lower()
    if ext in ('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.pnn', '.gif', '.tiff', '.ico'):
        return f"{t('Imagen')} ({ext.upper()[1:]})"
    elif ext == '.pdf':
        return t("Documento PDF")
    elif ext == '.txt':
        return t("Documento de texto")
    elif ext:
        return f"{t('Archivo')} {ext.upper()}"
    return t("Archivo")


# Botón de navegación con icono

def _nav_btn(icono_nombre, tooltip, size=28):
    from core.theme import ThemeManager
    tm = ThemeManager()
    is_light = (tm.resolver_nombre_tema(tm.current_theme) == "Claro")

    btn = QToolButton()
    ico = _ico(icono_nombre)
    if ico.isNull() and icono_nombre == 'favourite.png':
        ico = _ico('favorites.png')
    elif ico.isNull() and icono_nombre == 'download.png':
        ico = _ico('arrow_down.png')
    if not ico.isNull():
        btn.setIcon(ico)
    btn.setIconSize(QSize(16, 16))
    btn.setFixedSize(size, size)
    btn.setToolTip(tooltip)

    bg_col  = "#E2E2E2" if is_light else "#5C5C5C"
    brd_col = "#B0B0B0" if is_light else "#505050"
    hvr_col = "#D4D4D4" if is_light else "#6A6A6A"

    btn.setStyleSheet(f"""
        QToolButton {{
            background: {bg_col};
            border: 1px solid {brd_col};
            border-radius: 4px;
        }}
        QToolButton:hover {{ background: {hvr_col}; border-color: #0066CC; }}
        QToolButton:pressed {{ background: #0055AA; }}
        QToolButton:checked {{ background: #0066CC; border-color: #0055AA; }}
        QToolButton:disabled {{ background: {bg_col}; opacity: 0.4; }}
    """)
    return btn


# Constantes de modos de vista
VISTA_ICONOS = 0
VISTA_LISTA  = 1
VISTA_DETALLE = 2


class DialogoArchivo(QDialog):
    """
    Diálogo de exploración de archivos propio de PaintNotNet.
    Permite modos Íconos (Mosaico), Lista, Detalle, Favoritos personalizados,
    búsqueda de archivos y miniaturas variables.
    """

    def __init__(self, parent=None, modo="abrir", directorio=None,
                 filtros=None, nombre_sugerido="", titulo=None):
        super().__init__(parent)

        self._modo = modo
        self._ruta_seleccionada = None
        self._historial = []
        self._pos_historial = -1
        self.settings = QSettings("PaintNotNet", "PaintNotNet")

        # Cargar preferencias de vista y favoritos
        self._modo_vista = int(self.settings.value("dialogo_archivo/modo_vista", VISTA_LISTA))
        self._tam_miniatura = int(self.settings.value("dialogo_archivo/tam_miniatura", 80))
        self._orden_campo = str(self.settings.value("dialogo_archivo/orden_campo", "nombre"))
        self._orden_asc = str(self.settings.value("dialogo_archivo/orden_asc", "true")).lower() == "true"
        
        raw_fav = self.settings.value("dialogo_archivo/favoritos", [])
        if isinstance(raw_fav, list):
            self._favoritos = [str(f) for f in raw_fav if f]
        elif isinstance(raw_fav, str) and raw_fav:
            self._favoritos = [raw_fav]
        else:
            self._favoritos = []

        # Título
        if titulo:
            self.setWindowTitle(t(titulo))
        elif modo == "guardar":
            self.setWindowTitle(t("Guardar como…"))
        elif modo == "directorio":
            self.setWindowTitle(t("Seleccionar carpeta"))
        else:
            self.setWindowTitle(t("Abrir archivo"))

        self.setMinimumSize(920, 580)
        self.resize(1040, 640)

        # Filtros
        self._filtros = self._parsear_filtros(filtros)
        self._filtro_activo = 0

        # Directorio inicial
        if directorio and os.path.isdir(directorio):
            self._directorio = directorio
        else:
            self._directorio = self.settings.value("default_dir", os.path.expanduser('~'))
            if not os.path.isdir(self._directorio):
                self._directorio = os.path.expanduser('~')

        self._construir_ui(nombre_sugerido)
        self._aplicar_estilos()
        self._poblar_lugares()
        self._poblar_favoritos()
        self._actualizar_estado_controles_orden()
        self._navegar(self._directorio, agregar_historial=False)

    def _construir_ui(self, nombre_sugerido):
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(10, 10, 10, 10)

        # 1. Barra de navegación superior
        barra = QHBoxLayout()
        barra.setSpacing(4)

        self.btn_atras = _nav_btn('arrow_left.png', t('Atrás (Alt+←)'))
        self.btn_atras.setEnabled(False)
        self.btn_atras.clicked.connect(self._ir_atras)

        self.btn_adelante = _nav_btn('arrow_right.png', t('Adelante (Alt+→)'))
        self.btn_adelante.setEnabled(False)
        self.btn_adelante.clicked.connect(self._ir_adelante)

        self.btn_arriba = _nav_btn('arrow_up.png', t('Subir nivel (Backspace)'))
        self.btn_arriba.clicked.connect(self._subir_nivel)

        self.btn_home = _nav_btn('home.png', t('Carpeta personal'))
        self.btn_home.clicked.connect(self._ir_home)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setStyleSheet("color: #686868;")

        self.edit_ruta = QLineEdit()
        self.edit_ruta.setPlaceholderText(t("Ingresá una ruta…"))
        self.edit_ruta.returnPressed.connect(self._navegar_ruta_manual)

        self.btn_ir = _nav_btn('arrow_right.png', t('Ir a la ruta'))
        self.btn_ir.clicked.connect(self._navegar_ruta_manual)

        self.btn_fav_toggle = _nav_btn('favourite.png', t('Agregar / Quitar de favoritos'))
        self.btn_fav_toggle.setCheckable(True)
        self.btn_fav_toggle.clicked.connect(self._alternar_favorito_actual)

        sep2_nav = QFrame()
        sep2_nav.setFrameShape(QFrame.Shape.VLine)
        sep2_nav.setStyleSheet("color: #686868;")

        # Campo de búsqueda
        self.edit_buscar = QLineEdit()
        self.edit_buscar.setPlaceholderText(t("Buscar…"))
        self.edit_buscar.setMaximumWidth(210)
        self.edit_buscar.returnPressed.connect(self._ejecutar_busqueda)
        self.edit_buscar.textChanged.connect(self._al_cambiar_texto_busqueda)

        self.btn_buscar = _nav_btn('zoom.png', t('Buscar archivos'))
        self.btn_buscar.clicked.connect(self._ejecutar_busqueda)

        barra.addWidget(self.btn_atras)
        barra.addWidget(self.btn_adelante)
        barra.addWidget(self.btn_arriba)
        barra.addWidget(self.btn_home)
        barra.addWidget(sep1)
        barra.addWidget(self.edit_ruta, 3)
        barra.addWidget(self.btn_ir)
        barra.addWidget(self.btn_fav_toggle)
        barra.addWidget(sep2_nav)
        barra.addWidget(self.edit_buscar, 1)
        barra.addWidget(self.btn_buscar)

        root.addLayout(barra)

        # 2. Barra secundaria de opciones de visualización y ordenamiento
        barra_vista = QHBoxLayout()
        barra_vista.setSpacing(6)

        # Grupo de botones de modo de vista
        lbl_vistas = QLabel(t("Vista:"))
        self.btn_vista_iconos = QToolButton()
        self.btn_vista_iconos.setCheckable(True)
        self.btn_vista_iconos.setToolTip(t("Vista en Iconos / Mosaico"))
        ico_grid = _ico('view-grid.png')
        if ico_grid.isNull():
            ico_grid = _ico('grid.png')
        if not ico_grid.isNull():
            self.btn_vista_iconos.setIcon(ico_grid)
        else:
            self.btn_vista_iconos.setText("田 " + t("Iconos"))

        self.btn_vista_lista = QToolButton()
        self.btn_vista_lista.setCheckable(True)
        self.btn_vista_lista.setToolTip(t("Vista en Lista"))
        ico_list = _ico('view-list.png')
        if not ico_list.isNull():
            self.btn_vista_lista.setIcon(ico_list)
        else:
            self.btn_vista_lista.setText("≡ " + t("Lista"))

        self.btn_vista_detalle = QToolButton()
        self.btn_vista_detalle.setCheckable(True)
        self.btn_vista_detalle.setToolTip(t("Vista Detallada (Nombre, Tipo, Tamaño, Fecha)"))
        ico_det = _ico('view-details.png')
        if not ico_det.isNull():
            self.btn_vista_detalle.setIcon(ico_det)
        else:
            self.btn_vista_detalle.setText("📑 " + t("Detalles"))

        self._grupo_vistas = QButtonGroup(self)
        self._grupo_vistas.setExclusive(True)
        self._grupo_vistas.addButton(self.btn_vista_iconos, VISTA_ICONOS)
        self._grupo_vistas.addButton(self.btn_vista_lista, VISTA_LISTA)
        self._grupo_vistas.addButton(self.btn_vista_detalle, VISTA_DETALLE)
        self._grupo_vistas.idClicked.connect(self._cambiar_modo_vista)

        if self._modo_vista == VISTA_ICONOS:
            self.btn_vista_iconos.setChecked(True)
        elif self._modo_vista == VISTA_DETALLE:
            self.btn_vista_detalle.setChecked(True)
        else:
            self.btn_vista_lista.setChecked(True)

        # Selector de tamaño de miniaturas
        self.lbl_tam = QLabel(t("Miniaturas:"))
        self.combo_tam_miniatura = QComboBox()
        self.combo_tam_miniatura.addItem(t("Pequeño (48px)"), 48)
        self.combo_tam_miniatura.addItem(t("Mediano (80px)"), 80)
        self.combo_tam_miniatura.addItem(t("Grande (128px)"), 128)
        self.combo_tam_miniatura.addItem(t("Extra Grande (192px)"), 192)
        
        idx_tam = self.combo_tam_miniatura.findData(self._tam_miniatura)
        if idx_tam >= 0:
            self.combo_tam_miniatura.setCurrentIndex(idx_tam)
        self.combo_tam_miniatura.currentIndexChanged.connect(self._cambiar_tamano_miniatura)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet("color: #686868;")

        # Controles de ordenación
        lbl_orden = QLabel(t("Ordenar por:"))
        self.combo_orden = QComboBox()
        self.combo_orden.addItem(t("Nombre"), "nombre")
        self.combo_orden.addItem(t("Tipo / Extensión"), "tipo")
        self.combo_orden.addItem(t("Fecha de modificación"), "mtime")
        self.combo_orden.addItem(t("Tamaño"), "tamano")
        
        idx_ord = self.combo_orden.findData(self._orden_campo)
        if idx_ord >= 0:
            self.combo_orden.setCurrentIndex(idx_ord)
        self.combo_orden.currentIndexChanged.connect(self._cambiar_criterio_orden)

        self.btn_direccion_orden = QToolButton()
        self.btn_direccion_orden.setToolTip(t("Alternar orden Ascendente / Descendente"))
        self.btn_direccion_orden.clicked.connect(self._alternar_direccion_orden)

        barra_vista.addWidget(lbl_vistas)
        barra_vista.addWidget(self.btn_vista_iconos)
        barra_vista.addWidget(self.btn_vista_lista)
        barra_vista.addWidget(self.btn_vista_detalle)
        barra_vista.addWidget(self.lbl_tam)
        barra_vista.addWidget(self.combo_tam_miniatura)
        barra_vista.addWidget(sep2)
        barra_vista.addWidget(lbl_orden)
        barra_vista.addWidget(self.combo_orden)
        barra_vista.addWidget(self.btn_direccion_orden)
        barra_vista.addStretch()

        root.addLayout(barra_vista)

        # 3. Splitter principal
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panel izquierdo compuesto: Lugares Rápidos + Favoritos
        panel_izq = QWidget()
        lay_izq = QVBoxLayout(panel_izq)
        lay_izq.setContentsMargins(0, 0, 0, 0)
        lay_izq.setSpacing(4)

        lbl_sec_lugares = QLabel(t("LUGARES"))
        lbl_sec_lugares.setStyleSheet("font-weight: bold; color: #888888; font-size: 10px; margin-top: 2px;")

        self.lista_lugares = QListWidget()
        self.lista_lugares.setIconSize(QSize(20, 20))
        self.lista_lugares.itemClicked.connect(self._lugar_clickado)

        # Encabezado de la sección Favoritos
        lbl_sec_fav = QLabel(t("FAVORITOS"))
        lbl_sec_fav.setStyleSheet("font-weight: bold; color: #888888; font-size: 10px; margin-top: 6px;")

        self.lista_favoritos = QListWidget()
        self.lista_favoritos.setIconSize(QSize(18, 18))
        self.lista_favoritos.itemClicked.connect(self._favorito_clickado)
        self.lista_favoritos.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lista_favoritos.customContextMenuRequested.connect(self._menu_contextual_favoritos)

        lay_izq.addWidget(lbl_sec_lugares)
        lay_izq.addWidget(self.lista_lugares, 3)
        lay_izq.addWidget(lbl_sec_fav)
        lay_izq.addWidget(self.lista_favoritos, 2)

        splitter.addWidget(panel_izq)

        # Panel derecho: Contenedor con StackedWidget para alternar entre List/Grid y Table (Detalles)
        self.stack_vistas = QStackedWidget()

        # Vista 0: QListWidget (para Íconos y Lista)
        self.lista_archivos = QListWidget()
        self.lista_archivos.setIconSize(QSize(24, 24))
        self.lista_archivos.itemClicked.connect(self._item_clic_lista)
        self.lista_archivos.itemDoubleClicked.connect(self._item_doble_clic_lista)
        self.lista_archivos.keyPressEvent = self._tecla_lista

        # Vista 1: QTreeWidget (para Detalle)
        self.tabla_archivos = QTreeWidget()
        self.tabla_archivos.setHeaderLabels([t("Nombre"), t("Tipo"), t("Tamaño"), t("Fecha de modificación")])
        self.tabla_archivos.setColumnCount(4)
        self.tabla_archivos.setIconSize(QSize(20, 20))
        self.tabla_archivos.setAlternatingRowColors(True)
        self.tabla_archivos.itemClicked.connect(self._item_clic_tabla)
        self.tabla_archivos.itemDoubleClicked.connect(self._item_doble_clic_tabla)
        self.tabla_archivos.keyPressEvent = self._tecla_tabla

        header = self.tabla_archivos.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(1, 140)
        header.resizeSection(2, 90)
        header.resizeSection(3, 140)
        header.sectionClicked.connect(self._header_tabla_clickado)

        self.stack_vistas.addWidget(self.lista_archivos)
        self.stack_vistas.addWidget(self.tabla_archivos)

        splitter.addWidget(self.stack_vistas)
        splitter.setSizes([220, 780])
        root.addWidget(splitter, 1)

        # 4. Fila de nombre y filtro
        fila_nombre = QHBoxLayout()
        fila_nombre.setSpacing(6)

        lbl_nombre = QLabel(t("Nombre:"))
        self.edit_nombre = QLineEdit()
        self.edit_nombre.setText(nombre_sugerido)
        self.edit_nombre.returnPressed.connect(self._confirmar)

        self.combo_filtro = QComboBox()
        self.combo_filtro.setMinimumWidth(220)
        for desc, _ in self._filtros:
            self.combo_filtro.addItem(t(desc))
        self.combo_filtro.currentIndexChanged.connect(self._cambiar_filtro)

        fila_nombre.addWidget(lbl_nombre)
        fila_nombre.addWidget(self.edit_nombre, 1)
        fila_nombre.addWidget(self.combo_filtro)

        root.addLayout(fila_nombre)

        # 5. Botones de acción inferiores
        fila_btns = QHBoxLayout()
        fila_btns.setSpacing(8)

        self.btn_cancelar = QPushButton(t("Cancelar"))
        self.btn_cancelar.setAutoDefault(False)
        self.btn_cancelar.setDefault(False)
        self.btn_cancelar.clicked.connect(self.reject)

        if self._modo == "guardar":
            texto_ok = t("Guardar")
        elif self._modo == "directorio":
            texto_ok = t("Seleccionar")
        else:
            texto_ok = t("Abrir")

        self.btn_ok = QPushButton(texto_ok)
        self.btn_ok.setObjectName("btn_ok")
        self.btn_ok.setMinimumWidth(110)
        self.btn_ok.setAutoDefault(False)
        self.btn_ok.setDefault(False)
        self.btn_ok.clicked.connect(self._confirmar)

        fila_btns.addWidget(self.btn_cancelar)
        fila_btns.addWidget(self.btn_ok)
        root.addLayout(fila_btns)

    # Estilos de interfaz

    def _aplicar_estilos(self):
        from core.theme import ThemeManager
        tm = ThemeManager()
        is_light = (tm.resolver_nombre_tema(tm.current_theme) == "Claro")

        if is_light:
            self.setStyleSheet("""
                QDialog {
                    background-color: #EFEFEF;
                    color: #222222;
                }
                QLabel {
                    color: #333333;
                    font-size: 12px;
                }
                QLineEdit {
                    background-color: #FFFFFF;
                    color: #222222;
                    border: 1px solid #B0B0B0;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 12px;
                }
                QLineEdit:focus {
                    border: 1px solid #0066CC;
                    background-color: #FFFFFF;
                }
                QPushButton {
                    background-color: #E2E2E2;
                    color: #222222;
                    border: 1px solid #B0B0B0;
                    border-radius: 4px;
                    padding: 4px 12px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #D4D4D4;
                    border-color: #0066CC;
                }
                QPushButton#btn_ok {
                    background-color: #0066CC;
                    border-color: #0055AA;
                    color: #FFFFFF;
                    font-weight: bold;
                }
                QPushButton#btn_ok:hover {
                    background-color: #0055AA;
                }
                QToolButton {
                    background-color: #E2E2E2;
                    color: #222222;
                    border: 1px solid #B0B0B0;
                    border-radius: 4px;
                    padding: 3px 6px;
                }
                QToolButton:hover {
                    background-color: #D4D4D4;
                    border-color: #0066CC;
                }
                QToolButton:checked {
                    background-color: #0066CC;
                    color: #FFFFFF;
                    border-color: #0055AA;
                }
                QListWidget, QTreeWidget {
                    background-color: #FFFFFF;
                    color: #222222;
                    border: 1px solid #B0B0B0;
                    border-radius: 4px;
                    font-size: 12px;
                    outline: none;
                }
                QListWidget::item {
                    padding: 4px 6px;
                    border-radius: 3px;
                    color: #222222;
                }
                QListWidget::item:selected, QTreeWidget::item:selected {
                    background-color: #0066CC;
                    color: #FFFFFF;
                }
                QHeaderView::section {
                    background-color: #E2E2E2;
                    color: #222222;
                    padding: 4px 8px;
                    border: 1px solid #B0B0B0;
                    font-weight: bold;
                }
                QComboBox {
                    background-color: #FFFFFF;
                    color: #222222;
                    border: 1px solid #B0B0B0;
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-size: 12px;
                }
                QSplitter::handle {
                    background-color: #C0C0C0;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #252525;
                    color: #EDEDED;
                }
                QLabel {
                    color: #b8b8b8;
                    font-size: 12px;
                }
                QLineEdit {
                    background-color: #1c1c1c;
                    color: #ececec;
                    border: 1px solid #626262;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 12px;
                }
                QLineEdit:focus {
                    border: 1px solid #4a7cc7;
                    background-color: #525252;
                }
                QPushButton {
                    background-color: #383838;
                    color: #EDEDED;
                    border: 1px solid #505050;
                    border-radius: 4px;
                    padding: 4px 12px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #454545;
                    border-color: #6a8fd0;
                }
                QPushButton#btn_ok {
                    background-color: #2c5490;
                    border-color: #3a6ac0;
                    color: #EDEDED;
                    font-weight: bold;
                }
                QPushButton#btn_ok:hover {
                    background-color: #3a6ac0;
                }
                QToolButton {
                    background-color: #383838;
                    color: #EDEDED;
                    border: 1px solid #505050;
                    border-radius: 4px;
                    padding: 3px 6px;
                }
                QToolButton:hover {
                    background-color: #454545;
                    border-color: #6a8fd0;
                }
                QToolButton:checked {
                    background-color: #2c5490;
                    color: #EDEDED;
                    border-color: #3a6ac0;
                }
                QListWidget, QTreeWidget {
                    background-color: #1c1c1c;
                    color: #EDEDED;
                    border: 1px solid #5C5C5C;
                    border-radius: 4px;
                    font-size: 12px;
                    outline: none;
                }
                QListWidget::item {
                    padding: 4px 6px;
                    border-radius: 3px;
                }
                QListWidget::item:selected, QTreeWidget::item:selected {
                    background-color: #2c5490;
                    color: #EDEDED;
                }
                QHeaderView::section {
                    background-color: #2d2d2d;
                    color: #EDEDED;
                    padding: 4px 8px;
                    border: 1px solid #5C5C5C;
                    font-weight: bold;
                }
                QComboBox {
                    background-color: #1c1c1c;
                    color: #EDEDED;
                    border: 1px solid #626262;
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-size: 12px;
                }
                QSplitter::handle {
                    background-color: #454545;
                }
            """)

    # Gestión de opciones de vista, ordenamiento y búsqueda

    def _ejecutar_busqueda(self):
        self._cargar_directorio(self._directorio)

    def _al_cambiar_texto_busqueda(self, texto):
        self._cargar_directorio(self._directorio)

    def _actualizar_estado_controles_orden(self):
        ico_asc = _ico('sort_asc.png')
        ico_desc = _ico('sort_desc.png')

        if self._orden_asc:
            if not ico_asc.isNull():
                self.btn_direccion_orden.setIcon(ico_asc)
                self.btn_direccion_orden.setText("")
            else:
                self.btn_direccion_orden.setText("▲ " + t("Asc"))
        else:
            if not ico_desc.isNull():
                self.btn_direccion_orden.setIcon(ico_desc)
                self.btn_direccion_orden.setText("")
            else:
                self.btn_direccion_orden.setText("▼ " + t("Desc"))

        es_iconos = (self._modo_vista == VISTA_ICONOS)
        self.lbl_tam.setVisible(es_iconos)
        self.combo_tam_miniatura.setVisible(es_iconos)

    def _cambiar_modo_vista(self, id_vista):
        self._modo_vista = id_vista
        self.settings.setValue("dialogo_archivo/modo_vista", id_vista)
        self._actualizar_estado_controles_orden()
        self._cargar_directorio(self._directorio)

    def _cambiar_tamano_miniatura(self, idx):
        tam = self.combo_tam_miniatura.itemData(idx)
        if tam:
            self._tam_miniatura = tam
            self.settings.setValue("dialogo_archivo/tam_miniatura", tam)
            if self._modo_vista == VISTA_ICONOS:
                self._cargar_directorio(self._directorio)

    def _cambiar_criterio_orden(self, idx):
        campo = self.combo_orden.itemData(idx)
        if campo:
            self._orden_campo = campo
            self.settings.setValue("dialogo_archivo/orden_campo", campo)
            self._cargar_directorio(self._directorio)

    def _alternar_direccion_orden(self):
        self._orden_asc = not self._orden_asc
        self.settings.setValue("dialogo_archivo/orden_asc", self._orden_asc)
        self._actualizar_estado_controles_orden()
        self._cargar_directorio(self._directorio)

    def _header_tabla_clickado(self, index_columna):
        mapa_columnas = {0: "nombre", 1: "tipo", 2: "tamano", 3: "mtime"}
        campo = mapa_columnas.get(index_columna, "nombre")
        if self._orden_campo == campo:
            self._alternar_direccion_orden()
        else:
            self._orden_campo = campo
            self.settings.setValue("dialogo_archivo/orden_campo", campo)
            idx_combo = self.combo_orden.findData(campo)
            if idx_combo >= 0:
                self.combo_orden.blockSignals(True)
                self.combo_orden.setCurrentIndex(idx_combo)
                self.combo_orden.blockSignals(False)
            self._cargar_directorio(self._directorio)

    # Lugares rápidos y Favoritos

    def _poblar_lugares(self):
        self.lista_lugares.clear()
        self._rutas_lugares = []
        for etiqueta, ruta, ico_nombre in _lugares_rapidos():
            ico = _ico(ico_nombre)
            if ico.isNull() and ico_nombre == 'download.png':
                ico = _ico('arrow_down.png')
            item = QListWidgetItem(ico, etiqueta)
            item.setToolTip(ruta)
            item.setSizeHint(QSize(0, 26))
            self.lista_lugares.addItem(item)
            self._rutas_lugares.append(ruta)

    def _lugar_clickado(self, item):
        idx = self.lista_lugares.row(item)
        if idx < len(self._rutas_lugares):
            self._navegar(self._rutas_lugares[idx])

    def _poblar_favoritos(self):
        self.lista_favoritos.clear()
        ico_fav = _ico('favourite.png')
        if ico_fav.isNull():
            ico_fav = _ico('favorites.png')
        if ico_fav.isNull():
            ico_fav = _ico('folder.png')

        for ruta in self._favoritos:
            nombre = os.path.basename(ruta) or ruta
            item = QListWidgetItem(ico_fav, nombre)
            item.setToolTip(ruta)
            item.setData(Qt.ItemDataRole.UserRole, ruta)
            item.setSizeHint(QSize(0, 26))
            self.lista_favoritos.addItem(item)

        self._actualizar_estado_favorito_actual()

    def _favorito_clickado(self, item):
        ruta = item.data(Qt.ItemDataRole.UserRole)
        if ruta and os.path.isdir(ruta):
            self._navegar(ruta)
        else:
            QMessageBox.warning(
                self, t("Carpeta no encontrada"),
                f"{t('La carpeta favorita ya no existe:')}\n{ruta}"
            )

    def _agregar_favorito_actual(self):
        ruta = self._directorio
        if ruta not in self._favoritos:
            self._favoritos.append(ruta)
            self.settings.setValue("dialogo_archivo/favoritos", self._favoritos)
            self._poblar_favoritos()

    def _quitar_favorito(self, ruta):
        if ruta in self._favoritos:
            self._favoritos.remove(ruta)
            self.settings.setValue("dialogo_archivo/favoritos", self._favoritos)
            self._poblar_favoritos()

    def _alternar_favorito_actual(self):
        if self._directorio in self._favoritos:
            self._quitar_favorito(self._directorio)
        else:
            self._agregar_favorito_actual()

    def _actualizar_estado_favorito_actual(self):
        es_fav = self._directorio in self._favoritos
        self.btn_fav_toggle.setChecked(es_fav)
        if es_fav:
            self.btn_fav_toggle.setToolTip(t("Quitar carpeta actual de favoritos"))
        else:
            self.btn_fav_toggle.setToolTip(t("Agregar carpeta actual a favoritos"))

    def _menu_contextual_favoritos(self, pos):
        item = self.lista_favoritos.itemAt(pos)
        if not item:
            return
        ruta = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        ico_bin = _ico('bin.png')
        accion_quitar = menu.addAction(ico_bin, t("Quitar de favoritos"))
        accion = menu.exec(self.lista_favoritos.mapToGlobal(pos))
        if accion == accion_quitar:
            self._quitar_favorito(ruta)

    # Navegación entre carpetas

    def _navegar(self, directorio, agregar_historial=True):
        if not os.path.isdir(directorio):
            return

        if agregar_historial:
            self._historial = self._historial[:self._pos_historial + 1]
            self._historial.append(directorio)
            self._pos_historial = len(self._historial) - 1

        self._directorio = directorio
        self.edit_ruta.setText(directorio)
        self.btn_atras.setEnabled(self._pos_historial > 0)
        self.btn_adelante.setEnabled(self._pos_historial < len(self._historial) - 1)
        self._actualizar_estado_favorito_actual()
        self._cargar_directorio(directorio)

        if self._modo == "directorio":
            self.edit_nombre.setText(directorio)

    def _ir_atras(self):
        if self._pos_historial > 0:
            self._pos_historial -= 1
            self._navegar(self._historial[self._pos_historial], agregar_historial=False)
            self.btn_atras.setEnabled(self._pos_historial > 0)
            self.btn_adelante.setEnabled(True)

    def _ir_adelante(self):
        if self._pos_historial < len(self._historial) - 1:
            self._pos_historial += 1
            self._navegar(self._historial[self._pos_historial], agregar_historial=False)
            self.btn_atras.setEnabled(True)
            self.btn_adelante.setEnabled(self._pos_historial < len(self._historial) - 1)

    def _subir_nivel(self):
        padre = os.path.dirname(self._directorio)
        if padre != self._directorio:
            self._navegar(padre)

    def _ir_home(self):
        home = _lugares_rapidos()[0][1]
        self._navegar(home)

    def _navegar_ruta_manual(self):
        ruta = self.edit_ruta.text().strip()
        if os.path.isdir(ruta):
            self._navegar(ruta)
        elif os.path.isfile(ruta):
            self.edit_nombre.setText(os.path.basename(ruta))
            self._navegar(os.path.dirname(ruta))
        else:
            QMessageBox.warning(self, t("Ruta inválida"), t("La ruta no existe:") + f"\n{ruta}")

    # Filtrado y ordenamiento

    def _parsear_filtros(self, filtros):
        if not filtros:
            return [(t("Todos los archivos"), set())]
        resultado = []
        for desc, patron in filtros:
            desc_trad = t(desc)
            exts = set()
            for parte in patron.split():
                if parte.startswith('*.'):
                    exts.add(parte[1:].lower())
                elif parte == '*':
                    exts = set()
                    break
            resultado.append((desc_trad, exts))
        return resultado

    def _archivo_visible(self, nombre):
        _, exts = self._filtros[self._filtro_activo]
        if not exts:
            return True
        ext = os.path.splitext(nombre)[1].lower()
        return ext in exts

    # Carga de directorio

    def _cargar_directorio(self, directorio):
        try:
            entradas = os.listdir(directorio)
        except PermissionError:
            QMessageBox.warning(self, t("Sin permiso"),
                                t("No se puede acceder a:") + f"\n{directorio}")
            return
        except Exception as e:
            QMessageBox.warning(self, t("Error"), str(e))
            return

        carpetas = []
        archivos = []
        query_busqueda = self.edit_buscar.text().strip().lower()

        for e in entradas:
            if e.startswith('.'):
                continue
            
            # Filtro por texto de búsqueda
            if query_busqueda and query_busqueda not in e.lower():
                continue

            ruta = os.path.join(directorio, e)
            es_dir = os.path.isdir(ruta)
            
            if es_dir:
                try:
                    st = os.stat(ruta)
                    mtime = st.st_mtime
                except OSError:
                    mtime = 0
                carpetas.append({
                    'nombre': e,
                    'ruta': ruta,
                    'es_dir': True,
                    'tamano': 0,
                    'mtime': mtime,
                    'tipo': _descripcion_tipo(e, True)
                })
            else:
                if self._modo != "directorio" and self._archivo_visible(e):
                    try:
                        st = os.stat(ruta)
                        tamano = st.st_size
                        mtime = st.st_mtime
                    except OSError:
                        tamano = 0
                        mtime = 0
                    archivos.append({
                        'nombre': e,
                        'ruta': ruta,
                        'es_dir': False,
                        'tamano': tamano,
                        'mtime': mtime,
                        'tipo': _descripcion_tipo(e, False)
                    })

        criterio = self._orden_campo
        reverse = not self._orden_asc

        def key_fn(item):
            val = item.get(criterio, "")
            if isinstance(val, str):
                return val.lower()
            return val

        carpetas.sort(key=key_fn, reverse=reverse)
        archivos.sort(key=key_fn, reverse=reverse)

        items_totales = carpetas + archivos

        if self._modo_vista == VISTA_DETALLE:
            self.stack_vistas.setCurrentIndex(1)
            self._poblar_tabla_detalles(items_totales)
        else:
            self.stack_vistas.setCurrentIndex(0)
            self._poblar_lista_o_iconos(items_totales)

    def _poblar_lista_o_iconos(self, items):
        self.lista_archivos.clear()

        if self._modo_vista == VISTA_ICONOS:
            self.lista_archivos.setViewMode(QListWidget.ViewMode.IconMode)
            self.lista_archivos.setResizeMode(QListWidget.ResizeMode.Adjust)
            self.lista_archivos.setMovement(QListWidget.Movement.Static)
            self.lista_archivos.setWordWrap(True)
            self.lista_archivos.setSpacing(10)

            size_px = self._tam_miniatura
            grid_w = size_px + 36
            grid_h = size_px + 45
            self.lista_archivos.setIconSize(QSize(size_px, size_px))
            self.lista_archivos.setGridSize(QSize(grid_w, grid_h))

            for elem in items:
                ruta = elem['ruta']
                nombre = elem['nombre']
                es_dir = elem['es_dir']

                if es_dir:
                    ico = _ico('folder.png')
                    if ico.isNull():
                        ico = _icono_archivo(ruta, size_px)
                else:
                    ico = _obtener_thumbnail_o_icono(ruta, size_px)

                item = QListWidgetItem(ico, nombre)
                item.setData(Qt.ItemDataRole.UserRole, ruta)
                item.setData(Qt.ItemDataRole.UserRole + 1, 'dir' if es_dir else 'file')
                
                info_tt = f"{nombre}\n{t('Tipo:')} {elem['tipo']}\n{t('Fecha:')} {_formato_fecha(elem['mtime'])}"
                if not es_dir:
                    info_tt += f"\n{t('Tamaño:')} {_formato_tamano(elem['tamano'])}"
                item.setToolTip(info_tt)
                self.lista_archivos.addItem(item)

        else: # VISTA_LISTA
            self.lista_archivos.setViewMode(QListWidget.ViewMode.ListMode)
            self.lista_archivos.setResizeMode(QListWidget.ResizeMode.Adjust)
            self.lista_archivos.setWordWrap(False)
            self.lista_archivos.setSpacing(2)
            self.lista_archivos.setGridSize(QSize())
            self.lista_archivos.setIconSize(QSize(22, 22))

            for elem in items:
                ruta = elem['ruta']
                nombre = elem['nombre']
                es_dir = elem['es_dir']

                if es_dir:
                    ico = _ico('folder.png')
                    if ico.isNull():
                        ico = _icono_archivo(ruta, 22)
                    texto = nombre
                else:
                    ico = _obtener_thumbnail_o_icono(ruta, 22)
                    tam_str = _formato_tamano(elem['tamano'])
                    texto = f"{nombre}   ({tam_str})"

                item = QListWidgetItem(ico, texto)
                item.setData(Qt.ItemDataRole.UserRole, ruta)
                item.setData(Qt.ItemDataRole.UserRole + 1, 'dir' if es_dir else 'file')
                item.setSizeHint(QSize(0, 26))
                
                info_tt = f"{nombre}\n{t('Tipo:')} {elem['tipo']}\n{t('Fecha:')} {_formato_fecha(elem['mtime'])}"
                if not es_dir:
                    info_tt += f"\n{t('Tamaño:')} {_formato_tamano(elem['tamano'])}"
                item.setToolTip(info_tt)
                self.lista_archivos.addItem(item)

    def _poblar_tabla_detalles(self, items):
        self.tabla_archivos.clear()

        for elem in items:
            ruta = elem['ruta']
            nombre = elem['nombre']
            es_dir = elem['es_dir']

            if es_dir:
                ico = _ico('folder.png')
                if ico.isNull():
                    ico = _icono_archivo(ruta, 20)
                str_tam = "-"
            else:
                ico = _obtener_thumbnail_o_icono(ruta, 20)
                str_tam = _formato_tamano(elem['tamano'])

            str_fecha = _formato_fecha(elem['mtime'])
            str_tipo = elem['tipo']

            item = QTreeWidgetItem([nombre, str_tipo, str_tam, str_fecha])
            item.setIcon(0, ico)
            item.setData(0, Qt.ItemDataRole.UserRole, ruta)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, 'dir' if es_dir else 'file')
            item.setTextAlignment(2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            self.tabla_archivos.addTopLevelItem(item)

    def _cambiar_filtro(self, idx):
        self._filtro_activo = idx
        self._cargar_directorio(self._directorio)

    # Interacción con la vista

    def _item_clic_lista(self, item):
        tipo = item.data(Qt.ItemDataRole.UserRole + 1)
        if tipo == 'file':
            ruta = item.data(Qt.ItemDataRole.UserRole)
            self.edit_nombre.setText(os.path.basename(ruta))

    def _item_doble_clic_lista(self, item):
        tipo = item.data(Qt.ItemDataRole.UserRole + 1)
        ruta = item.data(Qt.ItemDataRole.UserRole)
        if tipo == 'dir':
            self._navegar(ruta)
        else:
            self.edit_nombre.setText(os.path.basename(ruta))
            self._confirmar()

    def _item_clic_tabla(self, item, col):
        tipo = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if tipo == 'file':
            ruta = item.data(0, Qt.ItemDataRole.UserRole)
            self.edit_nombre.setText(os.path.basename(ruta))

    def _item_doble_clic_tabla(self, item, col):
        tipo = item.data(0, Qt.ItemDataRole.UserRole + 1)
        ruta = item.data(0, Qt.ItemDataRole.UserRole)
        if tipo == 'dir':
            self._navegar(ruta)
        else:
            self.edit_nombre.setText(os.path.basename(ruta))
            self._confirmar()

    def _tecla_lista(self, event):
        key = event.key()
        item_actual = self.lista_archivos.currentItem()

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if item_actual:
                tipo = item_actual.data(Qt.ItemDataRole.UserRole + 1)
                if tipo == 'dir':
                    self._navegar(item_actual.data(Qt.ItemDataRole.UserRole))
                else:
                    self.edit_nombre.setText(
                        os.path.basename(item_actual.data(Qt.ItemDataRole.UserRole))
                    )
                    self._confirmar()
        elif key == Qt.Key.Key_Backspace:
            self._subir_nivel()
        else:
            QListWidget.keyPressEvent(self.lista_archivos, event)

    def _tecla_tabla(self, event):
        key = event.key()
        item_actual = self.tabla_archivos.currentItem()

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if item_actual:
                tipo = item_actual.data(0, Qt.ItemDataRole.UserRole + 1)
                if tipo == 'dir':
                    self._navegar(item_actual.data(0, Qt.ItemDataRole.UserRole))
                else:
                    self.edit_nombre.setText(
                        os.path.basename(item_actual.data(0, Qt.ItemDataRole.UserRole))
                    )
                    self._confirmar()
        elif key == Qt.Key.Key_Backspace:
            self._subir_nivel()
        else:
            QTreeWidget.keyPressEvent(self.tabla_archivos, event)

    # Confirmación de selección

    def _confirmar(self):
        if self._modo == "directorio":
            self._ruta_seleccionada = self._directorio
            self.settings.setValue("default_dir", self._directorio)
            self.accept()
            return

        nombre = self.edit_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, t("Sin nombre"),
                                t("Por favor ingresá un nombre de archivo."))
            return

        if os.path.isabs(nombre):
            ruta = nombre
        else:
            ruta = os.path.join(self._directorio, nombre)

        if self._modo == "abrir":
            if not os.path.isfile(ruta):
                QMessageBox.warning(self, t("Archivo no encontrado"),
                                    t("El archivo no existe:") + f"\n{ruta}")
                return

        elif self._modo == "guardar":
            _, exts = self._filtros[self._filtro_activo]
            if exts and not any(nombre.lower().endswith(e) for e in exts):
                ext_defecto = sorted(exts)[0]
                nombre += ext_defecto
                ruta = os.path.join(self._directorio, nombre)

            if os.path.exists(ruta):
                resp = QMessageBox.question(
                    self, t("¿Sobreescribir?"),
                    f"'{os.path.basename(ruta)}' {t('ya existe.')}\n{t('¿Deseas reemplazarlo?')}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if resp != QMessageBox.StandardButton.Yes:
                    return

        self.settings.setValue("default_dir", self._directorio)
        self._ruta_seleccionada = ruta
        self.accept()

    # API pública

    def ruta_seleccionada(self):
        """Devuelve la ruta completa seleccionada, o None si se canceló."""
        return self._ruta_seleccionada

    # Teclado global

    def keyPressEvent(self, event):
        key = event.key()
        mod = event.modifiers()
        if key == Qt.Key.Key_Escape:
            self.reject()
        elif key == Qt.Key.Key_Left and mod == Qt.KeyboardModifier.AltModifier:
            self._ir_atras()
        elif key == Qt.Key.Key_Right and mod == Qt.KeyboardModifier.AltModifier:
            self._ir_adelante()
        else:
            super().keyPressEvent(event)
