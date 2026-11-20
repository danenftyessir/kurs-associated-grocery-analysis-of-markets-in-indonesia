# Instruksi agent — KAGAMI (INDONERIS 2026)

**KAGAMI** = *Kurs-Associated Grocery Analysis of Markets in Indonesia* (鏡, cermin). Nama lama: RupiahPass
(masih muncul di nama file PDF proposal saja; jangan dipakai di teks baru — D-028).

Dokumen ini adalah buku pegangan operasional untuk setiap sesi agent. Isinya: konteks, protokol kerja, peta kode,
aturan, data, metode ringkas, jebakan yang sudah ditemukan, dan template. Bagian §9 (inventaris fungsi) dijaga oleh
`tests/test_claude_md.py`: setiap kali sebuah stub diimplementasikan atau fungsi publik ditambah/dihapus, perbarui §9.

---

## 0. Cara memakai dokumen ini

### 0.1 Urutan baca di awal sesi
1. §2 (status saat ini), handoff terbuka untuk anggota sesi ini di `docs/handoff/`, dan entri teratas bagian anggota
   itu di `docs/SESSION_LOG.md`.
2. Papan status di `docs/WORKPLAN.md` → pilih WP.
3. Heading WP di WORKPLAN + bagian `docs/METHODS.md` yang dirujuk WP itu.
4. §9 (inventaris) untuk tahu fungsi mana yang harus diisi dan kontrak input/outputnya.
5. Bagian lain dokumen ini bila relevan (data §10, konvensi §15, jebakan §23).

### 0.2 Sumber kebenaran per topik (bila ada konflik, sumber di kolom kanan menang)

| Topik | Sumber kebenaran |
|---|---|
| Desain penelitian (RQ, hipotesis, metode, lingkup) | `docs/Proposal v4 — RupiahPass ... .pdf` (nama file lama, jangan diganti) → diringkas di `docs/PROJECT_OVERVIEW.md` |
| Aturan lomba | `docs/Juknis Data Mining Indoneris 2026.pdf` |
| Rumus & parameter metode | `docs/METHODS.md` + `configs/params.yaml` |
| Status & urutan pekerjaan | `docs/WORKPLAN.md` (papan status) |
| Kontrak artefak (path, kolom wajib, ship) | `src/utils/artifacts.py` (tabel di `docs/ARCHITECTURE.md` §5 adalah salinannya) |
| Data mentah (format, cakupan, keanehan) | `docs/DATASETS.md` + `configs/sources.yaml` |
| Keputusan yang sudah diambil | `docs/DECISIONS.md` |
| Masalah terbuka & risiko | `docs/OPEN_ISSUES.md` |
| Langkah Kaggle/Colab | `docs/NOTEBOOKS.md` |
| Pembagian anggota, kepemilikan file, jadwal, titik terbit | `docs/PEMBAGIAN_TUGAS.md` |
| Hipotesis yang dibekukan | `docs/PREREGISTRATION.md` (beku setelah G6) |
| Riwayat sesi (per anggota) | `docs/SESSION_LOG.md` |
| Pesan antar anggota (serah-terima) | `docs/handoff/*.md`, format `docs/HANDOFF.md` |

CLAUDE.md meringkas semua di atas agar agent bisa bekerja tanpa membuka semuanya; bila ringkasan di sini bertentangan
dengan sumber kebenaran, ikuti sumber kebenaran lalu perbaiki CLAUDE.md.

---

## 1. Konteks project

### 1.1 Lomba
- Lomba Data Mining INDONERIS 2026, tema "Realizing Impactful Innovation through Creative and Sustainable Technology".
- Gelombang 2: batas 30 Nov 2026. Target submit **29 Nov 2026**. Penjurian 1–10 Des, pengumuman 15 Des.
- Submission: (1) makalah PDF, (2) zip project berisi dataset + kode + library yang bisa dijalankan juri, (3) video demo.
- Struktur makalah wajib (juknis): judul; abstrak; pendahuluan (latar belakang, tujuan & manfaat, batasan); kajian
  pustaka; solusi usulan (deskripsi, dataset, metode, perbedaan dengan solusi sebelumnya, matriks evaluasi); hasil
  eksperimen & pengujian; analisis; kesimpulan & saran; daftar pustaka.
- Bobot penilaian: keaslian 20%, kebaruan dataset 15%, ketepatan metode 10%, manfaat 20%, kelengkapan projek 20%,
  kelengkapan laporan 15%.
- Konten wajib orisinal dan tidak melanggar hak cipta → kebijakan data turunan (D-015) dan larangan mengirim data mentah
  tanpa hak redistribusi.

### 1.2 Pertanyaan pemandu
Apakah kepekaan harga pangan eceran terhadap rupiah lebih ditentukan oleh **komoditasnya** atau oleh **lokasinya**?

Konteks: rupiah melemah sepanjang 2026 (JISDOR 18.250 pada 16 Nov 2026; nilai terakhir di data 18.252 pada 18 Nov).
Bukti agregat menunjukkan pass-through kurs ke harga pangan Indonesia lemah/tidak terdeteksi (Unuvar 2026: −0,012,
SE 0,150; Persada dkk. 2026; Hidayah & Askar 2026). Nol agregat bisa menyembunyikan komoditas/provinsi yang peka.
Pembingkaian tema: ketahanan harga pangan (SDG 2) — TPID tahu komoditas mana yang historisnya paling peka di
wilayahnya dan kapan responsnya muncul.

### 1.3 Jalur transmisi (dasar pemilihan komoditas & penggerak)
1. Impor langsung — bawang putih, gula, daging sapi.
2. Input impor — jagung & bungkil kedelai untuk pakan → daging ayam, telur.
3. Paritas ekspor — minyak sawit → minyak goreng.
Jalur 2–3 bekerja lewat harga dunia dalam rupiah → penggerak kedua `w` = harga dunia padanan × JISDOR.

### 1.4 Pertanyaan penelitian → task → keluaran

| RQ | Pertanyaan | Task | Artefak utama |
|---|---|---|---|
| RQ1 | Besar & kecepatan respons nasional per komoditas terhadap IDR/USD dan harga dunia rupiah; beda menurut jalur eksposur | 1, 3a | `profiles`, `events`, `mde`, `assoc` |
| RQ2 | Porsi variasi dari komoditas vs provinsi; apakah provinsi membentuk kelompok stabil | 1, 2 | `heterogeneity`, `clusters`, `coassign` |
| RQ3 | Asimetri depresiasi vs apresiasi + perbedaan terkecil yang terdeteksi | 1 | `profiles` (e_pos/e_neg), `response_features.A8`, `mde` |
| RQ4 | Karakteristik terukur yang berasosiasi dengan perbedaan respons | 3 | `assoc` |
| RQ5 | Apakah fitur kurs & harga dunia memperbaiki prediksi 4 & 8 minggu out-of-sample | 4 | `forecast_eval`, `ablation` |

### 1.5 Hipotesis (dibekukan di G6, 21 Nov; detail `docs/PREREGISTRATION.md`)

| Kode | Isi | Uji | Jenis |
|---|---|---|---|
| H0-Het | ≥ 1 komoditas: variasi respons antarprovinsi pada h=8 > noise (τ² > 0) | Q vs plasebo; BH FDR antar 10 | konfirmatori |
| H2 | Respons depresiasi ≠ apresiasi (level komoditas, arah bebas) | Wald β⁺(8)=β⁻(8), SE cluster minggu | konfirmatori bila MDE ≤ 0,5; selain itu deskriptif |
| H3 | Provinsi lebih terpencil → respons h=4 lebih kecil; h=12 arah bebas | meta-regresi efek acak | konfirmatori (waktu) |
| H5 | Jalur impor langsung & input impor: fitur kurs menurunkan MAE h=8 pada origin pergerakan kurs besar | rasio MAE + DM HAC | konfirmatori grup fokus |
| E1 | Impor langsung → PT(8) lebih besar dari domestik | Kendall τ, permutasi eksak N=10 | deskriptif |
| E2 | Respons sekitar perubahan HET/HAP berbeda | grafis per rezim | eksploratif |
| E3 | Frekuensi perubahan harga tinggi → respons lebih cepat | kovariat meta-regresi | eksploratif |

### 1.6 Batas klaim (berlaku untuk SEMUA teks keluaran: makalah, app, findings, komentar grafik)
Hasil asosiasional; tidak meramal kurs; tidak mengamati rantai pasok. Respons tak terdeteksi = batas atas kepekaan,
bukan kegagalan. k = 1, asosiasi nol, rasio MAE ≈ 1 adalah hasil sah. Tabel "Jangan tulis / Tulis": §20.

---

## 2. Status saat ini (perbarui setiap akhir sesi)

Tanggal acuan: 2026-11-20. Papan lengkap: `docs/WORKPLAN.md`.

- **Selesai:** WP-00 (skeleton v2: src berlapis + 6 notebook), WP-01 (snapshot), WP-02 (loader semua sumber), WP-03 (panel mingguan),
  WP-04 (kelayakan: 337/340 layak), WP-05 (penggerak & harga dunia rupiah), WP-12 (mesin statistik).
- **Artefak yang sudah ada (lokal):** `checksums`, `pihps_daily`, `panel_weekly`, `eligibility`, `world_prices_weekly`.
- **Tim (PEMBAGIAN_TUGAS.md):** Danen = jalur A data & ekonometrika inti (WP-06, 08–11, 13–17, 28–30); Ardell = jalur B
  data mining, prediksi & produk (WP-07, 18–27, 31–32); Abi = jalur C non-teknis (WP-11 naskah, 33–35, data manual).
- **Berikutnya — Danen:** WP-06 → WP-08 (terbit P1 21 Nov) → WP-09 (G-power 23 Nov). **Ardell:** WP-07, WP-25 (sintetis).
  **Abi:** email BI, U19, data manual §6.2, naskah praregistrasi.
  Paralel: WP-07, WP-25. Gerbang terdekat: **G6 = 21 Nov** (WP-11: bekukan varian D-011, bobot pakan D-012, grup fokus D-013).
- **Izin BI (U13):** diperoleh 2026-11-20, mencakup redistribusi data turunan → `panel_weekly` ikut paket juri (D-104).
- **Menunggu manusia (WP-35):** cek endpoint PIHPS resmi (U19), setup Kaggle + folder Drive tim
  (bagikan terbatas, `drive-push-raw`) + token Drive per anggota (U100), unggah CSV penduduk 2025 & kab/kota (U103),
  video, unggah.
- **Data baru 2026-11-20 (D-101):** BPS impor v2 (+bawang putih), revisi regulasi, `jarak_hub`, `konkordansi_hs`,
  `hortikultura_produksi` — input WP-07 (Ardell). Versi lama di `data/raw/_superseded/`.
- **Pertukaran artefak & data mentah:** folder Drive tim https://drive.google.com/drive/folders/15T5ry1VIP_ZhzXqdVAwPLI4vfRySOx8D lewat `utils.drive` (D-100).
- `python -m kagami stage0` saat ini berhenti di `NotImplementedYet: WP-06` (sesuai harapan).

---

## 3. Protokol sesi

### 3.0 Siapa yang sedang bekerja (tim 3 orang)
Proyek dikerjakan tiga anggota (detail `docs/PEMBAGIAN_TUGAS.md`): **Danen** (jalur A), **Ardell** (jalur B), **Abi** (jalur C,
non-teknis). User sesi ini bisa salah satu dari mereka; bila belum jelas, **tanyakan nama** sebelum mengubah file.
- Kerjakan hanya WP dengan PIC anggota itu (kolom PIC di papan WORKPLAN) dan hanya file miliknya (PEMBAGIAN_TUGAS §3).
  Perubahan pada file milik anggota lain → buat handoff `PERMINTAAN` (docs/HANDOFF.md), jangan diedit.
- Untuk Abi: jangan mengubah `src/`, `tests/`, `app/`, `configs/`, `notebooks/`; bantu riset, data manual (CSV di
  `data/raw/manual_*/` sesuai skema §6.2), makalah di `docs/paper/`, `results/findings.md`, audit klaim, administrasi.
- Konsumen artefak tahap lain (mis. Ardell untuk Task 2/3/4) tidak menunggu: kembangkan dengan data sintetis berskema
  `src/utils/artifacts.py` (label "dummy", tidak boleh masuk hasil), jalankan ulang dengan data asli saat artefak terbit (P1–P5).
- Penomoran baru: keputusan Danen D-100+, Ardell D-200+, Abi D-300+; isu Danen U100+, Ardell U200+, Abi U300+.
- Entri SESSION_LOG ditulis di bagian anggota sendiri. Pesan ke anggota lain (artefak terbit, permintaan, keputusan,
  blokir, angka untuk makalah) → file handoff di `docs/handoff/` sesuai `docs/HANDOFF.md` + versi pendek untuk chat.

### 3.1 Mulai
1. Baca §2, lalu **handoff terbuka** untuk anggota ini: file `docs/handoff/*.md` dengan `ke` = nama anggota atau `Semua`
   dan `status` ≠ `selesai`. Ringkas untuk user dan tawarkan tindak lanjutnya. Lalu entri teratas bagian anggota itu di
   SESSION_LOG.
2. `python -m kagami status` (atau tanpa instalasi: lihat §4.4) untuk melihat sumber & artefak.
3. Pilih satu WP: status ⬜, semua dependensi ✅, atau yang diminta user. Jangan mengerjakan WP yang user minta ditunda.
4. Ubah status WP di papan WORKPLAN menjadi 🔶.
5. Daftarkan langkah kerja di task list aplikasi (bukan di teks pesan).

### 3.2 Selama bekerja
- Baca kode stub WP itu (docstring = spesifikasi kontrak). Jangan mengubah signature yang dipanggil `pipelines/` tanpa
  memperbarui pemanggilnya dan dokumen.
- Tulis tes dulu atau bersamaan: data sintetis dengan jawaban yang diketahui (§16).
- Jalankan pada data asli bila tersedia; catat angka penting (jumlah baris, distribusi, nilai ekstrem).
- Temuan yang mengubah desain → laporkan ke user dan minta keputusan bila menyangkut pilihan penelitian (varian,
  ambang, cakupan). Pilihan teknis murni boleh diputuskan sendiri dan dicatat sebagai D-xxx.
- Bila menemukan bug di kode lama, perbaiki + tambah tes regresi + catat D-xxx (contoh: D-022).
- Bila file berubah di disk tanpa sebab (OneDrive, user, sesi lain), **jangan** langsung membalikkan; laporkan dan tanya
  (contoh nyata: user memindah isi `src/kagami/` ke `src/`, menjadi D-024).

### 3.3 Selesai
0. **Sinkronkan dokumen** menurut §3.4 untuk SETIAP perubahan sesi ini (kode, config, data, keputusan, proses).
1. `pytest` hijau (seluruh suite; ± 1 menit) — termasuk `tests/test_docs_sync.py` yang menolak dokumen basi.
2. Status WP ✅ di papan + perbarui bagian WP (angka penting, catatan hilir).
3. Perbarui §2 dan §9 dokumen ini (fungsi yang kini ✔).
4. Entri baru di atas **bagian anggota sendiri** di `docs/SESSION_LOG.md` (template §26.1).
4a. Bila pekerjaan memengaruhi anggota lain (artefak terbit, permintaan, keputusan, blokir, angka makalah): buat handoff
    `docs/handoff/YYYYMMDD-HHMM_<dari>-ke-<ke>_<topik>.md` dari template `docs/HANDOFF.md` §3 + versi pendek chat (§5).
    Handoff yang sudah ditindaklanjuti: ubah `status` (diterima/selesai) dan centang kotaknya.
5. Keputusan → `docs/DECISIONS.md` (template §26.2). Isu → `docs/OPEN_ISSUES.md` (template §26.3).
6. Bila `src/` berubah: ingatkan user bahwa bundle Kaggle/Drive perlu diperbarui (`python -m kagami bundle`).
7. Tutup turn dengan ringkasan + pertanyaan langkah berikutnya (tanpa command git kecuali diminta, §4.6).

### 3.4 Sinkronisasi dokumen (wajib; dokumen tidak boleh kadaluarsa)
Dokumen hidup (`README.md`, `CLAUDE.md`, `docs/*.md` selain catatan bertanggal) harus selalu menggambarkan keadaan
**saat ini**. Perbarui dokumen pada sesi yang sama dengan perubahannya — tidak ditunda ke sesi lain atau ke anggota lain.

| Jenis perubahan | Dokumen yang wajib diperbarui |
|---|---|
| Implementasi/stub WP berubah status | `docs/WORKPLAN.md` (papan + heading WP), CLAUDE.md §2 (daftar Selesai) & §9 (✔/⬜) |
| Fungsi publik baru/hapus/ganti nama/signature | CLAUDE.md §9; docstring; `docs/ARCHITECTURE.md` §2 bila modul baru |
| Modul/subpaket/folder baru atau dipindah | `docs/ARCHITECTURE.md` §2, CLAUDE.md §5–§6 & §9, `pyproject.toml` (packages), PEMBAGIAN_TUGAS §3 (pemilik) |
| Artefak/kolom baru | `src/utils/artifacts.py` + `docs/ARCHITECTURE.md` §5 + CLAUDE.md §8/§9.1 (jumlah artefak) + handoff `KEPUTUSAN` |
| `configs/params.yaml` berubah | CLAUDE.md §11.3, `docs/METHODS.md` bila rumus/ambang, PREREGISTRATION (setelah G6: DEVIASI di DECISIONS) |
| `configs/commodities.yaml` berubah | CLAUDE.md §11.1, `docs/PROJECT_OVERVIEW.md` §5 bila lingkup, DECISIONS |
| Sumber data baru/berubah | `configs/sources.yaml`, `docs/DATASETS.md`, CLAUDE.md §10, `tests/test_loaders.py` |
| Fakta data baru (cakupan, keanehan, angka) | `docs/DATASETS.md`, CLAUDE.md §10.2–§10.3; heading WP terkait |
| Keputusan | `docs/DECISIONS.md` + CLAUDE.md §21; dokumen yang isinya berubah karena keputusan itu |
| Isu baru/selesai | `docs/OPEN_ISSUES.md` + CLAUDE.md §22 |
| Metode/rumus | `docs/METHODS.md`, CLAUDE.md §12, docstring stub |
| Jadwal/gerbang/PIC | `docs/WORKPLAN.md`, `docs/PEMBAGIAN_TUGAS.md` §4, CLAUDE.md §13 |
| Notebook/runtime/cloud | `docs/NOTEBOOKS.md`, `docs/ARCHITECTURE.md` §3, CLAUDE.md §7 & §17 |
| Perintah CLI/cara menjalankan | `README.md`, `docs/ARCHITECTURE.md` §4, CLAUDE.md §4.4 |
| Aturan proses/tim (git, handoff, kepemilikan) | CLAUDE.md §3–§4, `docs/PEMBAGIAN_TUGAS.md`, `docs/HANDOFF.md` |
| Tes baru | CLAUDE.md §16.1, `docs/ARCHITECTURE.md` §2 (daftar tests) |
| Jebakan/bug baru ditemukan | CLAUDE.md §23 (+ D-xxx bila mengubah desain) |

Aturan menulis agar tidak cepat basi:
- Jangan menulis angka yang berubah sendiri di dokumen hidup (jumlah tes lolos, "kemarin", "minggu depan"); tulis tanggal
  absolut. Angka hasil data boleh, dengan nama artefak sumbernya.
- Satu fakta punya satu sumber kebenaran (§0.2); dokumen lain cukup merujuk atau meringkas. Bila meringkas, perbarui
  ringkasannya bersamaan.
- Catatan bertanggal — `docs/SESSION_LOG.md`, `docs/DECISIONS.md` (isi entri lama), `docs/handoff/*.md` — adalah jejak
  sejarah: jangan menulis ulang isinya. Keputusan yang berubah → entri baru / status `DIGANTI oleh D-xxx`.
- Penjaga otomatis: `tests/test_docs_sync.py` (tautan & path, papan WP vs stub, §2 vs papan, ID D-/U-, kunci `params.*`,
  sumber data, komoditas, notebook, subpaket), `tests/test_claude_md.py` (§9), `tests/test_wiring.py` (artefak di
  ARCHITECTURE), `tests/test_handoff.py` (format handoff). Tes hijau ≠ dokumen lengkap: matriks di atas tetap wajib.

---

## 4. Lingkungan & perkakas

### 4.1 Mesin user
- Windows 11, Python 3.13.7. Shell tool agent = **Git Bash** (sintaks POSIX); perintah yang diberikan ke user ditulis
  dalam blok `powershell`.
- Folder project ada di **OneDrive**: `C:\Users\HYPE R Series\OneDrive - Institut Teknologi Bandung\Documents\ITB\Competition\datmin`.
  Path mengandung spasi → selalu beri tanda kutip. OneDrive bisa menyinkronkan/mengubah file; perlakukan perubahan tak
  terduga sebagai disengaja sampai dikonfirmasi.
- Folder ini repo git (`main`, remote `origin` = github.com/danenftyessir/kurs-associated-grocery-analysis-of-markets-in-indonesia).
  **Agent dilarang commit/push** — lihat §4.6. Branch hanya `main`, `dev`, `feat/<topik>` (§4.6, D-103).
- Perangkat lokal terbatas: tahap berat (task1, task2, task4, robustness) dijalankan di Kaggle/Colab (§17).

### 4.2 Paket terpasang
numpy 2.3, pandas 2.3, scipy 1.16, scikit-learn 1.8, pyarrow 24, openpyxl 3.1, pyyaml 6, streamlit 1.57, plotly 6.7,
matplotlib 3.10, pytest 9.1, nbformat 5.10, joblib 1.5. Opsional `[drive]` (google-api-python-client, google-auth,
google-auth-oauthlib) untuk `drive-pull/push/auth` di lokal; belum terpasang di mesin Danen, sudah ada di Kaggle/Colab. **Tidak ada** statsmodels/linearmodels (D-009) — jangan
menambahkannya; pakai `src/stats/`.

### 4.3 Struktur paket (D-024)
Isi paket `kagami` ada **langsung di `src/`** (bukan `src/kagami/`). Import tetap `from kagami.x import ...`.
`pyproject.toml` memetakan `package-dir = {kagami = "src"}` dengan daftar `packages` eksplisit → subpaket baru di
`src/` wajib ditambahkan ke daftar itu. Jangan tambahkan `src` ke `PYTHONPATH` (modul `data`, `utils`, ... akan
terbaca sebagai modul top-level) dan jangan membuat folder `src/kagami/` (akan menutupi paket).

### 4.4 Menjalankan kode
- Dengan instalasi (sekali): `pip install -e ".[dev]"` lalu `python -m kagami <cmd>`.
- Tanpa instalasi: `pytest` dan app sudah punya alias (`tests/conftest.py`, `app/common.py`). Skrip ad-hoc:

```python
import importlib.util, sys
spec = importlib.util.spec_from_file_location("kagami", "src/__init__.py", submodule_search_locations=["src"])
mod = importlib.util.module_from_spec(spec); sys.modules["kagami"] = mod; spec.loader.exec_module(mod)
from kagami.utils.config import get_config
cfg = get_config()
```

  (jalankan dari root project). CLI tanpa instalasi: tambahkan `from kagami.cli import main; main(["status"])`.
- Hasil cloud ke lokal: `python -m kagami drive-pull all` (butuh token, §7.3). Hasil lokal ke tim: `drive-push <tahap>`.
- Data mentah dari Drive tim: `python -m kagami drive-pull-raw` (tidak menimpa). Danen memperbarui: `drive-push-raw`.

### 4.5 Jebakan perkakas yang sudah terjadi
- `Path.write_text` di Windows menulis **CRLF**. Semua file teks project sudah dinormalkan ke LF; saat mengedit lewat
  skrip Python, pakai `p.write_bytes(text.encode("utf-8"))` atau `open(p, "w", newline="\n")`, atau gunakan tool Edit/Write.
- Heredoc bash berisi tanda kutip tunggal/backtick dalam jumlah banyak bisa gagal ("unexpected EOF"). Untuk dokumen
  panjang pakai tool Write; untuk skrip, tulis file ke scratchpad lalu jalankan.
- Tool Write menolak menimpa file yang belum dibaca di sesi ini → Read dulu (cukup beberapa baris).
- `pdftotext` tersedia (`/mingw64/bin/pdftotext`) untuk membaca PDF di `docs/`; hasilnya bukan UTF-8 murni.
- File sementara → direktori scratchpad sesi, bukan folder project.
- Output tes lambat: `tests/test_loaders.py` (~25 dtk) dan `tests/test_app.py` memuat data/streamlit; jalankan subset
  dengan `-k` saat iterasi, seluruh suite sebelum selesai.

### 4.6 Git: agent TIDAK commit/push; command siap copas hanya bila diminta
Aturan tim (permintaan Danen, 2026-11-20; diperbarui: command hanya atas permintaan). Berlaku untuk semua agent di semua clone.
- **Dilarang dijalankan agent:** semua perintah yang mengubah index, riwayat, branch, atau remote — `git add`, `commit`,
  `push`, `pull`, `fetch`, `merge`, `rebase`, `reset`, `restore --staged`, `checkout`/`switch`, `branch` (buat/hapus),
  `stash`, `tag`, `cherry-pick`, `revert`, `remote add/set-url`, `gh pr create/merge`, serta fitur commit/PR otomatis
  dari aplikasi. Juga dilarang `git init` ulang atau menghapus `.git/`.
- **Boleh dijalankan agent (baca-saja):** `git status`, `git diff`, `git log`, `git show`, `git branch --show-current`,
  `git check-ignore`, `git ls-files`, `git remote -v` — hanya bila diperlukan untuk tugas atau permintaan user.
- **Jangan menawarkan atau menyiapkan command git secara otomatis** di akhir pekerjaan. Siapkan hanya bila user memintanya
  (mis. "buatin command git-nya"). Formatnya bila diminta: blok `powershell` siap copas, satu perintah per blok, urut:
  1. `git status` (cek), 2. `git add` dengan **path eksplisit** file yang diubah sesi ini (bukan `git add .` atau `-A`),
  3. `git commit -m "<pesan>"`, 4. `git push` ke branch `feat/<topik>` yang sedang dipakai — tidak pernah langsung ke
  `main` atau `dev`. Pesan commit: bahasa Indonesia, diawali kode WP, contoh `WP-06: episode depresiasi & mark_episode_weeks`.
- Sebelum menyusun `git add`, periksa dengan `git status --short` bahwa tidak ada file data mentah/turunan PIHPS yang lolos
  `.gitignore` (lihat §19). Bila ada, laporkan dan perbaiki `.gitignore`, bukan memasukkannya ke `git add`.
- Branch/PR/merge diputuskan dan dijalankan oleh anggota sendiri. Agent boleh menyiapkan command-nya bila diminta.
- **Aturan branch (D-103): hanya tiga jenis branch.**
  | Branch | Isi | Dibuat dari | Masuk ke |
  |---|---|---|---|
  | `main` | versi stabil (titik gerbang, pembekuan hasil 27 Nov, versi submission) | – | – (tidak ada commit langsung) |
  | `dev` | integrasi pekerjaan semua anggota | `main` | `main` lewat PR saat stabil |
  | `feat/<topik>` | satu WP / satu topik pekerjaan (kode atau dokumen) | `dev` | `dev` lewat PR, lalu dihapus |
  - Nama `feat/` huruf kecil + tanda hubung, diawali kode WP bila ada: `feat/wp06-episode`, `feat/wp07-reference-tables`,
    `feat/docs-branch-rules`. Tidak ada nama lain (`fix/`, `hotfix/`, `danen/...`, dll.): perbaikan bug juga `feat/<topik>`.
  - Tidak ada commit/push langsung ke `main` atau `dev`; semua lewat PR. Satu `feat/` dikerjakan satu anggota.
  - Abi tidak memakai git (berkas lewat Drive; Danen/Ardell yang meng-commit di `feat/` mereka).
  - Agent tetap tidak membuat branch/commit/push/PR; bila user meminta command, gunakan skema ini.

---

## 5. Peta repo

```
datmin/
├── CLAUDE.md                 dokumen ini
├── README.md                 ringkasan untuk manusia/juri (cara jalan, hak data)
├── .gitignore                mentah/turunan PIHPS/results tidak di-track (kecuali checksums, manual_regulation, findings.md)
├── pyproject.toml            dependensi, package-dir, daftar packages, pytest
├── configs/
│   ├── params.yaml           SEMUA angka analisis (dibekukan di G6)
│   ├── commodities.yaml      10 komoditas: varian, peran, jalur eksposur, padanan Pink Sheet, HS, FAOSTAT
│   ├── sources.yaml          20 sumber mentah: path relatif raw_dir, lisensi, redistribute, retrieval, availability
│   └── runtime.yaml          folder Drive tim (ID), kredensial Drive, folder kerja Colab (bukan parameter analisis)
├── data/
│   ├── raw/<sumber>/         snapshot mentah (TIDAK pernah ditimpa; salinan di Drive tim, D-101); raw/checksums.csv
│   ├── raw/_superseded/      versi lama yang digantikan (tidak dipakai, tidak diunggah)
│   ├── reference/            tabel buatan tim: region_crosswalk.csv, province_aliases.csv (+ hasil WP-07)
│   ├── interim/              pihps_daily.parquet, forecast_preds.parquet (boleh dihapus)
│   └── processed/            panel_weekly, panel_weekly_region, drivers_weekly, world_prices_weekly
├── results/                  stage0/, task1/, task2/, task3/, task4/, robustness.csv, findings.md
├── notebooks/                00_stage0_data … 05_robustness (.ipynb, tanpa output)
├── src/                      paket kagami (§6, §9)
├── app/                      Streamlit: Home.py (hal. 1), pages/2..6, common.py
├── tests/                    §16
├── docs/                     proposal & juknis (PDF) + dokumen kerja (§0.2); docs/arsip/ = inventaris dataset xlsx (arsip)
│   └── handoff/              satu file per serah-terima antar anggota (format docs/HANDOFF.md, dites)
└── dist/                     (dibuat oleh bundle/package; boleh dihapus)
```

---

## 6. Arsitektur lapisan (D-026)

```
utils  ←───────────── dipakai semua lapisan
stats  ←───────────── dipakai features/models/evaluation
data → features → models → evaluation → pipelines → (cli, notebooks) ; viz ← (app, notebooks)
```

| Lapisan | Tanggung jawab | Boleh import | Tidak boleh |
|---|---|---|---|
| `utils` | config, runtime, registry artefak, I/O, tanggal, stub | stdlib, pandas, yaml | import lapisan lain |
| `stats` | fungsi statistik murni (numpy/scipy) | numpy, scipy, pandas | baca/tulis file, Config |
| `data` | baca mentah, bersihkan, agregasi mingguan, penggerak, tabel referensi, QA | utils | estimasi model, write_artifact |
| `features` | turunan siap model (fitur respons, matriks clustering, fitur as-of) | utils, stats, data (fungsi murni) | baca file mentah |
| `models` | estimator: LP, deviasi, event study, clustering, asosiasi, peramalan | utils, stats, features | write_artifact |
| `evaluation` | inferensi, uji, metrik, MDE, robustness | utils, stats, features, models | write_artifact |
| `pipelines` | urutan langkah, `require` input, `write_artifact` | semua lapisan | logika analisis |
| `viz` | grafik plotly dari artefak | pandas, plotly | menghitung estimasi |

Aturan praktis:
- Fungsi lapisan bawah menerima & mengembalikan DataFrame/ndarray; yang membaca/menulis artefak hanya `pipelines/`.
  Pengecualian yang disengaja: `data/snapshot.run` dan `data/download.run` (operasi file mentah, dipanggil CLI).
- Satu fungsi yang dipakai ≥ 2 task dan bersifat statistik murni → pindahkan ke `stats/` + tes.
- Grafik baru → `viz/plots.py` dan harus dipakai app atau notebook (tes menolak fungsi viz yatim).
- Modul baru wajib terjangkau dari CLI atau di-import app/notebook (tes `test_every_module_used`).

---

## 7. Config & runtime (D-027)

### 7.1 `Config` (`src/utils/config.py`, dataclass frozen)

| Atribut / properti | Arti | Default lokal |
|---|---|---|
| `root` | folder kode (berisi `configs/params.yaml`) | dicari naik dari file config.py; env `KAGAMI_ROOT` |
| `raw_root` → `raw_dir` | folder data mentah; `sources.yaml: path` relatif ke sini | `root/data/raw`; env `KAGAMI_RAW_DIR` |
| `out_root` → `out_dir` | folder TULIS artefak | `root`; env `KAGAMI_OUT_DIR` |
| `artifact_dirs` | folder BACA tambahan (output tahap sebelumnya) | kosong; env `KAGAMI_ARTIFACT_DIRS` (pemisah `os.pathsep`) |
| `read_dirs` | urutan baca: out_dir → artifact_dirs → root | – |
| `reference_dir` | `root/data/reference` (tabel tim yang ikut kode) | – |
| `params`, `commodities`, `sources`, `runtime` | isi YAML (cached) | – |
| `regions`, `province_aliases` | CSV referensi (cached) | – |
| `source_path(key)` | `raw_dir / sources[key].path` | – |
| `source_files(key)` | daftar file konkret (mengurai `glob`) | – |
| `commodity_ids(role)` | id komoditas, opsional filter peran | – |
| `seed` | `params.seed` | 20261121 |
| `path(rel)` | `root / rel` (untuk configs/app, BUKAN artefak) | – |

### 7.2 Runtime per platform (`src/utils/env.py::init_runtime`)

| Platform | Deteksi | root | raw_dir | out_dir | artifact_dirs |
|---|---|---|---|---|---|
| local | default | folder project | `data/raw` | folder project | – |
| kaggle | env `KAGGLE_KERNEL_RUN_TYPE` atau `/kaggle/input` ada | dataset `kagami-code` | dataset `kagami-raw` bila dilampirkan (folder berisi `bi_pihps/`, kedalaman ≤ 3), selain itu `/kaggle/temp/kagami_raw` (pull dari Drive) | `/kaggle/working` | input yang memuat `results/`, `data/processed/` atau `data/interim/` (cadangan) |
| colab | `google.colab` ter-import / env `COLAB_RELEASE_TAG` | `DRIVE_DIR` | `DRIVE_DIR/data/raw` bila ada, selain itu `/content/kagami_raw` (pull dari Drive) | `/content/kagami_out` (`runtime.yaml`) | – |

`DRIVE_DIR` default `/content/drive/MyDrive/kagami` (kode & mentah). Env `KAGAMI_*` selalu menang.

### 7.3 Folder Drive tim (D-100)
- Semua artefak antar tahap/anggota disimpan di folder Drive tim https://drive.google.com/drive/folders/15T5ry1VIP_ZhzXqdVAwPLI4vfRySOx8D (ID di `configs/runtime.yaml`),
  dengan struktur = path artefak (`results/task1/profiles.parquet`, `data/processed/...`).
- Data mentah di `data/raw/` folder itu (D-101): `utils.drive.push_raw` (MD5 sama dilewati) / `pull_raw` (hanya file yang
  belum ada, tidak menimpa); CLI `drive-push-raw` / `drive-pull-raw`; notebook 00 memanggil `pull_raw`.
- `utils.drive.pull(cfg, names)` → unduh ke `cfg.out_dir`; `utils.drive.push(cfg, stages)` → unggah semua artefak milik tahap
  itu (timpa versi lama). Notebook memanggil keduanya; lokal lewat CLI `drive-pull` / `drive-push`.
- Kredensial: Colab login Google interaktif; Kaggle Secret `KAGAMI_DRIVE_TOKEN` (token OAuth akun anggota, Internet ON);
  lokal `~/.kagami/drive_token.json` (env `KAGAMI_DRIVE_TOKEN_FILE`) dari `python -m kagami drive-auth --client-secret F`.
- Default `strict`: Kaggle/Colab gagal keras bila Drive tak tersedia; lokal dilewati dengan pesan.
- Agent tidak boleh membuat/mengisi token, login ke akun Google/Kaggle user, atau mengubah izin berbagi folder — `[HUMAN]`.
- Token & `client_secret*.json` tidak pernah di-commit (`.gitignore`). Folder dibagikan terbatas ke akun anggota (U24).

### 7.3 Aturan
- Kode tahap TIDAK PERNAH menulis ke `raw_dir` atau `root`; semua tulisan lewat `write_artifact` → `out_dir`.
  (`download` menulis ke `out_dir/data/raw/_redownload/`.)
- Jangan memakai `cfg.path(...)` untuk artefak; pakai `utils.io`.
- Jangan hard-code `/kaggle/...` atau `/content/...` di luar `utils/env.py`.

---

## 8. Artefak & I/O

### 8.1 API (`src/utils/io.py`)
- `write_artifact(cfg, name, df_or_md)` → tulis ke `cfg.out_dir / ARTIFACTS[name].path`; validasi kolom wajib
  (kolom ekstra boleh). Parquet/CSV/MD menurut ekstensi.
- `read_artifact(cfg, name)` → baca dari lokasi pertama di `read_dirs`; validasi kolom; `ArtifactMissing` bila tak ada.
- `find_artifact`, `exists`, `artifact_path` (lokasi tulis), `require(cfg, *names)` (gagal cepat dengan petunjuk).
- `utils.env.artifact_status(cfg, stage=None)` → tabel ada/lokasi/WP (dipakai CLI `status` dan notebook).

### 8.2 Menambah/mengubah artefak (checklist)
1. Tambah/ubah entri di `src/utils/artifacts.py` (name, path relatif out_dir, stage, wp, kolom wajib, ship, deskripsi).
2. Tulis dari `pipelines/<tahap>.py` dengan `write_artifact(cfg, "<name>", ...)` (tes memeriksa pola ini).
3. Perbarui tabel `docs/ARCHITECTURE.md` §5 (tes memeriksa setiap nama artefak tercantum dengan backtick).
4. Bila dibaca tahap lain: tambahkan ke `REQUIRES` pipeline konsumen.
5. Bila dikirim ke juri (`ship=True`): pastikan tidak bisa merekonstruksi data mentah tanpa hak (D-015).
6. Bila dipakai app: tambahkan ke `need(...)` halaman terkait.

### 8.3 Konvensi kolom
- `week`: Timestamp Senin minggu ISO (`utils.dates.week_start`). Semua join antar sumber memakai ini (D-020).
- `commodity`: id internal snake_case (`beras`, `bawang_putih`, …), bukan nama PIHPS.
- `province_id`: int 1–34 (kerangka 34 provinsi lama, urutan PIHPS); `region`: 7 nilai di `region_crosswalk.csv`.
- `level` ∈ {national, region, province}; `unit` = `ALL` / nama wilayah / province_id (disimpan sebagai string bila campur).
- `driver` ∈ {e, w, e_pos, e_neg, PT}. Respons dalam Δ log harga per 1 poin log penggerak.
- Harga dalam log natural; perubahan = selisih log.
- Interval: `ci_low`, `ci_high` (95%). Setiap estimasi yang dilaporkan wajib punya interval.

### 8.4 Kebijakan `ship` (dikirim ke juri)
- Tidak dikirim: `pihps_daily`, semua mentah dengan `redistribute: false`. `panel_weekly` (panel provinsi mingguan) DIKIRIM:
  izin BI mencakup redistribusi data turunan (U13, D-104).
- Dikirim: panel 7 wilayah sebagai **indeks log** (relatif minggu pertama), penggerak sebagai log/perubahan log,
  semua hasil estimasi, tabel tim, sumber CC BY (Pink Sheet, FAOSTAT, FRED, tabel regulasi tim).

---

## 9. Inventaris modul & fungsi (dijaga `tests/test_claude_md.py`)

Format baris: `` - `nama` · ✔ · keterangan `` (sudah diimplementasi) atau `` - `nama` · ⬜ WP-xx · keterangan `` (stub).
Semua fungsi publik top-level (tanpa awalan `_`) di setiap modul `src/` wajib tercantum dengan status yang benar.
Saat mengimplementasikan stub: ganti `⬜ WP-xx` menjadi `✔` dan perbarui keterangan bila kontrak berubah.

### 9.1 Infrastruktur

#### src/cli.py
- `status` · ✔ · cetak sumber mentah (ada/tidak) dan artefak (ada, lokasi, WP, ship).
- `main` · ✔ · argparse: status, snapshot, download, stage0..robustness, all, package, bundle [--raw], app,
  drive-pull [TAHAP|all], drive-push TAHAP, drive-push-raw, drive-pull-raw, drive-auth --client-secret.

#### src/utils/config.py
- `get_config` · ✔ · `Config()` dengan default + env var.

#### src/utils/env.py
- `detect_platform` · ✔ · "kaggle" | "colab" | "local".
- `kaggle_raw_dir` · ✔ · cari folder input berisi `bi_pihps/`.
- `kaggle_artifact_dirs` · ✔ · cari input yang memuat results/ atau data/processed|interim/.
- `init_runtime` · ✔ · bangun Config per platform; cetak ringkasan lokasi.
- `describe` · ✔ · teks ringkasan lokasi (root, raw, out, artifact_dirs).
- `artifact_status` · ✔ · DataFrame artefak: available, location, wp, ship (opsional per stage).

#### src/utils/io.py
- `artifact_path` · ✔ · lokasi tulis.
- `find_artifact` · ✔ · lokasi baca pertama atau None.
- `exists` · ✔ · artefak ada di salah satu read_dirs.
- `write_artifact` · ✔ · tulis + validasi kolom.
- `read_artifact` · ✔ · baca + validasi kolom; `ArtifactMissing`.
- `require` · ✔ · gagal cepat bila input tahap belum ada.

#### src/utils/drive.py
(kelas `GoogleDriveClient` = pembungkus Drive API v3; `DriveClient` = protokol untuk tes; `DriveUnavailable`)
- `credentials` · ✔ · kredensial Google per platform (Colab login, Kaggle Secret, file token lokal).
- `connect` · ✔ · bangun klien Drive API v3; `DriveUnavailable` bila library/kredensial tidak ada.
- `pull` · ✔ · unduh artefak `names` dari folder Drive tim ke out_dir; laporkan yang belum ada di Drive.
- `push` · ✔ · unggah artefak milik `stages` dari out_dir ke folder Drive tim (path dicerminkan, timpa versi lama).
- `authorize_local` · ✔ · OAuth di browser → simpan token JSON (isi untuk Kaggle Secret).
- `push_raw` · ✔ · unggah semua file sumber + checksums ke `data/raw/` Drive tim; MD5 sama dilewati (D-101).
- `pull_raw` · ✔ · unduh file sumber yang belum ada di raw_dir (termasuk sumber glob); tidak pernah menimpa (D-101).

#### src/utils/dates.py
- `week_start` · ✔ · tanggal → Senin minggu ISO (normalize).

#### src/utils/todo.py
- `todo` · ✔ · lempar `NotImplementedYet("WP-xx ...")`.

#### src/utils/artifacts.py
(Tidak ada fungsi publik; berisi dataclass `Artifact` dan dict `ARTIFACTS` — 31 artefak.)

### 9.2 Lapisan data

#### src/data/loaders.py
- `norm_name` · ✔ · trim + spasi tunggal (mis. "Cabai Merah Keriting " → tanpa spasi akhir).
- `province_lookup` · ✔ · NAMA UPPER → province_id (crosswalk + alias + pemekaran).
- `map_province` · ✔ · Series nama → Int64 province_id (NaN bila tak dikenal, mis. "INDONESIA").
- `load_jisdor` · ✔ · → date, idr_per_usd (parse "9.760,00").
- `load_pihps` · ✔ · zip 34 CSV lebar → long: date, province_id, province, level, commodity_group, item, price; grup varian dari prefiks nama (D-022).
- `load_pihps_manifest` · ✔ · MANIFEST.csv di zip v2 atau None.
- `load_pinksheet` · ✔ · sheet "Monthly Prices" → month, series (dinormalisasi, tanpa `**`), unit, usd_price.
- `load_fred` · ✔ · key brent|dollar_index → date, value (hari libur dibuang).
- `load_faostat_sua` · ✔ · SUA Asia NOFLAG, filter Indonesia → year, item, element, unit, value.
- `load_bps_import_monthly` · ✔ · → month, hs8_code (str), hs_description, import_value_usd, import_netweight_kg.
- `load_bps_import_annual` · ✔ · 5 xlsx exim → hs8_code, hs_description, year, total (USD, D-019), file.
- `load_comtrade` · ✔ · → month, hs_code, hs_description, net_weight_kg, cif_usd, primary_value_usd.
- `load_bapanas_panel` · ✔ · → month, commodity_bapanas, province_id, province, price_geomean, status_map, ref_price.
- `load_bapanas_het_settings` · ✔ · → commodity_bapanas, type, zone, price, start_date, end_date.
- `load_padi` · ✔ · tahun 2024|2025 → year, province_raw, province_id, harvest_ha, productivity_ku_ha, production_ton_gkg.
- `load_konsumsi_beras` · ✔ · → province_raw, province_id, year, kg_per_capita_year.
- `load_neraca_beras` · ✔ · kolom asli neraca beras nasional.
- `load_het_hap_current` · ✔ · kolom asli tabel HET/HAP berlaku.
- `load_regulation_history` · ✔ · kolom asli riwayat regulasi.
- `load_jarak_hub` · ✔ · → province_raw, province_id, capital, lat, lon, km_jakarta/surabaya/makassar, nearest_hub, dist_hub_km, ln1p_dist_hub (38 prov).
- `load_konkordansi_hs` · ✔ · konkordansi Comtrade → HS8 BPS, kode sebagai string, kolom asli.
- `load_hortikultura` · ✔ · → commodity_atap, province_raw, province_id, year, production_ton, note (baris nasional dibuang).

#### src/data/snapshot.py
- `sha256_file` · ✔ · hash file bertahap.
- `build_checksums` · ✔ · hash semua `source_files`; kolom `file` relatif raw_dir; pertahankan waktu catatan bila hash sama.
- `run` · ✔ · tulis artefak `checksums`.

#### src/data/download.py
- `find_link` · ✔ · tautan pertama di HTML yang cocok pola (dites tanpa jaringan).
- `resolve_url` · ✔ · tautan terbaru dari `landing_url`+`link_pattern` bila ada, selain itu `url` (U16).
- `download` · ✔ · sumber http → `out_dir/data/raw/_redownload/<key>/` (SSL via certifi) + bandingkan hash; manual → instruksi.
- `run` · ✔ · semua sumber atau daftar kunci.

#### src/data/weekly.py
- `select_variants` · ✔ · varian representatif per komoditas → pihps_daily (hanya hari teramati, harga > 0); error bila varian tak ada.
- `aggregate_weekly` · ✔ · grid 34×10×minggu; price = rerata hari teramati; status (D-021); kolom ekstra cf_share.
- `eligibility` · ✔ · missing_share ≤ 0,20, max_gap_weeks ≤ 8, min_year_coverage ≥ 0,70; hanya `missing` dihitung kosong.

#### src/data/drivers.py
- `driver_weeks` · ✔ · grid minggu penggerak: start − 52 minggu .. minggu freeze.
- `idulfitri_relative_week` · ✔ · minggu relatif Idulfitri terdekat dalam jendela [−6, 4], selain itu NaN.
- `build_national_drivers` · ✔ · log_e, de, de_pos, de_neg, log_brent, db, log_dxy, d_dxy, month, idf_rel_week, *_filled (tanpa episode).
- `build_world_prices` · ✔ · komposit Pink Sheet per komoditas, log_w_idr = log_w_usd + rerata log JISDOR bulanan; dw; available_at.
- `mark_episode_weeks` · ⬜ WP-06 · tambah kolom `episode` (0/1) ke drivers dari tabel episodes.
- `find_episodes` · ⬜ WP-06 · Σ de 8 minggu ≥ 0,03; gabung tumpang tindih → episode_id, start_week, end_week, cum_dlog_e.
- `fx_variation_table` · ⬜ WP-06 · jumlah & besar minggu depresiasi/apresiasi per tahun + total.

#### src/data/reference.py
- `haversine_km` · ✔ · jarak great-circle (km).
- `build_concordance` · ⬜ WP-07 · 10 baris PIHPS–HS–Pink Sheet–FAOSTAT + confidence.
- `build_exposure` · ⬜ WP-07 · rasio impor langsung (FAOSTAT; bawang putih via BPS/Comtrade), ordinal input impor, link harga dunia, source.
- `build_regulation` · ⬜ WP-07 · gabung 3 sumber regulasi; tanggal tak terverifikasi → verification='unverified'.
- `build_province_features` · ⬜ WP-07 · dist_hub_km, ln_dist_hub = ln(1+km), rice_sufficiency (butuh populasi, U14), n_kota (U15).

#### src/data/panel.py
- `build_region_panel` · ⬜ WP-08 · rerata log provinsi eligible per wilayah → indeks relatif minggu pertama + n_provinces.

#### src/data/qa.py
- `flag_price_outliers` · ⬜ WP-10 · lonjakan satu hari |Δlog| > 0,5 yang berbalik (ditandai, tidak dihapus).
- `check_import_totals` · ⬜ WP-10 · Σ BPS bulanan vs total tahunan.
- `check_bapanas_bias` · ⬜ WP-10 · rerata bulanan PIHPS vs Panel Harga Bapanas.
- `stage0_report` · ⬜ WP-10 · markdown laporan Tahap 0.

### 9.3 Lapisan features

#### src/features/response.py
- `shrink_deviations` · ⬜ WP-17 · τ² DL (+REML cek) per (komoditas, driver, h); tambah baris province shrunk=True.
- `response_features` · ⬜ WP-17 · R4/R8/R12, W4/W8/W12, PT8, t_half, A8.

#### src/features/clustering.py
- `feature_matrix` · ⬜ WP-19 · 34 provinsi × (R & W pada h 4/8/12 komoditas fokus), tersusut, z-score.
- `replicate_feature_matrices` · ⬜ WP-19 · satu matriks per rep dari placebo_stats / boot_replicates.

#### src/features/forecast.py
(konstanta `FEATURE_GROUPS`: base / fx / id)
- `origins` · ⬜ WP-25 · origin tiap 4 minggu 2021-01-04 .. freeze − h.
- `build_features` · ⬜ WP-25 · (train, test) per origin; as-of join `available_at`; target p_{t+h} − p_t.

### 9.4 Lapisan models

#### src/models/local_projection.py
- `build_design` · ⬜ WP-13 · y^{(h)} dan regresor (de/dw + lag, db lag 0..4, musiman), within-transform per seri.
- `fit_lp` · ⬜ WP-13 · OLS + SE cluster per minggu (`stats.regression.ols_cluster`).
- `fx_self_response` · ⬜ WP-13 · γ(h) untuk PT = β/γ.
- `national_profiles` · ⬜ WP-13 · loop komoditas × h 0..12 × {simetris, asimetris} → profiles level=national.

#### src/models/deviations.py
- `demean_cross_section` · ⬜ WP-15 · log harga − rerata lintas provinsi per (minggu, komoditas).
- `province_deviations` · ⬜ WP-15 · δ(i,r,h) per provinsi, Σ_r δ = 0.
- `region_profiles` · ⬜ WP-15 · profil 7 wilayah dari panel_weekly_region (Tingkat B).

#### src/models/event_study.py
- `event_paths` · ⬜ WP-14 · Δ log harga 0..12 minggu setelah start_week tiap episode.
- `placebo_bands` · ⬜ WP-14 · 499 jendela plasebo → placebo_lo/hi/p; gabung jadi artefak events.

#### src/models/clustering.py
- `ward_labels` · ⬜ WP-19 · Ward Euclidean; k=1 → semua 0.
- `select_k` · ⬜ WP-19 · silhouette maks asli vs p95 plasebo → cluster_selection.

#### src/models/association.py
- `kendall_exact` · ⬜ WP-22 · Kendall τ PT(8) vs rasio impor, permutasi eksak, LOCO.
- `meta_regression` · ⬜ WP-23 · meta-regresi efek acak δ ~ Z(r); interval max(bootstrap, CR2); jackknife.
- `fe_interaction` · ⬜ WP-24 · FE komoditas×minggu, interaksi Δe × Z(r) (dapat dipotong).

#### src/models/forecasting.py
(konstanta `MODELS` = M0..M3)
- `fit_predict` · ⬜ WP-26 · M0 nol, M1 ridge base, M2 + fx, M3 HGB + id; drop_groups untuk ablation.
- `rolling_predictions` · ⬜ WP-26 · loop horizon × origin × model → prediksi (disimpan data/interim/forecast_preds.parquet).

### 9.5 Lapisan evaluation

#### src/evaluation/power.py
- `compute_mde` · ⬜ WP-09 · MDE β & PT dari residual LP tanpa kurs, nasional & 7 wilayah, h 4/8/12.

#### src/evaluation/inference.py
- `joint_bootstrap` · ⬜ WP-16 · moving-block 13 minggu, satu indeks per replikasi untuk semua seri.
- `circular_placebo` · ⬜ WP-16 · np.roll de & dw ≥ 52 minggu; profil di bawah null.
- `bootstrap_ci` · ⬜ WP-16 · CI = yang lebih lebar dari ±1,96·SE dan persentil bootstrap.

#### src/evaluation/heterogeneity.py
- `heterogeneity_stats` · ⬜ WP-18 · Q, τ², I² per komoditas (h=8) + ρ̄ lintas komoditas.
- `placebo_pvalues` · ⬜ WP-18 · p plasebo + q BH → artefak heterogeneity.

#### src/evaluation/stability.py
- `kmeans_agreement` · ⬜ WP-20 · K-Means (n_init=50) + ARI vs Ward.
- `bootstrap_stability` · ⬜ WP-20 · ko-asignasi + Jaccard per klaster (weak < 0,6).
- `compare_partitions` · ⬜ WP-20 · ARI vs zona HET, Jawa/luar Jawa, kuantil n_kota.

#### src/evaluation/planted.py
- `recovery_curve` · ⬜ WP-21 · δ 0,1..0,5 × k_true 2/3 × planted_reps → recovery_rate, ari_mean.

#### src/evaluation/forecast_eval.py
- `evaluate` · ⬜ WP-27 · MAE/RMSE, rasio vs M1, DM HAC, n_origins, n_nonoverlap.
- `ablation` · ⬜ WP-27 · MAE(M2 tanpa fx) − MAE(M2).

#### src/evaluation/robustness.py
(konstanta `TIER1` 6 cek, `TIER2` 4 cek)
- `tier1` · ⬜ WP-28 · 6 cek wajib vs baseline.
- `validation` · ⬜ WP-29 · V2 studi kasus 2026, V4 LP vs event study.
- `tier2` · ⬜ WP-30 · opsional (dipotong pertama).

### 9.6 Mesin statistik (WP-12, semua ✔ dan dites di `tests/test_stats.py`)

#### src/stats/regression.py
- `ols_cluster` · ✔ · OLS + SE cluster CR1; buang baris NaN; return OLSResult(beta, se, n_obs, n_clusters, resid).
- `newey_west_lrv` · ✔ · varians jangka panjang kernel Bartlett.
- `diebold_mariano` · ✔ · DM dua sisi HAC (lag h−1) + koreksi HLN; stat > 0 = kandidat lebih akurat.

#### src/stats/resampling.py
- `moving_block_indices` · ✔ · indeks minggu dari blok berurutan (Künsch).
- `circular_shift` · ✔ · pergeseran s ∈ [min_shift, n − min_shift].
- `placebo_windows` · ✔ · sampel awal jendela plasebo dari kandidat.

#### src/stats/meta.py
- `dersimonian_laird` · ✔ · HetResult(mu, tau2, Q, I2, k).
- `reml_tau2` · ✔ · τ² REML (Fisher scoring).
- `eb_shrink` · ✔ · μ + τ²/(τ²+s²)·(est − μ); τ²=0 → semua μ.
- `bh_fdr` · ✔ · q-value Benjamini–Hochberg.

### 9.7 Pipelines (orkestrasi; satu modul = satu notebook = satu perintah CLI)

#### src/pipelines/stage0.py
- `run` · ✔ · snapshot → varian → panel → kelayakan → penggerak → harga dunia → episode → tabel tim → panel wilayah → MDE → QA.

#### src/pipelines/task1.py
- `run` · ✔ · REQUIRES drivers/world/episodes/region/eligibility; profil wilayah + (bila panel provinsi) nasional, deviasi, bootstrap, plasebo, EB.

#### src/pipelines/task2.py
- `run` · ✔ · heterogenitas vs plasebo → matriks fitur → pilih k → Ward → stabilitas → partisi → struktur tertanam.

#### src/pipelines/task3.py
- `run` · ✔ · Kendall (selalu) + meta-regresi & FE (bila panel provinsi).

#### src/pipelines/task4.py
- `run` · ✔ · rolling_predictions → forecast_preds.parquet → evaluate + ablation.

#### src/pipelines/robustness.py
- `run` · ✔ · tier1 + validation (+ tier2 bila diminta).

#### src/pipelines/package.py
- `collect_submission` · ✔ · file zip juri + daftar artefak ship yang hilang.
- `submission` · ✔ · `dist/kagami_submission.zip` (gagal bila ada artefak ship hilang, kecuali allow_missing).
- `code_bundle` · ✔ · `dist/kagami_code.zip` (kode, configs, data/reference, notebook) untuk Kaggle/Colab.
- `raw_bundle` · ✔ · `dist/kagami_raw_PRIVATE.zip` (isi raw_dir + checksums) untuk dataset Kaggle PRIVAT.

### 9.8 Viz

#### src/viz/plots.py
- `response_curve` · ✔ · kurva respons h 0..12 + pita interval (app hal. 2, nb01).
- `fx_drivers` · ✔ · JISDOR mingguan + arsiran episode (nb00).
- `status_share` · ✔ · porsi status sel per komoditas (nb00).
- `coassign_heatmap` · ✔ · matriks ko-asignasi (app hal. 3, nb02).
- `recovery_curve` · ✔ · batas deteksi struktur tertanam (app hal. 3, nb02).
- `forecast_ratios` · ✔ · rasio MAE vs M1 (nb04).
- `forest` · ✔ · forest plot estimasi + interval (nb03, nb05).

---

## 10. Data

### 10.1 Sumber (rincian: `docs/DATASETS.md`)

| Kunci | Isi | Cakupan | Peran | Redistribusi |
|---|---|---|---|---|
| `pihps` | PIHPS v2 merged, 34 prov × 31 baris (10 komoditas + 21 varian), harian | 2017-03-28..2026-11-19 | outcome | tidak |
| `jisdor` | JISDOR harian | 2013-05-20..2026-11-18 | penggerak 1 | tidak |
| `pinksheet` | World Bank CMO bulanan USD | 1960-01..2026-10 | penggerak 2 | ya (CC BY) |
| `brent` | FRED DCOILBRENTEU | 2013..2026-11-11 | kontrol | ya |
| `dollar_index` | FRED DTWEXBGS | 2013..2026-11-13 | robustness | ya |
| `faostat_sua` | FAOSTAT SUA Asia | 2010..2023 | rasio impor | ya (CC BY) |
| `bps_import_monthly` | impor HS8 bulanan **v2** (111 kode, +bawang putih 070320) | 2023-01..2026-09 | cek silang | tidak |
| `bps_import_annual` | 5 xlsx exim tahunan (Totals = USD) | 2023..2026 | QA | tidak |
| `comtrade_import` | UN Comtrade HS4/HS6 bulanan (tanpa kedelai 1201) | 2017-01..2022-12 | rasio impor pra-2023 | tidak |
| `konkordansi_hs` | Comtrade HS2017/2022 → HS8 BPS + keyakinan (buatan tim) | statis | jembatan impor (WP-07) | ya |
| `bapanas_panel` | Panel Harga Bapanas bulanan, 38 prov | 2022-01..2026-10 | cek bias / Tier 2 | tidak |
| `bapanas_het_settings` | riwayat setting HET/HAP | 2024..2026 | regulasi | tidak |
| `padi_2024`, `padi_2025` | produksi padi GKG per provinsi (38) | 2024, 2025 | kecukupan beras | tidak |
| `konsumsi_beras` | konsumsi beras RT kg/kap/tahun | 2023..2025 | kecukupan beras | tidak |
| `neraca_beras` | neraca beras nasional | 2023..2026 | cek silang | tidak |
| `het_hap_current` | HET/HAP berlaku (buatan tim; revisi 20 Nov, 30 baris) | per 2026-11-19 | regulasi | ya |
| `regulation_history` | riwayat HET/HAP/HPP (buatan tim; revisi 20 Nov, 23 baris) | 2020..2025 | regulasi (E2) | ya |
| `hortikultura_produksi` | produksi bawang merah/putih, cabai besar/rawit per provinsi (ATAP Kementan) | 2020..2024 | rasio impor bawang putih, kecukupan | tidak |
| `jarak_hub` | jarak ibu kota ke Jakarta/Surabaya/Makassar (buatan tim, 38 prov) | statis | cek silang dist_hub_km | ya |

Menunggu diunggah (lokasi dialokasikan, U103): `bps_kependudukan/penduduk_provinsi_2025.csv`,
`bapanas/panelharga_konsumen_kabkota_snapshot_2026-10.csv`. Versi lama: `data/raw/_superseded/` (DATASETS.md).

### 10.2 Fakta data yang sudah diverifikasi
- Panel mingguan: 157.760 sel = 34 × 10 × 464 minggu (2018-01-01..2026-11-16). `pihps_daily` 800.642 hari teramati.
- Status sel: observed 49,2% · carry_forward 49,2% · missing 1,0% · short 0,6%.
- `carry_forward` sangat tinggi untuk komoditas diatur (beras 92%, daging sapi 90%, gula 85%, minyak goreng kemasan 87%)
  → kekakuan harga nyata, BUKAN artefak; jangan dipakai sebagai filter (U22).
- Kelayakan: 337/340 layak. Tidak layak: cabai_rawit Aceh (1), Sumbar (3), Kepri (5) → cabai rawit dianalisis 31 provinsi.
- Penggerak 2018–2026: sd(de) 0,0082; 259 minggu depresiasi / 200 apresiasi; de maks +0,063 (Mar 2020);
  corr(de, d_dxy) 0,52; 5 minggu tanpa fixing JISDOR (semua cuti Lebaran) diisi level sebelumnya (D-025).
- `world_prices_weekly`: 3.096 baris (6 komoditas × 516 minggu); NaN hanya 3 minggu Nov 2026 (Pink Sheet Nov belum rilis).
- FAOSTAT SUA tidak memuat bawang putih kering (hanya "Green garlic") → U5; pengganti: `hortikultura_produksi` + impor 070320.
- `hortikultura_produksi`: total nasional cocok; 148/152 nilai 2023 sama dengan BPS (4 selisih pembulatan); ATAP berhenti 2024.
- Konkordansi HS: perubahan HS2017→HS2022 hanya 0709.59; uji tumpang tindih Comtrade–BPS 2022 belum bisa (server BPS error, U102).
- Pink Sheet tim = rilis resmi 3 Nov 2026 (identik byte-per-byte; `Mismatch Details` bagian file resmi; U101 🟢).
  World Bank merevisi angka historis antar rilis → catat tanggal rilis setiap snapshot.
- Snapshot PIHPS pra-merge (`pihps_v1`) dipensiunkan ke `data/raw/_superseded/bi_pihps/` (D-102): inventaris tim menandainya rusak.
- Kolom `Totals` exim tahunan BPS = USD (Σ bulanan 2023 / Totals = 1,000) → D-019.
- Bapanas memakai ejaan "D.I Yogyakarta" (alias sudah ada).

### 10.3 Keanehan mentah yang harus selalu diingat
- PIHPS v2 menaruh varian hasil merge di **akhir file** (Aceh, Riau, Kepri, Lampung, Bali, Gorontalo, Sulsel) →
  jangan pernah menentukan grup dari urutan baris (D-022).
- "Cabai Merah Keriting " ber-spasi akhir → selalu `norm_name`.
- Lonjakan satu hari (contoh: Papua, Beras level 1, 2017-07-03: 29.750 lalu 9.500) → WP-10 menandai, tidak menghapus.
- Tanggal 2026-11-19 di PIHPS sebagian kosong.
- Pink Sheet: nama seri ber-spasi/`**` ("Beef **", "Rice, Thai 5% "), "…" = kosong; sheet "Mismatch Details" abaikan.
- JISDOR Excel: header di baris 5, angka format Indonesia "9.760,00", tanggal "5/20/2013 12:00:00 AM".
- BPS padi 2024: 4 baris judul + nama UPPERCASE; 2025 header normal; keduanya 38 provinsi + "INDONESIA"; produksi GKG.
- Bapanas 38 provinsi → pemetaan ke 34 lewat `province_aliases.csv` (pemekaran Papua → induk).
- Endpoint PIHPS di MANIFEST: `WebSite/TabelHarga/GetGridDataDaerah` → status "unduh resmi" belum dipastikan (U19).

### 10.4 Tabel buatan tim (`data/reference/`, CC BY 4.0)
- `region_crosswalk.csv`: province_id, province, region (7), capital, lat, lon, het_zone_beras (1/2/3), java.
  Kalsel = Banjarmasin, Malut = Sofifi; koordinat ±0,01°.
- `province_aliases.csv`: alias ejaan BPS/Bapanas + pemekaran Papua.
- Hasil WP-07 (belum): `concordance.csv`, `exposure.csv`, `regulation.csv`, `province_features.csv`.

### 10.5 Asal file
File mentah dipindah 2026-11-20 dari `data/` ke `data/raw/<sumber>/` (sebagian diganti nama); pemetaan nama asli ada
di `docs/DATASETS.md` §Asal file. Isi file tidak pernah diubah (hash di checksums.csv).

---

## 11. Desain analisis ringkas

### 11.1 Komoditas (`configs/commodities.yaml`)

| id | Varian representatif | Peran | Grup fokus | Jalur | Padanan Pink Sheet | HS |
|---|---|---|---|---|---|---|
| beras | Beras Kualitas Medium I | other | – | direct_import | Rice, Thai 5% | 1006 |
| bawang_putih | Bawang Putih Ukuran Sedang | focus | bawang_putih | direct_import | – | 070320 |
| gula_pasir | Gula Pasir Lokal | focus | gula_pasir | direct_import | Sugar, world | 1701 |
| minyak_goreng | Minyak Goreng Kemasan Bermerk 1 (D-023) | focus | minyak_goreng | export_parity | Palm oil | 1511, 1517 |
| daging_ayam | Daging Ayam Ras Segar | focus | pakan | imported_input | 0,6 Maize + 0,4 Soybean meal | 0207, 1005, 2304 |
| telur_ayam | Telur Ayam Ras Segar | focus | pakan | imported_input | 0,6 Maize + 0,4 Soybean meal | 0407, 1005, 2304 |
| daging_sapi | Daging Sapi Kualitas 1 | focus | daging_sapi | direct_import | Beef | 0102, 0201, 0202 |
| bawang_merah | Bawang Merah Ukuran Sedang | control | – | domestic | – | 070310 |
| cabai_merah | Cabai Merah Keriting | control | – | domestic | – | 070960, 090421 |
| cabai_rawit | Cabai Rawit Merah | control | – | domestic | – | 070960, 090421 |

Varian, bobot pakan, dan grup fokus PROVISIONAL sampai G6 (D-011, D-012, D-013), kecuali minyak goreng (FINAL, D-023).

### 11.2 Wilayah
34 provinsi lama (urutan & id PIHPS). 7 kelompok: Sumatra (1–10), Jawa (11–16), Bali–Nusa Tenggara (17–19),
Kalimantan (20–24), Sulawesi (25–30), Maluku (31–32), Papua (33–34). Hub keterpencilan: DKI Jakarta, Jawa Timur
(Surabaya), Sulawesi Selatan (Makassar). Zona HET beras (Kepbadan 299/2025): 1 = Jawa, Lampung, Sumsel, Bali, NTB,
Sulawesi; 2 = Sumatra lain, NTT, Kalimantan; 3 = Maluku, Papua.

### 11.3 Parameter kunci (`configs/params.yaml`; jangan disalin sebagai konstanta di kode)

| Kunci | Nilai |
|---|---|
| seed | 20261121 |
| period.start / start_fallback / freeze / driver_buffer_weeks | 2018-01-01 / 2020-01-06 / 2026-11-21 / 52 |
| calendar.idulfitri | 2017-06-25, 2018-06-15, 2019-06-05, 2020-05-24, 2021-05-13, 2022-05-02, 2023-04-22, 2024-04-10, 2025-03-31, 2026-03-20 |
| calendar.idulfitri_window | [−6, 4] |
| calendar.breaks | jisdor_method_change 2021-04-05; padg_7_2026 null (U3) |
| calendar.exclusions | covid 2020-03-01..2020-06-30; brent_extreme_abs_monthly_logchg 0,25 |
| weekly | short_week_days 2; carry_forward_run_days 5 |
| eligibility | max_missing_share 0,20; max_gap_weeks 8; min_year_coverage 0,70 |
| episodes | cum_depreciation 0,03; window_weeks 8 |
| lp | horizons 0..12; lags 4; lags_robust [2,4,8]; key_horizons [4,8,12] |
| inference | bootstrap_B 499; bootstrap_B_nonfocus 199; block_weeks 13; placebo_R 499; placebo_min_shift_weeks 52; event_placebo_windows 499; fdr_q 0,05 |
| shrinkage | tau2_method DL; tau2_check REML |
| power | α 0,05; power 0,80; mde_threshold_pt8 0,5; mde_commodities [bawang_putih, gula_pasir, minyak_goreng] |
| clustering | k_range 1..6; feature_horizons [4,8,12]; silhouette_placebo_pct 95; kmeans_restarts 50; jaccard_weak 0,6; planted_deltas 0,1..0,5; planted_reps 200 |
| association | hubs [DKI Jakarta, Jawa Timur, Sulawesi Selatan]; max_features 3 |
| forecast | horizons [4,8]; first_origin 2021-01-04; origin_step_weeks 4; large_move_pct 80; ridge_alphas [0.1,1,10,100]; feature_changes_weeks [1,4,8]; hgb {max_iter 300, lr 0,05, max_leaf_nodes 31}; bps_release_lag_days 45 |
| scenario | shocks_pct [1,3,5] |

### 11.4 Notasi
i komoditas, r provinsi, t minggu ISO, h horizon 0..12. p = log harga; y^{(h)} = p_{t+h} − p_{t−1};
e = log JISDOR rerata mingguan; de = Δe; w = log harga dunia padanan dalam rupiah; dw = Δw; b = log Brent.
β(i,h) respons kurs; ω(i,h) respons harga dunia; γ(h) respons kurs pada dirinya; PT = β/γ; δ(i,r,h) deviasi provinsi;
τ² varians antar-provinsi; I² porsi variasi; ρ̄ rerata korelasi deviasi antar komoditas.

---

## 12. Metode per task (ringkas; rumus lengkap `docs/METHODS.md`)

### Tahap 0 (notebook 00, ringan)
- WP-06 episode: Σ de 8 minggu ≥ 3%, gabung tumpang tindih; daftar episode harus memuat 2018, 2020, 2022, 2024–25,
  2026 bila ada; catat jumlahnya. Lalu `mark_episode_weeks` → kolom `episode` → baru `drivers_weekly` bisa ditulis.
- WP-07 tabel tim: input baru `hortikultura_produksi`, `konkordansi_hs`, `jarak_hub` (D-101); setiap angka punya `source`; tanggal regulasi tak terverifikasi tetap `unverified`; populasi provinsi
  belum ada (U14) → `rice_sufficiency` NaN bila tak terselesaikan; konversi GKG→beras didokumentasikan (U21).
- WP-08 panel wilayah: hanya seri eligible; indeks log relatif minggu pertama (bukan Rp).
- WP-09 MDE: SEBELUM melihat β; MDE_β = 2,80·SE; MDE_PT = MDE_β/γ; tulis keputusan G-power di D-007.
- WP-10 QA: outlier, total impor, bias Bapanas (pemetaan komoditas U20), laporan markdown.

### Task 1 (notebook 01, berat)
- LP dengan lag-augmentation (L = 4), efek tetap seri, SE cluster per **minggu**; asimetri via de⁺/de⁻.
- Event study per episode vs 499 jendela plasebo dari minggu tanpa episode.
- Deviasi provinsi: harga dikurangi rerata lintas provinsi per minggu; Σ_r δ = 0.
- Bootstrap: blok 13 minggu, B = 499, SATU vektor indeks minggu per replikasi dipakai ke harga & penggerak semua seri.
- Plasebo: np.roll de & dw sejauh ≥ 52 minggu; R = 499; provinsi cukup h ∈ {4,8,12}.
- EB: τ² DL (REML cek); τ² = 0 → semua provinsi = rerata (temuan sah).
- Target runtime: LP nasional 10 komoditas × 13 h < 2 menit; ukur bootstrap; bila > 30 menit, B = R = 199 untuk non-fokus + D-xxx.

### Task 2 (notebook 02, berat)
- H0-Het: Q, τ², I² per komoditas pada h = 8 vs distribusi plasebo; FDR BH antar 10.
- Clustering SELALU jalan (D-004): Ward pada 34 × fitur tersusut; k ∈ {2..6}; diterima bila silhouette maks > p95 plasebo,
  selain itu k = 1 ("tidak ada struktur regional terdeteksi").
- Stabilitas: K-Means ARI, ko-asignasi bootstrap, Jaccard < 0,6 → "pola lemah"; label netral K1, K2, …
- Struktur tertanam: δ 0,1–0,5 ditanam pada noise plasebo; recovery = P(k benar ∧ ARI ≥ 0,8) → batas deteksi.

### Task 3 (notebook 03, ringan)
- 3a Kendall τ PT(8) vs rasio impor (N = 10), p permutasi eksak (10! = 3.628.800), LOCO; kesimpulan "di antara 10 komoditas".
- 3b meta-regresi ≤ 3 fitur praregistrasi; interval = lebih lebar dari bootstrap blok dan CR2; jackknife provinsi.
- 3c FE komoditas×minggu, interaksi Δe × Z(r) (dapat dipotong).

### Task 4 (notebook 04, berat; paralel dengan Task 1)
- Target p_{t+h} − p_t, h ∈ {4, 8}; origin tiap 4 minggu sejak 2021-01-04 s.d. freeze − h.
- Train hanya baris dengan t + h ≤ origin; join harga dunia memakai `available_at` (as-of); tidak ada split acak.
- M0 nol; M1 ridge (lag Δp, musiman, Brent); M2 + kurs & harga dunia (1/4/8 minggu) + episode; M3 HGB + identitas.
- Metrik: MAE, RMSE, rasio vs M1 (semua origin & large_move > p80 latih), DM HAC; selalu laporkan n_origins & n_nonoverlap.
- Sebut "pseudo-real-time" (vintage revisi tidak tersedia).

### Robustness (notebook 05)
Tier 1 wajib: h 8 vs 12; lag 2/4/8; sub-periode sebelum/sesudah 2021-04-05 (V3); tanpa Mar–Jun 2020 & bulan Brent
ekstrem; dekomposisi de = komponen dolar global + spesifik rupiah; frekuensi bulanan. Validasi V2 (studi kasus 2026,
hanya origin dengan outcome lengkap) & V4 (LP vs event study). Tier 2 opsional (varian alternatif termasuk Minyak Goreng
Curah, agregasi observasi terakhir, definisi alternatif, outcome Bapanas).

### Pencegahan kebocoran (semua task)
Task 1–3 deskriptif: data bulanan diselaraskan menurut periode observasi. Task 4: as-of; Pink Sheet tersedia hari kerja
ke-2 bulan berikutnya; impor BPS +45 hari. Target Task 3 dari estimasi periode penuh → hanya deskriptif.

---

## 13. Gerbang, jadwal, pemotongan

| Gerbang | Tanggal | Syarat | Konsekuensi |
|---|---|---|---|
| G6 praregistrasi | 21 Nov | params, varian, bobot pakan, grup fokus, hipotesis beku + sha256 config di PREREGISTRATION | perubahan setelahnya = DEVIASI PRAREGISTRASI |
| G-power | 23 Nov | `mde.csv` | MDE PT(8) > 0,5 untuk bawang putih, gula, minyak goreng → LP sekunder; event study + harga dunia utama; Task 4 kontribusi DM utama |
| G-het | 25 Nov | `heterogeneity.csv` | tak ada yang lolos → nol + batas deteksi; clustering tetap jalan |
| Pembekuan hasil | 27 Nov | semua artefak ship ada | `results/` tidak diubah kecuali bug |
| G7 jalan ulang | 28 Nov | zip diekstrak di folder bersih → app & task4 jalan | – |
| G8 audit klaim | 28 Nov | semua teks lolos §20 | – |
| Submit | 29 Nov | `[HUMAN]` unggah | batas resmi 30 Nov |

Urutan pemotongan bila waktu habis (D-014): Tier 2 → analisis dalam-komoditas & Moran's I → Task 3c → M3.
**Tidak pernah dipotong:** Tier 1, distribusi plasebo, MDE.

Jalur kritis: WP-06 → WP-08 → WP-09 → WP-13 → WP-15 → WP-16 → WP-17 → WP-18 → WP-19..21 → WP-31/33 → WP-32/34.
Paralel: WP-07 (→ WP-22/23), WP-25 → WP-26 → WP-27, WP-11 sebelum 21 Nov.

---

## 14. Resep mengimplementasikan sebuah WP

1. **Baca kontrak:** docstring stub (input, output, kolom), heading WP di WORKPLAN, bagian METHODS, entri artefak di
   `utils/artifacts.py`, dan pemanggilnya di `pipelines/<tahap>.py`.
2. **Tes dulu:** buat/ubah `tests/test_<topik>.py` dengan data sintetis yang jawabannya diketahui (lihat §16.3).
3. **Implementasi** di modul lapisan yang sesuai. Ganti seluruh badan fungsi (hapus `todo(...)`); hapus import `todo`
   bila modul tak lagi punya stub. Hapus komentar `# noqa: F401 (WP-xx)` pada import yang kini benar-benar dipakai.
4. **Parameter** dari `cfg.params[...]`; bila butuh parameter baru, tambahkan ke `params.yaml` dengan komentar
   (setelah G6 = deviasi praregistrasi, catat di DECISIONS).
5. **Jalankan** tahapnya: ringan → `python -m kagami <tahap>` lokal; berat → uji dengan subset kecil lokal
   (mis. B = 9, satu komoditas) lalu jalankan penuh di Kaggle/Colab.
6. **Periksa hasil** pada data asli: bentuk, NaN, rentang nilai, angka penting; catat di bagian WP dan SESSION_LOG.
7. **Dokumentasi:** §2 & §9 CLAUDE.md, papan WORKPLAN, DECISIONS/OPEN_ISSUES bila ada.
8. **pytest** penuh.

Template fungsi:

```python
def nama_fungsi(cfg: Config, df: pd.DataFrame) -> pd.DataFrame:
    """WP-xx. Satu kalimat tujuan.

    Input : kolom yang dibutuhkan dari artefak X.
    Output: kolom keluaran (sesuai utils/artifacts.py: <artefak>).
    Aturan: parameter dari cfg.params["..."]; keputusan terkait D-xxx.
    """
    p = cfg.params["bagian"]
    rng = np.random.default_rng(cfg.seed + OFFSET)   # offset unik per fungsi, catat di docstring
    ...
    return out[[...kolom kontrak...]]
```

---

## 15. Konvensi kode

- Python ≥ 3.10, `from __future__ import annotations`, type hints pada fungsi publik.
- Docstring berbahasa Indonesia, diawali "WP-xx." untuk fungsi milik WP; jelaskan input/output/aturan.
- Nama kolom & id: snake_case Inggris/Indonesia sesuai kontrak artefak; jangan menamai ulang kolom kontrak.
- Tidak ada angka analisis di kode (ambang, horizon, B, R, tanggal) — semua dari `params.yaml`/`commodities.yaml`.
  Konstanta struktural (mis. urutan status, nama tier) boleh sebagai konstanta modul.
- pandas: hindari chained assignment (pakai `.copy()` setelah filter lalu assign); `groupby(...).agg` bernama;
  vektorisasi, hindari loop baris; join selalu pada `week`/`province_id`/`commodity`.
- RNG: `np.random.default_rng(cfg.seed + offset)`; offset berbeda per fungsi/tahap dan dicatat; jangan `np.random.seed`.
- Komputasi berat: vektorisasi numpy; paralel dengan `joblib` (tersedia di Kaggle/Colab) bila perlu; ukur waktu.
- Cetak progres singkat dengan prefiks `[tahap]` (contoh `[snapshot] <n> file -> ...`); tidak perlu logging framework.
- Error eksplisit lebih baik daripada hasil diam-diam salah (contoh: `select_variants` raise bila varian tidak ada).
- Jangan menghapus data diam-diam: tandai (flag/status) dan laporkan.
- File teks: UTF-8, LF.

---

## 16. Pengujian

### 16.1 File tes

| File | Menguji |
|---|---|
| `tests/conftest.py` | alias `kagami` → `src/` tanpa instalasi; fixture `cfg`, `pihps` (skip bila mentah tak ada) |
| `test_config.py` | desain komoditas (10; peran 6/3/1; 5 grup fokus), wilayah (34, 7, hub, zona), sumber ada, varian ada di PIHPS, seri Pink Sheet ada |
| `test_loaders.py` | loader semua sumber pada data asli + kolom; BPS v2 memuat bawang putih; bentuk PIHPS; grup varian dari prefiks (regresi D-022); nama provinsi terpetakan 34 |
| `test_stats.py` | OLS & SE cluster, DL/REML/EB, BH, block bootstrap, circular shift, DM |
| `test_weekly.py` | status sel sintetis, grid, week_start, select_variants (asli & error), aggregate asli, aturan kelayakan |
| `test_drivers.py` | grid penggerak, de & pengisian minggu libur, jendela Idulfitri, harga dunia (komposit, dw bulanan, available_at) |
| `test_runtime.py` | lokasi default, tulis out/baca artefak tahap sebelumnya, override raw, deteksi Kaggle, layout Colab |
| `test_notebooks.py` | satu notebook per tahap, valid, sel 0–1 identik, tanpa output, sel setup jalan lokal |
| `test_viz.py` | semua fungsi viz membangun figure dari artefak sintetis |
| `test_app.py` | 6 halaman Streamlit jalan tanpa exception (artefak ada/belum) |
| `test_wiring.py` | modul terpakai (CLI/app/notebook), fungsi viz terpakai, todo → WP ada, artefak WP ada, artefak punya produsen & terdokumentasi, halaman app |
| `test_claude_md.py` | §9 dokumen ini sinkron dengan kode (fungsi publik & status stub) |
| `test_handoff.py` | format setiap `docs/handoff/*.md`: nama file, frontmatter, bagian wajib, status vs kotak centang |
| `test_drive.py` | sinkron Drive dengan Drive palsu di memori: path dicerminkan, timpa bukan duplikat, pull ke anggota lain, hanya tahap diminta, lokal tanpa token dilewati, push/pull data mentah bolak-balik (MD5, glob, tidak menimpa) |
| `test_download.py` | resolusi tautan unduhan terbaru (pola Pink Sheet) & url cadangan, tanpa jaringan |
| `test_docs_sync.py` | dokumen hidup tidak basi: tautan & path ada, papan WP vs stub, §2 vs papan, ID D-/U- ada, kunci `params.*` ada, sumber/komoditas/notebook/subpaket/tes terdokumentasi (§3.4) |

### 16.2 Menjalankan
- Semua: `python -m pytest -q` (~1 menit). Subset: `python -m pytest -q tests/test_weekly.py -k eligibility`.
- Tes yang butuh mentah di-skip otomatis bila mentah tidak ada (paket juri).

### 16.3 Pola tes yang disarankan
- Data sintetis kecil dengan jawaban pasti (contoh: `tests/test_weekly.py::synthetic`, `tests/test_drivers.py::_daily`).
- Untuk estimator: bangkitkan data dari model diketahui (β benar) → cek dipulihkan dalam ±2 SE.
- Untuk inferensi: cek properti (panjang indeks, rentang shift, satu indeks per replikasi).
- Untuk kebocoran (Task 4): untuk origin acak, assert tidak ada `available_at` > origin dan tidak ada target t+h > origin di train.
- Satu tes pada data asli per artefak (bentuk, NaN wajar), di-skip bila mentah tidak ada.
- Perhatikan kalender: 2024 punya 53 hari Senin (pelajaran dari tes kelayakan).

---

## 17. Notebook & cloud

- Enam notebook di `notebooks/`, satu per tahap. Struktur: markdown pengantar → sel 0 setup (identik) → sel 1
  `init_runtime` (identik) → `drive.pull` + cek input (`require`) → `pipelines.<tahap>.run(cfg)` → `drive.push` →
  diagnostik `viz.plots`. Tes memastikan setiap notebook punya pull & push untuk tahapnya.
- Logika analisis TIDAK boleh ditulis di notebook. Kebutuhan baru → fungsi di `src/` (+ viz bila grafik).
- Simpan notebook **tanpa output**. Sel 0–1 harus identik di semua notebook (tes). Bila mengubah sel 0/1, ubah keenamnya.
- Mengedit notebook: pakai `nbformat` (baca → ubah `cell.source` → tulis) atau tool NotebookEdit; jangan edit JSON manual.
- Beban: 00 & 03 ringan (lokal); 01, 02, 04 berat; 05 sedang–berat → Kaggle/Colab.
- Urutan: 00 → (01 ∥ 04) → 02, 03 → 05. Input diambil dari folder Drive tim (§7.3), bukan dari output notebook lain.
- Distribusi kode/data: `python -m kagami bundle [--raw]` → `dist/kagami_code.zip`,
  `dist/kagami_raw_PRIVATE.zip`. Dataset Kaggle `kagami-code` (**PRIVAT**; `kagami-raw` opsional karena data mentah di Drive tim) atau Google Drive
  `MyDrive/kagami/`. Pengunggahan = tugas `[HUMAN]`; agent tidak masuk ke akun Kaggle/Google user.
- Hasil cloud ke project lokal: `python -m kagami drive-pull all` (tanpa salin manual).
- Langkah rinci: `docs/NOTEBOOKS.md`.

---

## 18. App Streamlit

- `app/Home.py` = halaman 1 (Ringkasan & Status Data); `pages/2..6`: Kepekaan Harga Regional, Pola Respons, Eksposur &
  Nilai Prediktif, Penjelajah Skenario Bersyarat, Temuan Penelitian. Jalankan `python -m kagami app`.
- `common.py`: alias paket, `CFG`, `load` (cache), `need` (label "Menunggu hasil (WP-xx)"), `page_header`, `footer`,
  `not_detected_badge`, `commodity_labels`.
- Aturan (D-010, proposal §7.1): hanya membaca artefak; tidak ada login, input data pengguna, atau estimasi runtime.
  Setiap grafik: sumber, satuan, periode, interval, label "asosiasi, bukan kausalitas". Lencana "tidak terdeteksi" bila
  interval memuat nol. Halaman 3 menangani k = 1. Halaman 5: PT(h)·x, x ∈ {1,3,5}%, bendera ekstrapolasi, label
  "skenario bersyarat, bukan ramalan". Halaman 6 membaca `results/findings.md`.
- Grafik memakai `viz.plots`; jangan menulis plotly inline di halaman bila grafiknya juga berguna di notebook.

---

## 19. Hak data & paket juri

- Mentah dengan `redistribute: false` (PIHPS, JISDOR, BPS, Comtrade, Bapanas, BPS pangan) tidak boleh masuk zip juri.
- Zip juri (`python -m kagami package`): kode, configs, app, tes, docs/*.md, data/reference, artefak `ship=True`,
  mentah `redistribute: true`. Gagal bila artefak ship belum ada (kecuali `--allow-missing`).
- Dataset Kaggle mentah wajib **privat**; jangan membagikan tautan (U24). Izin BI (U13) mencakup redistribusi data turunan: `panel_weekly` ikut paket (D-104); PIHPS mentah & `pihps_daily` tidak.
- Saat menyebut data: "Dataset turunan kami yang dibangun dari PIHPS (Bank Indonesia)", bukan "dataset kami".
- Tiga tingkat reproduksi: A app dari results; B semua tahap dari data turunan yang dikirim (panel provinsi + wilayah, D-104);
  C unduh ulang mentah.

---

## 20. Rambu klaim & bahasa

| Jangan tulis | Tulis |
|---|---|
| "Penelitian pertama tentang ..." | "Sejauh penelusuran kami, belum ada studi yang ...; studi terdekat adalah ..." |
| "Pelemahan rupiah menyebabkan harga X naik" | "Kenaikan IDR/USD berasosiasi dengan kenaikan harga X sebesar ... (interval ...), setelah mengendalikan ..." |
| "KAGAMI memprediksi kenaikan harga" | "Skenario bersyarat berdasarkan pola historis"; "dalam evaluasi rolling-origin, fitur kurs menurunkan MAE sebesar ..." |
| "Komoditas impor lebih rentan" | "Di antara 10 komoditas yang diamati, komoditas A dan B menunjukkan PT(8) lebih besar" |
| "Provinsi terbagi menjadi k tipe kepekaan" (tanpa uji null) | "Provinsi membentuk k kelompok yang lolos uji plasebo dengan stabilitas Jaccard ..." / "tidak ada struktur regional yang terdeteksi; struktur dengan selisih ≥ ... akan terdeteksi" |
| "Faktor terpenting adalah ..." | "Karakteristik yang berasosiasi paling kuat adalah ... (β = ..., interval ...)" |
| "Model tervalidasi pada episode 2026" | "Dalam evaluasi bersyarat lintas episode 2021–2026, ...; studi kasus 2026 menunjukkan ..." |
| "Tidak ada pengaruh kurs" | "Pengaruh di atas X dapat dikesampingkan pada horizon 8 minggu" |
| "Kerentanan provinsi" | "Kepekaan harga eceran terhadap kurs" |
| "Dataset kami" (PIHPS mentah) | "Dataset turunan kami yang dibangun dari PIHPS (Bank Indonesia)" |

Tambahan: setiap angka disertai interval & satuan; hasil nol ditulis sebagai batas atas; Task 4 disebut "evaluasi
bersyarat, pseudo-real-time"; E1 ditulis "di antara 10 komoditas yang diamati"; rujukan "belum diverifikasi" (U12)
tidak boleh dikutip sebelum dicek.

---

## 21. Ringkasan keputusan (lengkap: `docs/DECISIONS.md`)

| ID | Keputusan | Status |
|---|---|---|
| D-001 | Paket Python + CLI per tahap | FINAL |
| D-002 | Mentah di `data/raw/<sumber>/`, nama dirapikan, isi tak diubah | FINAL |
| D-003 | Registry artefak = kontrak antar tahap | FINAL |
| D-004 | Clustering selalu jalan, dinilai vs plasebo | FINAL |
| D-005 | Inferensi berbasis minggu (cluster minggu) | FINAL |
| D-006 | Periode mulai 2018-01-01 (337/340 layak) | FINAL |
| D-007 | Aturan G-power (MDE PT(8) > 0,5) | FINAL ambang; angka menunggu WP-09 |
| D-008 | PIHPS v2_merged kanonik (bagian "v1 untuk QA" diganti D-102) | FINAL |
| D-009 | Mesin statistik numpy/scipy sendiri | FINAL |
| D-010 | App hanya membaca artefak | FINAL |
| D-011 | Varian representatif | PROVISIONAL (G6) |
| D-012 | Komposit pakan 0,6 Maize + 0,4 Soybean meal | PROVISIONAL (G6) |
| D-013 | 6 komoditas fokus dalam 5 grup (ayam+telur = pakan) | PROVISIONAL (G6) |
| D-014 | Urutan pemotongan lingkup | FINAL |
| D-015 | Kebijakan kirim data turunan (bagian panel provinsi diganti D-104) | FINAL |
| D-016 | Harga dunia bulanan → mingguan menurut bulan hari Senin | FINAL |
| D-017 | Kerangka 34 provinsi lama | FINAL |
| D-018 | Keterpencilan = ln(1 + km ke hub terdekat) | FINAL |
| D-019 | exim `Totals` = USD | FINAL |
| D-020 | Label minggu = Senin ISO | FINAL |
| D-021 | Prioritas status sel: missing > carry_forward > short > observed | FINAL |
| D-022 | Grup varian PIHPS dari prefiks nama | FINAL |
| D-023 | Minyak goreng = Kemasan Bermerk 1 (keputusan user) | FINAL |
| D-024 | Isi paket langsung di `src/` (keputusan user) | FINAL |
| D-025 | Konstruksi penggerak: isi minggu libur, JISDOR bulanan untuk w, buffer 52 minggu | FINAL |
| D-026 | `src/` berlapis (permintaan user) | FINAL |
| D-027 | Notebook per tahap lokal/Kaggle/Colab (permintaan user) | FINAL |
| D-028 | Nama proyek KAGAMI; paket/CLI `kagami` (keputusan user) | FINAL |
| D-100 | Input/output notebook lewat folder Drive tim (Drive API: pull/push) | FINAL |
| D-101 | Data mentah di Drive tim (push_raw/pull_raw) + alokasi dataset 20 Nov + `_superseded/` | FINAL |
| D-102 | `pihps_v1` dipensiunkan; QA v1 vs v2 dihapus dari WP-10 | FINAL |
| D-103 | Branch hanya `main`, `dev`, `feat/<topik>`; semua lewat PR | FINAL |
| D-104 | Panel provinsi `panel_weekly` ikut paket juri (izin BI mencakup redistribusi turunan) | FINAL |

---

## 22. Ringkasan isu terbuka (lengkap: `docs/OPEN_ISSUES.md`)

| ID | Isu | Status |
|---|---|---|
| U3 | Tanggal & isi PADG 7/2026 → `params.calendar.breaks.padg_7_2026` | 🔴 |
| U4 | Periode impor BPS terbaru (s.d. 2026-09 tersedia) | 🟡 |
| U5 | FAOSTAT tanpa bawang putih kering → `hortikultura_produksi` + impor BPS v2/Comtrade 070320 | 🟡 |
| U6 | Regulasi direvisi 20 Nov; sisa: HET Minyakita, tanggal Perbadan 4/5/6/2024, Kepbadan 299/2025, HET beras premium | 🟡 |
| U7 | Ketentuan BPS & FRED → mentah tidak dikirim | 🟡 |
| U8 | Kelayakan uji asimetri (tergantung MDE) | 🔴 |
| U9 | Daya deteksi heterogenitas provinsi | 🔴 |
| U10 | Varian representatif dibekukan di G6 | 🟡 |
| U11 | Kecukupan produksi hanya beras | 🟡 |
| U12 | Bibliografi belum lengkap | 🔴 |
| U13 | Izin BI diperoleh 2026-11-20, mencakup redistribusi data turunan (panel provinsi dikirim, D-104) | 🟢 |
| U14 | Populasi provinsi: CSV penduduk 2025 sudah diunduh, menunggu diunggah (U103) | 🟡 |
| U15 | `n_kota` per provinsi | 🔴 |
| U16 | URL Pink Sheet berubah per rilis → `download` resolusi otomatis dari halaman World Bank | 🟢 |
| U17 | Lonjakan harga satu hari | 🔴 (WP-10) |
| U19 | Endpoint PIHPS vs "unduh resmi" | 🔴 `[HUMAN]` |
| U20 | Pemetaan komoditas Bapanas → PIHPS | 🔴 (WP-10) |
| U21 | Konversi GKG → beras | 🔴 (WP-07) |
| U22 | `carry_forward` tinggi = kekakuan harga; bukan filter | 🟡 |
| U24 | Hosting mentah di Kaggle privat / Drive; folder Drive tim wajib dibagikan terbatas | 🟡 |
| U100 | Kredensial Drive untuk Kaggle (OAuth client + token per anggota) | 🔴 `[HUMAN]` |
| U101 | Keaslian Pink Sheet: identik dengan rilis resmi 3 Nov 2026 | 🟢 |
| U102 | Uji tumpang tindih Comtrade vs BPS 2022 (server BPS error) | 🔴 |
| U103 | Unggah CSV penduduk 2025 & snapshot kab/kota Panel Harga | 🔴 `[HUMAN]` |
| U104 | `pihps_v1` dipensiunkan ke `_superseded/` (D-102) | 🟢 |
Selesai: U1, U2, U18, U23.

---

## 23. Jebakan & pelajaran yang sudah ditemukan

1. **Urutan baris PIHPS v2 tidak bisa dipercaya** — varian hasil merge di akhir file; `ffill` grup salah menempelkan
   (Cabai Rawit Merah → Gula Pasir). Sebelum diperbaiki, cabai rawit & minyak goreng tampak hilang di banyak provinsi.
   Pelajaran: selalu validasi asumsi struktur file mentah dengan tes pada SEMUA file.
2. **"Data hilang" bisa artefak kode** — periksa loader sebelum menyimpulkan cakupan data buruk.
3. **carry_forward ≠ data jelek** — rangkaian harga identik panjang wajar untuk komoditas diatur.
4. **2024 punya 53 hari Senin** — tes yang mengasumsikan 52 minggu/tahun salah.
5. **Minggu Lebaran tanpa fixing JISDOR** — 5 minggu; tanpa pengisian, LP kehilangan 2 minggu per kejadian.
6. **Spasi akhir pada nama varian** dan ejaan provinsi berbeda antar sumber ("D.I Yogyakarta", "KEP. RIAU").
7. **Pink Sheet seri kosong/nol** — `np.log` pada kolom tak terpakai memicu warning; batasi ke seri yang dibutuhkan.
8. **dw bulanan vs de mingguan** — memakai JISDOR mingguan untuk w membuat dw ≈ de di dalam bulan (kolinear).
9. **Perubahan struktur oleh user** — isi `src/kagami/` dipindah ke `src/`; folder kosong yang tersisa menutupi
   paket sebagai namespace package. Jangan membalikkan perubahan user tanpa bertanya.
10. **CRLF dari `write_text` di Windows** dan heredoc bash yang rapuh (§4.5).
11. **Tes vs data asli**: kegagalan tes bisa karena asumsi tes keliru (bulan sintetis mulai Februari, NaN baris pertama);
    periksa dulu sebelum mengubah kode.
13. **Python Windows tanpa CA lokal** → `CERTIFICATE_VERIFY_FAILED` saat unduh; `download` memakai bundel `certifi`
    (verifikasi SSL tetap aktif; jangan pernah mematikannya).
14. **Membandingkan dengan rilis yang salah** memberi kesimpulan salah (selisih pembulatan dikira file rekayasa); selalu
    cocokkan tanggal rilis/versi sebelum menilai keaslian.
12. **`find_spec` pada nama fungsi** melempar `ModuleNotFoundError` (dipakai di tes wiring dengan try/except).

---

## 24. Larangan

- Mengubah/menimpa file di `data/raw/` atau menulis ke `raw_dir`.
- Angka analisis tersembunyi di kode; mengubah `params.yaml` setelah G6 tanpa catatan deviasi.
- Logika analisis di notebook atau app; estimasi saat runtime di app.
- Split acak per baris; memakai informasi masa depan di Task 4.
- Menghapus data diam-diam; mencampur varian berbeda dalam satu seri.
- Melihat β Task 1 sebelum MDE (WP-09) selesai.
- Memasang statsmodels/linearmodels; menambah dependensi tanpa alasan dan tanpa memperbarui pyproject.
- Mengirim data mentah tanpa hak ke zip juri; membuat dataset Kaggle mentah publik.
- Klaim kausal/prediktif (§20).
- Mengerjakan tugas `[HUMAN]` (email, login akun Kaggle/Google, unggah, video) — siapkan bahannya saja.
- Menjalankan perintah git yang mengubah index/riwayat/branch/remote (commit, push, add, dll.); command copas hanya bila diminta (§4.6).
- `git init` ulang, membuat folder `src/kagami/`, menambah `src` ke PYTHONPATH.
- Membalikkan perubahan file yang dibuat user/OneDrive tanpa bertanya.

---

## 25. Glosarium

| Istilah | Arti |
|---|---|
| PIHPS | Pusat Informasi Harga Pangan Strategis (Bank Indonesia) — harga eceran harian per provinsi |
| JISDOR | Jakarta Interbank Spot Dollar Rate (BI) — kurs IDR/USD harian |
| Pink Sheet / CMO | World Bank Commodity Price Data — harga dunia bulanan USD |
| HET / HAP / HPP | Harga Eceran Tertinggi / Harga Acuan Pembelian-Penjualan / Harga Pembelian Pemerintah |
| TPID | Tim Pengendalian Inflasi Daerah (pengguna sasaran) |
| LP | local projections (Jordà 2005) |
| PT | rasio pass-through β/γ |
| MDE | minimum detectable effect (α 0,05, power 0,80) |
| EB | penyusutan empirical Bayes |
| DL / REML | estimator τ² DerSimonian–Laird / restricted maximum likelihood |
| BH / FDR | Benjamini–Hochberg false discovery rate |
| ARI | adjusted Rand index |
| DM / HAC / HLN | uji Diebold–Mariano / varians tahan heteroskedastisitas-autokorelasi / koreksi Harvey–Leybourne–Newbold |
| CR1 / CR2 | koreksi SE cluster (CR2 = Bell–McCaffrey, untuk cluster sedikit) |
| GKG | gabah kering giling |
| Tingkat A/B/C | tingkat reproduksi juri (app / data turunan / unduh ulang) |
| G6, G-power, G-het, G7, G8 | gerbang keputusan (§13) |
| WP | work package di `docs/WORKPLAN.md` |
| `[HUMAN]` | tugas yang harus dilakukan manusia |

---

## 26. Template

### 26.1 Entri SESSION_LOG (di atas bagian anggota sendiri, ≤ 10 baris; handoff: `docs/HANDOFF.md`)
```
## YYYY-MM-DD — <Nama>: WP-xx ✅/🔶 (judul singkat)
- Yang diimplementasi + file utama + tes baru.
- Artefak ditulis (jumlah baris) + angka penting dari data asli.
- Bug/temuan + D-xxx / U-xx terkait.
- Belum selesai / diblokir oleh apa.
- Berikutnya: WP-.. → WP-..
```

### 26.2 Entri DECISIONS
```
### D-<nnn> — Judul keputusan · FINAL|PROVISIONAL|DIGANTI oleh D-<mmm> · YYYY-MM-DD (WP-xx) · <Nama>
(nomor baru: Danen D-100+, Ardell D-200+, Abi D-300+)
Apa yang diputuskan, alternatif yang ditolak dan alasannya, bukti (angka), dampak hilir.
(Setelah G6, tambahkan label DEVIASI PRAREGISTRASI bila mengubah hal yang dibekukan.)
```

### 26.3 Baris OPEN_ISSUES
```
| U<n> | Isu | Default sementara | Tenggat | WP | 🔴/🟡/🟢 + catatan resolusi bertanggal |
(nomor baru: Danen U100+, Ardell U200+, Abi U300+)
```

### 26.4 Ringkasan akhir turn ke user
Apa yang berubah (file, artefak), angka penting, temuan yang butuh keputusan user, yang belum diverifikasi,
lalu satu pertanyaan langkah berikutnya.
