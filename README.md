# ESP32-CAM Facial Emotion Detection

This repository contains a small end-to-end project that captures a video stream from an ESP32-CAM and runs real-time facial emotion detection using a Python client. Two emotion backends are suppor[...]

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

Visuals
-------
Add visual assets to `docs/visuals/` and the README will show them inline. Suggested files:
- docs/visuals/block_diagram.svg — system block diagram (ESP32-CAM -> Python client -> emotion backend -> UI/logs)
- docs/visuals/wiring_diagram.svg — simple ESP32-CAM pin wiring to camera and power
- docs/visuals/sample_output.png — screenshot or GIF of the GUI showing live stream / emotion events

Example embeds (place these where you want visuals to appear in the README):

![System block diagram](docs/visuals/block_diagram.svg)

![ESP32-CAM wiring](docs/visuals/wiring_diagram.svg)

![Example GUI output](docs/visuals/sample_output.png)

How to produce the sample_output.png / GIF:
- Start the GUI (`python -m sai_final_pt.python_client.interface`), open the log pane and start the stream.
- On Windows: use Snipping Tool or Win+G to capture; on macOS: Cmd+Shift+4; on Linux: use Flameshot or gnome-screenshot.
- For a short GIF of the stream use: Peek (Linux), LICEcap (Windows/macOS), or ffmpeg:
  - ffmpeg example to record 10s of the screen region: `ffmpeg -f gdigrab -framerate 15 -t 10 -i desktop -vf "crop=640:480:100:100" docs/visuals/sample_output.mp4`
  - Convert mp4 to gif: `ffmpeg -i docs/visuals/sample_output.mp4 -vf "fps=15,scale=640:-1:flags=lanczos" -t 10 docs/visuals/sample_output.gif`

Notes:
- Keep visuals in `docs/visuals/` so they are grouped and easy to update.
- SVG files are recommended for diagrams (small, editable, crisp at any size). PNG/GIF for screenshots or short animations.

Quick description
The ESP32 device serves a multipart MJPEG stream at http://<ESP32_IP>:81/stream and a health JSON at /health. The Python client reads frames from the stream, optionally resizes them, passes them t[...]

Requirements
- Python 3.10+ (project uses type hints/annotations consistent with 3.10+)
- A Python virtual environment (recommended)
- Packages (see `sai final pt/python_client/requirements.txt`): deepface, opencv-python, tensorflow, transformers, torch, pillow, torchvision
- An ESP32-CAM flashed with the provided `esp32_cam.ino` sketch, connected to the same network as the machine running the Python client.

ESP32-CAM (esp32_cam/esp32_cam.ino)
- Configure SSID and password in the sketch (`ssid`, `password`) before flashing.
- The sketch starts a simple HTTP camera server on port 81 with endpoints:
  - /stream — multipart MJPEG stream
  - /health — JSON containing ip, uptime, rssi
- After connecting, the sketch prints the Stream and Health URLs to Serial.

Python client: setup and run (Windows)
1. Create and activate a virtual environment from repository root:
   - py -m venv .venv
   - .venv\Scripts\python -m pip install -r "sai final pt\python_client\requirements.txt"
     (Path contains a space in this repo; use the correct path for your shell or rename the folder to avoid spaces.)

2. Edit environment variables or use the GUI:
   - CAM_URL — full URL of MJPEG stream (e.g. http://192.168.1.42:81/stream). If empty the client may attempt discovery.
   - EMOTION_BACKEND — `deepface` or `beit` (default `beit` in GUI and batch script)
   - MAX_FRAME_WIDTH — maximum width to scale frames to (default 480)
   - INFER_EVERY_N_FRAMES — integer; infer once every N frames to reduce compute (default 5)

3. Quick start (batch):
   - From repository root run: `sai final pt\run_ai_emotion.bat [CAM_URL]`
   - The batch file checks for `.venv\Scripts\activate.bat` then runs `python_client\emotion_stream.py`.

4. GUI start (Tkinter):
   - Run `python -m sai_final_pt.python_client.interface` (or run `interface.py` from the `python_client` directory).
   - The GUI will allow you to set CAM_URL, backend and parameters, then Start/Stop the client and view logs.

BEiT CLI
- `sai final pt\python_client\beit_emotion.py` is a small script to classify a single image using the BEiT model used by the project.
- Example: `python beit_emotion.py path/to/image.jpg` prints the predicted emotion label.

Notes on backends
- deepface: uses DeepFace.analyze with `detector_backend='opencv'` and returns `dominant_emotion`. This backend can run on CPU or GPU depending on your TensorFlow/PyTorch setup.
- beit: uses a Hugging Face BEiT image classification model (`Tanneru/Facial-Emotion-Detection-FER-RAFDB-AffectNet-BEIT-Large`). The code maps model labels to normalized emotion names and returns [...]

Development & troubleshooting
- If the Python client fails to start, check the `.venv` activation and that dependencies are installed.
- The batch script and GUI expect a Windows environment by default; adapt scripts for Unix-like shells (activate `.venv/bin/activate` and run `python3`).
- If using BEiT, ensure you have the proper PyTorch and transformers versions; downloading the model will require network access and may need significant disk/VRAM.

Security & privacy
- This project captures and processes facial images. Do not deploy it without explicit consent from people being recorded and comply with local laws and institutional policies.

Contributing
- Fixes, improvements and documentation updates are welcome. If you rename the `sai final pt` folder to remove spaces, update paths in the batch/script and README accordingly.

License
- Add a LICENSE file in the repository if you wish to apply an open source license. Currently no license file is included in this repository.

Contact
- Repository owner: sundhar1947
