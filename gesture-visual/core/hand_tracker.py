"""
core/hand_tracker.py
====================
Wrapper around MediaPipe Hands that provides:
  • process(frame)        → list of per-hand landmark sets
  • is_pinching()         → bool  (with built-in cooldown / debounce)
  • get_pinch_midpoint()  → (x, y) anchor for new region spawn
  • get_pinch_distance()  → pixel distance between thumb-tip & index-tip

Pinch is defined as the euclidean distance between landmark 4 (thumb tip)
and landmark 8 (index finger tip) falling below PINCH_THRESHOLD_PX.
"""

from __future__ import annotations

import math
import time
from typing import List, Tuple

import cv2
import mediapipe as mp
import numpy as np
from loguru import logger

import config


# MediaPipe landmark indices
_THUMB_TIP = 4
_INDEX_TIP = 8


class HandTracker:
    """Detects hands and pinch gestures from a webcam frame."""

    def __init__(
        self,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        # Timestamp of the last accepted pinch event (for cooldown).
        self._last_pinch_time: float = 0.0

    # ── Public API ─────────────────────────────────────────────────

    def process(self, frame: np.ndarray) -> List[List[Tuple[float, float, float]]]:
        """
        Run MediaPipe hand detection on *frame* (BGR).

        Returns a list (one entry per detected hand).  Each entry is a list
        of 21 (x_px, y_px, z) tuples — the hand landmarks scaled to pixel
        coordinates.
        """
        h, w = frame.shape[:2]
        # MediaPipe expects RGB input.
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._hands.process(rgb)

        if not results.multi_hand_landmarks:
            return []

        landmarks_list: List[List[Tuple[float, float, float]]] = []
        for hand_lm in results.multi_hand_landmarks:
            scaled: List[Tuple[float, float, float]] = []
            for lm in hand_lm.landmark:
                # Normalised coords (0-1) → pixel coords.
                scaled.append((lm.x * w, lm.y * h, lm.z))
            landmarks_list.append(scaled)
        return landmarks_list

    def is_pinching(
        self,
        landmarks: List[Tuple[float, float, float]],
        frame_w: int | None = None,
        frame_h: int | None = None,
    ) -> bool:
        """
        Return True when the hand described by *landmarks* is pinching
        **and** the global cooldown has elapsed since the last accepted
        pinch.

        The cooldown is enforced *inside* this method so that the caller
        doesn't need to manage debouncing.
        """
        if frame_w is None:
            frame_w = config.FRAME_WIDTH
        if frame_h is None:
            frame_h = config.FRAME_HEIGHT

        dist = self.get_pinch_distance(landmarks, frame_w, frame_h)

        if dist < config.PINCH_THRESHOLD_PX:
            now = time.time()
            if now - self._last_pinch_time >= config.PINCH_COOLDOWN_SEC:
                self._last_pinch_time = now
                logger.debug(f"Pinch accepted  dist={dist:.1f}px")
                return True
        return False

    @staticmethod
    def get_pinch_distance(
        landmarks: List[Tuple[float, float, float]],
        frame_w: int,
        frame_h: int,
    ) -> float:
        """
        Euclidean distance (in pixels) between thumb tip (landmark 4)
        and index finger tip (landmark 8).
        """
        thumb = landmarks[_THUMB_TIP]
        index = landmarks[_INDEX_TIP]
        dx = thumb[0] - index[0]
        dy = thumb[1] - index[1]
        return math.hypot(dx, dy)

    @staticmethod
    def get_pinch_midpoint(
        landmarks: List[Tuple[float, float, float]],
    ) -> Tuple[int, int]:
        """
        Midpoint between thumb tip and index tip — used as the anchor
        position for spawning a new Region.
        """
        thumb = landmarks[_THUMB_TIP]
        index = landmarks[_INDEX_TIP]
        mx = (thumb[0] + index[0]) / 2.0
        my = (thumb[1] + index[1]) / 2.0
        return (int(mx), int(my))

    # ── Cleanup ────────────────────────────────────────────────────

    def release(self) -> None:
        """Release the underlying MediaPipe resources."""
        self._hands.close()
