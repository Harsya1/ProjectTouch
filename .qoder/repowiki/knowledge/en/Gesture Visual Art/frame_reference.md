## Frame Prototype Visual Reference Map

300 PNG frames at 60 FPS (~10 seconds) from a TouchDesigner project (`project1/jul18`, canvas 1372×772).

### Effect Timeline

| Frames | Timecode | Effect | Visual Signature |
|---|---|---|---|
| 001–030 | 00:00:00–00:30 | Raw Webcam | Person visible, white tracking box appears around upper body |
| 030–060 | 00:30–01:28 | Region Lock | White-bordered region fixed in place, hands gesturing |
| 060–120 | 01:28–02:28 | Sketch Portrait | Progressive edge-based face sketch, faint lines, green accents |
| 120–170 | 02:28–03:56 | Glitch Abstract | RGB split, color bands (white/green/pink/blue/yellow), pixel displacement |
| 170–220 | 03:56–05:46 | Mosaic Grid | Non-uniform pixel grid, grayscale blocks, duotone blue portrait, green accent block |
| 220–270 | 05:46–08:20 | Point Cloud Scan | Blue face, horizontal wave distortion lines, starfield particles, dark background |
| 270–300 | 08:20–10:00 | Point Cloud (end) | Peace sign in blue neon/thermal style, contour scan waves, particles |

### Key Visual Anchors for Implementation
- **White border**: thin (~2px), solid white, around every active region
- **Green accent**: appears in sketch (green strokes), mosaic (green block), consistent motif
- **Blue/cyan palette**: dominates point cloud effect, starfield white dots
- **Progressive reveal**: sketch lines draw incrementally (progress 0→1)
- **Region size**: approximately 200×500 px relative to a 1372×772 canvas (vertical/portrait orientation)
- **Background**: real room with vinyl records, speakers, metal shelving, potted plant — always visible behind/around regions

### Quality Assessment
- **Completeness**: All 4 effects are demonstrated with clear start/end transitions
- **Quality**: High — each effect is clearly distinguishable and shows key visual characteristics
- **Gaps**: The prototype shows effects sequentially; the spec requires multiple simultaneous regions
- **Resolution**: Frames are screen captures at 1372×772 — sufficient as visual reference but not for pixel-perfect reproduction