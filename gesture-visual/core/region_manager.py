"""
core/region_manager.py
======================
Manages the full lifecycle of Region objects:
  • Spawning  — create a new region on a validated pinch event
  • Updating  — advance animation progress & handle fade-out
  • Eviction  — FIFO removal when MAX_REGIONS is exceeded

The manager also enforces the global pinch cooldown so that
rapid-fire pinches don't create duplicate regions.
"""

from __future__ import annotations

import time
from typing import List

from loguru import logger

import config
from core.region import Region


class RegionManager:
    """Owns and manages all active Region instances."""

    def __init__(self) -> None:
        self.regions: List[Region] = []
        self._next_id: int = 0
        # Round-robin pointer into config.EFFECT_TYPES.
        self._effect_index: int = 0
        # Timestamp of the last spawn (secondary cooldown guard).
        self._last_spawn_time: float = 0.0

    # ── Spawning ───────────────────────────────────────────────────

    def _next_effect_type(self) -> str:
        """Return the next effect type in the round-robin cycle."""
        effect = config.EFFECT_TYPES[self._effect_index % len(config.EFFECT_TYPES)]
        self._effect_index += 1
        return effect

    def on_pinch_detected(self, midpoint: tuple[int, int]) -> None:
        """
        Called when a pinch gesture is accepted by the HandTracker.

        Creates a new Region centred on *midpoint*, assigns it the next
        effect type, and appends it to the managed list.  If the list
        exceeds ``MAX_REGIONS``, the oldest region is marked for
        fade-out.
        """
        # Secondary cooldown guard (belt-and-suspenders with HandTracker).
        now = time.time()
        if now - self._last_spawn_time < config.PINCH_COOLDOWN_SEC:
            return
        self._last_spawn_time = now

        mx, my = midpoint
        rw = config.REGION_DEFAULT_WIDTH
        rh = config.REGION_DEFAULT_HEIGHT

        # Clamp position so region stays within the frame.
        x = max(0, mx - rw // 2)
        y = max(0, my - rh // 2)

        effect_type = self._next_effect_type()

        region = Region(
            id=self._next_id,
            x=x,
            y=y,
            width=rw,
            height=rh,
            effect_type=effect_type,
            locked=True,
            created_at=now,
            progress=0.0,
        )
        self._next_id += 1
        self.regions.append(region)

        logger.info(
            f"Spawned region #{region.id}  effect={effect_type}  "
            f"pos=({x},{y})  size={rw}x{rh}  total={len(self.regions)}"
        )

        # FIFO eviction: mark oldest region for fade-out when over limit.
        if len(self.regions) > config.MAX_REGIONS:
            for r in self.regions:
                if not r.fading_out:
                    r.fading_out = True
                    logger.debug(f"Region #{r.id} marked for fade-out")
                    break

    # ── Per-frame Update ───────────────────────────────────────────

    def update(self, dt: float) -> None:
        """
        Advance animation progress for every region and remove regions
        whose fade-out transition has completed.

        Parameters
        ----------
        dt : float
            Elapsed time since the previous frame (seconds).
        """
        # Advance progress (0 → 1) for the reveal animation.
        for region in self.regions:
            if region.progress < 1.0:
                region.progress = min(
                    1.0,
                    region.progress + dt / config.ANIMATION_DURATION_SEC,
                )

            # Drive the fade-out transition (1.0 → 0.0 over 0.5 s).
            if region.fading_out:
                region.fade_progress = max(0.0, region.fade_progress - dt / 0.5)

        # Collect fully-faded regions for removal.
        expired = [r for r in self.regions if r.fading_out and r.fade_progress <= 0.0]
        for r in expired:
            self.regions.remove(r)
            logger.debug(f"Region #{r.id} removed (fade-out complete)")
