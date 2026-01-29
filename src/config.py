"""
Voice Changer Pro - Configuration
"""

# Audio settings
SAMPLE_RATE = 44100
CHUNK_SIZE = 1024
CHANNELS_IN = 1
CHANNELS_OUT = 2

# Voice presets
VOICE_PRESETS = {
    "normal": {
        "pitch_shift": 0,
        "effect": None
    },
    "male": {
        "pitch_shift": -4,
        "effect": None
    },
    "female": {
        "pitch_shift": 4,
        "effect": None
    },
    "robot": {
        "pitch_shift": 0,
        "effect": "ring_mod",
        "mod_freq": 50
    },
    "chipmunk": {
        "pitch_shift": 8,
        "effect": None
    },
    "deep": {
        "pitch_shift": -8,
        "effect": None
    }
}

# UI settings
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 500
THEME = "dark"
COLOR_THEME = "blue"

# App info
APP_NAME = "Voice Changer Pro"
APP_VERSION = "0.1.0"
