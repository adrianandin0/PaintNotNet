"""
core/emergency_save.py — Sistema de Autoguardado de Emergencia para PaintNotNet.

Guarda automáticamente los lienzos abiertos en formato .pnn en una carpeta temporal
de respaldos cada vez que se registran cambios.
Formato de nombre: {nombre_lienzo}_{DDMMAAAA}_{HHMMSS}.pnn
"""
import os
import glob
from datetime import datetime
from PyQt6.QtCore import QSettings, QTimer, QObject, Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox
from core.i18n import t
from core.pnn_format import guardar_proyecto_pnn, cargar_proyecto_pnn


def obtener_directorio_emergencia():
    """Devuelve la ruta absoluta del directorio de respaldos de emergencia."""
    settings = QSettings("PaintNotNet", "PaintNotNet")
    def_path = settings.value("default_save_path", None)

    if def_path and os.path.exists(str(def_path)):
        base_dir = os.path.join(str(def_path), "emergency_backups")
    else:
        user_home = os.path.expanduser("~")
        base_dir = os.path.join(user_home, ".paintnotnet", "emergency_backups")

    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def buscar_respaldos_emergencia():
    """Devuelve la lista de archivos .pnn de respaldos de emergencia encontrados."""
    backup_dir = obtener_directorio_emergencia()
    pattern = os.path.join(backup_dir, "*.pnn")
    archivos = glob.glob(pattern)
    archivos.sort(key=os.path.getmtime, reverse=False)
    return archivos


def limpiar_todos_los_respaldos():
    """Elimina todos los archivos .pnn de respaldos de emergencia."""
    archivos = buscar_respaldos_emergencia()
    for f in archivos:
        try:
            if os.path.exists(f):
                os.remove(f)
        except Exception as e:
            print(f"[EmergencySave] Error al eliminar {f}: {e}")


class DialogoRestauracionEmergencia(QDialog):
    """Diálogo de aviso al inicio para restaurar o descartar respaldos de emergencia tras un cierre inesperado."""
    def __init__(self, count_files=1, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("Restauración de Emergencia"))
        self.setMinimumWidth(480)
        self.setStyleSheet("""
            QDialog {
                background-color: #262626;
                color: #FFFFFF;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Encabezado con Ícono y Mensaje Principal
        layout_header = QHBoxLayout()
        layout_header.setSpacing(14)

        lbl_icon = QLabel()
        from PyQt6.QtGui import QIcon
        lbl_icon.setPixmap(QIcon("gui/iconos/warning.png").pixmap(32, 32))
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignTop)

        lbl_msg = QLabel(t(
            "Se han detectado archivos de autoguardado de emergencia debidos a un cierre inesperado.\n\n"
            "¿Deseas restaurar tus lienzos?"
        ))
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("font-size: 13px; font-weight: bold; color: #FFFFFF; background: transparent; line-height: 1.3;")

        layout_header.addWidget(lbl_icon, alignment=Qt.AlignmentFlag.AlignTop)
        layout_header.addWidget(lbl_msg, stretch=1)
        layout.addLayout(layout_header)

        # Checkbox de Confirmación con Texto Multilínea Responsivo
        layout_chk = QHBoxLayout()
        layout_chk.setSpacing(10)
        layout_chk.setContentsMargins(0, 4, 0, 4)

        self.chk_confirm = QCheckBox()
        self.chk_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_confirm.setStyleSheet("""
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)

        lbl_chk = QLabel(t(
            "Entiendo que al seleccionar \"No\", todos los archivos de emergencia se eliminarán permanentemente y no se podrán recuperar."
        ))
        lbl_chk.setWordWrap(True)
        lbl_chk.setStyleSheet("font-size: 11px; color: #DDDDDD; background: transparent;")
        lbl_chk.setCursor(Qt.CursorShape.PointingHandCursor)
        lbl_chk.mousePressEvent = lambda e: self.chk_confirm.setChecked(not self.chk_confirm.isChecked())

        layout_chk.addWidget(self.chk_confirm, alignment=Qt.AlignmentFlag.AlignTop)
        layout_chk.addWidget(lbl_chk, stretch=1)
        layout.addLayout(layout_chk)

        # Botones Confirmar / Cancelar
        layout_btns = QHBoxLayout()
        layout_btns.setSpacing(12)

        btn_yes = QPushButton(t("Sí"))
        btn_yes.setDefault(True)
        btn_yes.setFixedHeight(32)
        btn_yes.setMinimumWidth(110)
        btn_yes.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_yes.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
                border: none;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        btn_yes.clicked.connect(self._on_yes)

        self.btn_no = QPushButton(t("No"))
        self.btn_no.setFixedHeight(32)
        self.btn_no.setMinimumWidth(110)
        self.btn_no.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_no.setStyleSheet("""
            QPushButton {
                background-color: #3b3b3b;
                color: #ffffff;
                font-size: 12px;
                border-radius: 4px;
                border: 1px solid #555555;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        self.btn_no.clicked.connect(self._on_no)

        layout_btns.addStretch()
        layout_btns.addWidget(btn_yes)
        layout_btns.addWidget(self.btn_no)
        layout.addLayout(layout_btns)

        self.adjustSize()

    def _on_yes(self):
        self.done(QDialog.DialogCode.Accepted)

    def _on_no(self):
        if not self.chk_confirm.isChecked():
            self.chk_confirm.setChecked(True)
            return
        self.done(QDialog.DialogCode.Rejected)


class EmergencySaveManager(QObject):
    """Gestor de Autoguardado de Emergencia asociado al ciclo de vida de cada Canvas."""

    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.active_backups = {}  # {canvas: backup_filepath}
        self.timers = {}  # {canvas: QTimer}

    def registrar_canvas(self, canvas, titulo=None):
        """Asigna un archivo de respaldo .pnn único a un canvas y programa el primer autoguardado."""
        if not canvas or canvas in self.active_backups:
            return

        backup_dir = obtener_directorio_emergencia()

        if not titulo:
            if canvas.archivo_actual:
                titulo = os.path.basename(canvas.archivo_actual)
            else:
                titulo = "Lienzo"

        # Nombre sanitizado
        nombre_base = os.path.splitext(titulo)[0]
        for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
            nombre_base = nombre_base.replace(char, '_')

        now = datetime.now()
        date_str = now.strftime("%d%m%Y")
        time_str = now.strftime("%H%M%S")

        backup_filename = f"{nombre_base}_{date_str}_{time_str}.pnn"
        backup_filepath = os.path.join(backup_dir, backup_filename)

        self.active_backups[canvas] = backup_filepath

        # Crear timer con debounce para no saturar durante el dibujo
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(400)
        timer.timeout.connect(lambda c=canvas: self.ejecutar_guardado_emergencia(c))
        self.timers[canvas] = timer

        # Guardado inicial diferido
        timer.start()

    def solicitar_guardado_emergencia(self, canvas):
        """Notifica que se produjo un cambio en el canvas para programar un autoguardado diferido."""
        if not canvas:
            return
        if canvas not in self.active_backups:
            self.registrar_canvas(canvas)
        else:
            timer = self.timers.get(canvas)
            if timer:
                timer.start()

    def ejecutar_guardado_emergencia(self, canvas):
        """Realiza en silencio la escritura del archivo .pnn de emergencia."""
        filepath = self.active_backups.get(canvas)
        if not filepath or not canvas:
            return
        try:
            guardar_proyecto_pnn(canvas, filepath)
        except Exception as e:
            print(f"[EmergencySave] Error al realizar autoguardado en {filepath}: {e}")

    def eliminar_respaldo_canvas(self, canvas):
        """Elimina el archivo de respaldo .pnn del canvas."""
        if not canvas:
            return
        filepath = self.active_backups.pop(canvas, None)
        timer = self.timers.pop(canvas, None)
        if timer:
            timer.stop()

        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"[EmergencySave] Error al eliminar respaldo {filepath}: {e}")

    def limpiar_todos(self):
        """Limpia todos los respaldos asociados al cerrar la aplicación de forma limpia."""
        for canvas in list(self.active_backups.keys()):
            self.eliminar_respaldo_canvas(canvas)
