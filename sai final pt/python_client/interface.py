import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk


class EmotionClientInterface:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("ESP32 Emotion Client Interface")
        self.root.geometry("640x360")

        self.process: subprocess.Popen | None = None

        self.cam_url_var = tk.StringVar(value="")
        self.backend_var = tk.StringVar(value="beit")
        self.max_width_var = tk.StringVar(value="480")
        self.infer_every_var = tk.StringVar(value="5")
        self.status_var = tk.StringVar(value="Idle")

        self._build_ui()
        self.root.after(100, self.start_client)

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="ESP32 Stream URL").grid(row=0, column=0, sticky="w")
        ttk.Entry(main, textvariable=self.cam_url_var, width=70).grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 8))

        ttk.Label(main, text="Emotion Backend").grid(row=2, column=0, sticky="w")
        backend = ttk.Combobox(main, textvariable=self.backend_var, values=["deepface", "beit"], state="readonly", width=20)
        backend.grid(row=3, column=0, sticky="w", pady=(0, 8))

        ttk.Button(main, text="Start", command=self.start_client).grid(row=3, column=1, padx=6, sticky="w")
        ttk.Button(main, text="Stop", command=self.stop_client).grid(row=3, column=2, sticky="w")

        ttk.Label(main, text="Max Frame Width").grid(row=4, column=0, sticky="w")
        ttk.Entry(main, textvariable=self.max_width_var, width=12).grid(row=5, column=0, sticky="w", pady=(0, 8))

        ttk.Label(main, text="Infer Every N Frames").grid(row=4, column=1, sticky="w")
        ttk.Entry(main, textvariable=self.infer_every_var, width=12).grid(row=5, column=1, sticky="w", pady=(0, 8))

        ttk.Label(main, text="Status").grid(row=6, column=0, sticky="w")
        ttk.Label(main, textvariable=self.status_var).grid(row=7, column=0, columnspan=3, sticky="w")

        ttk.Label(main, text="Logs").grid(row=8, column=0, sticky="w", pady=(8, 0))
        self.log_box = tk.Text(main, height=10)
        self.log_box.grid(row=9, column=0, columnspan=3, sticky="nsew")

        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=0)
        main.columnconfigure(2, weight=0)
        main.rowconfigure(9, weight=1)

    def _append_log(self, text: str) -> None:
        self.log_box.insert(tk.END, text)
        self.log_box.see(tk.END)

    def start_client(self) -> None:
        if self.process and self.process.poll() is None:
            self.status_var.set("Client already running")
            return

        project_root = Path(__file__).resolve().parents[1]
        script_path = project_root / "python_client" / "emotion_stream.py"
        python_exe = project_root / ".venv" / "Scripts" / "python.exe"

        env = os.environ.copy()
        env["CAM_URL"] = self.cam_url_var.get().strip()
        env["EMOTION_BACKEND"] = self.backend_var.get().strip().lower()
        env["MAX_FRAME_WIDTH"] = self.max_width_var.get().strip()
        env["INFER_EVERY_N_FRAMES"] = self.infer_every_var.get().strip()

        cmd = [str(python_exe), str(script_path)]
        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=str(project_root),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except Exception as exc:
            self.status_var.set(f"Launch failed: {type(exc).__name__}")
            self._append_log(f"Launch failed: {exc}\n")
            return

        self.status_var.set("Running")
        self._append_log("Started client\n")

        thread = threading.Thread(target=self._read_output, daemon=True)
        thread.start()

    def _read_output(self) -> None:
        if not self.process or not self.process.stdout:
            return
        for line in self.process.stdout:
            self.root.after(0, self._append_log, line)

        code = self.process.poll()
        self.root.after(0, self.status_var.set, f"Stopped (exit code {code})")

    def stop_client(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.status_var.set("Stopping...")
        else:
            self.status_var.set("No running client")


def main() -> None:
    root = tk.Tk()
    app = EmotionClientInterface(root)
    root.protocol("WM_DELETE_WINDOW", app.stop_client)
    root.mainloop()


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        try:
            from ctypes import windll

            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    main()
