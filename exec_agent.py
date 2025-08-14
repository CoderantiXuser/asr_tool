import subprocess
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController, Button
from enhanced_logger import log_message

class ExecutionAgent:
    def __init__(self):
        self.keyboard_controller = KeyboardController()
        self.mouse_controller = MouseController()

    def _press_and_release(self, key):
        self.keyboard_controller.press(key)
        self.keyboard_controller.release(key)

    def _combo(self, keys):
        with self.keyboard_controller.pressed(*keys):
            pass

    def execute_command_action(self, action_type, value):
        """Execute a single command action."""
        log_message(f"Executing action: {action_type} - {value}", level="INFO")

        if action_type == "key_press":
            try:
                key = getattr(Key, value.lower())
                self._press_and_release(key)
            except AttributeError:
                self._press_and_release(value)

        elif action_type == "key_combo":
            keys_to_press = []
            for k_str in value.split('+'):
                k_str = k_str.strip()
                try:
                    keys_to_press.append(getattr(Key, k_str.lower()))
                except AttributeError:
                    keys_to_press.append(k_str)
            self._combo(keys_to_press)

        elif action_type == "launch_application":
            try:
                subprocess.Popen([value], start_new_session=True)
            except FileNotFoundError:
                log_message(f"Application not found: {value}", level="ERROR")
            except Exception as e:
                log_message(f"Failed to launch application: {e}", level="ERROR")

        elif action_type == "execute_shell":
            try:
                subprocess.Popen(value, shell=True)
            except Exception as e:
                log_message(f"Shell command error: {e}", level="ERROR")

        elif action_type == "mouse_click":
            button = Button.left
            count = 1
            if isinstance(value, dict):
                button_str = value.get("button", "left")
                count = value.get("count", 1)
                if button_str == "right":
                    button = Button.right
                elif button_str == "middle":
                    button = Button.middle
            elif isinstance(value, str):
                if value == "right":
                    button = Button.right
                elif value == "middle":
                    button = Button.middle

            self.mouse_controller.click(button, count)

        elif action_type == "scroll":
            scroll_dy = 1 if value == "down" else -1
            self.mouse_controller.scroll(0, scroll_dy)

        elif action_type == "clipboard_action":
            if value == "copy":
                self._combo([Key.ctrl, 'c'])
            elif value == "paste":
                self._combo([Key.ctrl, 'v'])
            elif value == "cut":
                self._combo([Key.ctrl, 'x'])

        elif action_type == "window_action":
            if value == "close":
                self._combo([Key.alt, Key.f4])
            elif value == "minimize":
                self._combo([Key.cmd, Key.down])
            elif value == "maximize":
                self._combo([Key.cmd, Key.up])
            elif value == "switch":
                self._combo([Key.alt, Key.tab])

        elif action_type == "system_action":
            if value == "screenshot":
                self._combo([Key.cmd, Key.shift, 's'])
            elif value == "lock_screen":
                self._combo([Key.cmd, 'l'])

        elif action_type == "text_manipulation":
            actions = {
                "undo": ([Key.ctrl, 'z']),
                "select_word": lambda: self.mouse_controller.click(Button.left, 2),
                "delete_word": ([Key.ctrl, Key.backspace]),
                "delete_line": ([Key.home, Key.shift, Key.end, Key.delete]),
                "select_all": ([Key.ctrl, 'a']),
                "new_line": ([Key.enter]),
                "indent": ([Key.tab]),
                "unindent": ([Key.shift, Key.tab]),
                "find": ([Key.ctrl, 'f']),
                "replace": ([Key.ctrl, 'h']),
                "select_line": ([Key.home, Key.shift, Key.end])
            }
            action = actions.get(value)
            if callable(action):
                action()
            elif isinstance(action, list):
                self._combo(action)
            else:
                log_message(f"Unknown text manipulation value: {value}", level="WARNING")

        else:
            log_message(f"Unknown action type: {action_type}", level="WARNING")
