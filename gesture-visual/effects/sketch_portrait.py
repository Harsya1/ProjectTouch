"""
effects/sketch_portrait.py
==========================
Progressive edge-based line sketch of the webcam feed inside a region.

Algorithm
---------
1. Convert crop to grayscale and apply Gaussian blur.
2. Run Canny edge detection.
3. Extract contours and sort by arc-length (longest first).
4. Progressively draw contours using ``region.progress`` (0→1) as a
   cumulative arc-length budget — lines appear gradually.
5. A fraction of contours (``SKETCH_GREEN_RATIO``) receive a green
   accent stroke instead of the default grey.

Output is rendered on a light canvas so it reads as "pencil on paper".
Contours are computed once per region and cached for subsequent frames.
"""

from __future__ import annotations

from typing import Dict, List

import cv2
import numpy as np

import config
from core.region import Region
from effects.base_effect import BaseEffect


class SketchPortraitEffect(BaseEffect):
    """Edge-based progressive sketch portrait effect."""

    def __init__(self) -> None:
        # Contour cache keyed by region.id (computed once, drawn incrementally).
        self._contour_cache: Dict[int, List[np.ndarray]] = {}

    def render(self, frame: np.ndarray, region: Region) -> np.ndarray:
        h, w = frame.shape[:2]

        # ── Edge detection ─────────────────────────────────────────
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 1.0)
        edges = cv2.Canny(gray, config.SKETCH_CANNY_LOW, config.SKETCH_CANNY_HIGH)

        # ── Contour extraction (cached per region) ─────────────────
        if region.id not in self._contour_cache:
            contours, _ = cv2.findContours(
                edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
            )
            # Draw longest contours first (visually most important).
            contours = sorted(contours, key=cv2.arcLength, reverse=True)
            self._contour_cache[region.id] = contours

        contours = self._contour_cache[region.id]

        # ── Canvas ─────────────────────────────────────────────────
        # Off-white paper background.
        canvas = np.full((h, w, 3), 245, dtype=np.uint8)

        if not contours:
            return canvas

        # Total arc-length across all contours.
        total_length = sum(cv2.arcLength(c) for c in contours)
        if total_length == 0:
            return canvas

        # How much arc-length we are allowed to draw this frame.
        target_length = total_length * region.progress

        # Seeded RNG so the green-accent selection is stable per region.
        rng = np.random.RandomState(region.id)

        drawn_length = 0.0
        for contour in contours:
            arc = cv2.arcLength(contour)
            if drawn_length + arc > target_length:
                # Partial contour — draw only the portion that fits.
                remaining = target_length - drawn_length
                if arc > 0 and remaining > 0:
                    ratio = remaining / arc
                    num_pts = max(2, int(len(contour) * ratio))
                    partial = contour[:num_pts]
                    is_accent = rng.random() < config.SKETCH_GREEN_RATIO
                    colour = (80, 180, 60) if is_accent else (80, 80, 80)
                    cv2.polylines(
                        canvas, [partial], False, colour, 1, cv2.LINE_AA
                    )
                break
            else:
                # Full contour.
                is_accent = rng.random() < config.SKETCH_GREEN_RATIO
                colour = (80, 180, 60) if is_accent else (80, 80, 80)
                cv2.polylines(
                    canvas, [contour], False, colour, 1, cv2.LINE_AA
                )
                drawn_length += arc

        return canvas
