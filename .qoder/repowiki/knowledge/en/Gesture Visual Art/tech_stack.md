| Requirement | Library | Version |
|---|---|---|
| Webcam capture & image ops | opencv-python | >=4.9.0 |
| Hand tracking (landmarks + pinch) | mediapipe | >=0.10.9 |
| Array/math processing | numpy | >=1.26.0 |
| Image compositing/blending | Pillow | >=10.2.0 |
| Edge detection (sketch effect) | scikit-image | >=0.22.0 |
| Optional GPU shader rendering | moderngl + moderngl-window | >=5.10.0 / >=2.4.6 |
| Logging/debug overlay | loguru | >=0.7.2 |
| Config/state (built-in) | dataclasses, enum | stdlib |

**Evidence**: `requirements.txt` in the project specification (`master_prompt_gesture_visual.md`, Section 2).

**Notes**:
- OpenCV is the primary image processing backbone; Pillow is used only for compositing/blending operations.
- `moderngl` is optional — only needed if NumPy-based pixel operations cause FPS drops below 20.
- MediaPipe provides normalized landmark coordinates (0-1 range); these must be scaled to pixel coordinates using frame dimensions.
- `scikit-image` supplements OpenCV for advanced edge detection in the sketch effect.