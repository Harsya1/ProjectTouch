## Setup
```bash
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

## Run
```bash
python main.py
```

## Quit
Press `q` in the display window.

## Camera Selection
Change `CAMERA_INDEX` in `config.py` (default: 0).

## Key Tunables (config.py)
- `PINCH_THRESHOLD_PX = 35` — distance threshold for pinch detection
- `PINCH_COOLDOWN_SEC = 0.8` — debounce between pinch spawns
- `REGION_DEFAULT_WIDTH = 200` / `REGION_DEFAULT_HEIGHT = 500` — region size
- `MAX_REGIONS = 5` — max simultaneous regions (FIFO eviction)
- `ANIMATION_DURATION_SEC = 2.0` — effect reveal duration

## Frame Prototype Reference
The `Frame Prototype/` folder contains 300 PNG frames (60 FPS, ~10 sec) from a TouchDesigner reference implementation. Use these as visual ground truth for effect appearance and timing.