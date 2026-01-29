#!/usr/bin/env python3
"""
Voice Changer Pro - Record & Convert voice transformation
"""

import customtkinter as ctk
import sounddevice as sd
import numpy as np
import threading
import wave
import os
import tempfile
from datetime import datetime
from scipy.io import wavfile
from scipy import signal

# Configure UI theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class AudioProcessor:
    """Handles audio recording and processing"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.is_recording = False
        self.recorded_audio = []
        self.converted_audio = None
        
        # Voice settings
        self.voice_type = "female"
        self.pitch_shift = 0
        
    def start_recording(self):
        """Start recording audio"""
        self.is_recording = True
        self.recorded_audio = []
        
        def callback(indata, frames, time, status):
            if self.is_recording:
                self.recorded_audio.append(indata.copy())
        
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32',
            callback=callback
        )
        self.stream.start()
        
    def stop_recording(self):
        """Stop recording and return audio data"""
        self.is_recording = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
        if self.recorded_audio:
            return np.concatenate(self.recorded_audio, axis=0)
        return None
    
    def pitch_shift_audio(self, audio: np.ndarray, semitones: float) -> np.ndarray:
        """Pitch shift using resampling with formant preservation attempt"""
        if semitones == 0:
            return audio
        
        ratio = 2 ** (semitones / 12)
        
        # Resample
        n_samples = int(len(audio) / ratio)
        if n_samples == 0:
            return audio
            
        shifted = signal.resample(audio, n_samples)
        
        # Time-stretch back to original length (preserves duration)
        stretched = signal.resample(shifted, len(audio))
        
        return stretched.astype(np.float32)
    
    def apply_formant_shift(self, audio: np.ndarray, shift_factor: float) -> np.ndarray:
        """Apply formant shifting for more natural voice conversion"""
        # Simple formant shift using spectral envelope manipulation
        from scipy.fft import fft, ifft
        
        # Window the audio
        window_size = 2048
        hop_size = 512
        
        # Pad audio
        pad_length = window_size - (len(audio) % window_size)
        audio_padded = np.pad(audio.flatten(), (0, pad_length))
        
        output = np.zeros_like(audio_padded)
        window = np.hanning(window_size)
        
        for i in range(0, len(audio_padded) - window_size, hop_size):
            frame = audio_padded[i:i+window_size] * window
            
            # FFT
            spectrum = fft(frame)
            magnitude = np.abs(spectrum)
            phase = np.angle(spectrum)
            
            # Shift formants by interpolating magnitude spectrum
            freqs = np.arange(len(magnitude))
            new_freqs = freqs / shift_factor
            new_freqs = np.clip(new_freqs, 0, len(magnitude) - 1)
            
            shifted_magnitude = np.interp(freqs, new_freqs, magnitude)
            
            # Reconstruct
            shifted_spectrum = shifted_magnitude * np.exp(1j * phase)
            frame_out = np.real(ifft(shifted_spectrum)) * window
            
            output[i:i+window_size] += frame_out
        
        # Normalize
        output = output[:len(audio)]
        max_val = np.max(np.abs(output))
        if max_val > 0:
            output = output / max_val * 0.9
            
        return output.astype(np.float32)
    
    def convert_voice(self, audio: np.ndarray) -> np.ndarray:
        """Convert voice based on selected type"""
        audio = audio.flatten()
        
        if self.voice_type == "female":
            # Higher pitch + formant shift for female
            converted = self.pitch_shift_audio(audio, 4 + self.pitch_shift)
            converted = self.apply_formant_shift(converted, 1.2)
            
        elif self.voice_type == "male":
            # Lower pitch + formant shift for male
            converted = self.pitch_shift_audio(audio, -4 + self.pitch_shift)
            converted = self.apply_formant_shift(converted, 0.85)
            
        elif self.voice_type == "robot":
            # Ring modulation for robot
            t = np.arange(len(audio)) / self.sample_rate
            modulator = np.sin(2 * np.pi * 50 * t)
            converted = (audio * modulator * 0.7 + audio * 0.3).astype(np.float32)
            
        elif self.voice_type == "whisper":
            # Add noise and reduce harmonics
            noise = np.random.randn(len(audio)) * 0.1
            converted = (audio * 0.3 + noise * np.abs(audio) * 2).astype(np.float32)
            
        elif self.voice_type == "deep":
            # Very low pitch
            converted = self.pitch_shift_audio(audio, -8 + self.pitch_shift)
            converted = self.apply_formant_shift(converted, 0.75)
            
        elif self.voice_type == "chipmunk":
            # Very high pitch
            converted = self.pitch_shift_audio(audio, 10 + self.pitch_shift)
            converted = self.apply_formant_shift(converted, 1.4)
            
        else:
            converted = self.pitch_shift_audio(audio, self.pitch_shift)
        
        self.converted_audio = converted
        return converted
    
    def play_audio(self, audio: np.ndarray):
        """Play audio through speakers"""
        sd.play(audio, self.sample_rate)
        sd.wait()
        
    def save_audio(self, audio: np.ndarray, filename: str):
        """Save audio to WAV file"""
        # Normalize to 16-bit
        audio_16bit = (audio * 32767).astype(np.int16)
        wavfile.write(filename, self.sample_rate, audio_16bit)


class VoiceChangerApp(ctk.CTk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("Voice Changer Pro 🎤")
        self.geometry("450x650")
        self.resizable(True, True)
        
        # Audio processor
        self.audio = AudioProcessor()
        self.current_recording = None
        
        # Build UI
        self.setup_ui()
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def setup_ui(self):
        """Create the user interface"""
        
        # Main container with scroll
        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title = ctk.CTkLabel(
            self.main_frame, 
            text="🎤 Voice Changer Pro",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=15)
        
        # Status indicator
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_frame.pack(pady=10, padx=10, fill="x")
        
        self.status_dot = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=ctk.CTkFont(size=20),
            text_color="gray"
        )
        self.status_dot.pack(side="left", padx=10)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready - Click Record to start",
            font=ctk.CTkFont(size=14)
        )
        self.status_label.pack(side="left")
        
        # Voice type selector
        voice_frame = ctk.CTkFrame(self.main_frame)
        voice_frame.pack(pady=15, padx=10, fill="x")
        
        voice_label = ctk.CTkLabel(
            voice_frame,
            text="Voice Type:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        voice_label.pack(pady=10)
        
        self.voice_var = ctk.StringVar(value="female")
        
        voices = [
            ("👩 Female", "female"),
            ("👨 Male", "male"),
            ("🤖 Robot", "robot"),
            ("🐿️ Chipmunk", "chipmunk"),
            ("😈 Deep", "deep"),
            ("🌬️ Whisper", "whisper"),
        ]
        
        voice_grid = ctk.CTkFrame(voice_frame, fg_color="transparent")
        voice_grid.pack(pady=5)
        
        for i, (text, value) in enumerate(voices):
            rb = ctk.CTkRadioButton(
                voice_grid,
                text=text,
                variable=self.voice_var,
                value=value,
                command=self.on_voice_change
            )
            rb.grid(row=i//2, column=i%2, padx=20, pady=5, sticky="w")
        
        # Pitch slider
        pitch_frame = ctk.CTkFrame(self.main_frame)
        pitch_frame.pack(pady=15, padx=10, fill="x")
        
        pitch_label = ctk.CTkLabel(
            pitch_frame,
            text="Fine Tune Pitch:",
            font=ctk.CTkFont(size=14, weight="bold")
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
        
        # Control buttons
        btn_frame = ctk.CTkFrame(self.main_frame)
        btn_frame.pack(pady=20, padx=10, fill="x")
        
        # Record button
        self.record_btn = ctk.CTkButton(
            btn_frame,
            text="🎙️ Record",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.toggle_recording
        )
        self.record_btn.pack(pady=10, padx=20, fill="x")
        
        # Convert button
        self.convert_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 Convert Voice",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            fg_color="#3498db",
            hover_color="#2980b9",
            command=self.convert_voice,
            state="disabled"
        )
        self.convert_btn.pack(pady=10, padx=20, fill="x")
        
        # Play buttons frame
        play_frame = ctk.CTkFrame(btn_frame, fg_color="transparent")
        play_frame.pack(pady=10, fill="x")
        
        # Play original button
        self.play_orig_btn = ctk.CTkButton(
            play_frame,
            text="▶️ Original",
            font=ctk.CTkFont(size=14),
            height=40,
            width=120,
            fg_color="#7f8c8d",
            hover_color="#636e72",
            command=self.play_original,
            state="disabled"
        )
        self.play_orig_btn.pack(side="left", padx=10, expand=True)
        
        # Play converted button
        self.play_conv_btn = ctk.CTkButton(
            play_frame,
            text="▶️ Converted",
            font=ctk.CTkFont(size=14),
            height=40,
            width=120,
            fg_color="#27ae60",
            hover_color="#1e8449",
            command=self.play_converted,
            state="disabled"
        )
        self.play_conv_btn.pack(side="right", padx=10, expand=True)
        
        # Save button
        self.save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Save Converted Audio",
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="#9b59b6",
            hover_color="#8e44ad",
            command=self.save_converted,
            state="disabled"
        )
        self.save_btn.pack(pady=10, padx=20, fill="x")
        
    def on_voice_change(self):
        """Handle voice type change"""
        self.audio.voice_type = self.voice_var.get()
        
    def on_pitch_change(self, value):
        """Handle pitch slider change"""
        pitch = int(value)
        self.audio.pitch_shift = pitch
        self.pitch_value.configure(text=f"{pitch:+d} semitones")
        
    def toggle_recording(self):
        """Start or stop recording"""
        if self.audio.is_recording:
            # Stop recording
            self.current_recording = self.audio.stop_recording()
            self.record_btn.configure(text="🎙️ Record", fg_color="#e74c3c")
            self.status_label.configure(text="Recording saved! Click Convert")
            self.status_dot.configure(text_color="orange")
            
            if self.current_recording is not None:
                self.convert_btn.configure(state="normal")
                self.play_orig_btn.configure(state="normal")
        else:
            # Start recording
            self.audio.start_recording()
            self.record_btn.configure(text="⏹️ Stop", fg_color="#27ae60")
            self.status_label.configure(text="Recording... Speak now!")
            self.status_dot.configure(text_color="red")
            
            # Reset buttons
            self.convert_btn.configure(state="disabled")
            self.play_orig_btn.configure(state="disabled")
            self.play_conv_btn.configure(state="disabled")
            self.save_btn.configure(state="disabled")
            
    def convert_voice(self):
        """Convert the recorded voice"""
        if self.current_recording is None:
            return
            
        self.status_label.configure(text="Converting...")
        self.status_dot.configure(text_color="yellow")
        self.update()
        
        # Run conversion in thread
        def do_convert():
            self.audio.convert_voice(self.current_recording)
            self.after(0, self.conversion_done)
            
        threading.Thread(target=do_convert, daemon=True).start()
        
    def conversion_done(self):
        """Called when conversion is complete"""
        self.status_label.configure(text="Conversion complete! Click Play")
        self.status_dot.configure(text_color="green")
        self.play_conv_btn.configure(state="normal")
        self.save_btn.configure(state="normal")
        
    def play_original(self):
        """Play original recording"""
        if self.current_recording is not None:
            self.status_label.configure(text="Playing original...")
            threading.Thread(
                target=lambda: (
                    self.audio.play_audio(self.current_recording),
                    self.after(0, lambda: self.status_label.configure(text="Ready"))
                ),
                daemon=True
            ).start()
            
    def play_converted(self):
        """Play converted audio"""
        if self.audio.converted_audio is not None:
            self.status_label.configure(text="Playing converted...")
            threading.Thread(
                target=lambda: (
                    self.audio.play_audio(self.audio.converted_audio),
                    self.after(0, lambda: self.status_label.configure(text="Ready"))
                ),
                daemon=True
            ).start()
            
    def save_converted(self):
        """Save converted audio to file"""
        if self.audio.converted_audio is None:
            return
            
        # Create output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        voice_type = self.voice_var.get()
        filename = f"converted_{voice_type}_{timestamp}.wav"
        
        # Save to user's documents or current directory
        docs_path = os.path.expanduser("~/Documents")
        if os.path.exists(docs_path):
            filepath = os.path.join(docs_path, filename)
        else:
            filepath = filename
            
        self.audio.save_audio(self.audio.converted_audio, filepath)
        self.status_label.configure(text=f"Saved: {filename}")
            
    def on_close(self):
        """Handle window close"""
        if self.audio.is_recording:
            self.audio.stop_recording()
        sd.stop()
        self.destroy()


def main():
    app = VoiceChangerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
