class StateManager:
    """A centralized class to manage the application's state."""
    def __init__(self):
        self._listening_active = False
        self._typing_active = False
        self._command_mode_active = False
        self._quit_requested = False
        self._smart_mode_active = False
        self._precision_mode_active = False

    # --- Getters ---
    def is_listening(self):
        return self._listening_active

    def is_typing(self):
        return self._typing_active

    def is_command_mode(self):
        return self._command_mode_active

    def is_quit_requested(self):
        return self._quit_requested

    def is_smart_mode(self):
        return self._smart_mode_active

    def is_precision_mode(self):
        return self._precision_mode_active

    # --- Mutators ---
    def toggle_listening(self):
        self._listening_active = not self._listening_active
        return self._listening_active

    def toggle_typing(self):
        self._typing_active = not self._typing_active
        return self._typing_active

    def toggle_command_mode(self):
        self._command_mode_active = not self._command_mode_active
        return self._command_mode_active

    def toggle_smart_mode(self):
        self._smart_mode_active = not self._smart_mode_active
        return self._smart_mode_active

    def toggle_precision_mode(self):
        self._precision_mode_active = not self._precision_mode_active
        return self._precision_mode_active

    def activate_quick_dictation(self):
        self._listening_active = True
        self._typing_active = True

    def deactivate_command_mode(self):
        self._command_mode_active = False

    def request_quit(self):
        self._quit_requested = True
