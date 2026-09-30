class HistoryManager:
    """Maneja el historial lineal no destructivo de modificaciones con rama activa y límite de memoria RAM."""
    def __init__(self, max_states=200, max_memory_mb=512):
        self.max_states = max_states
        self.max_memory_mb = max_memory_mb
        self.history_stack = []
        self.current_index = -1
        self.on_change = None

    def set_max_memory_mb(self, max_mb):
        """Actualiza el límite dinámico de memoria RAM en MB y purga los estados excedentes."""
        self.max_memory_mb = int(max_mb)
        self._enforce_memory_limit()

    def calculate_memory_usage_bytes(self):
        """Calcula el uso real de memoria en bytes de las imágenes únicas (CoW) en la pila de historial."""
        seen_keys = set()
        total_bytes = 0
        for state, _ in self.history_stack:
            if isinstance(state, dict) and 'layers' in state:
                for l_info in state['layers']:
                    img = l_info.get('image')
                    if img and hasattr(img, 'cacheKey') and hasattr(img, 'sizeInBytes'):
                        key = img.cacheKey()
                        if key not in seen_keys:
                            seen_keys.add(key)
                            total_bytes += img.sizeInBytes()
                pkg = state.get('floating_pkg')
                if pkg and isinstance(pkg, dict):
                    for k in ('floating_image', 'unscaled_floating_image', 'original_raw_image', 'initial_canvas'):
                        f_img = pkg.get(k)
                        if f_img and hasattr(f_img, 'cacheKey') and hasattr(f_img, 'sizeInBytes'):
                            f_key = f_img.cacheKey()
                            if f_key not in seen_keys:
                                seen_keys.add(f_key)
                                total_bytes += f_img.sizeInBytes()
            elif hasattr(state, 'cacheKey') and hasattr(state, 'sizeInBytes'):
                key = state.cacheKey()
                if key not in seen_keys:
                    seen_keys.add(key)
                    total_bytes += state.sizeInBytes()
        return total_bytes

    def calculate_memory_usage_mb(self):
        return self.calculate_memory_usage_bytes() / (1024.0 * 1024.0)

    def _enforce_memory_limit(self):
        """Purga los estados más antiguos si se excede el límite máximo de memoria RAM."""
        if self.max_memory_mb <= 0:
            return

        max_bytes = self.max_memory_mb * 1024 * 1024
        while len(self.history_stack) > 1 and self.calculate_memory_usage_bytes() > max_bytes:
            if self.current_index > 0:
                self.history_stack.pop(0)
                self.current_index -= 1
            else:
                break

    def push_state(self, state, action_name="Acción"):
        if self.current_index < len(self.history_stack) - 1:
            self.history_stack = self.history_stack[:self.current_index + 1]

        self.history_stack.append((state, action_name))
        if len(self.history_stack) > self.max_states:
            self.history_stack.pop(0)
            self.current_index -= 1

        self.current_index = len(self.history_stack) - 1
        self._enforce_memory_limit()
        self._notify()

    def undo(self, current_state=None):
        if self.current_index > 0:
            self.current_index -= 1
            self._notify()
            return self.history_stack[self.current_index][0]
        return None

    def redo(self, current_state=None):
        if self.current_index < len(self.history_stack) - 1:
            self.current_index += 1
            self._notify()
            return self.history_stack[self.current_index][0]
        return None

    def jump_to_index(self, index):
        if 0 <= index < len(self.history_stack):
            self.current_index = index
            self._notify()
            return self.history_stack[self.current_index][0]
        return None

    def clear(self):
        self.history_stack.clear()
        self.current_index = -1
        self._notify()

    def pop_last_state(self):
        """Elimina la última entrada del stack sin restaurar el buffer."""
        if self.current_index >= 0 and self.current_index == len(self.history_stack) - 1:
            self.history_stack.pop()
            self.current_index = len(self.history_stack) - 1
            self._notify()

    def _notify(self):
        if callable(self.on_change):
            self.on_change()
