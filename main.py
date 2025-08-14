import vosk
import pyaudio
import json
import os
import time
import subprocess
import argparse
import re
from pynput.keyboard import Key
from hk_agent import HotkeyAgent
from enhanced_logger import log_message, display_partial, clear_partial, overlay
from exec_agent import ExecutionAgent
from text_formatter import TextFormatter
from confidence_tracker import ConfidenceTracker
from context_manager import ContextManager

# Configuration Constants
MODEL_BASE_PATH = "/usr/share/piper-tts-vosk-asr-models/vosk-models/"
DEFAULT_MODEL = "vosk-model-small-en-us-0.15"
SAMPLERATE = 16000
BUFFER_SIZE = 8192
MIN_CONFIDENCE_THRESHOLD = 0.6

def load_commands(file_path):
    """Load commands from json file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        log_message(f"Error: {os.path.basename(file_path)} not found at {file_path}", level="ERROR")
        return {}
    except json.JSONDecodeError:
        log_message(f"Error: Invalid JSON in {file_path}", level="ERROR")
        return {}

def process_command(text, commands, exec_agent):
    """Process recognized text for commands."""
    for phrase, actions in commands.items():
        if phrase.lower() in text.lower():
            log_message(f"Executing command: {phrase}")
            for action in actions:
                if isinstance(action, dict) and "type" in action and "value" in action:
                    exec_agent.execute_command_action(action["type"], action["value"])
                else:
                    log_message(f"Invalid command action format: {action}", level="ERROR")
            return True
    return False

def process_dictation_command(text, dict_commands, exec_agent, text_formatter):
    """Process dictation-specific commands using robust regex matching and return cleaned text."""
    executed_command = False
    processed_text = text

    # Sort commands by length, longest first, to avoid partial matches (e.g., "delete that" before "delete")
    sorted_phrases = sorted(dict_commands.keys(), key=len, reverse=True)

    for phrase in sorted_phrases:
        # Use regex to find the command phrase as a whole word/phrase
        pattern = r'\b' + re.escape(phrase) + r'\b'

        # Check if the pattern exists in the processed text
        if re.search(pattern, processed_text, re.IGNORECASE):
            log_message(f"Executing dictation command: {phrase}")
            executed_command = True
            actions = dict_commands[phrase]

            for action in actions:
                if isinstance(action, dict) and "type" in action and "value" in action:
                    exec_agent.execute_command_action(action["type"], action["value"])
                else:
                    log_message(f"Invalid dictation command action format: {action}", level="ERROR")
            
            # Remove the command phrase from the text using regex
            processed_text = re.sub(pattern, '', processed_text, flags=re.IGNORECASE)

    # Clean up any extra whitespace left after removing commands
    processed_text = re.sub(r'\s\s+', ' ', processed_text).strip()

    # Format the remaining text if any is left
    if processed_text:
        processed_text = text_formatter.format_text(processed_text)
    
    return processed_text, executed_command

def select_model():
    """Handle model selection via command line argument."""
    parser = argparse.ArgumentParser(description="Enhanced real-time voice transcriber with Vosk ASR.")
    parser.add_argument("-M", "--models-list", action="store_true", 
                       help="List available Vosk models and choose one.")
    parser.add_argument("-c", "--confidence", type=float, default=MIN_CONFIDENCE_THRESHOLD,
                       help=f"Set minimum confidence threshold (default: {MIN_CONFIDENCE_THRESHOLD})")
    args = parser.parse_args()
    
    model_path = os.path.join(MODEL_BASE_PATH, DEFAULT_MODEL)
    
    if args.models_list:
        available_models = [d for d in os.listdir(MODEL_BASE_PATH) 
                          if os.path.isdir(os.path.join(MODEL_BASE_PATH, d))]
        if not available_models:
            log_message(f"No Vosk models found in {MODEL_BASE_PATH}", level="ERROR")
            exit(1)

        log_message("Available Vosk models:")
        for i, model_name in enumerate(available_models):
            log_message(f"{i+1}. {model_name}")

        while True:
            try:
                choice = input("Enter the number of the model to load (or press Enter for default): ")
                if not choice:
                    log_message(f"Loading default model: {DEFAULT_MODEL}")
                    break
                choice_index = int(choice) - 1
                if 0 <= choice_index < len(available_models):
                    model_path = os.path.join(MODEL_BASE_PATH, available_models[choice_index])
                    log_message(f"Loading selected model: {available_models[choice_index]}")
                    break
                else:
                    log_message("Invalid choice. Please enter a valid number.", level="ERROR")
            except ValueError:
                log_message("Invalid input. Please enter a number.", level="ERROR")
    
    return model_path, args.confidence

def create_enhanced_recognizer(model, samplerate, grammar_list=None):
    """Create an enhanced recognizer with better configuration."""
    if grammar_list:
        # Create recognizer with grammar and enable partial results
        recognizer = vosk.KaldiRecognizer(model, samplerate, json.dumps(grammar_list))
    else:
        recognizer = vosk.KaldiRecognizer(model, samplerate)
    
    # Configure recognizer for better performance
    recognizer.SetWords(True)
    return recognizer

def main():
    # Initialize components
    exec_agent = ExecutionAgent()
    text_formatter = TextFormatter()
    confidence_tracker = ConfidenceTracker()
    context_manager = ContextManager()
    
    # Load commands
    cmd_path = os.path.join(os.path.dirname(__file__), "cmd.json")
    dict_cmd_path = os.path.join(os.path.dirname(__file__), "dict_cmds_config.json")
    
    commands = load_commands(cmd_path)
    dict_commands = load_commands(dict_cmd_path)
    
    # Select model and get confidence threshold
    model_path, min_confidence = select_model()
    confidence_tracker.set_threshold(min_confidence)
    
    # Ensure model path exists
    if not os.path.exists(model_path):
        log_message(f"Error: Vosk model not found at {model_path}", level="ERROR")
        log_message("Please download a Vosk model and extract it to the specified path.", level="ERROR")
        log_message("For example: https://alphacephei.com/vosk/models", level="ERROR")
        exit(1)

    # Load Vosk model and create recognizers
    base_model = vosk.Model(model_path)
    
    # Generate grammars
    command_grammar = list(commands.keys())
    dictation_grammar = list(dict_commands.keys())
    
    log_message(f"Command grammar: {command_grammar}")
    log_message(f"Dictation grammar: {dictation_grammar}")
    
    # Create recognizer instances with enhanced configuration
    default_recognizer = create_enhanced_recognizer(base_model, SAMPLERATE)
    command_recognizer = create_enhanced_recognizer(base_model, SAMPLERATE, command_grammar)
    dictation_recognizer = create_enhanced_recognizer(base_model, SAMPLERATE, dictation_grammar)
    current_recognizer = default_recognizer
    
    # PyAudio setup with error handling
    p = pyaudio.PyAudio()
    try:
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=SAMPLERATE,
                        input=True,
                        frames_per_buffer=BUFFER_SIZE,
                        input_device_index=None)  # Use default input device
    except Exception as e:
        log_message(f"Error opening audio stream: {e}", level="ERROR")
        p.terminate()
        exit(1)
    
    # Initialize Hotkey Agent and overlay
    hk_agent = HotkeyAgent()
    overlay.start()
    
    log_message("Enhanced Vosk ASR initialized. Features:")
    log_message("- Auto text formatting in dictation mode")
    log_message("- Confidence tracking and adaptive recognition")
    log_message("- Context-aware processing")
    log_message("- Dictation commands support")
    log_message("- Enhanced audio processing")
    log_message("Waiting for hotkey to start listening...")
    
    try:
        last_command_mode = False
        last_typing_mode = False
        audio_buffer = []
        silence_counter = 0
        max_silence_frames = 10  # Frames of silence before processing
        
        while not hk_agent.is_quit_requested():
            # Handle recognizer switching
            command_mode_active = hk_agent.is_command_mode_active()
            listening_active = hk_agent.is_listening_active()
            typing_active = hk_agent.is_typing_active()
            
            # Switch recognizer based on mode
            recognizer_changed = False
            if command_mode_active != last_command_mode or typing_active != last_typing_mode:
                if command_mode_active:
                    current_recognizer = command_recognizer
                    log_message("Switched to Command Mode Recognizer", 
                              typing_active=typing_active, listening_active=listening_active)
                elif typing_active:
                    current_recognizer = dictation_recognizer
                    log_message("Switched to Enhanced Dictation Recognizer", 
                              typing_active=typing_active, listening_active=listening_active)
                else:
                    current_recognizer = default_recognizer
                    log_message("Switched to Default Recognizer", 
                              typing_active=typing_active, listening_active=listening_active)
                
                current_recognizer.Reset()
                recognizer_changed = True
                last_command_mode = command_mode_active
                last_typing_mode = typing_active
            
            # Read audio data with buffer management
            try:
                data = stream.read(BUFFER_SIZE, exception_on_overflow=False)
                if len(data) == 0:
                    time.sleep(0.01)
                    continue
                
                # Enhanced audio processing with buffering
                audio_buffer.append(data)
                
                # Detect silence (simple energy-based)
                audio_energy = sum(abs(int.from_bytes(data[i:i+2], 'little', signed=True)) 
                                 for i in range(0, len(data), 2))
                
                if audio_energy < 1000000:  # Silence threshold
                    silence_counter += 1
                else:
                    silence_counter = 0
                
            except Exception as e:
                log_message(f"Audio read error: {e}", level="ERROR")
                time.sleep(0.01)
                continue
            
            if listening_active:
                if current_recognizer.AcceptWaveform(data):
                    # Final recognition result
                    result = json.loads(current_recognizer.Result())
                    text = result.get("text", "")
                    confidence = result.get("confidence", 0.0)
                    
                    if text and confidence >= min_confidence:
                        clear_partial()
                        confidence_tracker.add_recognition(confidence)
                        
                        log_message(f"Recognized: {text} (confidence: {confidence:.2f})", 
                                  typing_active=typing_active, listening_active=listening_active)
                        
                        # Update context
                        context_manager.add_text(text)
                        
                        # Handle typing mode with dictation commands
                        if typing_active and not command_mode_active:
                            formatted_text, cmd_executed = process_dictation_command(
                                text, dict_commands, exec_agent, text_formatter)
                            
                            if formatted_text:
                                exec_agent.keyboard_controller.type(formatted_text + " ")
                                log_message(f"[DICTATION] {formatted_text}", 
                                          typing_active=typing_active, listening_active=listening_active)
                            
                            if cmd_executed:
                                overlay.show_message(f"DICTATION CMD: {text}", color="blue", duration=1.5)
                        
                        # Handle command mode
                        elif command_mode_active:
                            command_executed = process_command(text, commands, exec_agent)
                            if command_executed:
                                overlay.show_message(f"EXECUTED: {text}", color="green", duration=1.5)
                            else:
                                overlay.show_message(f"UNKNOWN CMD: {text}", color="red", duration=1.5)
                            
                            hk_agent.deactivate_command_mode()
                            current_recognizer.Reset()
                            time.sleep(0.1)
                    
                    elif text and confidence < min_confidence:
                        log_message(f"Low confidence rejected: {text} (confidence: {confidence:.2f})", 
                                  level="WARNING", typing_active=typing_active, listening_active=listening_active)
                        confidence_tracker.add_rejection(confidence)
                
                else:
                    # Partial recognition result
                    partial_result = json.loads(current_recognizer.PartialResult())
                    partial_text = partial_result.get("partial", "")
                    
                    if partial_text:
                        if command_mode_active:
                            overlay.show_message(f"Command: {partial_text}", color="orange")
                        elif typing_active:
                            # Show formatted preview for dictation
                            formatted_preview = text_formatter.preview_formatting(partial_text)
                            display_partial(f"Dictating: {formatted_preview}", 
                                          typing_active=typing_active, listening_active=listening_active)
                        else:
                            display_partial(partial_text, 
                                          typing_active=typing_active, listening_active=listening_active)
            
            else:
                # Not listening - clear display and reset
                clear_partial()
                current_recognizer.Reset()
                audio_buffer.clear()
                silence_counter = 0
                time.sleep(0.1)
            
            # Adaptive confidence adjustment
            if confidence_tracker.should_adjust_threshold():
                new_threshold = confidence_tracker.get_adaptive_threshold()
                if abs(new_threshold - min_confidence) > 0.05:
                    min_confidence = new_threshold
                    log_message(f"Adaptive confidence threshold: {min_confidence:.2f}")
    
    except KeyboardInterrupt:
        log_message("Exiting via KeyboardInterrupt...")
    except Exception as e:
        log_message(f"Unexpected error: {e}", level="ERROR")
    finally:
        log_message("Cleaning up resources...")
        try:
            stream.stop_stream()
            stream.close()
            p.terminate()
        except:
            pass
        hk_agent.stop()
        overlay.stop()
        log_message("Enhanced application terminated.")

if __name__ == "__main__":
    main()