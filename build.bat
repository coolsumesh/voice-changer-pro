@echo off
echo Building Voice Changer Pro...
echo.

REM Activate virtual environment if exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Install/update dependencies
pip install -r requirements.txt
pip install pyinstaller

REM Build executable
pyinstaller --onefile --noconsole --name VoiceChangerPro --icon=assets/icon.ico src/main.py

echo.
echo Build complete! Check dist/VoiceChangerPro.exe
pause
