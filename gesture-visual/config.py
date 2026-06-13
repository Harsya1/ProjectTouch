"""
Global configuration constants for the Gesture Visual Art application.

All tunable parameters live here so they can be adjusted without
modifying implementation code.
"""

# ── Camera ──────────────────────────────────────────────────────────
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# ── Pinch Detection ────────────────────────────────────────────────
# Euclidean distance (in pixels) between thumb tip and index tip
# below which a pinch is considered active.
PINCH_THRESHOLD_PX = 35

# Minimum interval (seconds) between two consecutive pinch-triggered
# region spawns, preventing rapid-fire creation.
PINCH_COOLDOWN_SEC = 0.8

# ── Region Defaults ────────────────────────────────────────────────
# Size of each spawned region (portrait-oriented rectangle).
REGION_DEFAULT_WIDTH = 200
REGION_DEFAULT_HEIGHT = 500

# Maximum number of simultaneous regions on the canvas.
# When exceeded, the oldest region is faded out and removed (FIFO).
MAX_REGIONS = 5

# ── Effect Catalogue ───────────────────────────────────────────────
# Ordered list of available generative effects.
# New regions are assigned round-robin from this list.
EFFECT_TYPES = ["sketch", "glitch", "mosaic", "pointcloud"]

# ── Animation ──────────────────────────────────────────────────────
# Duration (seconds) for a region's progress to go from 0.0 → 1.0.
ANIMATION_DURATION_SEC = 2.0

# ── Sketch Portrait Effect ─────────────────────────────────────────
SKETCH_CANNY_LOW = 50
SKETCH_CANNY_HIGH = 150
# Fraction of contours that receive a green accent stroke.
SKETCH_GREEN_RATIO = 0.10

# ── Glitch Abstract Effect ─────────────────────────────────────────
# Maximum pixel shift for RGB channel displacement.
GLITCH_MAX_SHIFT = 15
# Number of random solid-colour blocks overlaid per frame.
GLITCH_NUM_BLOCKS = 8
# Maximum width/height (px) of each noise block.
GLITCH_BLOCK_MAX_SIZE = 40

# ── Mosaic Grid Effect ─────────────────────────────────────────────
# Maximum recursion depth for the quadtree-like subdivision.
MOSAIC_MAX_DEPTH = 5
# A cell smaller than this (px) will not be subdivided further.
MOSAIC_MIN_CELL_SIZE = 15

# ── Point Cloud / Depth Scan Effect ────────────────────────────────
# Resolution of the downsampled point grid.
POINTCLOUD_GRID_X = 80
POINTCLOUD_GRID_Y = 60
# Number of horizontal contour scan lines.
POINTCLOUD_NUM_SCAN_LINES = 18
# Number of static starfield particles.
POINTCLOUD_NUM_STARS = 250

# ── Compositor / Border ────────────────────────────────────────────
BORDER_COLOR = (255, 255, 255)   # thin white outline around each region
BORDER_THICKNESS = 2
