# Protokol audit D-155 — validitas S1 (universe ranking), V1 vs V2, anggaran pemantauan, selisih C1-tuned vs IW_NAT

Ditulis 2026-11-25 sebelum perhitungan audit; tidak diubah sesudahnya (sha256 di laporan). Menjawab audit Danen atas D-152–D-154.
Tidak ada model baru, tidak ada pemilihan baru. Periode test 2024+ **bukan** data independen (sudah dipakai D-145–D-154); semua angka test
di sini adalah evaluasi eksploratif dengan definisi yang ditetapkan sebelumnya.

## 1. Universe ranking yang benar
Kandidat pada origin o = semua baris provinsi × komoditas dengan fitur lag tersedia pada o (`split_forward` D-152: tidak mensyaratkan
target). Baris y = 0 tetap kandidat (bukan kenaikan material). Baris yang targetnya kemudian tidak teramati tetap kandidat dan, bila
ditandai, dihitung **bukan** kena (utama); analisis kepekaan mengeluarkannya dari penyebut presisi. Skor model untuk baris tanpa target
diisi dengan C1-tuned yang dilatih ulang pada origin itu (latih identik; baris bertarget harus sama persis dengan prediksi D-151).

## 2. Kebijakan daftar pantau (deskriptif; tidak ada K yang dipilih)
- V1-K: K = 1, 2, 3 komoditas skor tertinggi per provinsi per origin (K = 2 = S1 D-154).
- V2-10%: 10% kandidat nasional per origin (D-154).
- V2-setara: N kandidat nasional per origin dengan N = jumlah alarm V1-K2 pada origin itu (jumlah alarm sama → V1 dan V2 dapat
  dibandingkan langsung).
- Per kebijakan × skor (C1-tuned, 4 aturan naif): alarm per origin, presisi, recall, alarm palsu per origin, jumlah provinsi dengan
  ≥ 1 alarm per origin, porsi alarm per komoditas.
- Interval resmi hanya untuk S1 (V1-K2 vs pembanding naif pilihan dev: `R_mom` h 4, `R_nat` h 8); `R_rev` = kepekaan. Lainnya deskriptif.

## 3. Selisih C1-tuned vs IW_NAT (prediksi D-151 dev & test)
Jumlah baris dengan arah prediksi berbeda; di antara yang berbeda (y ≠ 0): diperbaiki IW_NAT (C1 salah → IW benar) vs dirusak (C1 benar →
IW salah); per komoditas; per kuintil |y| (ambang dari baris C1-tuned per horizon). Deskriptif, tanpa keputusan.
