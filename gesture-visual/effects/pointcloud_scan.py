"""
effects/pointcloud_scan.py
===========================
Point-cloud / depth-scan effect inspired by the reference frames (220-300).

The effect is composited from three layers (bottom → top):

1. **Black background** — provides contrast for the glowing particles.

2. **Starfield particles** — 200-300 fixed white dots seeded per region.
   Each dot has a random phase; opacity is modulated sinusoidally over
   time so some stars appear to "twinkle".

3. **Contour scan lines** — 15-20 horizontal polylines spanning the full
   region width.  Each line's y-coordinate is displaced by the
   Gaussian-smoothed brightness of the webcam grayscale at that x
   position, creating a "topographic" wave that follows the face shape.
   Lines are coloured cyan / green-cyan with time-varying opacity.
   A slow vertical oscillation animates the lines.

4. **Point cloud** — the webcam crop is converted to grayscale and
   downsampled to an 80×60 grid.  Each grid point whose brightness
   exceeds a threshold is rendered as a small filled circle whose
   colour interpolates from deep blue (dim) to bright cyan (bright),
   simulating a pseudo-depth-map point cloud.  Points are revealed
   progressively via ``region.progress``.

Since no real depth sensor is available, brightness serves as a
proxy for depth (brighter = closer).
"""

from __future__ import annotations

import time
from typing import Dict

import cv2
import numpy as np

import config
from core.region import Region
from effects.base_effect import BaseEffect


class PointCloudScanEffect(BaseEffect):
    """Cyan point cloud with contour scan lines and starfield."""

    def __init__(self) -> None:
        # Fixed star positions per region (seeded).
        self._star_cache: Dict[int, np.ndarray] = {}

    # ── Main render ────────────────────────────────────────────────

    def render(self, frame: np.ndarray, region: Region) -> np.ndarray:
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        t = time.time()

        # Layer 1: black background.
        result = np.zeros((h, w, 3), dtype=np.uint8)

        # Layer 2: starfield.
        self._draw_starfield(result, w, h, region.id, t)

        # Layer 3: contour scan lines.
        scan = self._render_scan_lines(gray, w, h, t)
        mask = scan.sum(axis=2) > 0
        result[mask] = scan[mask]

        # Layer 4: point cloud (progressive reveal).
        points = self._render_point_cloud(gray, w, h, region.progress)
        pmask = points.sum(axis=2) > 0
        result[pmask] = points[pmask]

        return result

    # ── Starfield ──────────────────────────────────────────────────

    def _get_stars(self, w: int, h: int, region_id: int) -> np.ndarray:
        """Return (N, 3) array of [x, y, phase] for fixed stars."""
        if region_id not in self._star_cache:
            rng = np.random.RandomState(region_id + 777)
            sx = rng.randint(0, max(1, w), size=config.POINTCLOUD_NUM_STARS)
            sy = rng.randint(0, max(1, h), size=config.POINTCLOUD_NUM_STARS)
            phase = rng.uniform(0, 2 * np.pi, size=config.POINTCLOUD_NUM_STARS)
            self._star_cache[region_id] = np.column_stack([sx, sy, phase])
        return self._star_cache[region_id]

    def _draw_starfield(
        self,
        canvas: np.ndarray,
        w: int,
        h: int,
        region_id: int,
        t: float,
    ) -> None:
        """Draw twinkling white dots onto *canvas* in-place."""
        stars = self._get_stars(w, h, region_id)
        # Sinusoidal blink: each star has its own phase.
        blink = np.sin(t * 2.0 + stars[:, 2]) * 0.5 + 0.5
        for i in range(len(stars)):
            sx, sy = int(stars[i, 0]), int(stars[i, 1])
            if 0 <= sx < w and 0 <= sy < h:
                val = int(80 + 175 * blink[i])
                canvas[sy, sx] = (val, val, val)

    # ── Contour scan lines ─────────────────────────────────────────

    def _render_scan_lines(
        self,
        gray: np.ndarray,
        w: int,
        h: int,
        t: float,
    ) -> np.ndarray:
        """
        Draw horizontal contour lines displaced by the smoothed
        brightness profile of the webcam frame.
        """
        result = np.zeros((h, w, 3), dtype=np.uint8)
        num_lines = config.POINTCLOUD_NUM_SCAN_LINES

        # Heavy blur for smooth displacement curves.
        smoothed = cv2.GaussianBlur(gray, (21, 21), 5.0)

        # Slow vertical oscillation for a "scanning" animation.
        anim_offset = np.sin(t * 0.5) * 10

        for i in range(num_lines):
            base_y = int(h * (i + 0.5) / num_lines + anim_offset)

            # Build polyline points: each x → displaced y.
            xs = np.arange(0, w, 2)
            sample_y = np.clip(base_y, 0, smoothed.shape[0] - 1)
            brightness_row = smoothed[sample_y, np.clip(xs, 0, smoothed.shape[1] - 1)]

            # Map brightness (0-255) to vertical displacement (-15…+15 px).
            displacement = (brightness_row.astype(np.float64) - 128) / 128.0 * 15
            ys = np.clip(base_y + displacement.astype(int), 0, h - 1)

            pts = np.column_stack([xs, ys]).reshape((-1, 1, 2)).astype(np.int32)

            if len(pts) >= 2:
                # Time-varying opacity per line.
                alpha = 0.5 + 0.3 * np.sin(t * 0.8 + i * 0.5)
                colour = (
                    int(200 * alpha),  # B
                    int(255 * alpha),  # G
                    int(100 * alpha),  # R
                )
                cv2.polylines(result, [pts], False, colour, 1, cv2.LINE_AA)

        return result

    # ── Point cloud ────────────────────────────────────────────────

    def _render_point_cloud(
        self,
        gray: np.ndarray,
        w: int,
        h: int,
        progress: float,
    ) -> np.ndarray:
        """
        Render a grid of coloured dots where brightness > threshold.
        Colour ramps from deep blue (dim) to bright cyan (bright).
        """
        gx = config.POINTCLOUD_GRID_X
        gy = config.POINTCLOUD_GRID_Y
        result = np.zeros((h, w, 3), dtype=np.uint8)

        cell_w = max(1, w / gx)
        cell_h = max(1, h / gy)

        # Downsample grayscale to the point-grid resolution.
        downsampled = cv2.resize(gray, (gx, gy), interpolation=cv2.INTER_AREA)

        threshold = 40  # skip very dark pixels (background)
        num_points = int(gx * gy * progress)  # progressive reveal
        count = 0

        for iy in range(gy):
            for ix in range(gx):
                if count >= num_points:
                    break
                brightness = int(downsampled[iy, ix])
                if brightness < threshold:
                    count += 1
                    continue

                # Centre of this grid cell in output pixels.
                px = int(ix * cell_w + cell_w / 2)
                py = int(iy * cell_h + cell_h / 2)
                if px >= w or py >= h:
                    count += 1
                    continue

                # Normalised brightness for colour interpolation.
                norm = (brightness - threshold) / max(1, 255 - threshold)

                # BGR colour: deep blue → bright cyan.
                blue = int(255 * norm)
                green = int(200 * norm + 55)
                red = int(80 * norm)
                colour = (blue, green, red)

                radius = max(1, int(2 * norm))
                cv2.circle(result, (px, py), radius, colour, -1, cv2.LINE_AA)
                count += 1
            if count >= num_points:
                break

        return result
