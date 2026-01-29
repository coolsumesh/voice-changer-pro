# Voice Changer Pro 🎤

Real-time voice transformation app for Windows gamers.

## Features

- 🎭 Multiple voice presets (Male, Female, Robot)
- 🎚️ Fine-tune pitch control (-12 to +12 semitones)
- ⚡ Low-latency real-time processing
- 🎨 Clean dark-mode UI

## Installation

### Requirements
- Python 3.10+
- Windows 10/11

### Setup

```bash
# Clone or download the project
cd voice-changer-app

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python src/main.py
```

## Building Standalone .exe

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --noconsole --name VoiceChangerPro src/main.py

# Output will be in dist/VoiceChangerPro.exe
```

## Usage

1. Launch the app
2. Select a voice preset (Normal, Male, Female, Robot)
3. Adjust pitch with the slider if needed
4. Click "Start" to begin voice transformation
5. Speak into your microphone — your transformed voice plays through speakers

## Roadmap

- [ ] Add more voice presets
- [ ] RVC model integration for realistic voice cloning
- [ ] Virtual audio device output (for Discord/games)
- [ ] Custom voice training
- [ ] Settings persistence

## License

MIT
