"""
core/opengl_canvas.py — Widget de lienzo acelerado por hardware mediante QOpenGLWidget.
"""
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QRectF, QSettings
from PyQt6.QtGui import (
    QPainter, QImage, QPixmap, QColor, QPen, QBrush, QPainterPath, QCursor
)
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from core.canvas import CanvasWidget


class OpenGLCanvasWidget(QOpenGLWidget, CanvasWidget):
    """
    Widget de lienzo acelerado por GPU derivado de QOpenGLWidget.
    Mantiene la misma interfaz pública y funciones que CanvasWidget (software),
    pero acelera el viewport, zoom, pan y presentación mediante OpenGL.
    """

    def __init__(self, width=800, height=600, parent=None):
        QOpenGLWidget.__init__(self, parent)
        # Inicializar todos los atributos y componentes de CanvasWidget
        CanvasWidget.__init__(self, width, height, parent)

        self.content_dirty = True
        self._cached_composite_pixmap = None

    def initializeGL(self):
        """Inicializa el contexto OpenGL."""
        try:
            from core.theme import ThemeManager
            bg_col = ThemeManager().obtener_color_area_canvas()
        except Exception:
            pass

    def resizeGL(self, w, h):
        """Maneja el cambio de tamaño del viewport OpenGL."""
        pass

    def invalidate_cache(self):
        """Marca el contenido del lienzo como sucio para forzar la recomposición en el siguiente paintGL."""
        self.content_dirty = True
        self._cached_composite_pixmap = None
        if hasattr(self, 'layer_mgr') and self.layer_mgr:
            self.layer_mgr.invalidate_cache()
        self.update()

    def paintGL(self):
        """Renderizado acelerado del lienzo dentro del contexto OpenGL."""
        painter = QPainter(self)
        self.render_canvas(painter)
        painter.end()

    def paintEvent(self, event):
        """Redirige el evento de pintado al pipeline de paintGL de QOpenGLWidget."""
        super().paintEvent(event)
