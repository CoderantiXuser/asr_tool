from pynput import keyboard
import time
import threading

class HotkeyManager:
    """Handles all keyboard hotkey bindings and dispatches state change requests."""
    def __init__(self, state_manager, ui_manager):
        self.state_manager = state_manager
        self.ui_manager = ui_manager

        # Timestamps for multi-press detection
        self._last_ctrl_press = 0
        self._second_last_ctrl_press = 0
        self._last_alt_press = 0
        self._second_last_alt_press = 0
        self._last_shift_press = 0
        self._second_last_shift_press = 0
        self._last_esc_press = 0

        self._multi_press_threshold = 0.3  # seconds

        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener_thread = None

    def start(self):
        """Start the keyboard listener thread."""
        if not self._listener_thread or not self._listener_thread.is_alive():
            self._listener_thread = threading.Thread(target=self._listener.start, daemon=True)
            self._listener_thread.start()

    def stop(self):
        """Stop the keyboard listener and cleanup."""
        if self._listener and self._listener.is_alive():
            self._listener.stop()
            if self._listener_thread and self._listener_thread.is_alive():
                self._listener_thread.join(timeout=1)

    def _on_press(self, key):
        """Handle key press events and delegate to the state manager."""
        current_time = time.time()

        try:
            # --- Quit ---
            if key == keyboard.Key.esc:
                if current_time - self._last_esc_press < self._multi_press_threshold:
                    self.state_manager.request_quit()
                    self.ui_manager.show_overlay("QUITTING...", color="red", duration=2)
                self._last_esc_press = current_time

            # --- Left Ctrl: Listening (double) / Smart Mode (triple) ---
            elif key == keyboard.Key.ctrl_l:
                is_triple = (current_time - self._last_ctrl_press < self._multi_press_threshold and
                             self._last_ctrl_press - self._second_last_ctrl_press < self._multi_press_threshold)
                is_double = current_time - self._last_ctrl_press < self._multi_press_threshold

                if is_triple:
                    self.state_manager.toggle_listening()  # Revert double-press
                    is_on = self.state_manager.toggle_smart_mode()
                    self.ui_manager.show_overlay(f"SMART MODE {'ON' if is_on else 'OFF'}",
                                                 color="blue" if is_on else "gray", duration=2)
                    self._last_ctrl_press, self._second_last_ctrl_press = 0, 0
                elif is_double:
                    is_on = self.state_manager.toggle_listening()
                    self.ui_manager.show_overlay(f"LISTENING {'ON' if is_on else 'OFF'}",
                                                 color="green" if is_on else "red", duration=2)

                self._second_last_ctrl_press = self._last_ctrl_press
                self._last_ctrl_press = current_time

            # --- Right Ctrl: Command Mode ---
            elif key == keyboard.Key.ctrl_r:
                is_on = self.state_manager.toggle_command_mode()
                if is_on:
                    self.ui_manager.show_overlay("COMMAND MODE ACTIVE", color="orange")
                else:
                    self.ui_manager.hide_overlay()

            # --- Left Alt: Typing (double) / Precision Mode (triple) ---
            elif key == keyboard.Key.alt_l:
                is_triple = (current_time - self._last_alt_press < self._multi_press_threshold and
                             self._last_alt_press - self._second_last_alt_press < self._multi_press_threshold)
                is_double = current_time - self._last_alt_press < self._multi_press_threshold

                if is_triple:
                    self.state_manager.toggle_typing()  # Revert double-press
                    is_on = self.state_manager.toggle_precision_mode()
                    self.ui_manager.show_overlay(f"PRECISION MODE {'ON' if is_on else 'OFF'}",
                                                 color="purple" if is_on else "gray", duration=2)
                    self._last_alt_press, self._second_last_alt_press = 0, 0
                elif is_double:
                    is_on = self.state_manager.toggle_typing()
                    self.ui_manager.show_overlay(f"TYPING {'ON' if is_on else 'OFF'}",
                                                 color="green" if is_on else "red", duration=2)

                self._second_last_alt_press = self._last_alt_press
                self._last_alt_press = current_time

            # --- Right Alt: Quick Dictation ---
            elif key == keyboard.Key.alt_r:
                self.state_manager.activate_quick_dictation()
                self.ui_manager.show_overlay("QUICK DICTATION", color="cyan", duration=1.5)

            # --- Shift: Session Stats (triple) ---
            elif key in (keyboard.Key.shift, keyboard.Key.shift_r):
                is_triple = (current_time - self._last_shift_press < self._multi_press_threshold and
                             self._last_shift_press - self._second_last_shift_press < self._multi_press_threshold)

                if is_triple:
                    self.ui_manager.show_overlay("SESSION STATS", color="yellow", duration=3)
                    self._last_shift_press, self._second_last_shift_press = 0, 0

                self._second_last_shift_press = self._last_shift_press
                self._last_shift_press = current_time

        except AttributeError:
            pass  # Ignore special keys that don't have expected attributes
