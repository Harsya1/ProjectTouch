# Gesture-Triggered Generative Visual Art

A real-time interactive generative art application that uses webcam hand
tracking to spawn visual effect regions overlaid on the live camera feed.

## Quick Start

```bash
# 1. Create & activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| **Pinch** (thumb + index finger) | Spawn a new effect region at the pinch location |
| `q` | Quit the application |
| `c` | Clear all active regions |

## Visual Effects

Each new region cycles through four effects in round-robin order:

1. **Sketch Portrait** — Progressive edge-based line drawing with green
   accent strokes on a paper-white canvas.
2. **Glitch Abstract** — RGB channel split, row displacement, and
   time-varying colour-block noise.
3. **Mosaic Grid** — Recursive non-uniform subdivision with average-colour
   fill, a duotone photo overlay, and a green accent block.
4. **Point Cloud / Depth Scan** — Cyan point cloud on a black background
   with horizontal contour scan lines and a twinkling starfield.

## Architecture

```
main.py                 Entry point & render loop
config.py               All tunable constants
core/
  hand_tracker.py       MediaPipe Hands wrapper + pinch detection
  region.py             Region dataclass (position, size, effect, state)
  region_manager.py     Region lifecycle: spawn, update, evict
  compositor.py         Alpha-blend effects onto the webcam frame
effects/
  base_effect.py        Abstract BaseEffect interface
  sketch_portrait.py    Effect 1 — progressive sketch
  glitch_abstract.py    Effect 2 — glitch art
  mosaic_grid.py        Effect 3 — mosaic grid
  pointcloud_scan.py    Effect 4 — point cloud + scan lines
utils/
  image_ops.py          Image-processing helpers
  timing.py             FrameTimer & progress utilities
assets/
  overlay_images/       Optional duotone photos for mosaic effect
```

## Configuration

All tunables live in `config.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `CAMERA_INDEX` | `0` | Webcam device index |
| `FRAME_WIDTH` | `1280` | Camera width |
| `FRAME_HEIGHT` | `720` | Camera height |
| `PINCH_THRESHOLD_PX` | `35` | Max distance (px) for pinch |
| `PINCH_COOLDOWN_SEC` | `0.8` | Debounce between spawns |
| `REGION_DEFAULT_WIDTH` | `200` | Region width (px) |
| `REGION_DEFAULT_HEIGHT` | `500` | Region height (px) |
| `MAX_REGIONS` | `5` | Max simultaneous regions |
| `ANIMATION_DURATION_SEC` | `2.0` | Effect reveal duration |

## Tech Stack

- **OpenCV** — webcam capture, image processing, display
- **MediaPipe** — hand landmark detection
- **NumPy** — array operations, vectorised pixel math
- **Pillow** — image compositing utilities
- **scikit-image** — supplementary edge detection
- **Loguru** — structured logging

## Performance

Target: **20–30 FPS** at 1280×720 with up to 5 simultaneous regions.
If performance drops, consider migrating heavy effects to GPU shaders
via `moderngl`.
