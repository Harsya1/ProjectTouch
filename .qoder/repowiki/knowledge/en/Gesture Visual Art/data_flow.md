## Runtime Data Flow

```
Webcam (60 FPS)
    │
    ▼
cv2.flip(frame, 1)  ──►  Mirrored Frame
    │
    ├──► HandTracker.process(frame)
    │       │
    │       ▼
    │    list[HandLandmarks]
    │       │
    │       ├──► is_pinching(landmarks) ──► bool
    │       │       (threshold: 35px, cooldown: 0.8s)
    │       │
    │       └──► get_pinch_midpoint(landmarks) ──► (x, y)
    │
    ├──► [if pinch] RegionManager.on_pinch_detected(midpoint)
    │       │
    │       ▼
    │    New Region(x, y, 200, 500, effect_type=round-robin)
    │    locked=True, progress=0.0
    │
    ├──► RegionManager.update(dt)
    │       │
    │       ▼
    │    region.progress += dt / 2.0  (clamp to 1.0)
    │    FIFO eviction if len(regions) > 5
    │
    └──► Compositor.composite(frame, regions)
            │
            ▼  (for each region)
         crop frame[x:x+w, y:y+h]
            │
            ├──► effect.render(crop, region) ──► effect_output
            │
            ▼
         alpha_blend(base_frame, effect_output, region, progress)
         draw_border(region)
            │
            ▼
         Final Frame ──► cv2.imshow()
```

## Effect Selection Order
Round-robin cycle: sketch → glitch → mosaic → pointcloud → sketch → ...
Each new region gets the next effect in the sequence.