"""
gui/shortcut_manager.py — Gestor centralizado de atajos de teclado e interceptación de foco.
"""
from PyQt6.QtCore import QObject, QEvent, Qt
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (
    QApplication, QDialog, QLineEdit, QTextEdit, QPlainTextEdit,
    QAbstractSpinBox, QComboBox
)


class ShortcutManager(QObject):
    """Gestor de interceptación de eventos de teclado y activación de herramientas."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window

    def process_key_event(self, event) -> bool:
        """
        Evalúa si un QKeyEvent debe ser procesado como un atajo de teclado de 1 letra.
        Devuelve True si el atajo fue consumido y manejado, False en caso contrario.
        """
        # 1. Si el foco está en un control de entrada (spinbox, combobox, lineedit), ignorar atajos de herramienta
        focus_w = QApplication.focusWidget()
        if focus_w:
            if focus_w.window() != self.main_window and isinstance(focus_w.window(), QDialog):
                return False
            if isinstance(focus_w, (QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox, QComboBox)):
                return False

        # 2. Si la herramienta Texto está activa Y el usuario está editando activamente un cuadro de texto en el lienzo, no interceptar
        canvas = getattr(self.main_window, 'lienzo', getattr(self.main_window, 'canvas', None))
        if canvas and hasattr(canvas, 'active_tool_obj'):
            from tools.text import TextTool
            if isinstance(canvas.active_tool_obj, TextTool) and getattr(canvas.active_tool_obj, 'is_editing', False):
                return False

        # 3. Evaluar si la tecla presionada es un atajo simple de 1 letra (sin Ctrl/Alt)
        key = event.key()
        key_text = QKeySequence(key).toString().upper()
        if not key_text:
            key_text = event.text().upper()

        if key_text and len(key_text) == 1 and not (event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)):
            from gui.dialogo_atajos import cargar_atajos
            atajos = cargar_atajos()

            for tool_name, char in atajos.items():
                if char and char.upper() == key_text:
                    tool_panel = getattr(self.main_window, 'tool_panel', None)
                    if tool_panel and hasattr(tool_panel, 'button_group'):
                        for btn in tool_panel.button_group.buttons():
                            tool = btn.property("tool_obj")
                            if tool and hasattr(tool, 'name') and tool.name == tool_name:
                                tool_panel.select_tool(tool)
                                if canvas:
                                    canvas.setFocus()
                                return True

        return False
