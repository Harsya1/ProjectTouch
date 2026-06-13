"""Benchmark — measure warm-cache composite performance."""
import sys, time
sys.path.insert(0, ".")

import numpy as np
from core.region import Region
from core.compositor import composite
import config

frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
regions = [
    Region(id=i, x=100 + i * 220, y=100, width=200, height=500,
           effect_type=config.EFFECT_TYPES[i], progress=1.0)
    for i in range(4)
]

# Warm-up pass (populates caches).
composite(frame, regions)

# Benchmark 20 frames.
N = 20
t0 = time.time()
for _ in range(N):
    composite(frame, regions)
elapsed = time.time() - t0

avg_ms = (elapsed / N) * 1000
fps = N / elapsed
print(f"Warm-cache: {avg_ms:.1f} ms/frame  ({fps:.1f} FPS)  over {N} frames")
print(f"With 4 simultaneous effects at 1280x720")
