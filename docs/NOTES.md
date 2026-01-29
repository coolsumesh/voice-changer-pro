# Voice Changer App Notes

## Project Overview
- **Goal:** Windows desktop app for real-time voice changing
- **Target:** Gamers
- **Initial focus:** English to English with gender change
- **Key requirement:** Low latency, standalone application

## Features
- [ ] Real-time voice transformation
- [ ] Multiple voice options (Male, Female, Robot, etc.)
- [ ] Gender swapping (M→F, F→M)
- [ ] Volume control
- [ ] Low-latency audio processing
- [ ] Standalone .exe executable

## Tech Stack
- **Language:** Python (prototype) → C# hybrid if needed
- **UI:** CustomTkinter (Python) or C# WPF
- **Audio:** sounddevice/PyAudio (Python) or NAudio (C#)
- **Voice Model:** RVC or So-VITS-SVC
- **Packaging:** PyInstaller → .exe

## Architecture
```
[Audio Input] → [Capture] → [Voice Model] → [Output] → [Speakers]
                                              ↓
                                        [Discord/etc.]
```

## Payment Model: Freemium
- **Free tier:** Basic voice, limited features
- **Pro ($20 one-time):** All voices, no watermark, future updates

## Roadmap
- [ ] Set up project structure
- [ ] Build UI skeleton (CustomTkinter)
- [ ] Implement audio capture/playback
- [ ] Integrate voice model (RVC)
- [ ] Test latency
- [ ] Package as .exe
- [ ] Add more voice options
- [ ] Implement payment system

## Ideas
- Voice presets (Deep, Chipmunk, etc.)
- Custom voice training?
- Discord integration plugin
- Recording mode
- Voice modulation sliders

## Resources
- RVC: https://github.com/RVC-Project/Retrieval-based-Voice-Conversion
- So-VITS-SVC: https://github.com/svc-develop-team/so-vits-svc
- CustomTkinter: https://customtkinter.tomschimansky.com
- sounddevice: https://python-sounddevice.readthedocs.io

## Next Steps
1. Create project directory structure
2. Install dependencies
3. Test the starter template
4. Profile audio latency
5. Research RVC integration
