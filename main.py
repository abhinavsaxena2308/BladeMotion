"""
BladeMotion – Entry Point
Parses CLI arguments, generates assets, and launches the game.
"""

import argparse
import logging
import sys
import os

# ── Make sure src/ is importable regardless of CWD ───────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Asset generation (runs once if assets missing) ────────────────────────────
from src.asset_gen import generate_all_assets
generate_all_assets()

# ── MediaPipe model download (runs once if model missing) ─────────────────────
_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "assets", "hand_landmarker.task")
_MODEL_URL  = ("https://storage.googleapis.com/mediapipe-models/"
               "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task")

if not os.path.exists(_MODEL_PATH):
    import urllib.request
    print("Downloading MediaPipe hand landmarker model (~6 MB)…")
    try:
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
        print("Model downloaded successfully.")
    except Exception as e:
        print(f"WARNING: Could not download model ({e}). Camera will be disabled.")
        print("         Run with --mouse to play without webcam.")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("BladeMotion")


def main():
    parser = argparse.ArgumentParser(
        prog="BladeMotion",
        description="Fruit Ninja – Hand Tracking Edition",
    )
    parser.add_argument("--camera",     type=int, default=0,
                        help="Camera device index (default 0).")
    parser.add_argument("--mouse",      action="store_true",
                        help="Force mouse mode (disable webcam).")
    parser.add_argument("--fullscreen", action="store_true",
                        help="Launch in fullscreen mode.")
    parser.add_argument("--debug",      action="store_true",
                        help="Show hand landmarks and camera feed overlay.")
    args = parser.parse_args()

    log.info("Starting BladeMotion | camera=%d mouse=%s debug=%s",
             args.camera, args.mouse, args.debug)

    from src.game import Game
    game = Game(
        camera_index=args.camera,
        debug=args.debug,
        mouse_mode=args.mouse,
        fullscreen=args.fullscreen,
    )
    game.run()


if __name__ == "__main__":
    main()
