import sys
import tkinter as tk
import threading
import time
import json
import os
from datetime import datetime
from collections import deque

# ANSI color codes - Enhanced palette
COLOR_RESET = "\033[0m"
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_MAGENTA = "\033[95m"
COLOR_CYAN = "\033[96m"
COLOR_WHITE = "\033[97m"
COLOR_GRAY = "\033[90m"
COLOR_BRIGHT_RED = "\033[101m"
COLOR_BRIGHT_GREEN = "\033[102m"
COLOR_BRIGHT_YELLOW = "\033[103m"
COLOR_BRIGHT_BLUE = "\033[104m"
COLOR_BRIGHT_MAGENTA = "\033[105m"
COLOR_BRIGHT_CYAN = "\033[106m"

# Additional formatting
BOLD = "\033[1m"
DIM = "\033[2m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"

class EnhancedLogger:
    def __init__(self, log_file=None, max_history=1000):
        self.log_history = deque(maxlen=max_history)
        self.log_file = log_file or os.path.join(os.path.dirname(__file__), "voice_recognition.log")
        self.session_start = datetime.now()
        self.enable_file_logging = True
        self.enable_console_logging = True
        self.log_level_filter = ["DEBUG", "INFO", "WARNING", "ERROR"]
        
        # Performance tracking
        self.log_counts = {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0}
        self.last_partial_line = ""
        
        # Initialize log file with session header
        self._write_session_header()
    
    def _write_session_header(self):
        """Write session start header to log file."""
        if not self.enable_file_logging:
            return
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"VOICE RECOGNITION SESSION STARTED: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*80}\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")
    
    def _get_level_color(self, level):
        """Get color for log level."""
        level_colors = {
            "DEBUG": COLOR_GRAY,
            "INFO": COLOR_CYAN,
            "WARNING": COLOR_YELLOW,
            "ERROR": COLOR_RED,
            "SUCCESS": COLOR_GREEN,
            "CRITICAL": COLOR_BRIGHT_RED
        }
        return level_colors.get(level.upper(), COLOR_WHITE)
    
    def _format_console_message(self, message, level="INFO", typing_active=None, listening_active=None, 
                               command_active=None, smart_active=None, precision_active=None):
        """Format message for console output."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
        
        # Build state indicators
        state_indicators = []
        
        if listening_active is not None:
            l_status = "L" if listening_active else "l"
            l_color = COLOR_BRIGHT_GREEN if listening_active else COLOR_RED
            state_indicators.append(f"{l_color}{l_status}{COLOR_RESET}")
        
        if typing_active is not None:
            t_status = "T" if typing_active else "t"
            t_color = COLOR_BRIGHT_GREEN if typing_active else COLOR_RED
            state_indicators.append(f"{t_color}{t_status}{COLOR_RESET}")
        
        if command_active is not None:
            c_status = "C" if command_active else "c"
            c_color = COLOR_BRIGHT_YELLOW if command_active else COLOR_GRAY
            state_indicators.append(f"{c_color}{c_status}{COLOR_RESET}")
        
        if smart_active is not None:
            s_status = "S" if smart_active else "s"
            s_color = COLOR_BRIGHT_CYAN if smart_active else COLOR_GRAY
            state_indicators.append(f"{s_color}{s_status}{COLOR_RESET}")
        
        if precision_active is not None:
            p_status = "P" if precision_active else "p"
            p_color = COLOR_BRIGHT_MAGENTA if precision_active else COLOR_GRAY
            state_indicators.append(f"{p_color}{p_status}{COLOR_RESET}")
        
        state_info = f"[{'/'.join(state_indicators)}] " if state_indicators else ""
        
        # Level formatting
        level_color = self._get_level_color(level)
        level_formatted = f"{level_color}{BOLD}{level.ljust(7)}{COLOR_RESET}"
        
        # Message formatting based on content
        if "EXECUTED" in message.upper():
            message = f"{COLOR_GREEN}{message}{COLOR_RESET}"
        elif "FAILED" in message.upper() or "ERROR" in message.upper():
            message = f"{COLOR_RED}{message}{COLOR_RESET}"
        elif "Recognized:" in message:
            message = f"{COLOR_CYAN}{message}{COLOR_RESET}"
        elif "DICTATION" in message:
            message = f"{COLOR_BLUE}{message}{COLOR_RESET}"
        
        return f"[{COLOR_GRAY}{timestamp}{COLOR_RESET}] {state_info}{level_formatted} {message}"
    
    def _format_file_message(self, message, level="INFO", typing_active=None, listening_active=None,
                           command_active=None, smart_active=None, precision_active=None):
        """Format message for file output."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Build state info
        states = []
        if listening_active is not None:
            states.append(f"L:{'ON' if listening_active else 'OFF'}")
        if typing_active is not None:
            states.append(f"T:{'ON' if typing_active else 'OFF'}")
        if command_active is not None:
            states.append(f"C:{'ON' if command_active else 'OFF'}")
        if smart_active is not None:
            states.append(f"S:{'ON' if smart_active else 'OFF'}")
        if precision_active is not None:
            states.append(f"P:{'ON' if precision_active else 'OFF'}")
        
        state_info = f" [{'/'.join(states)}]" if states else ""
        
        return f"[{timestamp}]{state_info} [{level.ljust(7)}] {message}"

def log_message(message, level="INFO", typing_active=None, listening_active=None, 
               command_active=None, smart_active=None, precision_active=None):
    """Enhanced log message function with rich formatting."""
    
    # Use global logger instance or create one
    if not hasattr(log_message, 'logger'):
        log_message.logger = EnhancedLogger()
    
    logger = log_message.logger
    
    # Filter by log level if needed
    if level.upper() not in logger.log_level_filter:
        return
    
    # Update log counts
    if level.upper() in logger.log_counts:
        logger.log_counts[level.upper()] += 1
    
    # Add to history
    log_entry = {
        'timestamp': datetime.now(),
        'level': level,
        'message': message,
        'states': {
            'typing_active': typing_active,
            'listening_active': listening_active,
            'command_active': command_active,
            'smart_active': smart_active,
            'precision_active': precision_active
        }
    }
    logger.log_history.append(log_entry)
    
    # Console output
    if logger.enable_console_logging:
        formatted_message = logger._format_console_message(
            message, level, typing_active, listening_active, 
            command_active, smart_active, precision_active
        )
        print(formatted_message)
    
    # File output
    if logger.enable_file_logging:
        try:
            file_message = logger._format_file_message(
                message, level, typing_active, listening_active,
                command_active, smart_active, precision_active
            )
            with open(logger.log_file, 'a', encoding='utf-8') as f:
                f.write(file_message + '\n')
        except Exception as e:
            print(f"Error writing to log file: {e}")

def display_partial(text, typing_active=None, listening_active=None, 
                   command_active=None, smart_active=None, precision_active=None):
    """Enhanced partial display with rich formatting."""
    if not hasattr(display_partial, 'logger'):
        display_partial.logger = EnhancedLogger()
    
    logger = display_partial.logger
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Build state indicators (same as log_message)
    state_indicators = []
    
    if listening_active is not None:
        l_status = "L" if listening_active else "l"
        l_color = COLOR_BRIGHT_GREEN if listening_active else COLOR_RED
        state_indicators.append(f"{l_color}{l_status}{COLOR_RESET}")
    
    if typing_active is not None:
        t_status = "T" if typing_active else "t"
        t_color = COLOR_BRIGHT_GREEN if typing_active else COLOR_RED
        state_indicators.append(f"{t_color}{t_status}{COLOR_RESET}")
    
    if command_active is not None:
        c_status = "C" if command_active else "c"
        c_color = COLOR_BRIGHT_YELLOW if command_active else COLOR_GRAY
        state_indicators.append(f"{c_color}{c_status}{COLOR_RESET}")
    
    state_info = f"[{'/'.join(state_indicators)}] " if state_indicators else ""
    
    # Format partial text with color
    partial_colored = f"{COLOR_MAGENTA}{DIM}{text}{COLOR_RESET}"
    
    display_text = f"[{COLOR_GRAY}{timestamp}{COLOR_RESET}] {state_info}{COLOR_YELLOW}Partial:{COLOR_RESET} {partial_colored}"
    
    # Clear previous line and display new one
    sys.stdout.write(f"\r{' ' * 120}\r{display_text}")
    sys.stdout.flush()
    
    logger.last_partial_line = display_text

def clear_partial():
    """Clear the partial display line with enhanced clearing."""
    sys.stdout.write(f"\r{' ' * 120}\r")
    sys.stdout.flush()

class NotificationOverlay:
    def __init__(self):
        self.root = None
        self.label = None
        self.thread = None
        self.message_queue = []
        self.queue_lock = threading.Lock()
        self.running = False
        self.current_message = ""
        self.position = "top_center"  # top_center, top_left, top_right, bottom_center, etc.
        self.style_theme = "dark"  # dark, light, colorful
        
        # Enhanced styling options
        self.themes = {
            "dark": {
                "bg": "#1e1e1e",
                "fg": "#ffffff",
                "font": ("Segoe UI", 18, "bold"),
                "alpha": 0.9
            },
            "light": {
                "bg": "#f0f0f0",
                "fg": "#000000",
                "font": ("Segoe UI", 18, "bold"),
                "alpha": 0.9
            },
            "colorful": {
                "bg": "#2d2d30",
                "fg": "#ffffff",
                "font": ("Arial", 20, "bold"),
                "alpha": 0.95
            }
        }
    
    def _run_tk(self):
        """Run the tkinter main loop with enhanced styling."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-toolwindow', True)  # Prevent focus stealing
        
        # Get current theme
        theme = self.themes.get(self.style_theme, self.themes["dark"])
        self.root.attributes('-alpha', theme["alpha"])
        
        # Create label with enhanced styling
        self.label = tk.Label(
            self.root,
            text="",
            font=theme["font"],
            fg=theme["fg"],
            bg=theme["bg"],
            padx=25,
            pady=15,
            relief="flat",
            borderwidth=2
        )
        self.label.pack()
        
        self._position_window()
        self.root.deiconify()
        self.running = True
        
        # Start processing message queue
        self._process_queue()
        self.root.mainloop()
    
    def _position_window(self):
        """Position window based on position setting."""
        self.root.update_idletasks()
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        positions = {
            "top_center": (screen_width // 2 - window_width // 2, 50),
            "top_left": (50, 50),
            "top_right": (screen_width - window_width - 50, 50),
            "bottom_center": (screen_width // 2 - window_width // 2, screen_height - window_height - 100),
            "center": (screen_width // 2 - window_width // 2, screen_height // 2 - window_height // 2)
        }
        
        x, y = positions.get(self.position, positions["top_center"])
        self.root.geometry(f"+{x}+{y}")
    
    def _process_queue(self):
        """Enhanced message queue processing."""
        if not self.running:
            return
        
        with self.queue_lock:
            if self.message_queue:
                message_info = self.message_queue.pop(0)
                message = message_info["message"]
                color = message_info.get("color", "white")
                duration = message_info.get("duration", 0)
                style = message_info.get("style", "normal")
                
                self._update_label(message, color, style)
                
                if duration > 0:
                    self.root.after(int(duration * 1000), self._clear_after_delay)
        
        self.root.after(100, self._process_queue)
    
    def _update_label(self, message, color, style="normal"):
        """Enhanced label update with styling options."""
        if self.label and self.running:
            self.current_message = message
            
            # Color mapping for better visibility
            color_map = {
                "white": "#ffffff",
                "green": "#00ff00",
                "red": "#ff4444",
                "yellow": "#ffff00",
                "orange": "#ff8800",
                "blue": "#4488ff",
                "cyan": "#00ffff",
                "lime": "#88ff00",
                "purple": "#ff00ff",
                "gray": "#888888"
            }
            
            fg_color = color_map.get(color.lower(), color)
            
            # Style modifications
            current_theme = self.themes[self.style_theme]
            font = current_theme["font"]
            
            if style == "bold":
                font = (font[0], font[1], "bold")
            elif style == "italic":
                font = (font[0], font[1], "italic")
            
            self.label.config(text=message, fg=fg_color, font=font)
            
            # Add border for important messages
            if color.lower() in ["red", "yellow", "orange"]:
                self.label.config(relief="solid", borderwidth=2, highlightbackground=fg_color)
            else:
                self.label.config(relief="flat", borderwidth=0)
            
            self._position_window()
    
    def _clear_after_delay(self):
        """Clear label after delay with fade effect simulation."""
        if self.label and self.running:
            with self.queue_lock:
                if not self.message_queue:
                    # Simple fade effect by changing alpha
                    try:
                        current_alpha = self.root.attributes('-alpha')
                        for alpha in [current_alpha * 0.7, current_alpha * 0.4, 0.0]:
                            self.root.attributes('-alpha', alpha)
                            time.sleep(0.1)
                        
                        self.label.config(text="")
                        self.current_message = ""
                        
                        # Restore alpha
                        theme = self.themes[self.style_theme]
                        self.root.attributes('-alpha', theme["alpha"])
                    except:
                        # Fallback to simple clear
                        self.label.config(text="")
                        self.current_message = ""
    
    def start(self):
        """Start the overlay."""
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._run_tk, daemon=True)
            self.thread.start()
            time.sleep(0.2)  # Give more time for initialization
    
    def stop(self):
        """Stop the overlay."""
        self.running = False
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
    
    def show_message(self, message, color="white", duration=0, style="normal", position=None):
        """Show message with enhanced options."""
        if not self.running:
            return
        
        if position:
            self.position = position
        
        message_info = {
            "message": message,
            "color": color,
            "duration": duration,
            "style": style
        }
        
        with self.queue_lock:
            if duration == 0:
                self.message_queue.clear()
            self.message_queue.append(message_info)
    
    def hide_message(self):
        """Hide current message."""
        self.show_message("", duration=0)
    
    def set_theme(self, theme_name):
        """Change the overlay theme."""
        if theme_name in self.themes:
            self.style_theme = theme_name
    
    def set_position(self, position):
        """Change overlay position."""
        valid_positions = ["top_center", "top_left", "top_right", "bottom_center", "center"]
        if position in valid_positions:
            self.position = position

# Global enhanced overlay instance
overlay = NotificationOverlay()