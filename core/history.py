class HistoryManager:
    """Maneja el historial lineal no destructivo de modificaciones con rama activa."""
    def __init__(self, max_states=50):
        self.max_states = max_states
        self.history_stack = []
        self.current_index = -1
        self.on_change = None

    def push_state(self, state, action_name="Acción"):
        if self.current_index < len(self.history_stack) - 1:
            self.history_stack = self.history_stack[:self.current_index + 1]

        self.history_stack.append((state, action_name))
        if len(self.history_stack) > self.max_states:
            self.history_stack.pop(0)

        self.current_index = len(self.history_stack) - 1
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
        """Elimina la última entrada del stack sin restaurar el buffer.
        Usar cuando se cancela una operación que ya restauró el buffer manualmente.
        Esto evita que undo() retroceda un paso extra al estado anterior a la op."""
        if self.current_index >= 0 and self.current_index == len(self.history_stack) - 1:
            self.history_stack.pop()
            self.current_index = len(self.history_stack) - 1
            self._notify()

    def _notify(self):
        if callable(self.on_change):
            self.on_change()
