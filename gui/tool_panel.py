from PyQt6.QtWidgets import QWidget, QGridLayout, QToolButton, QButtonGroup, QVBoxLayout
from PyQt6.QtGui import QIcon, QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtCore import QSize, Qt, QRectF

from tools.select_rect import SelectRectTool
from tools.move_select_only import MoveSelectOnlyTool
from tools.select_free import SelectFreeTool
from tools.move_select_pixels import MoveSelectPixelsTool
from tools.select_ellipse import SelectEllipseTool
from tools.invert_selection import InvertSelectionTool
from tools.zoom import ZoomTool
from tools.bucket import BucketTool
from tools.eraser import EraserTool
from tools.brush import BrushTool
from tools.eyedropper import EyedropperTool
from tools.pencil import PencilTool
from tools.text import TextTool
from tools.magic_wand import MagicWandTool
from tools.line import LineTool
from tools.gradient import GradientTool
from tools.shapes import ShapesTool
from tools.blur import BlurTool


class ShortcutToolButton(QToolButton):
    """QToolButton personalizado que dibuja una insignia con fondo gris/negro en la esquina inferior izquierda."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.shortcut_char = ""

    def set_shortcut_char(self, char_str):
        self.shortcut_char = str(char_str).upper() if char_str else ""
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.shortcut_char:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            
            # Recuadro gris oscuro de 8x8 en la esquina inferior izquierda
            bg_rect = QRectF(2, self.height() - 10, 8, 8)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(30, 30, 30, 230)))
            p.drawRect(bg_rect)

            # Letra blanca centrada de 6px
            font = QFont("Arial", 6, QFont.Weight.Bold)
            p.setFont(font)
            p.setPen(QPen(QColor(255, 255, 255)))
            p.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, self.shortcut_char)
            p.end()


class ToolPanelWidget(QWidget):
    """Panel de herramientas centrado con 18 herramientas e insignias de atajos."""
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)

        grid = QGridLayout()
        grid.setSpacing(4)
        grid.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.tools_grid = [
            [SelectRectTool(), MoveSelectOnlyTool()],
            [SelectFreeTool(), MoveSelectPixelsTool()],
            [SelectEllipseTool(), InvertSelectionTool()],
            [BucketTool(), GradientTool()],
            [BrushTool(), EyedropperTool()],
            [PencilTool(), EraserTool()],
            [MagicWandTool(), LineTool()],
            [TextTool(), ZoomTool()],
            [ShapesTool(), BlurTool()],
        ]

        def _make_tool_handler(tool_obj):
            return lambda *args: self.select_tool(tool_obj)

        for row_idx, row in enumerate(self.tools_grid):
            for col_idx, tool in enumerate(row):
                btn = ShortcutToolButton()
                btn.setCheckable(True)
                btn.setToolTip(tool.name)
                btn.setProperty("tool_obj", tool)
                btn.setFixedSize(32, 32)
                btn.setIconSize(QSize(24, 24))

                if tool.icon_path:
                    btn.setIcon(QIcon(tool.icon_path))
                btn.clicked.connect(_make_tool_handler(tool))

                if isinstance(tool, PencilTool):
                    btn.setChecked(True)

                self.button_group.addButton(btn)
                grid.addWidget(btn, row_idx, col_idx)

        layout.addLayout(grid)
        layout.addStretch()
        self.setLayout(layout)
        self.setFixedWidth(82)

        self.actualizar_insignias_atajos()

    def actualizar_insignias_atajos(self):
        from gui.dialogo_atajos import cargar_atajos
        atajos = cargar_atajos()

        for btn in self.button_group.buttons():
            tool = btn.property("tool_obj")
            if tool:
                nombre = tool.name
                char = atajos.get(nombre, "")
                if isinstance(btn, ShortcutToolButton):
                    btn.set_shortcut_char(char)

    def select_tool(self, tool):
        for btn in self.button_group.buttons():
            t = btn.property("tool_obj")
            if t and (t == tool or type(t) is type(tool) or (hasattr(t, 'name') and hasattr(tool, 'name') and t.name == tool.name)):
                btn.setChecked(True)
                break

        if self.main_window and hasattr(self.main_window, 'canvas'):
            self.main_window.canvas.set_active_tool(tool)
            if isinstance(tool, InvertSelectionTool):
                self.main_window.canvas.invertir_seleccion()
