import json
import os
import time
import argparse
import re
import queue

from state_manager import StateManager
from ui_manager import UIManager
from hotkey_manager import HotkeyManager
from audio_processor import AudioProcessor
from exec_agent import ExecutionAgent
from text_formatter import TextFormatter
from confidence_tracker import ConfidenceTracker
from context_manager import ContextManager

class App:
    """The main application class that orchestrates all components."""
    def __init__(self):
        self.state = StateManager()
        self.ui = UIManager()
        self.hotkeys = HotkeyManager(self.state, self.ui)
        self.executor = ExecutionAgent()
        self.formatter = TextFormatter()
        self.confidence_tracker = ConfidenceTracker()
        self.context_manager = ContextManager()

        self._load_config()

        self.audio_processor = AudioProcessor(self.model_path)
        self.audio_processor.create_recognizers(list(self.commands.keys()), list(self.dict_commands.keys()))

    def _load_config(self):
        """Loads configurations, commands, and selects the ASR model."""
        parser = argparse.ArgumentParser(description="A modular, enhanced voice recognition system.")
        parser.add_argument("-m", "--model-path", type=str, default="/usr/share/piper-tts-vosk-asr-models/vosk-models/vosk-model-small-en-us-0.15",
                            help="Path to the Vosk ASR model.")
        parser.add_argument("-c", "--confidence", type=float, default=0.7,
                            help="Minimum confidence threshold for recognition.")
        args = parser.parse_args()

        self.model_path = args.model_path
        self.min_confidence = args.confidence
        self.confidence_tracker.set_threshold(self.min_confidence)

        if not os.path.exists(self.model_path):
            self.ui.log(f"Model path not found: {self.model_path}", "ERROR")
            exit(1)

        cmd_path = os.path.join(os.path.dirname(__file__), "cmd.json")
        dict_cmd_path = os.path.join(os.path.dirname(__file__), "dict_cmds_config.json")
        self.commands = self._load_json(cmd_path)
        self.dict_commands = self._load_json(dict_cmd_path)

    def _load_json(self, file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.ui.log(f"Error loading {os.path.basename(file_path)}: {e}", "ERROR")
            return {}

    def run(self):
        """Starts all components and enters the main application loop."""
        self.ui.start()
        self.hotkeys.start()
        self.audio_processor.start()
        self.ui.log("Application initialized. Waiting for hotkey...", "SUCCESS", self.state)

        try:
            while not self.state.is_quit_requested():
                self._handle_state_changes()

                try:
                    result = self.audio_processor.recognition_queue.get_nowait()
                    self._handle_recognition(result)
                except queue.Empty:
                    time.sleep(0.1)

        except KeyboardInterrupt:
            self.ui.log("Caught KeyboardInterrupt. Shutting down...", "WARNING")
        finally:
            self.shutdown()

    def _handle_state_changes(self):
        """Checks for state changes and updates components accordingly."""
        mode = 'default'
        if self.state.is_command_mode():
            mode = 'command'
        elif self.state.is_typing():
            mode = 'dictation'

        self.audio_processor.switch_recognizer(mode)

    def _handle_recognition(self, result):
        """Handles a recognition result from the audio processor."""
        text = result.get("text", "")
        if not self.state.is_listening() or not text:
            return

        self.ui.log(f"Recognized: '{text}'", "INFO", self.state)
        self.confidence_tracker.add_recognition(result.get("confidence", 0.0))
        self.context_manager.add_text(text)

        if self.state.is_command_mode():
            self._process_command(text)
        elif self.state.is_typing():
            self._process_dictation(text)

    def _process_command(self, text):
        """Processes text in command mode using robust regex matching."""
        sorted_phrases = sorted(self.commands.keys(), key=len, reverse=True)
        for phrase in sorted_phrases:
            pattern = r'\b' + re.escape(phrase) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                self.ui.show_overlay(f"EXECUTED: {phrase}", color="green", duration=1.5)
                for action in self.commands[phrase]:
                    self.executor.execute_command_action(action.get("type"), action.get("value"))
                self.state.deactivate_command_mode()
                return
        self.ui.show_overlay(f"UNKNOWN CMD: {text}", color="red", duration=1.5)
        self.state.deactivate_command_mode()

    def _process_dictation(self, text):
        """Processes text in dictation mode."""
        processed_text = text
        command_executed = False

        sorted_phrases = sorted(self.dict_commands.keys(), key=len, reverse=True)
        for phrase in sorted_phrases:
            pattern = r'\b' + re.escape(phrase) + r'\b'
            if re.search(pattern, processed_text, re.IGNORECASE):
                command_executed = True
                for action in self.dict_commands[phrase]:
                    self.executor.execute_command_action(action.get("type"), action.get("value"))
                processed_text = re.sub(pattern, '', processed_text, flags=re.IGNORECASE)

        processed_text = re.sub(r'\s\s+', ' ', processed_text).strip()
        if processed_text:
            formatted_text = self.formatter.format_text(processed_text)
            self.executor.keyboard_controller.type(formatted_text + " ")
            self.ui.log(f"[DICTATION] {formatted_text}", "INFO", self.state)

        if command_executed:
            self.ui.show_overlay(f"DICTATION CMD: {text}", color="blue", duration=1.5)

    def shutdown(self):
        """Gracefully shuts down all application components."""
        self.ui.log("Shutting down all components...", "INFO")
        self.audio_processor.stop()
        self.hotkeys.stop()
        self.ui.stop()
        self.ui.log("Application terminated.", "SUCCESS")

if __name__ == "__main__":
    app = App()
    app.run()