"""
core/region.py
==============
Dataclass describing a single locked generative-art region on the canvas.

Each Region stores:
  • Spatial information (x, y, width, height)
  • Which visual effect to render (effect_type)
  • Animation state (progress 0→1, fading_out flag)
  • An optional frame_buffer for caching rendered output
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class Region:
    """
    Represents one locked rectangular area on the canvas that displays
    a generative visual effect.

    Attributes
    ----------
    id : int
        Unique monotonically-increasing identifier.  Also used to seed
        per-region random state so each region looks visually distinct.
    x, y : int
        Top-left corner in pixel coordinates.
    width, height : int
        Dimensions of the region in pixels.
    effect_type : str
        One of ``config.EFFECT_TYPES`` — determines which effect class
        renders inside this region.
    locked : bool
        Always True after creation (regions never move once spawned).
    created_at : float
        ``time.time()`` timestamp at spawn time.
    frame_buffer : np.ndarray | None
        Optional cache for the most recent rendered output.
    progress : float
        Animation progress in [0.0, 1.0].  Effects use this to
        progressively reveal their visuals.
    fading_out : bool
        When True the compositor starts a fade-out transition before
        the region is removed from the manager's list.
    fade_progress : float
        Goes from 1.0 → 0.0 during fade-out.  Multiplied with the
        effect's alpha in the compositor.
    """

    id: int
    x: int
    y: int
    width: int
    height: int
    effect_type: str          # "sketch" | "glitch" | "mosaic" | "pointcloud"
    locked: bool = True
    created_at: float = 0.0
    frame_buffer: Optional[np.ndarray] = field(default=None, repr=False)
    progress: float = 0.0
    fading_out: bool = False
    fade_progress: float = 1.0
