# Notebook per tahap — lokal, Kaggle, Colab

Satu notebook per tahap. Logika ada di `src/`; notebook hanya: (0) setup runtime, (1) `init_runtime`, (2) cek input,
(3) `pipelines.<tahap>.run(cfg)`, (4) visualisasi `viz.plots`, (5) simpan output. Arsitektur: ARCHITECTURE §3 (D-027).

| Notebook | Pipeline | Input (artefak) | Output utama | Beban | Disarankan |
|---|---|---|---|---|---|
| `00_stage0_data` | `stage0` | data mentah | panel, penggerak, harga dunia, referensi, MDE, QA | ringan | lokal / mana saja |
| `01_task1_profiles` | `task1` | output 00 | profiles, boot_replicates, placebo_stats, events, response_features | **berat** (B = R = 499) | Kaggle / Colab |
| `02_task2_patterns` | `task2` | output 01 | heterogeneity, clusters, coassign, planted_recovery | **berat** | Kaggle / Colab |
| `03_task3_association` | `task3` | output 00 + 01 | assoc | ringan | mana saja |
| `04_task4_forecast` | `task4` | output 00 | forecast_eval, ablation | **berat** (M3) | Kaggle / Colab |
| `05_robustness` | `robustness` | output 00 + 01 + 04 | robustness | sedang–berat | Kaggle / Colab |

Urutan: `00` → (`01` ∥ `04`) → `02`, `03` → `05`. Notebook 04 bisa jalan bersamaan dengan 01.

## Persiapan (sekali; ulangi bundle setiap kode berubah)

Lokal, dari folder project:

```powershell
python -m kagami bundle --raw
```

Menghasilkan `dist/kagami_code.zip` (kode + configs + `data/reference` + notebook; tanpa data) dan
`dist/kagami_raw_PRIVATE.zip` (isi `data/raw` + checksums). `[HUMAN]`: unggah keduanya.

### Kaggle
1. *Datasets → New Dataset* → unggah `kagami_code.zip` → nama **`kagami-code`**. Saat kode berubah: *New Version*.
2. *Datasets → New Dataset* → unggah `kagami_raw_PRIVATE.zip` → nama **`kagami-raw`**, visibilitas **Private**.
   Jangan pernah dijadikan publik (PIHPS/JISDOR/BPS tanpa hak redistribusi, U7/U13).
3. *Code → New Notebook → File → Import Notebook* → pilih `notebooks/0X_....ipynb` (dari zip kode atau repo lokal).
4. *Add Input*: dataset `kagami-code`, `kagami-raw` (hanya notebook 00), dan *Notebook Output* dari notebook tahap
   sebelumnya (mis. notebook 02 menambahkan output notebook 01). `init_runtime` menemukan semuanya otomatis.
5. *Settings*: Internet ON hanya bila sel setup harus memasang dependensi yang hilang (biasanya tidak perlu).
6. *Save Version → Save & Run All*. Output tersimpan di `/kaggle/working` dan menjadi input notebook berikutnya.

### Colab
1. Salin isi `kagami_code.zip` dan folder `data/raw` ke Google Drive: `MyDrive/kagami/` (struktur sama dengan repo).
2. Buka `MyDrive/kagami/notebooks/0X_....ipynb` dengan Colab. Sel 0 me-mount Drive; ubah `DRIVE_DIR` bila folder beda.
3. *Runtime → Run all*. Semua artefak tertulis ke `MyDrive/kagami/` sehingga notebook berikutnya langsung membacanya.
4. Sesi Colab bisa terputus: tahap berat menulis artefak di akhir `run`; jalankan ulang notebook bila terputus.

### Lokal
Jalankan Jupyter dari folder `notebooks/`. Atau tanpa notebook: `python -m kagami <tahap>`.

## Mengembalikan hasil cloud ke project lokal
Unduh output (Kaggle: tab *Output* → unduh; Colab: dari Drive) dan salin `results/` + `data/processed/` + `data/reference/`
ke folder project. Setelah itu `python -m kagami status`, app, dan `package` membaca hasil tersebut.

## Aturan mengubah notebook
- Logika baru masuk `src/` (lapisan yang tepat), bukan sel notebook. Notebook hanya memanggil pipeline dan `viz`.
- Sel 0 (setup) dan sel 1 (init) **identik** di semua notebook — `tests/test_notebooks.py` memeriksanya.
- Simpan notebook **tanpa output** (*Clear all outputs*) sebelum menaruhnya di repo; hasil ada di artefak, bukan di notebook.
- Grafik baru → fungsi di `src/viz/plots.py` yang dipakai notebook/app (`test_wiring` menolak fungsi viz yatim).
