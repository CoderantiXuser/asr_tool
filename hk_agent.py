from pynput import keyboard
import time
import threading
from enhanced_logger import overlay

class HotkeyAgent:
    def __init__(self):
        # Core states
        self._listening_active = False
        self._typing_active = False
        self._command_mode_active = False
        self._quit_requested = False
        
        # Smart features states
        self._smart_mode_active = False
        self._precision_mode_active = False

        # Timestamps for multi-press detection
        self._last_ctrl_press = 0
        self._second_last_ctrl_press = 0
        self._last_alt_press = 0
        self._second_last_alt_press = 0
        self._last_shift_press = 0
        self._second_last_shift_press = 0
        self._last_esc_press = 0

        self._multi_press_threshold = 0.3  # seconds
        
        self._setup_listener()
    
    def _setup_listener(self):
        """Initialize and start the keyboard listener."""
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener_thread = threading.Thread(target=self._listener.start, daemon=True)
        self._listener_thread.start()
    
    def _on_press(self, key):
        """Handle key press events with multi-press logic."""
        current_time = time.time()
        
        try:
            # --- Quit ---
            if key == keyboard.Key.esc:
                if current_time - self._last_esc_press < self._multi_press_threshold:
                    self._quit_requested = True
                    overlay.show_message("QUITTING...", color="red", duration=2)
                self._last_esc_press = current_time

            # --- Left Ctrl: Listening (double) / Smart Mode (triple) ---
            elif key == keyboard.Key.ctrl_l:
                is_triple = (current_time - self._last_ctrl_press < self._multi_press_threshold and
                             self._last_ctrl_press - self._second_last_ctrl_press < self._multi_press_threshold)
                is_double = current_time - self._last_ctrl_press < self._multi_press_threshold

                if is_triple:
                    self._listening_active = not self._listening_active # Revert double-press
                    self._smart_mode_active = not self._smart_mode_active
                    status = "SMART MODE ON" if self._smart_mode_active else "SMART MODE OFF"
                    color = "blue" if self._smart_mode_active else "gray"
                    overlay.show_message(status, color=color, duration=2)
                    self._last_ctrl_press, self._second_last_ctrl_press = 0, 0 # Reset
                elif is_double:
                    self._listening_active = not self._listening_active
                    status = "LISTENING ON" if self._listening_active else "LISTENING OFF"
                    color = "green" if self._listening_active else "red"
                    overlay.show_message(status, color=color, duration=2)
                
                self._second_last_ctrl_press = self._last_ctrl_press
                self._last_ctrl_press = current_time

            # --- Right Ctrl: Command Mode ---
            elif key == keyboard.Key.ctrl_r:
                self._command_mode_active = not self._command_mode_active
                if self._command_mode_active:
                    overlay.show_message("COMMAND MODE ACTIVE", color="orange")
                else:
                    overlay.hide_message()

            # --- Left Alt: Typing (double) / Precision Mode (triple) ---
            elif key == keyboard.Key.alt_l:
                is_triple = (current_time - self._last_alt_press < self._multi_press_threshold and
                             self._last_alt_press - self._second_last_alt_press < self._multi_press_threshold)
                is_double = current_time - self._last_alt_press < self._multi_press_threshold

                if is_triple:
                    self._typing_active = not self._typing_active # Revert double-press
                    self._precision_mode_active = not self._precision_mode_active
                    status = "PRECISION MODE ON" if self._precision_mode_active else "PRECISION MODE OFF"
                    color = "purple" if self._precision_mode_active else "gray"
                    overlay.show_message(status, color=color, duration=2)
                    self._last_alt_press, self._second_last_alt_press = 0, 0 # Reset
                elif is_double:
                    self._typing_active = not self._typing_active
                    status = "TYPING ON" if self._typing_active else "TYPING OFF"
                    color = "green" if self._typing_active else "red"
                    overlay.show_message(status, color=color, duration=2)

                self._second_last_alt_press = self._last_alt_press
                self._last_alt_press = current_time

            # --- Right Alt: Quick Dictation ---
            elif key == keyboard.Key.alt_r:
                self._listening_active = True
                self._typing_active = True
                overlay.show_message("QUICK DICTATION", color="cyan", duration=1.5)

            # --- Shift: Session Stats (triple) ---
            elif key in (keyboard.Key.shift, keyboard.Key.shift_r):
                is_triple = (current_time - self._last_shift_press < self._multi_press_threshold and
                             self._last_shift_press - self._second_last_shift_press < self._multi_press_threshold)

                if is_triple:
                    overlay.show_message("SESSION STATS", color="yellow", duration=3)
                    # In a real implementation, this would trigger a call to the analytics module.
                    self._last_shift_press, self._second_last_shift_press = 0, 0 # Reset

                self._second_last_shift_press = self._last_shift_press
                self._last_shift_press = current_time
        
        except AttributeError:
            pass # Ignore special keys that don't have expected attributes
    
    # --- Public Getters for State ---
    def is_listening_active(self): return self._listening_active
    def is_typing_active(self): return self._typing_active
    def is_command_mode_active(self): return self._command_mode_active
    def is_smart_mode_active(self): return self._smart_mode_active
    def is_precision_mode_active(self): return self._precision_mode_active
    def is_quit_requested(self): return self._quit_requested
    
    # --- Public Setters for State Control ---
    def deactivate_command_mode(self):
        self._command_mode_active = False
        overlay.hide_message()

    def reset_typing_mode(self):
        self._typing_active = False

    def stop(self):
        """Stop the keyboard listener and cleanup."""
        if self._listener.is_alive():
            self._listener.stop()
            self._listener_thread.join(timeout=1)
