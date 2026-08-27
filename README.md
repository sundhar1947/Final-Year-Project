# ESP32-CAM Facial Emotion Detection ![project-badge](https://img.shields.io/badge/project-ESP32--CAM-blue)

This repository contains a small end-to-end project that captures a video stream from an ESP32-CAM and runs real-time facial emotion detection using a Python client. Two emotion backends are supported[...] 

Contents
- sai final pt/
  - esp32_cam/
    - esp32_cam.ino — Arduino/ESP32 sketch that starts an MJPEG HTTP stream and health endpoint on port 81.
  - python_client/
    - emotion_stream.py — (entry) Python client that reads the stream, runs emotion detection and logs events (not included in this repo preview but referenced by tools).
    - emotion_module.py — EmotionAnalyzer wrapper supporting `deepface` and `beit` backends and normalising results.
    - interface.py — Tkinter GUI that launches the Python client in a .venv and shows logs & status.
    - beit_emotion.py — Minimal CLI to run the BEiT image classification model on a single image.
    - requirements.txt — Python dependencies used by the client.
  - emotion_events.csv — Example CSV log of timestamped emotion events captured during testing.
  - run_ai_emotion.bat — Windows batch helper to start the client using the repository .venv.


## Quick description ![quick-desc](https://img.shields.io/badge/description-quick-blue)
The ESP32 device serves a multipart MJPEG stream at http://<ESP32_IP>:81/stream and a health JSON at /health. The Python client reads frames from the stream, optionally resizes them, passes them to th[...] 

## Requirements ![requirements](https://img.shields.io/badge/requirements-green)
- Python 3.10+ (project uses type hints/annotations consistent with 3.10+)
- A Python virtual environment (recommended)
- Packages (see `sai final pt/python_client/requirements.txt`): deepface, opencv-python, tensorflow, transformers, torch, pillow, torchvision
- An ESP32-CAM flashed with the provided `esp32_cam.ino` sketch, connected to the same network as the machine running the Python client.

## ESP32-CAM (esp32_cam/esp32_cam.ino) ![esp32](https://img.shields.io/badge/ESP32--CAM-orange)
- Configure SSID and password in the sketch (`ssid`, `password`) before flashing.
- The sketch starts a simple HTTP camera server on port 81 with endpoints:
  - /stream — multipart MJPEG stream
  - /health — JSON containing ip, uptime, rssi
- After connecting, the sketch prints the Stream and Health URLs to Serial.

## Python client: setup and run (Windows) ![python-client](https://img.shields.io/badge/python-client-purple)
1. Create and activate a virtual environment from repository root:
   - py -m venv .venv
   - .venv\\Scripts\\python -m pip install -r "sai final pt\\python_client\\requirements.txt"
     (Path contains a space in this repo; use the correct path for your shell or rename the folder to avoid spaces.)

2. Edit environment variables or use the GUI:
   - CAM_URL — full URL of MJPEG stream (e.g. http://192.168.1.42:81/stream). If empty the client may attempt discovery.
   - EMOTION_BACKEND — `deepface` or `beit` (default `beit` in GUI and batch script)
   - MAX_FRAME_WIDTH — maximum width to scale frames to (default 480)
   - INFER_EVERY_N_FRAMES — integer; infer once every N frames to reduce compute (default 5)

3. Quick start (batch):
   - From repository root run: `sai final pt\\run_ai_emotion.bat [CAM_URL]`
   - The batch file checks for `.venv\\Scripts\\activate.bat` then runs `python_client\\emotion_stream.py`.

4. GUI start (Tkinter):
   - Run `python -m sai_final_pt.python_client.interface` (or run `interface.py` from the `python_client` directory).
   - The GUI will allow you to set CAM_URL, backend and parameters, then Start/Stop the client and view logs.

## BEiT CLI ![beit](https://img.shields.io/badge/BEiT-CLI-lightgrey)
- `sai final pt\\python_client\\beit_emotion.py` is a small script to classify a single image using the BEiT model used by the project.
- Example: `python beit_emotion.py path/to/image.jpg` prints the predicted emotion label.

## Notes on backends ![backends](https://img.shields.io/badge/backends-info-blue)
- deepface: uses DeepFace.analyze with `detector_backend='opencv'` and returns `dominant_emotion`. This backend can run on CPU or GPU depending on your TensorFlow/PyTorch setup.
- beit: uses a Hugging Face BEiT image classification model (`Tanneru/Facial-Emotion-Detection-FER-RAFDB-AffectNet-BEIT-Large`). The code maps model labels to normalized emotion names and returns a co[...] 

## Development & troubleshooting ![dev](https://img.shields.io/badge/development--troubleshooting-yellow)
- If the Python client fails to start, check the `.venv` activation and that dependencies are installed.
- The batch script and GUI expect a Windows environment by default; adapt scripts for Unix-like shells (activate `.venv/bin/activate` and run `python3`).
- If using BEiT, ensure you have the proper PyTorch and transformers versions; downloading the model will require network access and may need significant disk/VRAM.

## Security & privacy ![security](https://img.shields.io/badge/security--privacy-red)
- This project captures and processes facial images. Do not deploy it without explicit consent from people being recorded and comply with local laws and institutional policies.

## Contributing ![contrib](https://img.shields.io/badge/contributing-lightgrey)
- Fixes, improvements and documentation updates are welcome. If you rename the `sai final pt` folder to remove spaces, update paths in the batch/script and README accordingly.

## License ![license](https://img.shields.io/badge/license-none-lightgrey)
- Add a LICENSE file in the repository if you wish to apply an open source license. Currently no license file is included in this repository.

## Contact ![contact](https://img.shields.io/badge/contact-owner-lightgrey)
- Repository owner: sundhar1947
