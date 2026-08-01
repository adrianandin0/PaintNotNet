"""
dialogo_archivo.py – Gestor de archivos propio de PaintNotNet.
Reemplaza QFileDialog para evitar dependencias del entorno de escritorio (KDE/XFCE/GNOME).
"""

import os
import sys

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QComboBox, QPushButton, QLabel, QFrame,
    QSizePolicy, QAbstractItemView, QFileIconProvider,
    QMessageBox, QWidget
)
from PyQt6.QtCore import Qt, QSize, QFileInfo, QDir, QSettings, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon, QFont


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lugares_rapidos():
    """Devuelve una lista de (etiqueta, ruta) para el panel izquierdo."""
    lugares = []

    # Home del usuario real
    usuario_real = (
        os.environ.get('SUDO_USER') or
        os.environ.get('LOGNAME') or
        os.environ.get('USER') or
        os.environ.get('USERNAME')  # Windows
    )
    if usuario_real and usuario_real != 'root':
        home = os.path.join('/home', usuario_real)
        if not os.path.exists(home):
            home = os.path.expanduser('~')
    else:
        home = os.path.expanduser('~')

    lugares.append(('🏠  Inicio', home))

    # Escritorio
    for nombre in ('Desktop', 'Escritorio'):
        p = os.path.join(home, nombre)
        if os.path.isdir(p):
            lugares.append(('🖥  Escritorio', p))
            break

    # Imágenes
    for nombre in ('Pictures', 'Imágenes', 'Imagenes', 'Images'):
        p = os.path.join(home, nombre)
        if os.path.isdir(p):
            lugares.append(('🖼  Imágenes', p))
            break

    # Documentos
    for nombre in ('Documents', 'Documentos'):
        p = os.path.join(home, nombre)
        if os.path.isdir(p):
            lugares.append(('📄  Documentos', p))
            break

    # Descargas
    for nombre in ('Downloads', 'Descargas'):
        p = os.path.join(home, nombre)
        if os.path.isdir(p):
            lugares.append(('⬇  Descargas', p))
            break

    # Raíces de disco
    if sys.platform == 'win32':
        import string
        for letra in string.ascii_uppercase:
            raiz = f'{letra}:\\'
            if os.path.exists(raiz):
                lugares.append((f'💾  {raiz}', raiz))
    else:
        lugares.append(('🗄  Sistema (/)', '/'))
        media = '/media'
        if os.path.isdir(media):
            try:
                for sub in sorted(os.listdir(media)):
                    p = os.path.join(media, sub)
                    if os.path.isdir(p):
                        lugares.append((f'💿  {sub}', p))
            except PermissionError:
                pass

    return lugares


def _miniatura(ruta, size=48):
    """Devuelve un QIcon con miniatura para imágenes, o ícono genérico para el resto."""
    ext = os.path.splitext(ruta)[1].lower()
    if ext in ('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.gif'):
        pix = QPixmap(ruta)
        if not pix.isNull():
            pix = pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
            return QIcon(pix)
    proveedor = QFileIconProvider()
    return proveedor.icon(QFileInfo(ruta))


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------

class DialogoArchivo(QDialog):
    """
    Diálogo de exploración de archivos propio de PaintNotNet.

    Parámetros
    ----------
    parent : QWidget | None
    modo : str
        "abrir"   → botón "Abrir",  selección de archivo existente
        "guardar" → botón "Guardar", permite escribir nombre nuevo
    directorio : str
        Directorio inicial.
    filtros : list[tuple[str, str]]
        Lista de (descripción, patrón), e.g.:
        [("Imágenes PNG", "*.png"), ("Todos los archivos", "*")]
    nombre_sugerido : str
        Nombre de archivo pre-relleno (útil en modo guardar).
    titulo : str
        Título de la ventana.
    """

    def __init__(self, parent=None, modo="abrir", directorio=None,
                 filtros=None, nombre_sugerido="", titulo=None):
        super().__init__(parent)

        self._modo = modo
        self._ruta_seleccionada = None

        if titulo:
            self.setWindowTitle(titulo)
        elif modo == "guardar":
            self.setWindowTitle("Guardar como…")
        else:
            self.setWindowTitle("Abrir archivo")

        self.setMinimumSize(820, 520)
        self.resize(920, 580)

        # Filtros internos: lista de (descripción, set de extensiones)
        self._filtros = self._parsear_filtros(filtros)
        self._filtro_activo = 0  # índice en self._filtros

        # Directorio de trabajo
        if directorio and os.path.isdir(directorio):
            self._directorio = directorio
        else:
            self._directorio = os.path.expanduser('~')

        self._construir_ui(nombre_sugerido)
        self._poblar_lugares()
        self._navegar(self._directorio, agregar_historial=False)
        self._aplicar_estilos()

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _construir_ui(self, nombre_sugerido):
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(6)
        layout_principal.setContentsMargins(10, 10, 10, 10)

        # --- Barra de navegación ---
        barra_nav = QHBoxLayout()
        barra_nav.setSpacing(4)

        self.btn_atras = QPushButton("◀")
        self.btn_atras.setFixedSize(30, 30)
        self.btn_atras.setToolTip("Atrás")
        self.btn_atras.setEnabled(False)
        self.btn_atras.clicked.connect(self._ir_atras)

        self.btn_arriba = QPushButton("⬆")
        self.btn_arriba.setFixedSize(30, 30)
        self.btn_arriba.setToolTip("Subir un nivel")
        self.btn_arriba.clicked.connect(self._subir_nivel)

        self.btn_home = QPushButton("🏠")
        self.btn_home.setFixedSize(30, 30)
        self.btn_home.setToolTip("Ir al directorio de inicio")
        self.btn_home.clicked.connect(self._ir_home)

        self.lbl_ruta = QLineEdit()
        self.lbl_ruta.setReadOnly(False)
        self.lbl_ruta.setPlaceholderText("Ruta…")
        self.lbl_ruta.returnPressed.connect(self._navegar_ruta_manual)

        self.btn_ir = QPushButton("Ir")
        self.btn_ir.setFixedSize(36, 30)
        self.btn_ir.clicked.connect(self._navegar_ruta_manual)

        barra_nav.addWidget(self.btn_atras)
        barra_nav.addWidget(self.btn_arriba)
        barra_nav.addWidget(self.btn_home)
        barra_nav.addWidget(self.lbl_ruta, stretch=1)
        barra_nav.addWidget(self.btn_ir)
        layout_principal.addLayout(barra_nav)

        # --- Splitter central ---
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panel izquierdo – Lugares rápidos
        self.lista_lugares = QListWidget()
        self.lista_lugares.setFixedWidth(180)
        self.lista_lugares.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.lista_lugares.itemClicked.connect(self._lugar_clickado)
        splitter.addWidget(self.lista_lugares)

        # Panel derecho – Contenido del directorio
        self.lista_archivos = QListWidget()
        self.lista_archivos.setViewMode(QListWidget.ViewMode.ListMode)
        self.lista_archivos.setIconSize(QSize(48, 48))
        self.lista_archivos.setSpacing(2)
        self.lista_archivos.setUniformItemSizes(False)
        self.lista_archivos.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.lista_archivos.itemDoubleClicked.connect(self._item_doble_clic)
        self.lista_archivos.itemClicked.connect(self._item_clic)
        self.lista_archivos.keyPressEvent = self._tecla_lista_archivos
        splitter.addWidget(self.lista_archivos)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        layout_principal.addWidget(splitter, stretch=1)

        # --- Fila nombre + filtro ---
        fila_nombre = QHBoxLayout()
        fila_nombre.setSpacing(6)
        fila_nombre.addWidget(QLabel("Nombre:"))

        self.edit_nombre = QLineEdit(nombre_sugerido)
        self.edit_nombre.setPlaceholderText("nombre del archivo…")
        if self._modo == "abrir":
            self.edit_nombre.setReadOnly(True)
        fila_nombre.addWidget(self.edit_nombre, stretch=1)

        fila_nombre.addWidget(QLabel("Tipo:"))
        self.combo_filtro = QComboBox()
        self.combo_filtro.setMinimumWidth(200)
        for desc, _ in self._filtros:
            self.combo_filtro.addItem(desc)
        self.combo_filtro.currentIndexChanged.connect(self._cambiar_filtro)
        fila_nombre.addWidget(self.combo_filtro)

        layout_principal.addLayout(fila_nombre)

        # --- Botones de acción ---
        fila_btns = QHBoxLayout()
        fila_btns.addStretch()

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setFixedWidth(100)
        self.btn_cancelar.clicked.connect(self.reject)

        etiqueta_ok = "Guardar" if self._modo == "guardar" else "Abrir"
        self.btn_ok = QPushButton(etiqueta_ok)
        self.btn_ok.setFixedWidth(100)
        self.btn_ok.setDefault(True)
        self.btn_ok.clicked.connect(self._confirmar)

        fila_btns.addWidget(self.btn_cancelar)
        fila_btns.addWidget(self.btn_ok)
        layout_principal.addLayout(fila_btns)

        # Historial de navegación
        self._historial = []
        self._pos_historial = -1

    # ------------------------------------------------------------------
    # Estilos
    # ------------------------------------------------------------------

    def _aplicar_estilos(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QLabel {
                color: #c0c0c0;
                font-size: 13px;
            }
            QLineEdit {
                background-color: #1e1e1e;
                color: #e8e8e8;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #5a8fd0;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #6a8fd0;
            }
            QPushButton:pressed {
                background-color: #2e5094;
            }
            QPushButton#btn_ok {
                background-color: #2e5094;
                border-color: #3a6ac0;
                font-weight: bold;
            }
            QPushButton#btn_ok:hover {
                background-color: #3a6ac0;
            }
            QListWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 4px;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                padding: 4px 6px;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #2e5094;
                color: #ffffff;
            }
            QListWidget::item:hover:!selected {
                background-color: #383838;
            }
            QComboBox {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: #e0e0e0;
                selection-background-color: #2e5094;
            }
            QSplitter::handle {
                background-color: #444;
                width: 3px;
            }
        """)
        self.btn_ok.setObjectName("btn_ok")

    # ------------------------------------------------------------------
    # Lugares rápidos
    # ------------------------------------------------------------------

    def _poblar_lugares(self):
        self.lista_lugares.clear()
        self._rutas_lugares = []
        for etiqueta, ruta in _lugares_rapidos():
            item = QListWidgetItem(etiqueta)
            item.setToolTip(ruta)
            self.lista_lugares.addItem(item)
            self._rutas_lugares.append(ruta)

    def _lugar_clickado(self, item):
        idx = self.lista_lugares.row(item)
        ruta = self._rutas_lugares[idx]
        self._navegar(ruta)

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------

    def _navegar(self, directorio, agregar_historial=True):
        if not os.path.isdir(directorio):
            return

        if agregar_historial:
            # Truncar historial al índice actual
            self._historial = self._historial[:self._pos_historial + 1]
            self._historial.append(directorio)
            self._pos_historial = len(self._historial) - 1

        self._directorio = directorio
        self.lbl_ruta.setText(directorio)
        self.btn_atras.setEnabled(self._pos_historial > 0)
        self._cargar_directorio(directorio)

    def _ir_atras(self):
        if self._pos_historial > 0:
            self._pos_historial -= 1
            self._navegar(self._historial[self._pos_historial], agregar_historial=False)
            self.btn_atras.setEnabled(self._pos_historial > 0)

    def _subir_nivel(self):
        padre = os.path.dirname(self._directorio)
        if padre != self._directorio:
            self._navegar(padre)

    def _ir_home(self):
        home = _lugares_rapidos()[0][1]
        self._navegar(home)

    def _navegar_ruta_manual(self):
        ruta = self.lbl_ruta.text().strip()
        if os.path.isdir(ruta):
            self._navegar(ruta)
        elif os.path.isfile(ruta):
            self.edit_nombre.setText(os.path.basename(ruta))
            self._navegar(os.path.dirname(ruta))
        else:
            QMessageBox.warning(self, "Ruta inválida",
                                f"La ruta no existe:\n{ruta}")

    # ------------------------------------------------------------------
    # Carga del directorio
    # ------------------------------------------------------------------

    def _parsear_filtros(self, filtros):
        """Convierte los filtros a lista de (descripción, set_extensiones)."""
        if not filtros:
            return [("Todos los archivos", set())]
        resultado = []
        for desc, patron in filtros:
            exts = set()
            for parte in patron.split():
                if parte.startswith('*.'):
                    exts.add(parte[1:].lower())  # ".png"
                elif parte == '*':
                    exts = set()  # vacío = todos
                    break
            resultado.append((desc, exts))
        return resultado

    def _archivo_visible(self, nombre):
        """True si el archivo pasa el filtro activo."""
        _, exts = self._filtros[self._filtro_activo]
        if not exts:
            return True
        ext = os.path.splitext(nombre)[1].lower()
        return ext in exts

    def _cargar_directorio(self, directorio):
        self.lista_archivos.clear()
        try:
            entradas = sorted(os.listdir(directorio))
        except PermissionError:
            QMessageBox.warning(self, "Sin permiso",
                                f"No se puede acceder a:\n{directorio}")
            return

        # Primero carpetas, luego archivos
        carpetas = [e for e in entradas
                    if os.path.isdir(os.path.join(directorio, e))
                    and not e.startswith('.')]
        archivos = [e for e in entradas
                    if os.path.isfile(os.path.join(directorio, e))
                    and not e.startswith('.')
                    and self._archivo_visible(e)]

        proveedor = QFileIconProvider()

        for nombre in carpetas:
            ruta = os.path.join(directorio, nombre)
            icono = proveedor.icon(QFileInfo(ruta))
            item = QListWidgetItem(icono, f"📁 {nombre}")
            item.setData(Qt.ItemDataRole.UserRole, ruta)
            item.setData(Qt.ItemDataRole.UserRole + 1, 'dir')
            self.lista_archivos.addItem(item)

        for nombre in archivos:
            ruta = os.path.join(directorio, nombre)
            icono = _miniatura(ruta, 48)
            tam = os.path.getsize(ruta)
            tam_str = self._formato_tamano(tam)
            item = QListWidgetItem(icono, f"{nombre}\n{tam_str}")
            item.setData(Qt.ItemDataRole.UserRole, ruta)
            item.setData(Qt.ItemDataRole.UserRole + 1, 'file')
            self.lista_archivos.addItem(item)

    def _formato_tamano(self, bytes_):
        if bytes_ < 1024:
            return f"{bytes_} B"
        elif bytes_ < 1024 * 1024:
            return f"{bytes_ / 1024:.1f} KB"
        else:
            return f"{bytes_ / (1024*1024):.1f} MB"

    # ------------------------------------------------------------------
    # Interacción con la lista de archivos
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

    def _tecla_lista_archivos(self, event):
        """Navegación por teclado en la lista de archivos."""
        key = event.key()
        item_actual = self.lista_archivos.currentItem()

        if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
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

    def _cambiar_filtro(self, idx):
        self._filtro_activo = idx
        self._cargar_directorio(self._directorio)

    # ------------------------------------------------------------------
    # Confirmación
    # ------------------------------------------------------------------

    def _confirmar(self):
        nombre = self.edit_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Sin nombre",
                                "Por favor ingresá un nombre de archivo.")
            return

        ruta = os.path.join(self._directorio, nombre)

        if self._modo == "abrir":
            if not os.path.isfile(ruta):
                QMessageBox.warning(self, "Archivo no encontrado",
                                    f"El archivo no existe:\n{ruta}")
                return
        elif self._modo == "guardar":
            # Agregar extensión automáticamente si no tiene
            _, exts = self._filtros[self._filtro_activo]
            if exts and not any(nombre.lower().endswith(e) for e in exts):
                ext_defecto = sorted(exts)[0]
                nombre += ext_defecto
                ruta = os.path.join(self._directorio, nombre)

            # Confirmar sobreescritura
            if os.path.exists(ruta):
                resp = QMessageBox.question(
                    self, "¿Sobreescribir?",
                    f"'{nombre}' ya existe. ¿Deseas reemplazarlo?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if resp != QMessageBox.StandardButton.Yes:
                    return

        # Guardar último directorio en QSettings
        settings = QSettings("PaintNotNet", "PaintNotNet")
        settings.setValue("default_dir", self._directorio)

        self._ruta_seleccionada = ruta
        self.accept()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def ruta_seleccionada(self):
        """Devuelve la ruta completa seleccionada/escrita, o None si se canceló."""
        return self._ruta_seleccionada

    # ------------------------------------------------------------------
    # Teclado global del diálogo
    # ------------------------------------------------------------------

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
