import cv2
import time
import csv
import os
import re
import socket
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

from emotion_module import EmotionAnalyzer

# Set CAM_URL env var to use a specific ESP32 stream URL.
# If unset, the script auto-discovers the ESP32-CAM on the local network.
CAM_URL = os.getenv("CAM_URL", "")
EMOTION_BACKEND = os.getenv("EMOTION_BACKEND", "deepface")
MAX_FRAME_WIDTH = int(os.getenv("MAX_FRAME_WIDTH", "640"))
INFER_EVERY_N_FRAMES = max(1, int(os.getenv("INFER_EVERY_N_FRAMES", "3")))
STREAM_TIMEOUT_MSEC = int(os.getenv("STREAM_TIMEOUT_MSEC", "5000"))
LOG_FILE = Path("emotion_events.csv")


def get_quote(emotion: str) -> str:
    return {
        "happy": "Keep smiling",
        "sad": "Stay strong",
        "angry": "Relax",
        "fear": "You are safe",
        "surprise": "Stay curious",
        "neutral": "Stay focused",
    }.get(emotion, "Stay focused")


def draw_face_box(frame, region: dict[str, int] | None) -> None:
    if not region:
        return
    x = region["x"]
    y = region["y"]
    w = region["w"]
    h = region["h"]
    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 2)


def initialize_log_file(path: Path) -> None:
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "emotion", "confidence"])


def log_event(path: Path, emotion: str, confidence: float) -> None:
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            emotion,
            f"{confidence:.2f}",
        ])


def get_local_prefix() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        local_ip = sock.getsockname()[0]
    finally:
        sock.close()
    return ".".join(local_ip.split(".")[:3])


def hosts_from_arp(prefix: str) -> list:
    try:
        output = subprocess.check_output(["arp", "-a"], text=True, encoding="utf-8", errors="ignore")
    except Exception:
        return []

    ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", output)
    hosts = []
    for ip in ips:
        if ip.startswith(prefix + "."):
            try:
                host = int(ip.split(".")[-1])
            except ValueError:
                continue
            if 1 < host < 255:
                hosts.append(host)
    return sorted(set(hosts))


def is_stream_endpoint(url: str, timeout: float = 0.25) -> bool:
    try:
        request = Request(url, method="GET")
        with urlopen(request, timeout=timeout) as response:
            content_type = (response.headers.get("Content-Type") or "").lower()
            return "multipart" in content_type or "image/jpeg" in content_type
    except Exception:
        return False


def build_stream_candidates(camera_url: str) -> list[str]:
    candidate_urls: list[str] = []
    normalized = camera_url.strip().rstrip("/")

    if normalized.endswith("/stream"):
        base = normalized[:-7].rstrip("/")
        candidate_urls.extend([
            normalized,
            f"{base}/stream",
            f"{base}/",
            base,
        ])
    else:
        candidate_urls.extend([
            normalized,
            f"{normalized}/stream",
        ])

    if normalized.startswith("http://") or normalized.startswith("https://"):
        without_scheme = normalized.split("://", 1)[1]
        host_only = without_scheme.split("/", 1)[0]
        candidate_urls.extend([
            f"http://{host_only}:81/stream",
            f"http://{host_only}:80/stream",
            f"http://{host_only}:81",
            f"http://{host_only}:80",
        ])

    deduped: list[str] = []
    seen: set[str] = set()
    for url in candidate_urls:
        if url and url not in seen:
            seen.add(url)
            deduped.append(url)
    return deduped


def open_stream_capture(camera_url: str) -> cv2.VideoCapture:
    candidates = build_stream_candidates(camera_url)
    last_capture = None

    ffmpeg_options = os.getenv("OPENCV_FFMPEG_CAPTURE_OPTIONS")
    if not ffmpeg_options:
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
            f"rw_timeout;{STREAM_TIMEOUT_MSEC * 1000}|timeout;{STREAM_TIMEOUT_MSEC}"
        )

    for candidate in candidates:
        print(f"Trying stream: {candidate}")
        capture = cv2.VideoCapture(candidate)
        try:
            capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        for prop_name in ("CAP_PROP_OPEN_TIMEOUT_MSEC", "CAP_PROP_READ_TIMEOUT_MSEC"):
            prop_id = getattr(cv2, prop_name, None)
            if prop_id is not None:
                try:
                    capture.set(prop_id, STREAM_TIMEOUT_MSEC)
                except Exception:
                    pass
        last_capture = capture
        if capture.isOpened():
            if candidate != camera_url:
                print(f"Using fallback stream: {candidate}")
            return capture

    if last_capture is not None:
        last_capture.release()

    raise RuntimeError(
        "Unable to open ESP32 stream. Check the IP, Wi-Fi network, and whether the camera server is running."
    )


def resize_for_speed(frame, max_width: int):
    if max_width <= 0:
        return frame

    height, width = frame.shape[:2]
    if width <= max_width:
        return frame

    ratio = max_width / float(width)
    new_height = max(1, int(height * ratio))
    return cv2.resize(frame, (max_width, new_height), interpolation=cv2.INTER_AREA)


def discover_camera_url() -> str:
    prefixes = []
    try:
        prefixes.append(get_local_prefix())
    except Exception:
        pass
    prefixes.extend(["192.168.1", "192.168.0"])

    seen = set()
    for prefix in prefixes:
        if prefix in seen:
            continue
        seen.add(prefix)

        arp_hosts = hosts_from_arp(prefix)
        sweep_hosts = [h for h in range(2, 255) if h not in arp_hosts]
        for host in arp_hosts + sweep_hosts:
            candidate = f"http://{prefix}.{host}:81/stream"
            if is_stream_endpoint(candidate):
                return candidate

    raise RuntimeError("ESP32-CAM stream not found on local network")


if not CAM_URL:
    print("Discovering ESP32-CAM stream URL...")
    CAM_URL = discover_camera_url()

print(f"Using stream: {CAM_URL}")
print(f"Emotion backend: {EMOTION_BACKEND}")

cap = open_stream_capture(CAM_URL)

analyzer = EmotionAnalyzer(backend=EMOTION_BACKEND)

max_retries = 5
retry_count = 0
last_time = time.time()
last_emotion = "unknown"
inference_ms = 0.0
last_confidence = 0.0
last_region = None
frame_index = 0

initialize_log_file(LOG_FILE)

while True:
    ret, frame = cap.read()
    if not ret:
        retry_count += 1
        print(f"Frame read failed ({retry_count}/{max_retries}), reconnecting...")
        cap.release()
        time.sleep(1)
        try:
            cap = open_stream_capture(CAM_URL)
        except Exception:
            if retry_count >= max_retries:
                try:
                    print("Trying camera rediscovery...")
                    CAM_URL = discover_camera_url()
                    print(f"Rediscovered stream: {CAM_URL}")
                    cap = open_stream_capture(CAM_URL)
                    retry_count = 0
                except Exception:
                    print("Unable to recover stream. Exiting.")
                    break
            else:
                continue

        if not cap.isOpened():
            print("Unable to recover stream. Exiting.")
            break
        continue

    retry_count = 0
    frame_index += 1
    frame = resize_for_speed(frame, MAX_FRAME_WIDTH)

    try:
        if frame_index % INFER_EVERY_N_FRAMES == 0:
            inference_start = time.time()
            result = analyzer.analyze(frame)
            inference_ms = (time.time() - inference_start) * 1000
            emotion = result.emotion
            confidence = result.confidence
            last_region = result.region
            last_confidence = confidence

            if emotion != last_emotion:
                log_event(LOG_FILE, emotion, confidence)
                last_emotion = emotion

        emotion = last_emotion
        confidence = last_confidence
        draw_face_box(frame, last_region)

        cv2.putText(
            frame,
            f"Emotion: {emotion} ({confidence:.1f}%)",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2,
        )

        cv2.putText(
            frame,
            get_quote(emotion),
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
    except Exception as exc:
        cv2.putText(
            frame,
            f"Analyze error: {type(exc).__name__}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )

    current_time = time.time()
    elapsed = max(current_time - last_time, 1e-6)
    fps = 1.0 / elapsed
    last_time = current_time

    cv2.putText(
        frame,
        f"FPS: {fps:.1f}",
        (20, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2,
    )

    cv2.putText(
        frame,
        f"Inference: {inference_ms:.1f} ms",
        (20, 155),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2,
    )

    cv2.imshow("AI Emotion", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
