"""
effects/mosaic_grid.py
======================
Recursive-subdivision mosaic with colour-block fill and duotone overlay.

Algorithm
---------
1. **Recursive subdivision** (quadtree-like): the region area is split
   randomly (horizontal or vertical, biased toward the longer axis)
   until ``MOSAIC_MAX_DEPTH`` or ``MOSAIC_MIN_CELL_SIZE`` is reached.
   A small probability of early termination produces a mix of large
   and small cells — the "treemap" look seen in the reference frames.

2. **Average-colour fill**: each cell is filled with the mean BGR
   colour of the corresponding webcam crop (``cv2.mean``), giving
   a pixelated but recognisable representation of the live feed.

3. **Duotone photo overlay**: once progress ≥ 0.6 the largest cell is
   replaced with a generated blue-white duotone patch, framed with a
   white border — mimicking the "focal photo" in the reference.

4. **Green accent block**: once progress ≥ 0.8 a solid green square
   appears in the bottom-right corner, matching the visual reference.

Cell layout is computed once per region and cached.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import cv2
import numpy as np

import config
from core.region import Region
from effects.base_effect import BaseEffect

# Type alias for a cell rectangle: (x, y, w, h).
_Cell = Tuple[int, int, int, int]


class MosaicGridEffect(BaseEffect):
    """Non-uniform recursive grid mosaic with duotone overlay."""

    def __init__(self) -> None:
        self._cell_cache: Dict[int, List[_Cell]] = {}
        self._duotone_cache: Dict[tuple, np.ndarray] = {}

    # ── Public render ──────────────────────────────────────────────

    def render(self, frame: np.ndarray, region: Region) -> np.ndarray:
        h, w = frame.shape[:2]

        # Build (or retrieve) the cell layout for this region.
        if region.id not in self._cell_cache:
            cells: List[_Cell] = []
            self._subdivide(0, 0, w, h, 0, region.id, cells)
            self._cell_cache[region.id] = cells

        cells = self._cell_cache[region.id]
        result = np.zeros((h, w, 3), dtype=np.uint8)

        # Progressive reveal: only fill a fraction of cells.
        num_visible = max(1, int(len(cells) * region.progress))

        largest_cell: _Cell | None = None
        largest_area = 0

        for i, (cx, cy, cw, ch) in enumerate(cells):
            if i >= num_visible:
                break

            cx_end = min(cx + cw, w)
            cy_end = min(cy + ch, h)
            if cx_end <= cx or cy_end <= cy:
                continue

            # Fill cell with average colour from the webcam crop.
            crop_cell = frame[cy:cy_end, cx:cx_end]
            if crop_cell.size > 0:
                mean_bgr = cv2.mean(crop_cell)[:3]
                result[cy:cy_end, cx:cx_end] = (
                    int(mean_bgr[0]),
                    int(mean_bgr[1]),
                    int(mean_bgr[2]),
                )

            # Thin black border between cells.
            cv2.rectangle(
                result, (cx, cy), (cx_end - 1, cy_end - 1), (0, 0, 0), 1
            )

            area = cw * ch
            if area > largest_area:
                largest_area = area
                largest_cell = (cx, cy, cw, ch)

        # ── Duotone overlay in the largest cell (progress ≥ 0.6) ──
        if region.progress >= 0.6 and largest_cell is not None:
            lcx, lcy, lcw, lch = largest_cell
            lcx_end = min(lcx + lcw, w)
            lcy_end = min(lcy + lch, h)
            pw = lcx_end - lcx
            ph = lcy_end - lcy
            if pw > 10 and ph > 10:
                duotone = self._get_duotone_patch(pw, ph, region.id)
                result[lcy:lcy_end, lcx:lcx_end] = duotone
                # White photo frame around the duotone cell.
                cv2.rectangle(
                    result,
                    (lcx, lcy),
                    (lcx_end - 1, lcy_end - 1),
                    (255, 255, 255),
                    2,
                )

        # ── Green accent block (progress ≥ 0.8) ───────────────────
        if region.progress >= 0.8:
            gx = max(0, w - 25)
            gy = max(0, h - 25)
            result[gy:h, gx:w] = (60, 180, 50)

        return result

    # ── Recursive subdivision ──────────────────────────────────────

    def _subdivide(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        depth: int,
        seed: int,
        cells: List[_Cell],
    ) -> None:
        """Recursively split the rectangle into sub-cells."""
        rng = np.random.RandomState(seed + depth * 100 + x * 7 + y * 13)

        # Termination conditions.
        if (
            depth >= config.MOSAIC_MAX_DEPTH
            or w < config.MOSAIC_MIN_CELL_SIZE * 2
            or h < config.MOSAIC_MIN_CELL_SIZE * 2
        ):
            cells.append((x, y, w, h))
            return

        # 30 % chance to stop early → produces larger cells (variety).
        if rng.random() < 0.3:
            cells.append((x, y, w, h))
            return

        # Split along the longer axis for more natural proportions.
        if w > h:
            split = int(w * rng.uniform(0.3, 0.7))
            self._subdivide(x, y, split, h, depth + 1, seed, cells)
            self._subdivide(x + split, y, w - split, h, depth + 1, seed, cells)
        else:
            split = int(h * rng.uniform(0.3, 0.7))
            self._subdivide(x, y, w, split, depth + 1, seed, cells)
            self._subdivide(x, y + split, w, h - split, depth + 1, seed, cells)

    # ── Duotone patch generator ────────────────────────────────────

    def _get_duotone_patch(
        self, pw: int, ph: int, region_id: int
    ) -> np.ndarray:
        """
        Generate (and cache) a blue-white duotone patch of size *pw*×*ph*.

        Uses a Gaussian-smoothed random noise field mapped to a
        dark-blue → light-white gradient, mimicking the reference
        "focal photo" effect.
        """
        key = (region_id, pw, ph)
        if key not in self._duotone_cache:
            rng = np.random.RandomState(region_id + 42)
            noise = rng.rand(ph, pw).astype(np.float32)
            noise = cv2.GaussianBlur(noise, (11, 11), 3.0)

            # BGR endpoints for the duotone ramp.
            dark = np.array([180, 80, 30], dtype=np.float32)     # dark blue
            light = np.array([255, 220, 180], dtype=np.float32)   # warm white

            duotone = np.zeros((ph, pw, 3), dtype=np.uint8)
            for c in range(3):
                channel = noise * (light[c] - dark[c]) + dark[c]
                duotone[:, :, c] = np.clip(channel, 0, 255).astype(np.uint8)

            self._duotone_cache[key] = duotone
        return self._duotone_cache[key]
