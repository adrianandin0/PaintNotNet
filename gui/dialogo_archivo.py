"""
dialogo_archivo.py – Gestor de archivos propio de PaintNotNet.
Reemplaza QFileDialog para evitar dependencias del entorno de escritorio.
"""

import os
import sys

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QLineEdit, QComboBox,
    QPushButton, QLabel, QSizePolicy, QAbstractItemView,
    QFileIconProvider, QMessageBox, QWidget, QToolButton, QFrame
)
from PyQt6.QtCore import Qt, QSize, QFileInfo, QDir, QSettings, QTimer
from PyQt6.QtGui import QPixmap, QIcon, QFont, QColor
from core.i18n import t


# ---------------------------------------------------------------------------
# Rutas de iconos
# ---------------------------------------------------------------------------

_BASE = "gui/iconos"

def _ico(nombre):
    return QIcon(os.path.join(_BASE, nombre))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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

    lugares.append(('Inicio', home, 'home.png'))

    for nombre in ('Desktop', 'Escritorio'):
        p = os.path.join(home, nombre)
        if os.path.isdir(p):
            lugares.append(('Escritorio', p, 'desktop.png'))
            break

    for nombre in ('Pictures', 'Imágenes', 'Imagenes', 'Images'):
        p = os.path.join(home, nombre)
        if os.path.isdir(p):
            lugares.append(('Imágenes', p, 'gallery.png'))
            break

    for nombre in ('Documents', 'Documentos'):
        p = os.path.join(home, nombre)
        if os.path.isdir(p):
            lugares.append(('Documentos', p, 'documents.png'))
            break

    for nombre in ('Downloads', 'Descargas'):
        p = os.path.join(home, nombre)
        if os.path.isdir(p):
            lugares.append(('Descargas', p, 'arrow_down.png'))
            break

    if sys.platform == 'win32':
        import string
        for letra in string.ascii_uppercase:
            raiz = f'{letra}:\\'
            if os.path.exists(raiz):
                lugares.append((f'{raiz}', raiz, 'disk.png'))
    else:
        lugares.append(('Sistema (/)', '/', 'disk.png'))
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


def _icono_archivo(ruta, thumb_size=48):
    """Devuelve QIcon: miniatura para imágenes, pnn.png para .pnn, folder para dirs, picture para el resto."""
    if os.path.isdir(ruta):
        return _ico('folder.png')

    ext = os.path.splitext(ruta)[1].lower()

    if ext == '.pnn':
        return _ico('pnn.png')

    if ext in ('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.gif'):
        pix = QPixmap(ruta)
        if not pix.isNull():
            pix = pix.scaled(thumb_size, thumb_size,
                             Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
            return QIcon(pix)
        return _ico('picture.png')

    return _ico('picture.png')


def _formato_tamano(bytes_):
    if bytes_ < 1024:
        return f"{bytes_} B"
    elif bytes_ < 1024 * 1024:
        return f"{bytes_ / 1024:.1f} KB"
    else:
        return f"{bytes_ / (1024*1024):.1f} MB"


# ---------------------------------------------------------------------------
# Botón de navegación con icono
# ---------------------------------------------------------------------------

def _nav_btn(icono_nombre, tooltip, size=28):
    btn = QToolButton()
    btn.setIcon(_ico(icono_nombre))
    btn.setIconSize(QSize(16, 16))
    btn.setFixedSize(size, size)
    btn.setToolTip(tooltip)
    btn.setStyleSheet("""
        QToolButton {
            background: #3a3a3a;
            border: 1px solid #505050;
            border-radius: 4px;
        }
        QToolButton:hover { background: #4a4a4a; border-color: #6a8fd0; }
        QToolButton:pressed { background: #2e5094; }
        QToolButton:disabled { background: #2d2d2d; border-color: #3a3a3a; opacity: 0.4; }
    """)
    return btn


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------

class DialogoArchivo(QDialog):
    """
    Diálogo de exploración de archivos propio de PaintNotNet.

    Parámetros
    ----------
    parent       : QWidget | None
    modo         : "abrir" | "guardar" | "directorio"
    directorio   : str  — directorio inicial
    filtros      : list[tuple[str, str]]  — [(descripción, patrón), …]
    nombre_sugerido : str
    titulo       : str
    """

    def __init__(self, parent=None, modo="abrir", directorio=None,
                 filtros=None, nombre_sugerido="", titulo=None):
        super().__init__(parent)

        self._modo = modo
        self._ruta_seleccionada = None
        self._historial = []
        self._pos_historial = -1

        # Título
        if titulo:
            self.setWindowTitle(titulo)
        elif modo == "guardar":
            self.setWindowTitle(t("Guardar como…"))
        elif modo == "directorio":
            self.setWindowTitle(t("Seleccionar carpeta"))
        else:
            self.setWindowTitle(t("Abrir archivo"))

        self.setMinimumSize(820, 520)
        self.resize(960, 580)

        # Filtros
        self._filtros = self._parsear_filtros(filtros)
        self._filtro_activo = 0

        # Directorio inicial
        if directorio and os.path.isdir(directorio):
            self._directorio = directorio
        else:
            self._directorio = os.path.expanduser('~')

        self._construir_ui(nombre_sugerido)
        self._aplicar_estilos()
        self._poblar_lugares()
        self._navegar(self._directorio, agregar_historial=False)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _construir_ui(self, nombre_sugerido):
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(10, 10, 10, 10)

        # ── Barra de navegación ──────────────────────────────────────────
        barra = QHBoxLayout()
        barra.setSpacing(3)

        self.btn_atras = _nav_btn('arrow_left.png', 'Atrás (Alt+←)')
        self.btn_atras.setEnabled(False)
        self.btn_atras.clicked.connect(self._ir_atras)

        self.btn_adelante = _nav_btn('arrow_right.png', 'Adelante (Alt+→)')
        self.btn_adelante.setEnabled(False)
        self.btn_adelante.clicked.connect(self._ir_adelante)

        self.btn_arriba = _nav_btn('arrow_up.png', 'Subir nivel (Backspace)')
        self.btn_arriba.clicked.connect(self._subir_nivel)

        self.btn_home = _nav_btn('home.png', 'Carpeta personal')
        self.btn_home.clicked.connect(self._ir_home)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #444;")

        self.edit_ruta = QLineEdit()
        self.edit_ruta.setPlaceholderText(t("Ruta o nombre de carpeta…"))
        self.edit_ruta.returnPressed.connect(self._navegar_ruta_manual)

        self.btn_ir = QPushButton(t("Ir"))
        self.btn_ir.setFixedWidth(40)
        self.btn_ir.setFixedHeight(28)
        self.btn_ir.clicked.connect(self._navegar_ruta_manual)

        barra.addWidget(self.btn_atras)
        barra.addWidget(self.btn_adelante)
        barra.addWidget(self.btn_arriba)
        barra.addWidget(self.btn_home)
        barra.addWidget(sep)
        barra.addWidget(self.edit_ruta, stretch=1)
        barra.addWidget(self.btn_ir)
        root.addLayout(barra)

        # ── Splitter central ─────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panel izquierdo – Lugares rápidos
        self.lista_lugares = QListWidget()
        self.lista_lugares.setFixedWidth(170)
        self.lista_lugares.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.lista_lugares.setIconSize(QSize(16, 16))
        self.lista_lugares.itemClicked.connect(self._lugar_clickado)
        splitter.addWidget(self.lista_lugares)

        # Panel derecho – Contenido
        self.lista_archivos = QListWidget()
        self.lista_archivos.setViewMode(QListWidget.ViewMode.ListMode)
        self.lista_archivos.setIconSize(QSize(48, 48))
        self.lista_archivos.setSpacing(2)
        self.lista_archivos.setUniformItemSizes(False)
        self.lista_archivos.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.lista_archivos.itemDoubleClicked.connect(self._item_doble_clic)
        self.lista_archivos.itemClicked.connect(self._item_clic)
        self.lista_archivos.keyPressEvent = self._tecla_lista
        splitter.addWidget(self.lista_archivos)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, stretch=1)

        # ── Fila nombre + filtro ─────────────────────────────────────────
        fila_nombre = QHBoxLayout()
        fila_nombre.setSpacing(6)

        lbl_nombre = QLabel(t("Nombre:"))
        lbl_nombre.setFixedWidth(60)
        fila_nombre.addWidget(lbl_nombre)

        self.edit_nombre = QLineEdit(nombre_sugerido)
        self.edit_nombre.setPlaceholderText(t("nombre del archivo…"))
        if self._modo == "abrir":
            self.edit_nombre.setReadOnly(True)
        # Solo en modos abrir/guardar, Enter en el nombre confirma.
        # En modo directorio, Enter nunca confirma (sólo el botón lo hace).
        if self._modo != "directorio":
            self.edit_nombre.returnPressed.connect(self._confirmar)
        fila_nombre.addWidget(self.edit_nombre, stretch=1)

        if self._modo != "directorio":
            lbl_tipo = QLabel(t("Tipo:"))
            lbl_tipo.setFixedWidth(36)
            fila_nombre.addWidget(lbl_tipo)

            self.combo_filtro = QComboBox()
            self.combo_filtro.setMinimumWidth(210)
            for desc, _ in self._filtros:
                self.combo_filtro.addItem(desc)
            self.combo_filtro.currentIndexChanged.connect(self._cambiar_filtro)
            fila_nombre.addWidget(self.combo_filtro)

        root.addLayout(fila_nombre)

        # ── Botones de acción ────────────────────────────────────────────
        fila_btns = QHBoxLayout()
        fila_btns.setSpacing(6)
        fila_btns.addStretch()

        self.btn_cancelar = QPushButton(t("  Cancelar"))
        self.btn_cancelar.setIcon(_ico('cancel.png'))
        self.btn_cancelar.setIconSize(QSize(16, 16))
        self.btn_cancelar.setFixedHeight(32)
        self.btn_cancelar.setMinimumWidth(110)
        self.btn_cancelar.setAutoDefault(False)
        self.btn_cancelar.setDefault(False)
        self.btn_cancelar.clicked.connect(self.reject)

        if self._modo == "guardar":
            etiq_ok, ico_ok = t("  Guardar"), 'save.png'
        elif self._modo == "directorio":
            etiq_ok, ico_ok = t("  Seleccionar"), 'open.png'
        else:
            etiq_ok, ico_ok = t("  Abrir"), 'open.png'

        self.btn_ok = QPushButton(etiq_ok)
        self.btn_ok.setIcon(_ico(ico_ok))
        self.btn_ok.setIconSize(QSize(16, 16))
        self.btn_ok.setObjectName("btn_ok")
        self.btn_ok.setFixedHeight(32)
        self.btn_ok.setMinimumWidth(110)
        self.btn_ok.setAutoDefault(False)
        self.btn_ok.setDefault(False)
        self.btn_ok.clicked.connect(self._confirmar)

        fila_btns.addWidget(self.btn_cancelar)
        fila_btns.addWidget(self.btn_ok)
        root.addLayout(fila_btns)

    # ------------------------------------------------------------------
    # Estilos
    # ------------------------------------------------------------------

    def _aplicar_estilos(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #252525;
                color: #e0e0e0;
            }
            QLabel {
                color: #b8b8b8;
                font-size: 12px;
            }
            QLineEdit {
                background-color: #1c1c1c;
                color: #ececec;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #4a7cc7;
                background-color: #1e1e1e;
            }
            QLineEdit:read-only {
                background-color: #1a1a1a;
                color: #aaaaaa;
            }
            QPushButton {
                background-color: #383838;
                color: #e0e0e0;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #454545;
                border-color: #6a8fd0;
            }
            QPushButton:pressed {
                background-color: #2a4a8a;
            }
            QPushButton#btn_ok {
                background-color: #2c5490;
                border-color: #3a6ac0;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton#btn_ok:hover {
                background-color: #3a6ac0;
            }
            QPushButton#btn_ok:pressed {
                background-color: #1e3c70;
            }
            QListWidget {
                background-color: #1c1c1c;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                font-size: 12px;
                outline: none;
            }
            QListWidget::item {
                padding: 5px 6px;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #2c5490;
                color: #ffffff;
            }
            QListWidget::item:hover:!selected {
                background-color: #303030;
            }
            QComboBox {
                background-color: #383838;
                color: #e0e0e0;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QComboBox:hover { border-color: #6a8fd0; }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: #e0e0e0;
                selection-background-color: #2c5490;
                border: 1px solid #404040;
            }
            QSplitter::handle {
                background-color: #333333;
                width: 2px;
            }
            QScrollBar:vertical {
                background: #1c1c1c;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #505050;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background: #6a8fd0; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar:horizontal {
                background: #1c1c1c;
                height: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #505050;
                border-radius: 4px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover { background: #6a8fd0; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        """)

    # ------------------------------------------------------------------
    # Lugares rápidos
    # ------------------------------------------------------------------

    def _poblar_lugares(self):
        self.lista_lugares.clear()
        self._rutas_lugares = []
        for etiqueta, ruta, ico_nombre in _lugares_rapidos():
            item = QListWidgetItem(_ico(ico_nombre), etiqueta)
            item.setToolTip(ruta)
            item.setSizeHint(QSize(0, 28))
            self.lista_lugares.addItem(item)
            self._rutas_lugares.append(ruta)

    def _lugar_clickado(self, item):
        idx = self.lista_lugares.row(item)
        if idx < len(self._rutas_lugares):
            self._navegar(self._rutas_lugares[idx])

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------

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
        self._cargar_directorio(directorio)

        # En modo directorio, el campo nombre muestra la carpeta actual
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


    # ------------------------------------------------------------------
    # Carga del directorio
    # ------------------------------------------------------------------

    def _parsear_filtros(self, filtros):
        if not filtros:
            return [("Todos los archivos", set())]
        resultado = []
        for desc, patron in filtros:
            exts = set()
            for parte in patron.split():
                if parte.startswith('*.'):
                    exts.add(parte[1:].lower())
                elif parte == '*':
                    exts = set()
                    break
            resultado.append((desc, exts))
        return resultado

    def _archivo_visible(self, nombre):
        _, exts = self._filtros[self._filtro_activo]
        if not exts:
            return True
        ext = os.path.splitext(nombre)[1].lower()
        return ext in exts

    def _cargar_directorio(self, directorio):
        self.lista_archivos.clear()
        try:
            entradas = sorted(os.listdir(directorio), key=lambda x: x.lower())
        except PermissionError:
            QMessageBox.warning(self, t("Sin permiso"),
                                t("No se puede acceder a:") + f"\n{directorio}")
            return

        carpetas = [e for e in entradas
                    if os.path.isdir(os.path.join(directorio, e))
                    and not e.startswith('.')]

        if self._modo == "directorio":
            archivos = []
        else:
            archivos = [e for e in entradas
                        if os.path.isfile(os.path.join(directorio, e))
                        and not e.startswith('.')
                        and self._archivo_visible(e)]

        for nombre in carpetas:
            ruta = os.path.join(directorio, nombre)
            item = QListWidgetItem(_ico('folder.png'), nombre)
            item.setData(Qt.ItemDataRole.UserRole, ruta)
            item.setData(Qt.ItemDataRole.UserRole + 1, 'dir')
            item.setSizeHint(QSize(0, 58))
            self.lista_archivos.addItem(item)

        for nombre in archivos:
            ruta = os.path.join(directorio, nombre)
            icono = _icono_archivo(ruta, 48)
            tam_str = _formato_tamano(os.path.getsize(ruta))
            item = QListWidgetItem(icono, f"{nombre}\n{tam_str}")
            item.setData(Qt.ItemDataRole.UserRole, ruta)
            item.setData(Qt.ItemDataRole.UserRole + 1, 'file')
            item.setSizeHint(QSize(0, 58))
            self.lista_archivos.addItem(item)

    def _cambiar_filtro(self, idx):
        self._filtro_activo = idx
        self._cargar_directorio(self._directorio)

    # ------------------------------------------------------------------
    # Interacción con la lista
    # ------------------------------------------------------------------

    def _item_clic(self, item):
        tipo = item.data(Qt.ItemDataRole.UserRole + 1)
        if tipo == 'file':
            ruta = item.data(Qt.ItemDataRole.UserRole)
            self.edit_nombre.setText(os.path.basename(ruta))

    def _item_doble_clic(self, item):
        tipo = item.data(Qt.ItemDataRole.UserRole + 1)
        ruta = item.data(Qt.ItemDataRole.UserRole)
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

    # ------------------------------------------------------------------
    # Confirmación
    # ------------------------------------------------------------------

    def _confirmar(self):
        if self._modo == "directorio":
            self._ruta_seleccionada = self._directorio
            settings = QSettings("PaintNotNet", "PaintNotNet")
            settings.setValue("default_dir", self._directorio)
            self.accept()
            return

        nombre = self.edit_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, t("Sin nombre"),
                                t("Por favor ingresá un nombre de archivo."))
            return

        # Si el nombre tiene ruta absoluta, usarla directamente
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
            # Agregar extensión automáticamente si falta
            _, exts = self._filtros[self._filtro_activo]
            if exts and not any(nombre.lower().endswith(e) for e in exts):
                ext_defecto = sorted(exts)[0]
                nombre += ext_defecto
                ruta = os.path.join(self._directorio, nombre)

            if os.path.exists(ruta):
                resp = QMessageBox.question(
                    self, "¿Sobreescribir?",
                    f"'{os.path.basename(ruta)}' ya existe.\n¿Deseas reemplazarlo?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if resp != QMessageBox.StandardButton.Yes:
                    return

        settings = QSettings("PaintNotNet", "PaintNotNet")
        settings.setValue("default_dir", self._directorio)

        self._ruta_seleccionada = ruta
        self.accept()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def ruta_seleccionada(self):
        """Devuelve la ruta completa seleccionada, o None si se canceló."""
        return self._ruta_seleccionada

    # ------------------------------------------------------------------
    # Teclado global
    # ------------------------------------------------------------------

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
