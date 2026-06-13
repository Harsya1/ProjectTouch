"""
effects/glitch_abstract.py
===========================
Abstract glitch-art effect combining three techniques:

1. **RGB channel split & shift** — Each colour channel (B, G, R) is
   independently rolled horizontally by a small random offset that
   slowly oscillates with time, creating chromatic aberration.

2. **Row displacement** — Random horizontal bands are shifted laterally,
   simulating pixel-sorting / data-mosh artefacts.

3. **Block noise** — Solid-colour rectangles (green, blue, pink, yellow)
   are composited at seeded-random positions with time-varying opacity.

All random state is seeded from ``region.id`` so the visual is stable
per region but evolves slowly via ``time.time()`` modulation.
"""

from __future__ import annotations

import time

import cv2
import numpy as np

import config
from core.region import Region
from effects.base_effect import BaseEffect


# Palette of noise-block colours (BGR).
_BLOCK_COLOURS = [
    (100, 220, 80),     # green
    (220, 80, 100),     # pink
    (80, 180, 255),     # blue
    (255, 255, 80),     # yellow
    (255, 100, 200),    # magenta
    (80, 255, 200),     # cyan-green
]


class GlitchAbstractEffect(BaseEffect):
    """RGB-split + displacement + colour-block glitch effect."""

    def render(self, frame: np.ndarray, region: Region) -> np.ndarray:
        h, w = frame.shape[:2]
        result = frame.copy()

        # Slow oscillation factor — keeps the effect "alive" without
        # being frantic.
        t = time.time()
        slow_t = t * 0.3

        # ── 1. RGB channel split ───────────────────────────────────
        rng_shift = np.random.RandomState(region.id)
        shift_r = int(
            rng_shift.randint(-config.GLITCH_MAX_SHIFT, config.GLITCH_MAX_SHIFT + 1)
            + np.sin(slow_t) * 5
        )
        shift_g = int(
            rng_shift.randint(-config.GLITCH_MAX_SHIFT, config.GLITCH_MAX_SHIFT + 1)
            + np.cos(slow_t * 0.7) * 3
        )
        shift_b = int(
            rng_shift.randint(-config.GLITCH_MAX_SHIFT, config.GLITCH_MAX_SHIFT + 1)
            + np.sin(slow_t * 1.3) * 4
        )

        b, g, r = cv2.split(result)
        r = np.roll(r, shift_r, axis=1)
        g = np.roll(g, shift_g, axis=1)
        b = np.roll(b, shift_b, axis=1)
        result = cv2.merge([b, g, r])

        # ── 2. Row displacement ────────────────────────────────────
        rng_row = np.random.RandomState(region.id + 500)
        num_bands = rng_row.randint(3, 8)
        for _ in range(num_bands):
            row = rng_row.randint(0, max(1, h))
            thickness = rng_row.randint(1, max(2, h // 20))
            shift = rng_row.randint(-20, 21) + int(
                np.sin(slow_t + row * 0.1) * 8
            )
            y_end = min(row + thickness, h)
            result[row:y_end] = np.roll(result[row:y_end], shift, axis=1)

        # ── 3. Colour-block noise ──────────────────────────────────
        rng_block = np.random.RandomState(region.id + 1000)
        # Scale number of visible blocks by progress for a reveal effect.
        num_blocks = int(config.GLITCH_NUM_BLOCKS * region.progress)
        for _ in range(num_blocks):
            bx = rng_block.randint(0, max(1, w - config.GLITCH_BLOCK_MAX_SIZE))
            by = rng_block.randint(0, max(1, h - config.GLITCH_BLOCK_MAX_SIZE))
            bw = rng_block.randint(5, config.GLITCH_BLOCK_MAX_SIZE + 1)
            bh = rng_block.randint(5, config.GLITCH_BLOCK_MAX_SIZE + 1)
            colour = _BLOCK_COLOURS[
                rng_block.randint(0, len(_BLOCK_COLOURS))
            ]

            bx_end = min(bx + bw, w)
            by_end = min(by + bh, h)
            overlay = result.copy()
            overlay[by:by_end, bx:bx_end] = colour

            # Slowly oscillating opacity per block.
            alpha = 0.4 + 0.2 * np.sin(slow_t + bx * 0.05)
            result = cv2.addWeighted(overlay, alpha, result, 1.0 - alpha, 0)

        return result
