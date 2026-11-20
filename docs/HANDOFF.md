# Format Handoff (serah-terima antar anggota)

Handoff = catatan tertulis setiap kali pekerjaan seorang anggota **dibutuhkan, diubah, atau diteruskan** oleh anggota lain.
Tujuannya agar penerima bisa langsung bekerja tanpa bertanya. Tidak ada rapat; handoff menggantikan "kabar-kabari".

- **Satu handoff = satu file** di `docs/handoff/`. Tidak pernah bentrok saat merge karena tiap file unik.
- **Versi pendek** (§5) ditempel di chat tim sebagai notifikasi, berisi tautan ke file lengkapnya.
- Format dicek otomatis oleh `tests/test_handoff.py`.
- Hubungan dengan dokumen lain: `SESSION_LOG.md` = catatan kerja pribadi per sesi; **handoff** = pesan ke orang lain;
  `DECISIONS.md` / `OPEN_ISSUES.md` = keputusan/isu (handoff hanya merujuk ID-nya).

## 1. Kapan wajib membuat handoff

| Jenis | Kapan | Contoh |
|---|---|---|
| `TERBIT` | Artefak yang dipakai anggota lain sudah tersedia (titik terbit P1–P5) | Danen → Ardell: P1 `drivers_weekly`, `panel_weekly_region` |
| `PERMINTAAN` | Butuh perubahan pada file/WP milik anggota lain | Ardell → Danen: tambah kolom di `profiles` |
| `SERAH-TERIMA-WP` | WP berpindah PIC atau dilanjutkan orang lain | Danen → Ardell: WP-10 dilanjutkan Ardell |
| `DATA-MANUAL` | Abi menyerahkan CSV data manual (PEMBAGIAN_TUGAS §6.2) | Abi → Ardell: `populasi_provinsi.csv` |
| `ANGKA-MAKALAH` | Angka/tabel/gambar final untuk makalah, findings, atau video | Ardell → Abi: rasio MAE Task 4 |
| `KEPUTUSAN` | Keputusan baru (D-xxx) yang mengubah kerja anggota lain | Danen → Semua: hasil G-power |
| `BLOKIR` | Ada hal yang menghentikan kerja; penerima perlu bertindak | Abi → Danen: endpoint PIHPS bukan unduh resmi (U19) |
| `ONBOARDING` | Memulai anggota baru / awal kolaborasi | Danen → Semua: skeleton siap |

Tidak perlu handoff untuk pekerjaan yang hanya memengaruhi diri sendiri; cukup SESSION_LOG.

## 2. Nama file

```
docs/handoff/YYYYMMDD-HHMM_<dari>-ke-<ke>_<topik-singkat>.md
```

- `<dari>`, `<ke>`: `danen`, `ardell`, `abi`, atau `semua` (huruf kecil). Untuk beberapa penerima pakai `semua`, lalu
  sebutkan namanya di field `ke`.
- `<topik-singkat>`: huruf kecil + tanda hubung, contoh `p1-penggerak`, `wp10-qa`, `populasi-provinsi`.
- Contoh: `20261121-1730_danen-ke-ardell_p1-penggerak.md`.

## 3. Template lengkap (salin ke file baru)

````markdown
---
dari: Danen
ke: Ardell
jenis: TERBIT
terkait: WP-06, WP-08, P1
status: terbuka
dibuat: 2026-11-21 17:30
tenggat_respon: 2026-11-22
---

# <Judul singkat: apa yang diserahkan>

## Ringkasan
Satu sampai dua kalimat: apa yang sudah siap/berubah dan apa yang perlu penerima lakukan.

## Yang diserahkan
| Item | Lokasi | Versi | Catatan |
|---|---|---|---|
| `drivers_weekly` | Drive tim `data/processed/` | commit `abc1234` (branch `danen/wp-08`) | 516 minggu, kolom `episode` sudah terisi |

## Perubahan kontrak
- Artefak/kolom/skema: tidak ada | aditif: <sebutkan>
- `configs/*.yaml`: tidak ada | <kunci> = <nilai lama> → <nilai baru> (D-xxx)
- Fungsi publik yang berubah signature: tidak ada | <modul::fungsi>

## Yang perlu dilakukan penerima
- [ ] Langkah 1 (konkret, bisa dicentang)
- [ ] Langkah 2

## Cara memverifikasi
```powershell
python -m kagami status
```
Hasil yang diharapkan: <apa yang harus terlihat>.

## Angka penting
| Besaran | Nilai | Sumber artefak |
|---|---|---|
| Jumlah episode depresiasi | 7 | `episodes` |

## Batasan, risiko, yang belum beres
- <hal yang belum selesai / asumsi sementara / kualitas data> (rujuk U-xx / D-xxx bila ada)

## Balasan
Penerima mengubah `status` menjadi `diterima` saat mulai menindaklanjuti dan `selesai` saat semua kotak dicentang.
Pertanyaan/penolakan → buat handoff balasan (jenis `PERMINTAAN` atau `BLOKIR`) yang merujuk nama file ini di `terkait`.
````

### Field wajib (frontmatter)

| Field | Isi yang valid |
|---|---|
| `dari` | `Danen` / `Ardell` / `Abi` |
| `ke` | satu atau lebih dari `Danen`, `Ardell`, `Abi` (dipisah koma) atau `Semua` |
| `jenis` | `TERBIT`, `PERMINTAAN`, `SERAH-TERIMA-WP`, `DATA-MANUAL`, `ANGKA-MAKALAH`, `KEPUTUSAN`, `BLOKIR`, `ONBOARDING` |
| `terkait` | ID yang relevan: `WP-xx`, `P1`–`P5`, `D-xxx`, `U-xx`, atau nama file handoff lain; `-` bila tidak ada |
| `status` | `terbuka` → `diterima` → `selesai` (atau `ditolak`, disertai handoff balasan) |
| `dibuat` | `YYYY-MM-DD HH:MM` (WIB) |
| `tenggat_respon` | `YYYY-MM-DD` atau `-` |

Bagian wajib di isi: **Ringkasan**, **Yang diserahkan**, **Yang perlu dilakukan penerima**. Bagian lain boleh berisi
"tidak ada" tetapi tidak dihapus, agar penerima tahu hal itu sudah dipertimbangkan.

## 4. Isi tambahan per jenis

| Jenis | Wajib ada di "Yang diserahkan" / "Angka penting" |
|---|---|
| `TERBIT` | Nama artefak persis seperti di registry; lokasi (folder Drive tim, sudah di-push); commit kode yang menghasilkannya; jumlah baris; hasil `python -m kagami status`; bahwa data bukan sintetis |
| `PERMINTAAN` | File/fungsi milik penerima yang perlu diubah; perubahan yang diminta; alasan; **solusi sementara** yang dipakai peminta agar tetap tidak menunggu |
| `SERAH-TERIMA-WP` | Branch & commit terakhir; fungsi yang sudah ✔ dan yang masih stub; tes yang ada/gagal; jebakan yang ditemukan; sisa langkah dari heading WP |
| `DATA-MANUAL` | Path CSV; kesesuaian dengan skema PEMBAGIAN_TUGAS §6.2; sumber (URL) per kolom; cakupan (provinsi/tahun); nilai yang tidak ditemukan |
| `ANGKA-MAKALAH` | Tabel angka **dengan interval & satuan**; artefak sumber; kalimat yang sudah lolos rambu klaim (CLAUDE.md §20); grafik yang dipakai (fungsi `viz.plots`) |
| `KEPUTUSAN` | ID D-xxx; ringkasan; dampak ke WP/anggota lain; apakah DEVIASI PRAREGISTRASI |
| `BLOKIR` | Apa yang terhenti; sejak kapan; apa yang dibutuhkan dari penerima; pekerjaan lain yang dikerjakan sementara |
| `ONBOARDING` | Status proyek; langkah pertama penerima; dokumen yang harus dibaca; akses yang dibutuhkan |

## 5. Versi pendek untuk chat (ditempel setelah file dibuat)

```
[KAGAMI] <JENIS> — <Dari> → <Ke>
Inti: <satu kalimat>
Lokasi: <Drive/Kaggle/branch + commit>
Aksi <Ke>: <langkah pertama>
Tenggat respon: <tanggal>
Detail: docs/handoff/<nama-file>.md
```

## 6. Siklus & aturan

1. **Pengirim** membuat file handoff di branch-nya, lalu commit & push sendiri (agent tidak commit/push; command git hanya bila diminta, CLAUDE.md
   §4.6), lalu menempel versi pendek di chat.
2. **Penerima** mengubah `status: diterima` saat mulai, mencentang kotak saat mengerjakan, dan `status: selesai` saat beres.
   Hanya field `status` dan kotak centang yang boleh diubah penerima; isi lain milik pengirim.
3. **Abi** (tanpa git): tulis handoff dengan template yang sama di folder Drive tim `handoff/` dan tempel versi
   pendek di chat; penerima (Danen/Ardell) menyalinnya ke `docs/handoff/` saat commit berikutnya.
4. Handoff tidak menggantikan sumber kebenaran: keputusan tetap dicatat di DECISIONS, isu di OPEN_ISSUES, status WP di WORKPLAN.
5. Handoff `terbuka` lebih dari 1 hari setelah `tenggat_respon` → pengirim menulis handoff `BLOKIR` atau memakai solusi sementara.
6. Jangan menghapus handoff lama; yang `selesai` tetap menjadi jejak.

## 7. Peran agent
- **Awal sesi:** cari handoff dengan `ke` = anggota sesi ini (atau `Semua`) dan `status` ≠ `selesai`; ringkas untuk user dan
  tawarkan tindak lanjutnya.
- **Akhir sesi:** bila pekerjaan memenuhi §1, buat file handoff dari template + versi pendek chat. Command git untuk
  meng-commit handoff hanya disiapkan bila user memintanya.
