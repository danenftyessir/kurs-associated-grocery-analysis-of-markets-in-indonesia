# Notebook per tahap — lokal, Kaggle, Colab

Satu notebook per tahap. Logika ada di `src/`; notebook hanya: (0) setup runtime, (1) `init_runtime`, (2) **pull input dari
Drive tim** + cek input, (3) `pipelines.<tahap>.run(cfg)`, (4) **push output ke Drive tim**, (5) visualisasi `viz.plots`.
Arsitektur: ARCHITECTURE §3 (D-027, D-100).

| Notebook | Pipeline | Input (artefak) | Output utama | Beban | Disarankan |
|---|---|---|---|---|---|
| `00_stage0_data` | `stage0` | data mentah | panel, penggerak, harga dunia, referensi, MDE, QA | ringan | lokal / mana saja |
| `01_task1_profiles` | `task1` | output 00 | profiles, boot_replicates, placebo_stats, events, response_features | **berat** (B = R = 499) | Kaggle / Colab |
| `02_task2_patterns` | `task2` | output 01 | heterogeneity, clusters, coassign, planted_recovery | **berat** | Kaggle / Colab |
| `03_task3_association` | `task3` | output 00 + 01 | assoc | ringan | mana saja |
| `04_task4_forecast` | `task4` | output 00 | forecast_eval, ablation | **berat** (M3) | Kaggle / Colab |
| `05_robustness` | `robustness` | output 00 + 01 + 04 | robustness | sedang–berat | Kaggle / Colab |

Urutan: `00` → (`01` ∥ `04`) → `02`, `03` → `05`. Notebook 04 bisa jalan bersamaan dengan 01.
`02` dan `03` butuh output `01` (`profiles`, `response_features`, `placebo_stats`, `boot_replicates`); `05` butuh output `01` dan `04`
(`forecast_eval`). Setiap tahap baru boleh dimulai setelah tahap sebelumnya selesai **dan** sel push ke Drive tim jalan.
Perkiraan `01` (2026-11-21, laptop): ± 7 dtk per replikasi (nasional + deviasi provinsi h kunci) → bootstrap + plasebo
B = R = 499 (non-fokus 199) ± 1,5–2 jam; Colab bisa lebih lambat. `01` menyimpan checkpoint `boot_replicates` dan `placebo_stats` ke Drive tim tiap 25 replikasi; bila sesi putus, jalankan ulang notebook (rep yang selesai dilewati, hasil akhir identik; D-204). Hapus artefak parsial lama bila konfigurasi/kode berubah.
Input opsional: `task1`, `task3`, `task4` punya `OPTIONAL` (terutama `panel_weekly`) yang ditarik notebook bersama `REQUIRES`;
tanpa panel provinsi tahap jatuh ke versi 7 wilayah dan mencetak PERINGATAN (D-122).

## Folder Drive tim (tempat semua output DAN data mentah)
Folder: https://drive.google.com/drive/folders/15T5ry1VIP_ZhzXqdVAwPLI4vfRySOx8D (ID di `configs/runtime.yaml: drive.folder_id`).
Isinya mencerminkan path artefak: `results/stage0/…`, `results/task1/…`, `data/processed/…`, `data/interim/…`,
`data/reference/…`. Modul `src/utils/drive.py`:
- sel "Cek input" → `drive.pull(cfg, <tahap>.REQUIRES)` mengunduh input tahap ke `out_dir`;
- sel "Simpan ke Drive tim" → `drive.push(cfg, stages=(...))` mengunggah semua artefak tahap itu (versi lama ditimpa).
Tidak perlu lagi mengunduh output manual atau menambahkan output notebook sebagai input.

**Data mentah** ada di `data/raw/` folder yang sama (D-101): Danen memperbarui dengan `python -m kagami drive-push-raw`
(file tak berubah dilewati); anggota mengambil dengan `python -m kagami drive-pull-raw` (hanya file yang belum ada).
Notebook 00 memanggil `drive.pull_raw(cfg)` otomatis.

**Akses:** bagikan folder hanya ke akun anggota tim (Editor), **bukan** "siapa saja yang punya link": isinya memuat
turunan PIHPS per provinsi (U24). Push gagal bila akun tidak punya akses Editor.

## Persiapan (sekali)

### 1. Kode & data mentah
Lokal, dari folder project:

```powershell
python -m kagami bundle --raw
```

Menghasilkan `dist/kagami_code.zip` (kode + configs + `data/reference` + notebook; tanpa data) dan
`dist/kagami_raw_PRIVATE.zip` (isi `data/raw` + checksums). Kaggle: dataset `kagami-code` (**Private**); dataset `kagami-raw`
kini **opsional** karena data mentah diambil dari folder Drive tim (D-101).
Colab: salin isi `kagami_code.zip` dan `data/raw` ke Google Drive `MyDrive/kagami/`. Ulangi bundle kode setiap `src/` berubah.

### 2. Akses Drive dari notebook
- **Colab:** tidak perlu persiapan; saat `drive.pull`/`drive.push` pertama muncul jendela login Google (akun yang punya akses
  Editor ke folder tim).
- **Kaggle** (Kaggle tidak bisa me-mount Drive, jadi memakai token OAuth), sekali per anggota:
  1. Google Cloud Console → buat project → aktifkan **Google Drive API** → *OAuth consent screen* (External, tambahkan email
     sendiri sebagai test user) → *Credentials* → *OAuth client ID* tipe **Desktop app** → unduh `client_secret_….json`
     (simpan di luar repo; `.gitignore` sudah menolak `client_secret*.json`).
  2. Lokal: pasang library opsional lalu buat token (browser terbuka untuk login):

     ```powershell
     pip install -e ".[drive]"
     ```

     ```powershell
     python -m kagami drive-auth --client-secret "C:\path\ke\client_secret.json"
     ```

     Token tersimpan di `~/.kagami/drive_token.json`. Token = akses penuh ke Drive akun itu: **jangan dibagikan/di-commit**.
  3. Kaggle → notebook → *Add-ons → Secrets* → tambah secret `KAGAMI_DRIVE_TOKEN` berisi isi file token → aktifkan untuk notebook.
  4. Notebook *Settings*: **Internet ON** (wajib untuk Drive API).
- **Lokal:** token dari langkah Kaggle no. 2 juga dipakai untuk `drive-pull`/`drive-push`. Tanpa token, sel Drive di notebook
  lokal dilewati dengan pesan (bukan error).

## Menjalankan

### Kaggle
1. *Code → New Notebook → File → Import Notebook* → pilih `notebooks/0X_....ipynb`.
2. *Add Input*: dataset `kagami-code` (semua notebook). Data mentah notebook 00 diunduh otomatis dari Drive tim (`drive.pull_raw`)
   ke `/kaggle/temp/kagami_raw` bila `kagami-raw` tidak dilampirkan. Output notebook lain tidak perlu
   ditambahkan; input diambil dari Drive tim.
3. Pastikan Secret `KAGAMI_DRIVE_TOKEN` aktif dan Internet ON → *Save Version → Save & Run All*.

### Colab
1. Buka `MyDrive/kagami/notebooks/0X_....ipynb` dengan Colab. Sel 0 me-mount Drive untuk kode & data mentah
   (ubah `DRIVE_DIR` bila folder beda).
2. *Runtime → Run all*. Artefak ditulis ke `/content/kagami_out` lalu di-push ke Drive tim.
3. Sesi Colab bisa terputus sebelum push: jalankan ulang notebook.

### Lokal
Jalankan Jupyter dari folder `notebooks/`, atau tanpa notebook:

```powershell
python -m kagami stage0
```

```powershell
python -m kagami drive-push stage0
```

## Mengambil hasil cloud ke project lokal
Satu perintah (butuh token): semua artefak di Drive tim → folder project.

```powershell
python -m kagami drive-pull all
```

Atau hanya input sebuah tahap, mis. `python -m kagami drive-pull task2`. Setelah itu `python -m kagami status`, app, dan
`package` membaca hasil tersebut.

## Catatan
- Push hanya berjalan bila sel "Jalankan tahap" selesai tanpa error. Bila tahap gagal di tengah tetapi artefak sebagian
  perlu dibagikan, jalankan sel "Simpan ke Drive tim" secara manual.
- Setelah push, kirim handoff `TERBIT` ke anggota yang membutuhkan (`docs/HANDOFF.md`) — Drive tidak memberi notifikasi.

## Aturan mengubah notebook
- Logika baru masuk `src/` (lapisan yang tepat), bukan sel notebook. Notebook hanya memanggil pipeline, `drive`, dan `viz`.
- Sel 0 (setup) dan sel 1 (init) **identik** di semua notebook; setiap notebook wajib punya `drive.pull(cfg, <tahap>.REQUIRES)`
  dan `drive.push(cfg, stages=(..., "<tahap>"))` — `tests/test_notebooks.py` memeriksanya.
- Simpan notebook **tanpa output** (*Clear all outputs*) sebelum menaruhnya di repo; hasil ada di artefak, bukan di notebook.
- Grafik baru → fungsi di `src/viz/plots.py` yang dipakai notebook/app (`test_wiring` menolak fungsi viz yatim).
