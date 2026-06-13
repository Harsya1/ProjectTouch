"""Quick functional test — renders all 4 effects on a dummy frame."""
import sys
import time
sys.path.insert(0, ".")

import numpy as np
from core.region import Region
from core.compositor import composite
import config

# Create a random 1280x720 test frame.
frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)

# Spawn one region per effect type.
regions = []
for i, effect_type in enumerate(config.EFFECT_TYPES):
    regions.append(Region(
        id=i,
        x=100 + i * 220,
        y=100,
        width=config.REGION_DEFAULT_WIDTH,
        height=config.REGION_DEFAULT_HEIGHT,
        effect_type=effect_type,
        progress=0.8,
    ))

print(f"Input frame : {frame.shape}")
print(f"Regions     : {len(regions)}")
for r in regions:
    print(f"  #{r.id}  {r.effect_type:12s}  pos=({r.x},{r.y})  progress={r.progress}")

# Time the composite call.
t0 = time.time()
output = composite(frame, regions)
elapsed = time.time() - t0

print(f"Output frame: {output.shape}")
print(f"Composite   : {elapsed*1000:.1f} ms  ({1/elapsed:.1f} FPS equivalent)")
print("ALL EFFECTS RENDERED SUCCESSFULLY")
