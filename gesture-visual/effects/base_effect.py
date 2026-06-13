"""
effects/base_effect.py
======================
Abstract interface that every visual effect must implement.

Contract
--------
``render(frame, region) -> np.ndarray``

  * ``frame``  — BGR crop of the webcam feed for the region's area
                 (shape: ``region.height x region.width x 3``).
  * ``region`` — The owning ``Region`` dataclass instance (provides
                 ``id``, ``progress``, etc.).
  * Returns a BGR image of the **same shape** as *frame*.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from core.region import Region


class BaseEffect(ABC):
    """Abstract base class for all generative visual effects."""

    @abstractmethod
    def render(self, frame: np.ndarray, region: Region) -> np.ndarray:
        """
        Render the effect for one frame inside a region.

        Must return an image with the same height, width, and dtype
        as *frame* (BGR ``uint8``).
        """
        ...
