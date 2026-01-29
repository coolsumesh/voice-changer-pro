#!/usr/bin/env python3
"""
Download and setup FFmpeg for Windows
Run this once: python setup_ffmpeg.py
"""

import os
import sys
import zipfile
import urllib.request
import shutil

FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))

def download_ffmpeg():
    print("Downloading FFmpeg...")
    zip_path = os.path.join(INSTALL_DIR, "ffmpeg.zip")
    
    # Download with progress
    def report(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(100, downloaded * 100 // total_size)
        print(f"\rDownloading: {percent}%", end="", flush=True)
    
    urllib.request.urlretrieve(FFMPEG_URL, zip_path, report)
    print("\nDownload complete!")
    
    return zip_path

def extract_ffmpeg(zip_path):
    print("Extracting FFmpeg...")
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Find the bin folder
        for name in zip_ref.namelist():
            if name.endswith('/bin/ffmpeg.exe'):
                # Extract just the bin contents
                folder_name = name.split('/')[0]
                break
        
        zip_ref.extractall(INSTALL_DIR)
    
    # Move ffmpeg.exe and ffprobe.exe to current directory
    extracted_folder = None
    for item in os.listdir(INSTALL_DIR):
        if item.startswith('ffmpeg-') and os.path.isdir(os.path.join(INSTALL_DIR, item)):
            extracted_folder = item
            break
    
    if extracted_folder:
        bin_path = os.path.join(INSTALL_DIR, extracted_folder, 'bin')
        for exe in ['ffmpeg.exe', 'ffprobe.exe']:
            src = os.path.join(bin_path, exe)
            dst = os.path.join(INSTALL_DIR, exe)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"Copied {exe}")
        
        # Clean up extracted folder
        shutil.rmtree(os.path.join(INSTALL_DIR, extracted_folder))
    
    # Clean up zip
    os.remove(zip_path)
    print("Cleanup complete!")

def setup_pydub():
    """Configure pydub to use local ffmpeg"""
    ffmpeg_path = os.path.join(INSTALL_DIR, "ffmpeg.exe")
    ffprobe_path = os.path.join(INSTALL_DIR, "ffprobe.exe")
    
    if os.path.exists(ffmpeg_path):
        # Create a config file for the app
        config_content = f'''# FFmpeg paths (auto-generated)
FFMPEG_PATH = r"{ffmpeg_path}"
FFPROBE_PATH = r"{ffprobe_path}"
'''
        config_path = os.path.join(INSTALL_DIR, "src", "ffmpeg_config.py")
        with open(config_path, 'w') as f:
            f.write(config_content)
        print(f"Created config at {config_path}")

def main():
    print("=" * 50)
    print("FFmpeg Setup for Voice Changer Pro")
    print("=" * 50)
    
    # Check if already exists
    ffmpeg_exe = os.path.join(INSTALL_DIR, "ffmpeg.exe")
    if os.path.exists(ffmpeg_exe):
        print("FFmpeg already installed!")
        return
    
    try:
        zip_path = download_ffmpeg()
        extract_ffmpeg(zip_path)
        setup_pydub()
        print("\n✅ FFmpeg installed successfully!")
        print("You can now run: python src/main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nManual install:")
        print("1. Download from: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip")
        print("2. Extract ffmpeg.exe and ffprobe.exe to this folder")
        sys.exit(1)

if __name__ == "__main__":
    main()
