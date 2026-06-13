"""
utils/image_ops.py
==================
Reusable image-processing helper functions used across effects and
the compositor.  All functions assume BGR ``uint8`` images unless
otherwise noted.
"""

from __future__ import annotations

import cv2
import numpy as np


def safe_crop(
    frame: np.ndarray, x: int, y: int, w: int, h: int
) -> np.ndarray:
    """
    Crop *frame* to the rectangle ``(x, y, w, h)``, clamping to the
    frame boundaries so no IndexError can occur.
    """
    fh, fw = frame.shape[:2]
    x = max(0, min(x, fw - 1))
    y = max(0, min(y, fh - 1))
    x2 = max(0, min(x + w, fw))
    y2 = max(0, min(y + h, fh))
    return frame[y:y2, x:x2].copy()


def blend_alpha(
    fg: np.ndarray, bg: np.ndarray, alpha: float
) -> np.ndarray:
    """
    Alpha-blend *fg* over *bg* with a single scalar *alpha* in [0, 1].
    """
    alpha = max(0.0, min(1.0, alpha))
    return cv2.addWeighted(fg, alpha, bg, 1.0 - alpha, 0)


def color_quantize(frame: np.ndarray, levels: int = 8) -> np.ndarray:
    """
    Reduce the colour depth of *frame* to *levels* discrete values
    per channel (posterisation).
    """
    factor = 256 // levels
    return (frame // factor) * factor + factor // 2


def to_duotone(
    gray: np.ndarray,
    dark_colour: tuple[int, int, int],
    light_colour: tuple[int, int, int],
) -> np.ndarray:
    """
    Map a grayscale image to a two-tone BGR image.

    *dark_colour* maps to black pixels, *light_colour* maps to white
    pixels; intermediate values are linearly interpolated.
    """
    if len(gray.shape) == 3:
        gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

    norm = gray.astype(np.float32) / 255.0
    result = np.zeros((*gray.shape, 3), dtype=np.uint8)

    dark = np.array(dark_colour, dtype=np.float32)
    light = np.array(light_colour, dtype=np.float32)

    for c in range(3):
        channel = norm * (light[c] - dark[c]) + dark[c]
        result[:, :, c] = np.clip(channel, 0, 255).astype(np.uint8)

    return result


def resize_fit(
    frame: np.ndarray, target_w: int, target_h: int
) -> np.ndarray:
    """
    Resize *frame* to fit inside a *target_w* × *target_h* canvas
    while preserving aspect ratio.  The result is centred on a black
    canvas of the exact target size.
    """
    h, w = frame.shape[:2]
    scale = min(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
    canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)

    ox = (target_w - new_w) // 2
    oy = (target_h - new_h) // 2
    canvas[oy:oy + new_h, ox:ox + new_w] = resized
    return canvas
