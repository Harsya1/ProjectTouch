# MASTER PROMPT: Gesture-Triggered Generative Visual Art (Python)

## 1. PROJECT OVERVIEW

Buatkan aplikasi real-time **interactive generative art** berbasis Python yang:

- Mengambil input dari **webcam** sebagai live feed/background.
- Melakukan **hand tracking** untuk mendeteksi gesture **pinch** (ujung jari telunjuk bertemu ujung jempol).
- Setiap kali pinch terdeteksi, sistem **spawn & lock sebuah "region/frame"** (kotak area) di kanvas pada posisi tersebut.
- Setiap region menampilkan **visual generatif berbeda** yang dirender secara real-time di dalam batas kotaknya (overlay di atas webcam feed).
- Tidak ada elemen audio/musik — murni visual & gesture-driven.
- Style referensi: distorsi/glitch RGB, sketsa portrait garis tipis yang ter-render progresif, dan mosaic/grid color-block dengan foto duotone.

Referensi visual yang harus diakomodasi (3 tipe efek minimal):
1. **Sketch Portrait Effect** — wajah pengguna di-render sebagai garis sketsa halus (edge-based line drawing), muncul progresif/animated.
2. **Glitch Abstract Effect** — blok warna abstrak dengan distorsi pixel/displacement/noise bergaya RGB split.
3. **Mosaic Grid Effect** — kanvas dipecah jadi grid sel berukuran variatif, tiap sel diisi warna rata-rata/gradasi, dengan satu foto duotone (misal biru-putih) sebagai focal point.
4. **Point Cloud / Depth Scan Effect** — wajah & tubuh pengguna direpresentasikan sebagai kumpulan titik-titik (point cloud) cyan/biru menyala di atas background hitam, dengan garis-garis kontur horizontal melengkung mengikuti bentuk wajah (mirip topographic/depth scan), ditambah partikel kecil acak tersebar di seluruh frame (efek "starfield").

---

## 2. TECH STACK

| Kebutuhan | Library |
|---|---|
| Webcam capture & image ops | `opencv-python` |
| Hand tracking (landmark + pinch detection) | `mediapipe` |
| Array/math processing | `numpy` |
| Image compositing/blending | `Pillow` |
| Edge detection untuk sketch effect | `opencv-python` (Canny) atau `scikit-image` |
| Optional shader-based rendering (jika fps berat) | `moderngl` |
| Config/state management | `dataclasses`, `enum` (built-in) |
| Logging/debug overlay | `opencv-python` putText, atau `loguru` |

### requirements.txt
```
opencv-python>=4.9.0
mediapipe>=0.10.9
numpy>=1.26.0
Pillow>=10.2.0
scikit-image>=0.22.0
moderngl>=5.10.0
moderngl-window>=2.4.6
loguru>=0.7.2
```

---

## 3. ARSITEKTUR & STRUKTUR FOLDER

```
gesture-visual/
├── main.py                  # entry point, render loop utama
├── config.py                # konstanta global (resolusi, threshold pinch, dll)
├── core/
│   ├── hand_tracker.py      # wrapper MediaPipe Hands + pinch detection
│   ├── region.py             # dataclass Region (posisi, ukuran, tipe efek, state)
│   ├── region_manager.py     # lifecycle: spawn, lock, update, render, hapus region
│   └── compositor.py         # blending semua region ke frame webcam
├── effects/
│   ├── base_effect.py        # abstract class BaseEffect (interface render(frame, region))
│   ├── sketch_portrait.py     # efek 1: edge/line sketch progresif
│   ├── glitch_abstract.py     # efek 2: pixel displacement + RGB split + noise
│   ├── mosaic_grid.py         # efek 3: grid color block + duotone photo overlay
│   └── pointcloud_scan.py      # efek 4: point cloud wajah + contour scan + starfield
├── utils/
│   ├── image_ops.py          # helper: resize, crop, blend, color quantize
│   └── timing.py              # delta time, animation progress tracking
├── assets/
│   └── overlay_images/        # foto-foto untuk mosaic effect (duotone, dll)
├── requirements.txt
└── README.md
```

---

## 4. SPESIFIKASI DETAIL MODUL

### 4.1 `core/hand_tracker.py`
- Inisialisasi `mediapipe.solutions.hands.Hands` (max_num_hands=2, min_detection_confidence=0.7).
- Fungsi `process(frame) -> list[HandLandmarks]`.
- Fungsi `get_pinch_distance(landmarks)`:
  - Ambil landmark **4** (thumb tip) dan **8** (index finger tip).
  - Hitung euclidean distance ternormalisasi (gunakan koordinat normalized 0-1, lalu scale ke pixel berdasarkan resolusi frame).
- Fungsi `is_pinching(landmarks, threshold_px=30) -> bool`.
- Fungsi `get_pinch_midpoint(landmarks) -> (x, y)` — titik tengah antara thumb tip & index tip, digunakan sebagai **anchor posisi region baru**.
- Tambahkan **debounce/cooldown** (misal 0.8 detik) agar satu pinch tidak spawn region berulang kali secara cepat.

### 4.2 `core/region.py`
```python
@dataclass
class Region:
    id: int
    x: int
    y: int
    width: int
    height: int
    effect_type: str          # "sketch" | "glitch" | "mosaic" | "pointcloud"
    locked: bool = False
    created_at: float = 0.0
    frame_buffer: np.ndarray | None = None  # cache hasil render efek
    progress: float = 0.0      # untuk animasi progresif (0.0 - 1.0)
```
- Saat pinch terdeteksi → buat instance `Region` baru dengan ukuran default (misal 200x500 px, mengikuti rasio di referensi) berpusat di pinch midpoint.
- `effect_type` dipilih **round-robin** atau **random** dari daftar efek yang tersedia setiap kali region baru dibuat.

### 4.3 `core/region_manager.py`
- Simpan list `self.regions: list[Region]`.
- `on_pinch_detected(midpoint)`:
  - Cek cooldown global.
  - Jika lolos, buat `Region` baru → `locked=True` → tambahkan ke list.
- `update(dt)`: update `progress` tiap region (increment sampai 1.0) untuk animasi efek progresif.
- `render(frame)`: loop semua region, panggil efek sesuai `effect_type`, simpan hasil ke `frame_buffer`, lalu serahkan ke compositor.
- Batasi jumlah region maksimum (misal 5) — region tertua di-remove/fade-out jika melebihi batas (FIFO).

### 4.4 `core/compositor.py`
- `composite(base_frame, regions) -> final_frame`:
  - Untuk setiap region, crop area `(x, y, w, h)` dari `base_frame`.
  - Render efek di area tersebut (lihat `effects/`).
  - Blend hasil efek kembali ke `base_frame` menggunakan alpha blending (opsional fade-in saat `progress < 1.0`).
  - Gambar border/frame putih tipis di sekeliling region (sesuai referensi visual — kotak putih outline).

---

## 5. SPESIFIKASI EFEK VISUAL

### 5.1 `effects/sketch_portrait.py` — **Sketch Portrait Effect**
- Ambil crop frame dari area region.
- Convert ke grayscale → `cv2.Canny()` untuk edge detection.
- Invert warna edge (garis hitam di atas putih, atau garis abu di atas putih sesuai referensi).
- Animasi progresif: gunakan `progress` (0→1) untuk **reveal garis secara bertahap** — bisa dengan mask berbasis arc-length (gambar garis sedikit demi sedikit menggunakan `cv2.polylines` pada kontur yang diekstrak via `cv2.findContours`).
- Tambahkan sedikit warna aksen (hijau/kuning tipis) pada beberapa stroke sesuai referensi (frame 6-10 menunjukkan ada garis hijau).
- Output: gambar grayscale/line-art dengan background putih bersih.

### 5.2 `effects/glitch_abstract.py` — **Glitch Abstract Effect**
- Ambil crop frame.
- Teknik kombinasi:
  - **RGB channel split & shift**: pisahkan channel R/G/B, shift masing-masing channel secara horizontal/vertikal dengan offset acak kecil.
  - **Pixel sorting / displacement**: pilih beberapa baris/kolom secara acak, geser pixel berdasarkan brightness.
  - **Block noise**: tambahkan blok warna solid acak (hijau, biru, kuning, pink — sesuai referensi frame 11-15) di area tertentu menggunakan `np.random` dengan seed yang konsisten per region (agar tidak berubah-ubah tiap frame, tapi tetap dinamis perlahan).
- Animasi: parameter shift/offset bisa berubah perlahan tiap frame menggunakan `time.time()` untuk efek "hidup".

### 5.3 `effects/mosaic_grid.py` — **Mosaic Grid Effect**
- Bagi area region menjadi grid dengan **ukuran sel tidak uniform** (mix antara sel besar dan kecil, sesuai referensi frame 16-20 — mirip treemap/quadtree).
- Pendekatan teknis:
  - Gunakan **recursive subdivision** (mirip quadtree): bagi area jadi 2 secara acak (horizontal/vertikal), ulangi pada masing-masing sub-area sampai kedalaman tertentu atau ukuran minimum.
  - Tiap sel diisi dengan warna rata-rata dari crop frame webcam pada posisi sel tersebut (`cv2.mean()`), atau gradient dari foto referensi.
  - Gambar border hitam tipis antar sel (`cv2.rectangle` dengan thickness=1).
- Tambahkan **satu foto overlay duotone** (load dari `assets/overlay_images/`, convert ke duotone biru-putih via color mapping) di salah satu sel terbesar, dengan border putih solid (frame).
- Tambahkan satu blok warna solid hijau di pojok bawah sebagai aksen (sesuai referensi).

### 5.4 `effects/pointcloud_scan.py` — **Point Cloud / Depth Scan Effect**
- Ambil crop frame dari area region, convert ke grayscale untuk dijadikan **pseudo depth map** (brightness pixel = proxy depth, karena tidak ada sensor depth asli).
- **Background**: isi penuh hitam.
- **Point cloud wajah**:
  - Downsample frame grayscale (misal ke grid 80x60) → tiap titik grid jadi satu "point".
  - Hanya render point di area yang terdeteksi sebagai wajah/tubuh (gunakan deteksi wajah `cv2.CascadeClassifier` atau MediaPipe Face Detection untuk mask area, atau cukup gunakan threshold brightness untuk area yang relevan).
  - Warna point: gradient cyan → biru muda berdasarkan brightness (`(brightness, 255, 255)` di HSV lalu convert ke BGR, atau interpolasi manual antara `(255,255,0)` dan `(255,150,80)` dalam BGR).
  - Render tiap point sebagai `cv2.circle` radius 1px atau langsung set pixel di array numpy untuk performa.
- **Contour scan lines**:
  - Buat beberapa garis horizontal (misal 15-20 garis) yang membentang penuh lebar region.
  - Tiap garis di-displace vertikal secara halus berdasarkan brightness map di posisi x tersebut (garis "naik" saat melewati area terang seperti wajah, "turun" di area gelap) — gunakan interpolasi/smoothing (`cv2.GaussianBlur` pada brightness profile per kolom) agar garis terlihat smooth, bukan jagged.
  - Gambar garis dengan `cv2.polylines`, warna cyan/hijau-cyan, opacity tinggi.
  - Animasikan offset vertikal garis secara perlahan menggunakan `time.time()` agar terlihat "bergerak/scanning".
- **Starfield particles**:
  - Generate set titik acak (misal 200-300 titik) dengan posisi fixed per region (seed konsisten), warna putih kecil, opacity bervariasi — beberapa berkedip dengan modulasi sinusoidal terhadap waktu.
- Komposisikan urutan layer: background hitam → starfield → contour lines → point cloud wajah (di atas).

---

## 6. MAIN LOOP (`main.py`)

```python
import cv2
from core.hand_tracker import HandTracker
from core.region_manager import RegionManager
from core.compositor import composite
import time

def main():
    cap = cv2.VideoCapture(0)
    tracker = HandTracker()
    region_manager = RegionManager()
    last_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)  # mirror, natural untuk webcam

        now = time.time()
        dt = now - last_time
        last_time = now

        landmarks_list = tracker.process(frame)
        for landmarks in landmarks_list:
            if tracker.is_pinching(landmarks):
                midpoint = tracker.get_pinch_midpoint(landmarks)
                region_manager.on_pinch_detected(midpoint)

        region_manager.update(dt)
        output = composite(frame, region_manager.regions)

        cv2.imshow("Gesture Visual", output)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
```

---

## 7. CONFIG (`config.py`)

```python
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

PINCH_THRESHOLD_PX = 35
PINCH_COOLDOWN_SEC = 0.8

REGION_DEFAULT_WIDTH = 200
REGION_DEFAULT_HEIGHT = 500
MAX_REGIONS = 5

EFFECT_TYPES = ["sketch", "glitch", "mosaic", "pointcloud"]

ANIMATION_DURATION_SEC = 2.0  # durasi progress 0 -> 1
```

---

## 8. SETUP & RUN INSTRUCTIONS

```bash
# 1. Buat virtual environment
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate       # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Jalankan
python main.py
```

---

## 9. PERFORMANCE & NEXT STEPS

- Jika fps drop karena efek pixel-level di NumPy/Pillow, migrasi rendering efek (`glitch_abstract`, `mosaic_grid`) ke **fragment shader via `moderngl`**, dengan webcam frame & region data dikirim sebagai texture/uniform.
- Tambahkan **fade-out/remove** untuk region terlama agar kanvas tidak penuh.
- Opsional: ganti `cv2.imshow` dengan window berbasis `moderngl_window` atau `pygame` jika ingin fullscreen/projector output untuk instalasi.
- Tambahkan **dua tangan** → bisa trigger dua region berbeda secara bersamaan, atau gesture lain (misal kedua tangan pinch bersamaan = clear all regions).

---

## 10. INSTRUKSI UNTUK AI CODE ASSISTANT

1. Generate seluruh struktur folder & file sesuai poin 3.
2. Implementasikan tiap modul sesuai spesifikasi poin 4 & 5 secara lengkap dan dapat dijalankan (`python main.py`).
3. Pastikan pinch detection responsif dan tidak ada false-trigger berulang.
4. Setiap efek harus terlihat jelas berbeda satu sama lain dan ter-render real-time minimal 20-30 fps di resolusi 1280x720.
5. Sertakan komentar kode yang menjelaskan logika tiap fungsi penting.
