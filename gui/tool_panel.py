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
from tools.spray import SprayTool
from tools.smudge import SmudgeTool
from tools.stamp import StampTool


class ShortcutToolButton(QToolButton):
    """QToolButton personalizado que dibuja una insignia con la letra de acceso directo en la esquina inferior izquierda."""
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
            
            from core.theme import ThemeManager
            tm = ThemeManager()
            is_dark = (tm.resolver_nombre_tema(tm.current_theme) == "Oscuro")

            if is_dark:
                bg_color = QColor(32, 32, 36, 230)
                border_color = QColor(85, 85, 90)
                text_color = QColor(255, 255, 255)
            else:
                bg_color = QColor(255, 255, 255, 240)
                border_color = QColor(140, 140, 145)
                text_color = QColor(20, 20, 20)

            # Recuadro un poco más grande con reborde en la esquina inferior derecha
            bg_rect = QRectF(self.width() - 13.0, self.height() - 13.0, 11.0, 11.0)
            p.setPen(QPen(border_color, 1.0))
            p.setBrush(QBrush(bg_color))
            p.drawRoundedRect(bg_rect, 2.0, 2.0)

            font = QFont()
            font.setPointSize(7)
            font.setBold(True)
            p.setFont(font)
            p.setPen(QPen(text_color))
            p.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, self.shortcut_char)
            p.end()


class ToolPanelWidget(QWidget):
    """Panel de herramientas centrado con herramientas e insignias de atajos."""
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
            [SelectRectTool(), MoveSelectOnlyTool(), SelectFreeTool()],
            [MoveSelectPixelsTool(), SelectEllipseTool(), InvertSelectionTool()],
            [BucketTool(), GradientTool(), BrushTool()],
            [EyedropperTool(), PencilTool(), EraserTool()],
            [SprayTool(), SmudgeTool(), StampTool()],
            [MagicWandTool(), LineTool(), TextTool()],
            [ZoomTool(), ShapesTool(), BlurTool()],
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
        self.setFixedWidth(118)

        self.actualizar_insignias_atajos()
        self.retraducir_tooltips()

    def retraducir_tooltips(self):
        from core.i18n import t
        for btn in self.button_group.buttons():
            tool = btn.property("tool_obj")
            if tool and hasattr(tool, 'name'):
                btn.setToolTip(t(tool.name))

    def actualizar_insignias_atajos(self):
        from gui.dialogo_atajos import cargar_atajos
        from PyQt6.QtCore import QSettings
        settings = QSettings("PaintNotNet", "PaintNotNet")
        show_shortcuts = settings.value("show_shortcuts", True, type=bool)

        atajos = cargar_atajos()

        for btn in self.button_group.buttons():
            tool = btn.property("tool_obj")
            if tool:
                nombre = tool.name
                char = atajos.get(nombre, "") if show_shortcuts else ""
                if isinstance(btn, ShortcutToolButton):
                    btn.set_shortcut_char(char)

    @property
    def active_tool_obj(self):
        btn = self.button_group.checkedButton()
        if btn:
            return btn.property("tool_obj")
        return PencilTool()

    def select_tool(self, tool):
        for btn in self.button_group.buttons():
            t = btn.property("tool_obj")
            if t and (t == tool or type(t) is type(tool) or (hasattr(t, 'name') and hasattr(tool, 'name') and t.name == tool.name)):
                btn.setChecked(True)
                break

        if self.main_window and hasattr(self.main_window, 'canvas'):
            if isinstance(tool, InvertSelectionTool):
                self.main_window.canvas.invertir_seleccion()
                prev_tool = getattr(self, 'herramienta_anterior', None)
                if prev_tool and not isinstance(prev_tool, InvertSelectionTool):
                    self.select_tool(prev_tool)
            else:
                self.herramienta_anterior = tool
                self.main_window.canvas.set_active_tool(tool)
