"""
utils/timing.py
===============
Frame-rate measurement and animation-progress helpers.

``FrameTimer`` tracks delta-time between frames and computes a
rolling FPS average.  ``clamp_progress`` is a convenience function
for advancing a region's animation progress.
"""

from __future__ import annotations

import time


class FrameTimer:
    """Tracks per-frame delta-time and a smoothed FPS counter."""

    def __init__(self) -> None:
        self._last_time: float = time.time()
        self._dt: float = 0.0
        self._fps: float = 0.0
        self._frame_count: int = 0
        self._fps_accum: float = 0.0

    def tick(self) -> float:
        """
        Call once at the start of every frame.

        Returns the elapsed time (seconds) since the previous ``tick()``
        call and updates the internal FPS estimate.
        """
        now = time.time()
        self._dt = now - self._last_time
        self._last_time = now

        # Accumulate for a 1-second rolling window.
        self._frame_count += 1
        self._fps_accum += self._dt
        if self._fps_accum >= 1.0:
            self._fps = self._frame_count / self._fps_accum
            self._frame_count = 0
            self._fps_accum = 0.0

        return self._dt

    @property
    def dt(self) -> float:
        """Most recent delta-time (seconds)."""
        return self._dt

    @property
    def fps(self) -> float:
        """Smoothed frames-per-second estimate (updated every ~1 s)."""
        return self._fps


def clamp_progress(progress: float, dt: float, duration: float) -> float:
    """
    Advance *progress* by ``dt / duration`` and clamp to [0, 1].

    Parameters
    ----------
    progress : float
        Current progress value.
    dt : float
        Time elapsed since last frame (seconds).
    duration : float
        Total animation duration (seconds).  0 → immediately returns 1.
    """
    if duration <= 0:
        return 1.0
    return min(1.0, progress + dt / duration)
