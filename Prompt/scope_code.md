# SCOPE: Python Prototyping Strategy (Replacing TouchDesigner)

## 1. KONTEKS

Tutorial referensi menggunakan **TouchDesigner** (node-based visual programming) untuk membangun project ini. Saat ini project berada di tahap **eksperimen visualisasi** — tujuan utamanya adalah memvalidasi dan mengeksplorasi efek-efek visual secara cepat menggunakan **full Python scripts**, belum masuk ke tahap produksi/optimisasi maupun migrasi platform lain (web, dll).

Fokus scope ini: **Fase 1 (Prototyping)** sebagai prioritas utama dan satu-satunya target saat ini. Fase 2 (optimisasi GPU/moderngl) dan migrasi web disimpan sebagai catatan arah masa depan, tapi **tidak dikerjakan sekarang**.

---

## 2. PERBANDINGAN TOUCHDESIGNER vs FULL-CODE PYTHON

| Aspek | TouchDesigner | Full-Code Python |
|---|---|---|
| Cara kerja | Node-based, visual graph (TOPs, CHOPs, SOPs) | Imperative script, modular file structure |
| GPU acceleration | Built-in (TOPs otomatis di GPU) | Manual via `moderngl` (OpenGL shader) |
| Hand tracking | Plugin/CHOP eksternal | `mediapipe` (native, akurat) |
| Particle/point system | Built-in Particle SOP | Manual via NumPy/shader |
| Portabilitas | Perlu TD installed (lisensi non-commercial terbatas) | Python env biasa, bisa di-package jadi `.exe` |
| Version control | Binary `.toe` file, sulit di-diff | Plain text `.py`, git-friendly |
| Custom logic (gesture, region state) | Harus dirangkai jadi puluhan node | Native Python, lebih fleksibel & terbaca |
| Extensibility ke platform lain | Terbatas (desktop TD only) | Bisa porting ke web (`p5.js`/`three.js`), exe, dll |

**Keputusan: Full Python untuk eksperimen visual.** Trade-off GPU acceleration (moderngl) dan migrasi platform lain ditunda — fokus saat ini adalah validasi cepat tiap efek secara visual.

---

## 3. STRATEGI EKSEKUSI: FOKUS PROTOTYPING (FASE 1)

### Pendekatan: Eksperimen per-Efek dengan Script Terpisah

Karena tahap ini bersifat **eksperimental**, struktur tidak langsung dipaksakan modular penuh seperti di master prompt. Pendekatan yang lebih cocok:

- Setiap efek dikembangkan & ditest sebagai **script standalone** terlebih dahulu (`experiments/`), agar bisa cepat iterasi visual tanpa bergantung pada keseluruhan sistem (hand tracking, region manager, dll).
- Setelah satu efek terasa "cukup bagus" secara visual, baru diintegrasikan ke struktur core (`hand_tracker`, `region_manager`, `compositor`) sebagai modul efek resmi.

```
experiments/
├── exp_sketch_portrait.py     # standalone: webcam -> sketch effect, fullscreen test
├── exp_glitch_abstract.py      # standalone: webcam -> glitch effect
├── exp_mosaic_grid.py           # standalone: webcam -> mosaic grid effect
├── exp_pointcloud_scan.py       # standalone: webcam -> point cloud + contour scan
└── exp_pinch_detection.py       # standalone: webcam -> MediaPipe pinch test only
```

Tiap script `exp_*.py`:
- Buka webcam sendiri, render full-frame (bukan dalam region kecil) supaya detail visual efek mudah dievaluasi.
- Punya beberapa parameter yang mudah di-tweak di bagian atas file (konstanta) — misal jumlah grid, threshold edge, intensitas glitch, jumlah starfield particle, dsb — untuk eksplorasi cepat.
- Tidak perlu dependency ke `core/` — fully self-contained.

### Tujuan Fase Prototyping
- Validasi visual tiap efek mendekati referensi (sketch, glitch, mosaic, point cloud).
- Validasi pinch detection (jarak threshold, debounce) secara terpisah.
- FPS belum prioritas — cukup cukup responsif untuk eksplorasi (>5-10fps masih oke).

### Setelah Prototyping Selesai
Begitu semua efek individual sudah "matang" secara visual:
- Refactor tiap `exp_*.py` menjadi `effects/*.py` yang mengikuti interface `BaseEffect.render(frame, region)` sesuai master prompt.
- Gabungkan dengan `core/hand_tracker.py`, `core/region_manager.py`, `core/compositor.py` untuk membentuk aplikasi utuh (`main.py`).

Tahap integrasi & optimisasi GPU (Fase 2 / moderngl) baru dibahas **setelah** prototyping visual ini dianggap cukup matang — belum menjadi bagian dari scope saat ini.

---

## 4. PEMBAGIAN TANGGUNG JAWAB (PROTOTYPING vs INTEGRASI)

```
experiments/exp_*.py        → standalone, self-contained, fokus eksplorasi visual cepat
                               (tidak bergantung pada struktur core sama sekali)

core/hand_tracker.py        → dipakai mulai tahap integrasi (setelah exp_pinch_detection.py matang)
core/region.py               → dipakai mulai tahap integrasi
core/region_manager.py       → dipakai mulai tahap integrasi
core/compositor.py           → dipakai mulai tahap integrasi (blend via NumPy/Pillow)
effects/*.py                  → hasil refactor dari experiments/exp_*.py, mengikuti
                                 interface BaseEffect.render(frame, region) -> ndarray
```

Interface `BaseEffect.render(frame, region) -> ndarray` baru relevan **setelah** prototyping, sebagai kontrak untuk integrasi ke `region_manager` & `compositor`.

---

## 5. DEPENDENCY UNTUK PROTOTYPING

```
opencv-python>=4.9.0
mediapipe>=0.10.9
numpy>=1.26.0
Pillow>=10.2.0
scikit-image>=0.22.0
```

Tidak ada dependency tambahan (`moderngl`, dll) di tahap ini — cukup stack CPU standar.

---

## 6. KRITERIA "DONE" UNTUK PROTOTYPING

Tiap `exp_*.py` dianggap selesai jika:
- Output visual sudah mendekati referensi (sketch, glitch, mosaic, atau point cloud).
- Parameter kunci sudah ditandai sebagai konstanta yang mudah diubah untuk eksplorasi lanjutan.
- Berjalan stabil tanpa crash selama beberapa menit (FPS rendah masih dapat diterima).

`exp_pinch_detection.py` dianggap selesai jika:
- Pinch terdeteksi konsisten pada jarak yang masuk akal, dengan debounce yang mencegah trigger berulang.

Setelah semua `exp_*.py` memenuhi kriteria di atas, baru lanjut ke tahap integrasi (struktur `core/` + `effects/` + `main.py` sesuai master prompt).

---

## 7. CATATAN MASA DEPAN (DI LUAR SCOPE SAAT INI)

- **Optimisasi GPU (moderngl/shader)**: dipertimbangkan hanya jika setelah integrasi performa terasa kurang (FPS rendah saat banyak region aktif).
- **Migrasi ke web (three.js/p5.js)**: belum direncanakan, hanya catatan opsi arsitektur jika suatu saat diperlukan.