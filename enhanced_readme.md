# Enhanced Voice Recognition System

A powerful, real-time voice recognition system with advanced dictation, command processing, and intelligent features.

## 🚀 New Features & Enhancements

### 1. **Smart Text Formatting**
- **Automatic punctuation**: Say "period", "comma", "question mark" → `.`, `,`, `?`
- **Number conversion**: Say "one", "two", "three" → `1`, `2`, `3`
- **Contractions**: Say "im", "youre", "dont" → `I'm`, `you're`, `don't`
- **Email formatting**: Say "john at gmail dot com" → `john@gmail.com`
- **Real-time preview**: See formatted text before it's typed
- **Custom corrections**: Automatically fix common speech recognition errors

### 2. **Dictation Commands (dict_cmds.json)**
Execute commands while dictating without leaving dictation mode:
- **"slap"** → Press Enter (new line)
- **"scratch that"** → Undo last action
- **"delete that"** → Delete current word
- **"copy that"** → Copy selection
- **"paste that"** → Paste clipboard
- **"bold"** → Toggle bold formatting (Ctrl+B)
- **"save"** → Save document (Ctrl+S)
- **"new line"** → Insert line break
- **Navigation**: "up arrow", "down arrow", "page up", "page down"
- **Window control**: "minimize", "maximize", "close window"

### 3. **Enhanced Hotkey System**
- **Double/Triple Press Detection**: Multi-level functionality on same keys
- **Smart Modes**:
  - Double Ctrl: Toggle listening
  - Triple Ctrl: Toggle smart mode (auto-pause on inactivity)
  - Double Alt: Toggle typing
  - Triple Alt: Toggle precision mode (higher confidence threshold)
  - Right Alt: Quick dictation (listening + typing instantly)
  - Triple Shift: Show session statistics

### 4. **Confidence Tracking & Adaptive Recognition**
- **Real-time confidence monitoring**: Tracks recognition accuracy
- **Adaptive thresholds**: Automatically adjusts confidence requirements
- **Performance analytics**: Tracks success/failure rates
- **Quality suggestions**: Recommends recalibration when needed

### 5. **Context-Aware Processing**
- **Domain detection**: Recognizes technical, business, medical, legal contexts
- **Word frequency tracking**: Learns your vocabulary patterns
- **Topic awareness**: Remembers recent subjects for better recognition
- **Pattern detection**: Identifies emails, phone numbers, dates, URLs
- **Word predictions**: Suggests completions based on context

### 6. **Advanced Audio Processing**
- **Enhanced buffering**: Better handling of audio streams
- **Silence detection**: Improved processing of speech pauses
- **Multiple recognizer modes**: Optimized for different use cases
- **Grammar-aware recognition**: Better accuracy for specific vocabularies

### 7. **Rich Console Interface**
- **Color-coded status**: Visual indicators for all modes
- **Real-time state display**: L/T/C/S/P indicators (Listening/Typing/Command/Smart/Precision)
- **Enhanced logging**: Detailed session tracking with timestamps
- **Performance metrics**: Live statistics display

### 8. **Smart Overlay System**
- **Multiple themes**: Dark, light, colorful
- **Positioning options**: Top, bottom, center, corners
- **Fade effects**: Smooth message transitions
- **Status persistence**: Important messages stay visible
- **Color-coded feedback**: Green (success), red (error), orange (commands)

### 9. **Advanced Command Execution**
- **Mouse control**: Click, move, scroll with voice
- **Window management**: Minimize, maximize, switch applications
- **System actions**: Lock screen, take screenshots, volume control
- **Text manipulation**: Select, copy, paste, format with precision
- **Macro support**: Execute complex command sequences
- **Process tracking**: Monitor and control launched applications

### 10. **Session Analytics**
- **Usage statistics**: Track listening/typing time percentages
- **Recognition metrics**: Success rates, confidence levels
- **Performance trends**: Monitor improvement over time
- **Export capabilities**: Save session data for analysis

## 📁 Configuration Files

### cmd.json
Standard command mode actions (existing functionality)

### dict_cmds.json (NEW)
Dictation-specific commands that work while typing:
```json
{
  "slap": [{"type": "key_press", "value": "enter"}],
  "scratch that": [{"type": "text_manipulation", "value": "undo"}],
  "bold": [{"type": "key_combo", "value": "ctrl+b"}]
}
```

### corrections.json (AUTO-GENERATED)
Custom word corrections for speech recognition errors:
```json
{
  "there": "their",
  "your": "you're",
  "its": "it's"
}
```

### abbreviations.json (AUTO-GENERATED)
Abbreviation expansions:
```json
{
  "btw": "by the way",
  "fyi": "for your information",
  "asap": "as soon as possible"
}
```

## 🎯 Usage Guide

### Basic Operation
1. **Start Listening**: Double-tap Left Ctrl
2. **Start Typing**: Double-tap Left Alt  
3. **Command Mode**: Press Right Ctrl
4. **Quick Dictation**: Press Right Alt
5. **Emergency Stop**: Triple-tap ESC
6. **Quit Application**: Double-tap ESC

### Smart Features
- **Auto-pause**: Enable with Triple Ctrl, pauses after 10s inactivity
- **Precision Mode**: Enable with Triple Alt for higher accuracy
- **Session Stats**: Triple-tap Shift to view performance

### Dictation Workflow
1. Enable listening (Double Ctrl) + typing (Double Alt)
2. Start speaking normally
3. Use dictation commands: "slap" for new lines, "bold" for formatting
4. Text is automatically formatted an