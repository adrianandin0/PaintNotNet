from PyQt6.QtWidgets import QWidget, QGridLayout, QToolButton, QButtonGroup, QVBoxLayout
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize, Qt

from tools.select_rect import SelectRectTool
from tools.move_select_only import MoveSelectOnlyTool
from tools.select_free import SelectFreeTool
from tools.move_select_pixels import MoveSelectPixelsTool
from tools.select_ellipse import SelectEllipseTool
from tools.zoom import ZoomTool
from tools.bucket import BucketTool
from tools.eraser import EraserTool
from tools.brush import BrushTool
from tools.eyedropper import EyedropperTool
from tools.pencil import PencilTool
from tools.text import TextTool
from tools.placeholder import PlaceholderTool


class ToolPanelWidget(QWidget):
    """Panel de herramientas centrado y adaptado a 82px de ancho."""
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)

        grid = QGridLayout()
        grid.setSpacing(4) # Aire prolijo entre botones
        grid.setAlignment(Qt.AlignmentFlag.AlignCenter) # <--- Centra la grilla en el panel

        self.tools_grid = [
            [SelectRectTool(), MoveSelectOnlyTool()],
            [SelectFreeTool(), MoveSelectPixelsTool()],
            [SelectEllipseTool(), ZoomTool()],
            [BucketTool(), EraserTool()],
            [BrushTool(), EyedropperTool()],
            [PencilTool(), TextTool()],
            [PlaceholderTool(1), PlaceholderTool(2)],
            [PlaceholderTool(3), PlaceholderTool(4)],
            [PlaceholderTool(5), PlaceholderTool(6)],
        ]

        for row_idx, row in enumerate(self.tools_grid):
            for col_idx, tool in enumerate(row):
                btn = QToolButton()
                btn.setCheckable(True)
                btn.setToolTip(tool.name)
                btn.setFixedSize(32, 32) # Botones algo más amplios para el ancho 82px
                btn.setIconSize(QSize(24, 24))

                btn.setIcon(QIcon(tool.icon_path))
                btn.clicked.connect(lambda checked, t=tool: self.select_tool(t))

                self.button_group.addButton(btn)
                grid.addWidget(btn, row_idx, col_idx)

        layout.addLayout(grid)
        layout.addStretch() # Empuja todo suavemente arriba
        self.setLayout(layout)
        self.setFixedWidth(82)

    def select_tool(self, tool):
        if self.main_window and hasattr(self.main_window, 'canvas'):
            self.main_window.canvas.set_active_tool(tool)
