#!/usr/bin/env python3
"""
Voice Changer Pro - ElevenLabs AI Voice Conversion
"""

import customtkinter as ctk
import sounddevice as sd
import numpy as np
import threading
import requests
import io
import os
import wave
import tempfile
from datetime import datetime
from scipy.io import wavfile

# Configure UI theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ElevenLabs API Configuration
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "sk_8269ab1484ed4e63425bc3490025eff813ddbbde40664c19")

# ElevenLabs Voice IDs (popular voices)
VOICES = {
    "Rachel (Female)": "21m00Tcm4TlvDq8ikWAM",
    "Domi (Female)": "AZnzlk1XvdvUeBnXmlld",
    "Bella (Female)": "EXAVITQu4vr4xnSDxMaL",
    "Antoni (Male)": "ErXwobaYiN019PkySvjV",
    "Josh (Male)": "TxGEqnHWrfWFTfGW9XjX",
    "Arnold (Male)": "VR6AewLTigWG4xSOukaG",
    "Adam (Male)": "pNInz6obpgDQGcFmaJgB",
    "Sam (Male)": "yoZ06aMxZJJ28mfd3POQ",
}

# Model options
MODELS = {
    "English Only": "eleven_english_sts_v2",
    "Multilingual": "eleven_multilingual_sts_v2",
}


class AudioProcessor:
    """Handles audio recording and ElevenLabs conversion"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.is_recording = False
        self.recorded_audio = []
        self.converted_audio = None
        self.selected_voice_id = list(VOICES.values())[0]
        self.selected_model = "eleven_multilingual_sts_v2"  # Default to multilingual
        
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
    
    def audio_to_wav_bytes(self, audio: np.ndarray) -> bytes:
        """Convert numpy audio to WAV bytes"""
        # Convert to 16-bit PCM
        audio_16bit = (audio.flatten() * 32767).astype(np.int16)
        
        # Create WAV in memory
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_16bit.tobytes())
        
        buffer.seek(0)
        return buffer.read()
    
    def convert_with_elevenlabs(self, audio: np.ndarray, voice_id: str) -> np.ndarray:
        """Convert voice using ElevenLabs Speech-to-Speech API"""
        
        # Convert audio to WAV bytes
        wav_bytes = self.audio_to_wav_bytes(audio)
        
        # ElevenLabs Speech-to-Speech endpoint with PCM output (no FFmpeg needed!)
        url = f"https://api.elevenlabs.io/v1/speech-to-speech/{voice_id}"
        
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Accept": "audio/mpeg",  # Request format
        }
        
        # Send as multipart form data
        files = {
            "audio": ("recording.wav", wav_bytes, "audio/wav"),
        }
        
        data = {
            "model_id": self.selected_model,
            "voice_settings": '{"stability": 0.5, "similarity_boost": 0.75}',
            "output_format": "pcm_44100"  # PCM format - no FFmpeg needed!
        }
        
        response = requests.post(url, headers=headers, files=files, data=data)
        
        if response.status_code == 200:
            # PCM format is raw 16-bit signed integers
            audio_bytes = response.content
            
            # Convert PCM bytes to numpy array
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # Convert to float32 [-1, 1]
            audio_float = audio_data.astype(np.float32) / 32767
            
            self.converted_sample_rate = 44100
            return audio_float
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', {}).get('message', str(error_data))
            except:
                error_msg = response.text
            raise Exception(f"API error: {error_msg}")
    
    def play_audio(self, audio: np.ndarray, sample_rate: int = None):
        """Play audio through speakers"""
        sr = sample_rate or self.sample_rate
        sd.play(audio, sr)
        sd.wait()
        
    def save_audio(self, audio: np.ndarray, filename: str, sample_rate: int = None):
        """Save audio to WAV file"""
        sr = sample_rate or self.sample_rate
        audio_16bit = (audio.flatten() * 32767).astype(np.int16)
        wavfile.write(filename, sr, audio_16bit)


class VoiceChangerApp(ctk.CTk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("Voice Changer Pro 🎤")
        self.geometry("500x700")
        self.resizable(True, True)
        
        # Audio processor
        self.audio = AudioProcessor()
        self.current_recording = None
        self.converted_sample_rate = 44100
        
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
        
        subtitle = ctk.CTkLabel(
            self.main_frame,
            text="Powered by ElevenLabs AI",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle.pack()
        
        # Status indicator
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_frame.pack(pady=15, padx=10, fill="x")
        
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
        
        # Voice selector
        voice_frame = ctk.CTkFrame(self.main_frame)
        voice_frame.pack(pady=15, padx=10, fill="x")
        
        voice_label = ctk.CTkLabel(
            voice_frame,
            text="Select Target Voice:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        voice_label.pack(pady=10)
        
        self.voice_var = ctk.StringVar(value=list(VOICES.keys())[0])
        
        self.voice_dropdown = ctk.CTkComboBox(
            voice_frame,
            values=list(VOICES.keys()),
            variable=self.voice_var,
            command=self.on_voice_change,
            width=300,
            font=ctk.CTkFont(size=14)
        )
        self.voice_dropdown.pack(pady=10)
        
        # Female voices
        female_label = ctk.CTkLabel(
            voice_frame,
            text="👩 Female: Rachel, Domi, Bella",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        female_label.pack()
        
        # Male voices
        male_label = ctk.CTkLabel(
            voice_frame,
            text="👨 Male: Antoni, Josh, Arnold, Adam, Sam",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        male_label.pack(pady=(0,10))
        
        # Language/Model selector
        lang_frame = ctk.CTkFrame(self.main_frame)
        lang_frame.pack(pady=10, padx=10, fill="x")
        
        lang_label = ctk.CTkLabel(
            lang_frame,
            text="Language Mode:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        lang_label.pack(pady=10)
        
        self.model_var = ctk.StringVar(value="Multilingual")
        
        self.model_dropdown = ctk.CTkComboBox(
            lang_frame,
            values=list(MODELS.keys()),
            variable=self.model_var,
            command=self.on_model_change,
            width=300,
            font=ctk.CTkFont(size=14)
        )
        self.model_dropdown.pack(pady=5)
        
        lang_info = ctk.CTkLabel(
            lang_frame,
            text="🌍 Multilingual: Supports 29 languages\n🇺🇸 English Only: Best for English speech",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        lang_info.pack(pady=(5,10))
        
        # Control buttons
        btn_frame = ctk.CTkFrame(self.main_frame)
        btn_frame.pack(pady=15, padx=10, fill="x")
        
        # Record button
        self.record_btn = ctk.CTkButton(
            btn_frame,
            text="🎙️ Record",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=60,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.toggle_recording
        )
        self.record_btn.pack(pady=10, padx=20, fill="x")
        
        # Convert button
        self.convert_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 Convert with AI",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=60,
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
            height=45,
            width=140,
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
            height=45,
            width=140,
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
            height=45,
            fg_color="#9b59b6",
            hover_color="#8e44ad",
            command=self.save_converted,
            state="disabled"
        )
        self.save_btn.pack(pady=10, padx=20, fill="x")
        
        # Info
        info_label = ctk.CTkLabel(
            self.main_frame,
            text="💡 Tip: Speak clearly for best results",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        info_label.pack(pady=10)
        
    def on_voice_change(self, choice):
        """Handle voice selection change"""
        self.audio.selected_voice_id = VOICES[choice]
        
    def on_model_change(self, choice):
        """Handle model/language selection change"""
        self.audio.selected_model = MODELS[choice]
        
    def toggle_recording(self):
        """Start or stop recording"""
        if self.audio.is_recording:
            # Stop recording
            self.current_recording = self.audio.stop_recording()
            self.record_btn.configure(text="🎙️ Record", fg_color="#e74c3c")
            self.status_label.configure(text="Recording saved! Click Convert")
            self.status_dot.configure(text_color="orange")
            
            if self.current_recording is not None and len(self.current_recording) > 0:
                duration = len(self.current_recording) / self.audio.sample_rate
                self.status_label.configure(text=f"Recorded {duration:.1f}s - Click Convert")
                self.convert_btn.configure(state="normal")
                self.play_orig_btn.configure(state="normal")
        else:
            # Start recording
            self.audio.start_recording()
            self.record_btn.configure(text="⏹️ Stop Recording", fg_color="#27ae60")
            self.status_label.configure(text="🔴 Recording... Speak now!")
            self.status_dot.configure(text_color="red")
            
            # Reset buttons
            self.convert_btn.configure(state="disabled")
            self.play_orig_btn.configure(state="disabled")
            self.play_conv_btn.configure(state="disabled")
            self.save_btn.configure(state="disabled")
            
    def convert_voice(self):
        """Convert the recorded voice using ElevenLabs"""
        if self.current_recording is None:
            return
            
        self.status_label.configure(text="🔄 Converting with AI... Please wait")
        self.status_dot.configure(text_color="yellow")
        self.convert_btn.configure(state="disabled")
        self.update()
        
        # Run conversion in thread
        def do_convert():
            try:
                voice_id = self.audio.selected_voice_id
                converted = self.audio.convert_with_elevenlabs(self.current_recording, voice_id)
                self.audio.converted_audio = converted
                
                if hasattr(self.audio, 'converted_sample_rate'):
                    self.converted_sample_rate = self.audio.converted_sample_rate
                    
                self.after(0, self.conversion_done)
            except Exception as e:
                self.after(0, lambda: self.conversion_error(str(e)))
            
        threading.Thread(target=do_convert, daemon=True).start()
        
    def conversion_done(self):
        """Called when conversion is complete"""
        self.status_label.configure(text="✅ Conversion complete! Click Play")
        self.status_dot.configure(text_color="green")
        self.convert_btn.configure(state="normal")
        self.play_conv_btn.configure(state="normal")
        self.save_btn.configure(state="normal")
        
    def conversion_error(self, error_msg):
        """Called when conversion fails"""
        self.status_label.configure(text=f"❌ Error: {error_msg[:50]}")
        self.status_dot.configure(text_color="red")
        self.convert_btn.configure(state="normal")
        print(f"Conversion error: {error_msg}")
        
    def play_original(self):
        """Play original recording"""
        if self.current_recording is not None:
            self.status_label.configure(text="▶️ Playing original...")
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
            self.status_label.configure(text="▶️ Playing converted...")
            threading.Thread(
                target=lambda: (
                    self.audio.play_audio(self.audio.converted_audio, self.converted_sample_rate),
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
        voice_name = self.voice_var.get().split()[0]
        filename = f"converted_{voice_name}_{timestamp}.wav"
        
        # Save to user's documents or current directory
        docs_path = os.path.expanduser("~/Documents")
        if os.path.exists(docs_path):
            filepath = os.path.join(docs_path, filename)
        else:
            filepath = filename
            
        self.audio.save_audio(self.audio.converted_audio, filepath, self.converted_sample_rate)
        self.status_label.configure(text=f"💾 Saved: {filename}")
            
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
