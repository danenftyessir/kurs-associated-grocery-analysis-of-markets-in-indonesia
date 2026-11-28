# Makalah KAGAMI (WP-33)

Makalah lomba (juknis INDONERIS 2026 §2c) dalam LaTeX. Berkas yang dikumpulkan: **`kagami_makalah.pdf`**.

| Berkas | Isi |
|---|---|
| `kagami_makalah.tex` | sumber makalah (bahasa Indonesia, sitasi penulis-tahun APA, daftar pustaka manual) |
| `kagami_makalah.pdf` | hasil kompilasi |
| `figures/*.pdf` | gambar; dibuat ulang dari artefak, tidak digambar tangan |
| `scripts/make_figures.py` | Gambar 1, 3–6, 8 dari artefak resmi (`results/`, `data/processed/`, hasil analisis red flag) |
| `scripts/capture_app.py` | Gambar 7: tangkapan layar app yang sedang berjalan (Chrome + Playwright) |
| `RUJUKAN.md` | verifikasi 55 rujukan (Crossref, arXiv, halaman resmi, teks lengkap) dan rujukan proposal yang tidak dikutip |
| `NASKAH_VIDEO.md` | naskah video demo (tugas `[HUMAN]`) |

## Membangun ulang

Dari root project:

```powershell
python docs/paper/scripts/make_figures.py
```

```powershell
python docs/paper/scripts/capture_app.py http://localhost:8511
```

Langkah kedua butuh app berjalan di port itu (`python -m streamlit run app/Home.py --server.port 8511`); lewati bila tampilan
app tidak berubah. Lalu dari folder `docs/paper`, jalankan dua kali (kali kedua untuk nomor gambar dan tabel):

```powershell
pdflatex --disable-installer -interaction=nonstopmode kagami_makalah.tex
```

Catatan MiKTeX di mesin Danen: pemasangan paket otomatis disetel "tanya dulu", sehingga paket yang belum terpasang memunculkan dialog
dan kompilasi menggantung. Opsi `--disable-installer` membuat kompilasi gagal cepat sebagai gantinya. Makalah sengaja hanya memakai
paket yang sudah terpasang (`natbib`, `multirow`, dan `unicode-math` tidak ada), jadi sitasi memakai makro `\citep`/`\citet` buatan
sendiri di preamble.

## Sebelum dikumpulkan (`[HUMAN]`)

- Pastikan nama anggota (diambil dari tabel anggota di `README.md`) dan afiliasi "Institut Teknologi Bandung" di blok judul.
- Baca ulang seluruh isi sebagai tim. Draf disusun dengan bantuan agent dari `results/findings.md` dan artefak resmi; putuskan
  apakah penggunaan bantuan AI perlu dinyatakan.
- Bila ada angka yang diubah, ubah juga di `results/findings.md` (tes `tests/test_paper.py` mencocokkan angka utama keduanya).

## Penjaga otomatis

`tests/test_paper.py` memeriksa bagian wajib juknis, kecocokan sitasi dengan daftar pustaka, rambu klaim CLAUDE.md §20, angka utama
yang sama dengan `results/findings.md`, serta keberadaan PDF dan semua gambar yang dirujuk.
