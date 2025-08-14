import sys
import tkinter as tk
import threading
import time
import os
from datetime import datetime
from collections import deque

# ANSI color codes
COLOR_RESET = "\033[0m"
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_MAGENTA = "\033[95m"
COLOR_CYAN = "\033[96m"
COLOR_GRAY = "\033[90m"
BOLD = "\033[1m"
DIM = "\033[2m"

class NotificationOverlay:
    """A tkinter-based overlay window for showing notifications."""
    def __init__(self):
        self.root = None
        self.label = None
        self.thread = None
        self.message_queue = deque()
        self.queue_lock = threading.Lock()
        self.running = False
        self.themes = {
            "dark": {"bg": "#1e1e1e", "fg": "#ffffff", "font": ("Segoe UI", 18, "bold"), "alpha": 0.9},
            "light": {"bg": "#f0f0f0", "fg": "#000000", "font": ("Segoe UI", 18, "bold"), "alpha": 0.9}
        }
        self.style_theme = "dark"
        self.position = "top_center"

    def _run_tk(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-toolwindow', True)

        theme = self.themes.get(self.style_theme, self.themes["dark"])
        self.root.attributes('-alpha', theme["alpha"])

        self.label = tk.Label(self.root, text="", font=theme["font"], fg=theme["fg"], bg=theme["bg"], padx=25, pady=15)
        self.label.pack()

        self._position_window()
        self.root.deiconify()
        self.running = True
        self._process_queue()
        self.root.mainloop()

    def _position_window(self):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        positions = {
            "top_center": (screen_width // 2 - window_width // 2, 50),
            "bottom_center": (screen_width // 2 - window_width // 2, screen_height - window_height - 100),
        }
        x, y = positions.get(self.position, positions["top_center"])
        self.root.geometry(f"+{int(x)}+{int(y)}")

    def _process_queue(self):
        if not self.running: return
        with self.queue_lock:
            if self.message_queue:
                message, color, duration = self.message_queue.popleft()
                self._update_label(message, color)
                if duration > 0: self.root.after(int(duration * 1000), self._clear_label)
        self.root.after(100, self._process_queue)

    def _update_label(self, message, color):
        if self.label and self.running:
            color_map = {"green": "#00ff00", "red": "#ff4444", "orange": "#ff8800", "blue": "#4488ff", "cyan": "#00ffff", "purple": "#ff00ff", "gray": "#888888"}
            fg_color = color_map.get(color.lower(), "#ffffff")
            self.label.config(text=message, fg=fg_color)
            self._position_window()

    def _clear_label(self):
        self._update_label("", "white")

    def start(self):
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._run_tk, daemon=True)
            self.thread.start()
            time.sleep(0.2)

    def stop(self):
        self.running = False
        if self.root:
            try: self.root.quit()
            except: pass
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)

    def show_message(self, message, color="white", duration=2):
        if not self.running: self.start()
        with self.queue_lock:
            self.message_queue.append((message, color, duration))

    def hide_message(self):
        with self.queue_lock:
            self.message_queue.clear()
            self.root.after(0, self._clear_label)

class UIManager:
    """Manages all user interface components, including console logging and overlays."""
    def __init__(self, log_file_path="voice_recognition.log"):
        self.log_history = deque(maxlen=1000)
        self.log_file = log_file_path
        self._write_session_header()
        self.overlay = NotificationOverlay()

    def start(self):
        self.overlay.start()

    def stop(self):
        self.overlay.stop()

    def _write_session_header(self):
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\nSESSION STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*80}\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")

    def _get_level_color(self, level):
        return {"INFO": COLOR_CYAN, "WARNING": COLOR_YELLOW, "ERROR": COLOR_RED, "SUCCESS": COLOR_GREEN}.get(level.upper(), COLOR_GRAY)

    def log(self, message, level="INFO", state=None):
        """Logs a message to the console and a file."""
        console_msg = self._format_console_message(message, level, state)
        print(console_msg)

        try:
            file_msg = self._format_file_message(message, level, state)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(file_msg + '\n')
        except Exception as e:
            print(f"Error writing to log file: {e}")

    def _format_console_message(self, message, level, state):
        timestamp = f"{COLOR_GRAY}{datetime.now().strftime('%H:%M:%S')}{COLOR_RESET}"
        level_color = self._get_level_color(level)
        level_formatted = f"{level_color}{BOLD}{level.ljust(7)}{COLOR_RESET}"

        state_str = ""
        if state:
            l = f"{COLOR_GREEN}L{COLOR_RESET}" if state.is_listening() else f"{COLOR_RED}l{COLOR_RESET}"
            t = f"{COLOR_GREEN}T{COLOR_RESET}" if state.is_typing() else f"{COLOR_RED}t{COLOR_RESET}"
            c = f"{COLOR_YELLOW}C{COLOR_RESET}" if state.is_command_mode() else f"{COLOR_GRAY}c{COLOR_RESET}"
            state_str = f"[{l}/{t}/{c}]"

        return f"[{timestamp}] {state_str} {level_formatted} {message}"

    def _format_file_message(self, message, level, state):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        state_str = ""
        if state:
            l = "ON" if state.is_listening() else "OFF"
            t = "ON" if state.is_typing() else "OFF"
            c = "ON" if state.is_command_mode() else "OFF"
            state_str = f" [L:{l}/T:{t}/C:{c}]"
        return f"[{timestamp}]{state_str} [{level.ljust(7)}] {message}"

    def display_partial(self, text):
        """Displays partial recognition results on the console."""
        timestamp = f"{COLOR_GRAY}{datetime.now().strftime('%H:%M:%S')}{COLOR_RESET}"
        partial_colored = f"{COLOR_MAGENTA}{DIM}{text}{COLOR_RESET}"
        display_text = f"[{timestamp}] {COLOR_YELLOW}Partial:{COLOR_RESET} {partial_colored}"
        sys.stdout.write(f"\r{' ' * 120}\r{display_text}")
        sys.stdout.flush()

    def clear_partial(self):
        """Clears the partial display line."""
        sys.stdout.write(f"\r{' ' * 120}\r")
        sys.stdout.flush()

    def show_overlay(self, message, color="white", duration=2):
        self.overlay.show_message(message, color, duration)

    def hide_overlay(self):
        self.overlay.hide_message()
