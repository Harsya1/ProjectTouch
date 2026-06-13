```
gesture-visual/
├── main.py                  # Entry point, render loop
├── config.py                # Global constants (resolution, thresholds)
├── core/
│   ├── hand_tracker.py      # MediaPipe Hands wrapper + pinch detection
│   ├── region.py            # Region dataclass (position, size, effect type, state)
│   ├── region_manager.py    # Lifecycle: spawn, lock, update, render, evict
│   └── compositor.py        # Blend all regions onto webcam frame
├── effects/
│   ├── base_effect.py       # Abstract BaseEffect interface
│   ├── sketch_portrait.py   # Effect 1: edge/line sketch, progressive
│   ├── glitch_abstract.py   # Effect 2: RGB split + displacement + noise
│   ├── mosaic_grid.py       # Effect 3: recursive grid + duotone overlay
│   └── pointcloud_scan.py   # Effect 4: point cloud + contour scan + starfield
├── utils/
│   ├── image_ops.py         # Resize, crop, blend, color quantize helpers
│   └── timing.py            # Delta time, animation progress tracking
├── assets/
│   └── overlay_images/      # Duotone photos for mosaic effect
├── requirements.txt
└── README.md
```

## Component Interaction
1. `main.py` reads webcam frames, passes to `HandTracker` for pinch detection.
2. On pinch, `RegionManager` spawns a `Region` at the pinch midpoint (round-robin effect type).
3. Each frame, `RegionManager.update(dt)` advances animation progress for all regions.
4. `Compositor.composite()` iterates regions, crops the base frame, delegates to the matching effect's `render()`, alpha-blends the result back, and draws a white border.
5. Effects implement `BaseEffect.render(frame, region) -> np.ndarray`.

## Key Design Decisions
- Regions are locked in place once spawned (no tracking follow).
- FIFO eviction when exceeding MAX_REGIONS (5).
- Effect type assigned round-robin to ensure visual variety.
- 0.8s cooldown on pinch detection prevents rapid-fire spawning.