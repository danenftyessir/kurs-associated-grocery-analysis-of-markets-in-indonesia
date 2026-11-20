# KAGAMI — Kurs-Associated Grocery Analysis of Markets in Indonesia

*Kagami* (鏡) berarti **cermin**: apakah harga pangan mencerminkan pergerakan rupiah, dan di mana pantulannya paling kuat?

Proyek Lomba Data Mining INDONERIS 2026. Mengukur seberapa besar dan seberapa cepat harga eceran 10 komoditas pangan
PIHPS di 34 provinsi bergerak bersama IDR/USD dan harga dunia dalam rupiah, lalu menguji apakah perbedaannya bersumber
dari komoditas atau lokasi. Hasil bersifat **asosiasional**, bukan kausal dan bukan ramalan.

## Menjalankan

```powershell
pip install -e ".[dev]"
```

```powershell
python -m kagami app
```

| Tingkat | Untuk | Perintah |
|---|---|---|
| A | Melihat hasil (tanpa internet) | `python -m kagami app` |
| B | Menjalankan ulang analisis dari data turunan yang disertakan | `python -m kagami task1` … `task4` |
| C | Mengunduh ulang data mentah dan membangun ulang semuanya | `python -m kagami download` → `snapshot` → `all` |

`python -m kagami status` menampilkan sumber dan artefak yang tersedia. Tes: `pytest`.

## Notebook (lokal, Kaggle, Colab)
Satu notebook per tahap di `notebooks/` (`00_stage0_data` … `05_robustness`); setiap notebook menjalankan
`kagami.pipelines.<tahap>` yang sama dengan CLI. Tahap berat (Task 1, 2, 4, robustness) disarankan di Kaggle/Colab:

```powershell
python -m kagami bundle --raw
```

lalu ikuti [docs/NOTEBOOKS.md](docs/NOTEBOOKS.md). Output setiap notebook tersimpan otomatis di folder Drive tim
(https://drive.google.com/drive/folders/15T5ry1VIP_ZhzXqdVAwPLI4vfRySOx8D) dan input tahap berikutnya diambil dari sana; di lokal: `python -m kagami drive-pull all`. Data mentah juga ada di sana
(`data/raw/`): `python -m kagami drive-pull-raw`. Data mentah hanya boleh diunggah ke dataset Kaggle **privat** / Drive pribadi.

## Hak data
Data mentah PIHPS & JISDOR (Bank Indonesia), BPS, Bapanas, dan UN Comtrade **tidak** disertakan; yang disertakan adalah skrip
unduh, checksum (`data/raw/checksums.csv`), dan keluaran turunan, termasuk panel mingguan per provinsi yang dibangun dari
PIHPS (Bank Indonesia) atas izin BI. Pink Sheet (Bank Dunia) dan FAOSTAT berlisensi
CC BY 4.0. Tabel buatan tim di `data/reference/` berlisensi CC BY 4.0. Rincian: [docs/DATASETS.md](docs/DATASETS.md).

## Dokumentasi
[Overview](docs/PROJECT_OVERVIEW.md) · [Arsitektur](docs/ARCHITECTURE.md) · [Notebook](docs/NOTEBOOKS.md) · [Metode](docs/METHODS.md) ·
[Dataset](docs/DATASETS.md) · [Rencana kerja](docs/WORKPLAN.md) · [Keputusan](docs/DECISIONS.md) ·
[Isu terbuka](docs/OPEN_ISSUES.md) · [Praregistrasi](docs/PREREGISTRATION.md) · [Pembagian tugas](docs/PEMBAGIAN_TUGAS.md) · [Handoff](docs/HANDOFF.md)
