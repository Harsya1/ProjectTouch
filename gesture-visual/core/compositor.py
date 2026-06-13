"""
core/compositor.py
==================
Renders every active Region's effect into the webcam frame:
  1. Crops the base frame to each region's bounding box.
  2. Delegates rendering to the matching effect class.
  3. Alpha-blends the effect output back onto the base frame,
     modulated by progress and fade-out state.
  4. Draws a thin white border around each region.

Effect instances are lazily created and cached for the lifetime
of the process (they are stateless except for per-region caches).
"""

from __future__ import annotations

from typing import Dict, List, Type

import cv2
import numpy as np
from loguru import logger

import config
from core.region import Region
from effects.base_effect import BaseEffect
from effects.sketch_portrait import SketchPortraitEffect
from effects.glitch_abstract import GlitchAbstractEffect
from effects.mosaic_grid import MosaicGridEffect
from effects.pointcloud_scan import PointCloudScanEffect


# ── Effect registry ────────────────────────────────────────────────

_EFFECT_MAP: Dict[str, Type[BaseEffect]] = {
    "sketch": SketchPortraitEffect,
    "glitch": GlitchAbstractEffect,
    "mosaic": MosaicGridEffect,
    "pointcloud": PointCloudScanEffect,
}

# Singleton instances (effects cache per-region data internally).
_effect_cache: Dict[str, BaseEffect] = {}


def _get_effect(effect_type: str) -> BaseEffect:
    """Return (and lazily create) the singleton effect for *effect_type*."""
    if effect_type not in _effect_cache:
        cls = _EFFECT_MAP.get(effect_type)
        if cls is None:
            raise ValueError(f"Unknown effect type: {effect_type!r}")
        _effect_cache[effect_type] = cls()
    return _effect_cache[effect_type]


# ── Public API ─────────────────────────────────────────────────────


def composite(base_frame: np.ndarray, regions: List[Region]) -> np.ndarray:
    """
    Composite all active regions onto a copy of *base_frame*.

    For each region:
      • Crop the base frame to the region's area.
      • Call the region's effect ``render()`` method.
      • Alpha-blend the result back, modulated by ``progress * fade_progress``.
      • Draw a thin white border.

    Returns the composited frame (a new copy — *base_frame* is not mutated).
    """
    output = base_frame.copy()
    frame_h, frame_w = output.shape[:2]

    for region in regions:
        # Clamp region bounds to the frame.
        rx = max(0, region.x)
        ry = max(0, region.y)
        rw = min(region.width, frame_w - rx)
        rh = min(region.height, frame_h - ry)
        if rw <= 0 or rh <= 0:
            continue

        # Crop the underlying webcam pixels.
        crop = output[ry:ry + rh, rx:rx + rw].copy()

        # Render the effect.
        effect = _get_effect(region.effect_type)
        rendered = effect.render(crop, region)

        # Composite alpha: combines reveal-progress and fade-out.
        alpha = region.progress * region.fade_progress
        if alpha < 1.0:
            blended = cv2.addWeighted(rendered, alpha, crop, 1.0 - alpha, 0)
        else:
            blended = rendered

        output[ry:ry + rh, rx:rx + rw] = blended

        # White border outline (the visual signature of a locked region).
        cv2.rectangle(
            output,
            (rx, ry),
            (rx + rw - 1, ry + rh - 1),
            config.BORDER_COLOR,
            config.BORDER_THICKNESS,
        )

    return output
