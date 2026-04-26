"""
run.py  —  DreamScape launcher
───────────────────────────────
Starts ComfyUI in the background, waits until it's ready,
then runs the full Dreamscape pipeline.

Usage:
    python run.py

Stop: Ctrl+C  (kills both ComfyUI and Dreamscape)
"""
import subprocess
import sys
import os
import time
import requests
import signal

# ── Config ────────────────────────────────────────────────────────────
COMFYUI_DIR    = r"C:\Users\karth\ComfyUI"
COMFYUI_VENV   = os.path.join(COMFYUI_DIR, "venv", "Scripts", "python.exe")
COMFYUI_MAIN   = os.path.join(COMFYUI_DIR, "main.py")
COMFYUI_URL    = "http://127.0.0.1:8188"
COMFYUI_FLAGS  = ["--force-fp16", "--cpu-vae", "--novram"]

DREAMSCAPE_DIR  = os.path.dirname(os.path.abspath(__file__))
DREAMSCAPE_MAIN = os.path.join(DREAMSCAPE_DIR, "backend", "main.py")

COMFYUI_READY_TIMEOUT = 120   # seconds to wait for ComfyUI to boot


def wait_for_comfyui(timeout: int = COMFYUI_READY_TIMEOUT) -> bool:
    """Poll ComfyUI /system_stats until it responds or timeout."""
    print(f"[run.py] Waiting for ComfyUI to be ready (max {timeout}s)...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{COMFYUI_URL}/system_stats", timeout=2)
            if r.status_code == 200:
                print("[run.py] ✅ ComfyUI is ready!")
                return True
        except Exception:
            pass
        time.sleep(3)
        elapsed = int(time.time() - start)
        print(f"[run.py]   ...waiting ({elapsed}s)", end="\r")
    return False


def main():
    comfyui_proc   = None
    dreamscape_proc = None

    try:
        # ── Step 1: Start ComfyUI ─────────────────────────────────
        print("[run.py] Starting ComfyUI...")
        print(f"[run.py]   Python : {COMFYUI_VENV}")
        print(f"[run.py]   Script : {COMFYUI_MAIN}")
        print(f"[run.py]   Flags  : {' '.join(COMFYUI_FLAGS)}")

        comfyui_proc = subprocess.Popen(
            [COMFYUI_VENV, COMFYUI_MAIN] + COMFYUI_FLAGS,
            cwd=COMFYUI_DIR,
            # Show ComfyUI logs in same terminal so you can see GPU errors
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        print(f"[run.py] ComfyUI started (PID {comfyui_proc.pid})")

        # ── Step 2: Stream ComfyUI logs while waiting ─────────────
        import threading

        def stream_comfyui_logs():
            for line in comfyui_proc.stdout:
                print(f"[ComfyUI] {line}", end="")

        log_thread = threading.Thread(target=stream_comfyui_logs, daemon=True)
        log_thread.start()

        # ── Step 3: Wait until ComfyUI HTTP server is up ──────────
        ready = wait_for_comfyui()
        if not ready:
            print("[run.py] ❌ ComfyUI did not start in time. Check logs above.")
            sys.exit(1)

        # ── Step 4: Run Dreamscape pipeline ───────────────────────
        print("\n[run.py] Starting Dreamscape pipeline...")
        print(f"[run.py]   Script : {DREAMSCAPE_MAIN}")
        print(f"[run.py]   CWD    : {DREAMSCAPE_DIR}\n")

        dreamscape_proc = subprocess.Popen(
            [sys.executable, DREAMSCAPE_MAIN],
            cwd=DREAMSCAPE_DIR,
        )

        # Wait for Dreamscape to finish
        dreamscape_proc.wait()
        print(f"\n[run.py] Dreamscape exited with code {dreamscape_proc.returncode}")

    except KeyboardInterrupt:
        print("\n[run.py] Interrupted by user.")

    finally:
        # ── Cleanup: kill ComfyUI ─────────────────────────────────
        if comfyui_proc and comfyui_proc.poll() is None:
            print("[run.py] Stopping ComfyUI...")
            comfyui_proc.terminate()
            try:
                comfyui_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                comfyui_proc.kill()
            print("[run.py] ComfyUI stopped.")

        if dreamscape_proc and dreamscape_proc.poll() is None:
            dreamscape_proc.terminate()


if __name__ == "__main__":
    main()
