import vosk
import pyaudio
import json
import threading
import queue

class AudioProcessor:
    """Handles all audio input, voice recognition, and recognizer management."""
    def __init__(self, model_path, samplerate=16000, buffer_size=8192):
        self.model = vosk.Model(model_path)
        self.samplerate = samplerate
        self.buffer_size = buffer_size

        self.recognition_queue = queue.Queue()
        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream = None

        self.default_recognizer = None
        self.command_recognizer = None
        self.dictation_recognizer = None
        self.current_recognizer = None

        self._running = False
        self._thread = None

    def create_recognizers(self, command_grammar=None, dictation_grammar=None):
        """Creates the different recognizer instances."""
        self.default_recognizer = vosk.KaldiRecognizer(self.model, self.samplerate)
        self.default_recognizer.SetWords(True)

        if command_grammar:
            self.command_recognizer = vosk.KaldiRecognizer(self.model, self.samplerate, json.dumps(command_grammar))
            self.command_recognizer.SetWords(True)

        if dictation_grammar:
            self.dictation_recognizer = vosk.KaldiRecognizer(self.model, self.samplerate, json.dumps(dictation_grammar))
            self.dictation_recognizer.SetWords(True)

        self.current_recognizer = self.default_recognizer

    def switch_recognizer(self, mode):
        """Switches the active recognizer based on the application mode."""
        if mode == 'command' and self.command_recognizer:
            self.current_recognizer = self.command_recognizer
        elif mode == 'dictation' and self.dictation_recognizer:
            self.current_recognizer = self.dictation_recognizer
        else:
            self.current_recognizer = self.default_recognizer
        self.current_recognizer.Reset()

    def start(self):
        """Starts the audio processing thread."""
        self.stream = self.pyaudio_instance.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.samplerate,
            input=True,
            frames_per_buffer=self.buffer_size
        )
        self._running = True
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stops the audio processing thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        self.pyaudio_instance.terminate()

    def _process_loop(self):
        """The main loop for reading audio and performing recognition."""
        while self._running:
            try:
                data = self.stream.read(self.buffer_size, exception_on_overflow=False)
                if self.current_recognizer.AcceptWaveform(data):
                    result = json.loads(self.current_recognizer.Result())
                    if result.get("text"):
                        self.recognition_queue.put(result)
                # Partial results could be put on a different queue here if needed
                # else:
                #     partial_result = json.loads(self.current_recognizer.PartialResult())
                #     if partial_result.get("partial"):
                #         # self.partial_queue.put(partial_result)
                #         pass
            except Exception as e:
                # In a real app, you'd want to log this error properly
                print(f"Audio processing error: {e}")
                break
