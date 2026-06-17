"""
BladeMotion – Hand Tracker  (MediaPipe 0.10+ Tasks API)
========================================================
MediaPipe 0.10+ removed mp.solutions in favour of mp.tasks.
This module uses the new HandLandmarker Tasks API with a LIVE_STREAM
running mode so inference happens on the camera thread and results
are delivered via callback — zero blocking on the main thread.

Falls back to mouse mode gracefully if camera or model is unavailable.
"""

import os
import threading
import time
import logging
from typing import Optional, Tuple, List

import cv2
import numpy as np

log = logging.getLogger(__name__)

# Path to the bundled hand landmarker model
_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "hand_landmarker.task",
)


class HandTracker:
    """
    Runs camera capture + MediaPipe HandLandmarker on a background thread.
    Main thread reads self.tip_pos (normalised 0-1) and self.landmarks.
    """

    def __init__(self, camera_index: int = 0, debug: bool = False):
        self.camera_index = camera_index
        self.debug        = debug

        self.tip_pos: Optional[Tuple[float, float]] = None   # (norm_x, norm_y)
        self.landmarks: list                         = []
        self.frame_rgb: Optional[np.ndarray]         = None  # latest camera frame (RGB)

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock    = threading.Lock()
        self._cap: Optional[cv2.VideoCapture] = None
        self._detector = None
        self._frame_ts = 0          # monotonic timestamp in ms for Tasks API

        self.camera_ok = False

    # ──────────────────────────────────────────────────────────────────────────
    def start(self) -> bool:
        """Initialise camera and MediaPipe detector. Returns True on success."""
        if not os.path.exists(_MODEL_PATH):
            log.warning(
                "Hand landmarker model not found at: %s\n"
                "Run: python -c \"import urllib.request; "
                "urllib.request.urlretrieve("
                "'https://storage.googleapis.com/mediapipe-models/"
                "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task',"
                " 'assets/hand_landmarker.task')\"",
                _MODEL_PATH,
            )
            return False

        try:
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision as mp_vision

            base_options = mp_python.BaseOptions(model_asset_path=_MODEL_PATH)
            options = mp_vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=mp_vision.RunningMode.LIVE_STREAM,
                num_hands=1,
                min_hand_detection_confidence=0.55,
                min_hand_presence_confidence=0.55,
                min_tracking_confidence=0.50,
                result_callback=self._on_result,
            )
            self._detector = mp_vision.HandLandmarker.create_from_options(options)
            log.info("HandLandmarker detector created (Tasks API).")
        except Exception as e:
            log.warning("MediaPipe Tasks API unavailable: %s", e)
            return False

        # Open camera
        self._cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            self._cap = cv2.VideoCapture(self.camera_index)

        if not self._cap.isOpened():
            log.warning("Camera %d not available.", self.camera_index)
            if self._detector:
                self._detector.close()
            return False

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._cap.set(cv2.CAP_PROP_FPS,          30)

        self.camera_ok = True
        self._running  = True
        self._thread   = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        log.info("Hand tracker started (camera %d, Tasks API).", self.camera_index)
        return True

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._cap:
            self._cap.release()
        if self._detector:
            self._detector.close()

    # ──────────────────────────────────────────────────────────────────────────
    def _on_result(self, result, mp_image, timestamp_ms: int):
        """Callback fired by MediaPipe on the detection thread."""
        tip  = None
        lmks = []

        if result.hand_landmarks:
            hand = result.hand_landmarks[0]   # list of NormalizedLandmark
            lmks = hand
            # index finger tip = landmark 8
            tip  = (hand[8].x, hand[8].y)

        with self._lock:
            self.tip_pos   = tip
            self.landmarks = lmks

    def _run_loop(self):
        from mediapipe import Image as MpImage, ImageFormat

        while self._running:
            ok, frame = self._cap.read()
            if not ok:
                time.sleep(0.01)
                continue

            # Mirror so movement feels natural
            frame = cv2.flip(frame, 1)
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Store camera frame for debug overlay
            with self._lock:
                self.frame_rgb = rgb.copy()

            # Build MediaPipe image and run async detection
            mp_img = MpImage(image_format=ImageFormat.SRGB, data=rgb)
            self._frame_ts += 1          # must be strictly increasing (ms)
            try:
                self._detector.detect_async(mp_img, self._frame_ts)
            except Exception as e:
                log.debug("detect_async error: %s", e)

            # ~30 FPS cadence
            time.sleep(0.033)

    # ──────────────────────────────────────────────────────────────────────────
    def get_tip(self) -> Optional[Tuple[float, float]]:
        with self._lock:
            return self.tip_pos

    def get_frame(self) -> Optional[np.ndarray]:
        with self._lock:
            return self.frame_rgb

    def get_landmarks(self):
        with self._lock:
            return list(self.landmarks)

    # ──────────────────────────────────────────────────────────────────────────
    @staticmethod
    def list_cameras(max_test: int = 5) -> List[int]:
        """Return indices of available cameras."""
        found = []
        for i in range(max_test):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                found.append(i)
                cap.release()
        return found
