@echo off
setlocal

cd /d "%~dp0"
set "CAM_URL=%~1"
set "EMOTION_BACKEND=beit"
set "MAX_FRAME_WIDTH=480"
set "INFER_EVERY_N_FRAMES=5"
set "STREAM_TIMEOUT_MSEC=5000"

if not exist ".venv\Scripts\activate.bat" (
	echo [ERROR] Virtual environment not found at .venv\Scripts\activate.bat
	echo Create it first with:
	echo   py -m venv .venv
	echo   .venv\Scripts\python -m pip install -r python_client\requirements.txt
	exit /b 1
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
	echo [ERROR] Failed to activate virtual environment.
	exit /b 1
)

if "%CAM_URL%"=="" (
	echo Starting AI Emotion with auto-discovered ESP32-CAM URL...
) else (
	echo Starting AI Emotion with CAM_URL=%CAM_URL%
)

python "python_client\emotion_stream.py"
if errorlevel 1 (
	echo [ERROR] Python client exited with an error.
	exit /b 1
)

endlocal
