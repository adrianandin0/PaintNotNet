class SelectionEngine:
    """Maneja el área seleccionada y sus transformaciones."""
    def __init__(self):
        self.active_rect = None
        self.floating_image = None
        self.rotation_angle = 0.0
        self.is_transforming = False

    def has_selection(self):
        return self.active_rect is not None and not self.active_rect.isEmpty()

    def set_selection(self, rect):
        self.active_rect = rect

    def clear_selection(self):
        self.active_rect = None
        self.floating_image = None
        self.rotation_angle = 0.0
        self.is_transforming = False
