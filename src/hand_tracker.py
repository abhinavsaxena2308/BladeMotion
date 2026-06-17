"""
BladeMotion – Hand Tracker
Wraps MediaPipe Hands and exposes index-finger-tip position + velocity.
Falls back gracefully to mouse mode if no camera is available.
"""

import threading
import time
import logging
from typing import Optional, Tuple, List

import cv2
import numpy as np

log = logging.getLogger(__name__)


class HandTracker:
    """
    Runs camera capture + MediaPipe inference on a background thread.
    Main thread reads self.tip_pos (normalised 0-1) and self.landmarks.
    """

    def __init__(self, camera_index: int = 0, debug: bool = False):
        self.camera_index = camera_index
        self.debug        = debug

        self.tip_pos: Optional[Tuple[float, float]] = None   # (norm_x, norm_y)
        self.landmarks: List                         = []
        self.frame_rgb: Optional[np.ndarray]         = None  # latest camera frame (RGB)

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock    = threading.Lock()
        self._cap: Optional[cv2.VideoCapture] = None
        self._mp_hands  = None
        self._hands_obj = None

        # camera availability
        self.camera_ok  = False

    # ──────────────────────────────────────────────────────────────────────────
    def start(self) -> bool:
        """Initialise camera and start background thread. Returns True on success."""
        try:
            import mediapipe as mp
            self._mp_hands  = mp.solutions.hands
            self._hands_obj = self._mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.6,
                min_tracking_confidence=0.5,
            )
        except Exception as e:
            log.warning("MediaPipe unavailable: %s", e)
            return False

        self._cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            self._cap = cv2.VideoCapture(self.camera_index)

        if not self._cap.isOpened():
            log.warning("Camera %d not available.", self.camera_index)
            return False

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._cap.set(cv2.CAP_PROP_FPS,          30)

        self.camera_ok = True
        self._running  = True
        self._thread   = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        log.info("Hand tracker started on camera %d.", self.camera_index)
        return True

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._cap:
            self._cap.release()
        if self._hands_obj:
            self._hands_obj.close()

    # ──────────────────────────────────────────────────────────────────────────
    def _run_loop(self):
        while self._running:
            ok, frame = self._cap.read()
            if not ok:
                time.sleep(0.01)
                continue

            # mirror so it feels natural
            frame = cv2.flip(frame, 1)
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            result = self._hands_obj.process(rgb)
            rgb.flags.writeable = True

            tip  = None
            lmks = []

            if result.multi_hand_landmarks:
                hand = result.multi_hand_landmarks[0]
                lmks = hand.landmark
                # index finger tip = landmark 8
                tip  = (hand.landmark[8].x, hand.landmark[8].y)

                if self.debug:
                    import mediapipe as mp
                    mp.solutions.drawing_utils.draw_landmarks(
                        frame, hand,
                        mp.solutions.hands.HAND_CONNECTIONS,
                    )

            with self._lock:
                self.tip_pos    = tip
                self.landmarks  = lmks
                self.frame_rgb  = rgb.copy()

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
