#!/usr/bin/env python3
"""
Voice Changer Pro - Real-time voice transformation for gamers
"""

import customtkinter as ctk
import sounddevice as sd
import numpy as np
import threading
import queue
from typing import Optional

# Configure UI theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class AudioProcessor:
    """Handles real-time audio capture and processing"""
    
    def __init__(self, sample_rate: int = 44100, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.is_running = False
        self.stream: Optional[sd.Stream] = None
        self.audio_queue = queue.Queue()
        
        # Voice settings
        self.pitch_shift = 0  # semitones
        self.voice_type = "normal"  # normal, male, female, robot
        self.volume = 1.0
        
    def pitch_shift_audio(self, audio: np.ndarray, semitones: float) -> np.ndarray:
        """Simple pitch shifting using resampling"""
        if semitones == 0:
            return audio
        
        # Calculate the ratio for pitch shift
        ratio = 2 ** (semitones / 12)
        
        # Resample to shift pitch
        from scipy import signal
        
        # Number of samples after resampling
        n_samples = int(len(audio) / ratio)
        if n_samples == 0:
            return audio
            
        shifted = signal.resample(audio, n_samples)
        
        # Pad or trim to original length
        if len(shifted) < len(audio):
            shifted = np.pad(shifted, (0, len(audio) - len(shifted)))
        else:
            shifted = shifted[:len(audio)]
            
        return shifted.astype(np.float32)
    
    def apply_voice_effect(self, audio: np.ndarray) -> np.ndarray:
        """Apply voice transformation based on selected type"""
        
        if self.voice_type == "normal":
            return audio
        elif self.voice_type == "male":
            # Lower pitch for male voice
            return self.pitch_shift_audio(audio, -4)
        elif self.voice_type == "female":
            # Higher pitch for female voice
            return self.pitch_shift_audio(audio, 4)
        elif self.voice_type == "robot":
            # Add robotic effect (simple ring modulation)
            t = np.arange(len(audio)) / self.sample_rate
            modulator = np.sin(2 * np.pi * 50 * t)  # 50 Hz modulation
            return (audio * modulator * 0.5 + audio * 0.5).astype(np.float32)
        
        return audio
    
    def audio_callback(self, indata, outdata, frames, time, status):
        """Real-time audio processing callback"""
        if status:
            print(f"Audio status: {status}")
        
        # Get mono audio
        audio = indata[:, 0].copy()
        
        # Apply voice effect
        processed = self.apply_voice_effect(audio)
        
        # Apply pitch shift if set
        if self.pitch_shift != 0:
            processed = self.pitch_shift_audio(processed, self.pitch_shift)
        
        # Apply volume
        processed = processed * self.volume
        
        # Clip to prevent distortion
        processed = np.clip(processed, -1.0, 1.0)
        
        # Output to both channels
        outdata[:, 0] = processed
        outdata[:, 1] = processed
    
    def start(self):
        """Start audio processing"""
        if self.is_running:
            return
            
        self.is_running = True
        self.stream = sd.Stream(
            samplerate=self.sample_rate,
            blocksize=self.chunk_size,
            channels=(1, 2),  # mono in, stereo out
            dtype='float32',
            callback=self.audio_callback,
            latency='low'
        )
        self.stream.start()
        
    def stop(self):
        """Stop audio processing"""
        self.is_running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None


class VoiceChangerApp(ctk.CTk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("Voice Changer Pro 🎤")
        self.geometry("400x700")
        self.resizable(True, True)
        
        # Audio processor
        self.audio = AudioProcessor()
        
        # Build UI
        self.setup_ui()
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def setup_ui(self):
        """Create the user interface"""
        
        # Title
        title = ctk.CTkLabel(
            self, 
            text="🎤 Voice Changer Pro",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # Status indicator
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.pack(pady=10, padx=20, fill="x")
        
        self.status_dot = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=ctk.CTkFont(size=20),
            text_color="gray"
        )
        self.status_dot.pack(side="left", padx=10)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=ctk.CTkFont(size=14)
        )
        self.status_label.pack(side="left")
        
        # Voice type selector
        voice_frame = ctk.CTkFrame(self)
        voice_frame.pack(pady=20, padx=20, fill="x")
        
        voice_label = ctk.CTkLabel(
            voice_frame,
            text="Voice Type:",
            font=ctk.CTkFont(size=14)
        )
        voice_label.pack(pady=10)
        
        self.voice_var = ctk.StringVar(value="normal")
        
        voices = [
            ("Normal", "normal"),
            ("Male", "male"),
            ("Female", "female"),
            ("Robot", "robot")
        ]
        
        for text, value in voices:
            rb = ctk.CTkRadioButton(
                voice_frame,
                text=text,
                variable=self.voice_var,
                value=value,
                command=self.on_voice_change
            )
            rb.pack(pady=5)
        
        # Pitch slider
        pitch_frame = ctk.CTkFrame(self)
        pitch_frame.pack(pady=20, padx=20, fill="x")
        
        pitch_label = ctk.CTkLabel(
            pitch_frame,
            text="Fine Tune Pitch:",
            font=ctk.CTkFont(size=14)
        )
        pitch_label.pack(pady=10)
        
        self.pitch_slider = ctk.CTkSlider(
            pitch_frame,
            from_=-12,
            to=12,
            number_of_steps=24,
            command=self.on_pitch_change
        )
        self.pitch_slider.pack(pady=5, padx=20, fill="x")
        self.pitch_slider.set(0)
        
        self.pitch_value = ctk.CTkLabel(
            pitch_frame,
            text="0 semitones",
            font=ctk.CTkFont(size=12)
        )
        self.pitch_value.pack()
        
        # Volume slider
        volume_frame = ctk.CTkFrame(self)
        volume_frame.pack(pady=10, padx=20, fill="x")
        
        volume_label = ctk.CTkLabel(
            volume_frame,
            text="Volume:",
            font=ctk.CTkFont(size=14)
        )
        volume_label.pack(pady=10)
        
        self.volume_slider = ctk.CTkSlider(
            volume_frame,
            from_=0,
            to=2,
            command=self.on_volume_change
        )
        self.volume_slider.pack(pady=5, padx=20, fill="x")
        self.volume_slider.set(1.0)
        
        # Start/Stop button
        self.toggle_btn = ctk.CTkButton(
            self,
            text="▶ Start",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=50,
            command=self.toggle_audio
        )
        self.toggle_btn.pack(pady=30, padx=40, fill="x")
        
    def on_voice_change(self):
        """Handle voice type change"""
        self.audio.voice_type = self.voice_var.get()
        
    def on_pitch_change(self, value):
        """Handle pitch slider change"""
        pitch = int(value)
        self.audio.pitch_shift = pitch
        self.pitch_value.configure(text=f"{pitch:+d} semitones")
        
    def on_volume_change(self, value):
        """Handle volume slider change"""
        self.audio.volume = value
        
    def toggle_audio(self):
        """Start or stop audio processing"""
        if self.audio.is_running:
            self.audio.stop()
            self.toggle_btn.configure(text="▶ Start")
            self.status_label.configure(text="Ready")
            self.status_dot.configure(text_color="gray")
        else:
            self.audio.start()
            self.toggle_btn.configure(text="⏹ Stop")
            self.status_label.configure(text="Processing...")
            self.status_dot.configure(text_color="green")
            
    def on_close(self):
        """Handle window close"""
        self.audio.stop()
        self.destroy()


def main():
    app = VoiceChangerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
