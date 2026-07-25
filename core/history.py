class HistoryManager:
    """Maneja las pilas de Undo / Redo."""
    def __init__(self, max_states=30):
        self.max_states = max_states
        self.undo_stack = []
        self.redo_stack = []

    def push_state(self, state):
        self.undo_stack.append(state)
        if len(self.undo_stack) > self.max_states:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self, current_state):
        if not self.undo_stack:
            return None
        self.redo_stack.append(current_state)
        return self.undo_stack.pop()

    def redo(self, current_state):
        if not self.redo_stack:
            return None
        self.undo_stack.append(current_state)
        return self.redo_stack.pop()

    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()
