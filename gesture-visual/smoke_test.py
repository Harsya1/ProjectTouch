"""Quick smoke test — verify hand tracker + compositor work together."""
import sys, time
sys.path.insert(0, ".")

import numpy as np
from core.hand_tracker import HandTracker
from core.region import Region
from core.region_manager import RegionManager
from core.compositor import composite
import config

print("1. Creating HandTracker...")
tracker = HandTracker()
print("   OK")

print("2. Creating RegionManager...")
rm = RegionManager()
print("   OK")

print("3. Testing composite with dummy frame...")
frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
regions = [
    Region(id=0, x=100, y=100, width=200, height=500,
           effect_type="sketch", progress=0.5)
]
output = composite(frame, regions)
print(f"   OK — output shape: {output.shape}")

print("4. Testing process() on dummy frame...")
result = tracker.process(frame)
print(f"   OK — detected {len(result)} hands (0 expected on random noise)")

print("5. Cleanup...")
tracker.release()
print("   OK")

print("\nALL SMOKE TESTS PASSED — main.py should work!")
