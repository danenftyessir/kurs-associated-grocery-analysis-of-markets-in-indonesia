# Praregistrasi KAGAMI (beku di G6)

**Status: BEKU (2026-11-20 23:29 WIB).** Perubahan apa pun pada isi dokumen ini, `configs/params.yaml`, atau
`configs/commodities.yaml` dicatat di DECISIONS.md dengan label DEVIASI PRAREGISTRASI.

## 1. Data & sampel
- Outcome: PIHPS pasar tradisional, varian representatif per `configs/commodities.yaml` (D-011, FINAL): Beras Kualitas Medium I,
  Bawang Putih/Merah Ukuran Sedang, Gula Pasir Lokal, Minyak Goreng Kemasan Bermerk 1, Daging Ayam Ras Segar, Telur Ayam Ras Segar,
  Daging Sapi Kualitas 1, Cabai Merah Keriting, Cabai Rawit Merah.
- Periode: 2018-01-01 .. 2026-11-21 (FINAL; 337/340 seri layak, fallback 2020 tidak dipakai, D-006).
- Komoditas fokus (D-013, FINAL): 5 grup konfirmatori — bawang putih, gula pasir, minyak goreng, pakan (daging ayam & telur,
  diestimasi terpisah), daging sapi. Kontrol domestik: bawang merah, cabai merah, cabai rawit. Lainnya: beras.
- Kelayakan seri: missing ≤ 20%, celah ≤ 8 minggu, setiap tahun ≥ 70%.
- Penggerak: Δ log JISDOR mingguan; Δ log harga dunia padanan dalam rupiah (komposit pakan 0,6·Maize + 0,4·Soybean meal, D-012 FINAL); kontrol Brent, musiman.

## 2. Hipotesis & uji
| Kode | Uji | α / koreksi | Status konfirmatori |
|---|---|---|---|
| H0-Het | Q per komoditas (h=8) vs 499 plasebo geser-melingkar | BH FDR q ≤ 0,05 antar 10 komoditas | Konfirmatori |
| H2 | Wald β⁺(8) = β⁻(8), SE cluster minggu | α = 0,05 dua arah | Konfirmatori hanya bila MDE asimetri ≤ 0,5 (ditentukan di G-power), selain itu deskriptif |
| H3 | Meta-regresi efek acak, koef. ln(1+jarak hub) | h=4: satu arah (<0), α = 0,05; h=12: dua arah | Konfirmatori (waktu) |
| H5 | Rasio MAE M2/M1 h=8, origin large_move, DM HAC | α = 0,05 keluarga atas 2 grup jalur {direct_import, imported_input}, koreksi **Holm** (`params.forecast.h5_correction`, D-109) | Konfirmatori |
| E1 | Kendall τ PT(8) vs rasio impor langsung, p permutasi eksak | – | Deskriptif |
| E2 | Profil respons per rezim HET/HAP | – | Eksploratif |
| E3 | Frekuensi perubahan harga sebagai kovariat meta-regresi | – | Eksploratif |

## 3. Parameter beku (dari `configs/params.yaml`)
Horizon 0–12, lag 4 (robust 2/8), B = 499, R = 499, blok 13 minggu, geser minimum 52 minggu, episode ≥ 3% dalam 8 minggu,
k ∈ {1..6}, persentil silhouette plasebo 95, K-Means 50 restart, Jaccard lemah < 0,6, δ tertanam 0,1–0,5,
Task 4: h ∈ {4, 8}, origin tiap 4 minggu sejak 2021-01-04, large_move = p80 data latih.

## 4. Aturan keputusan
- G-power (D-007): MDE PT(8) > 0,5 untuk bawang putih, gula, minyak goreng → LP sekunder.
- Struktur regional diterima hanya bila silhouette maks > p95 plasebo; selain itu k = 1.
- Hasil nol dilaporkan sebagai batas atas ("pengaruh di atas X dapat dikesampingkan").

## 5. Dibekukan pada
- Tanggal/jam: 2026-11-20 23:29 WIB (sebelum β Task 1 dilihat; MDE sementara sudah dihitung, D-007)
- sha256 `configs/params.yaml`: `67e0839820d744cd12e2fe702bbe12e1a15f6dcdc46a7670b78c8f93f5f7bfb7`
- sha256 `configs/commodities.yaml`: `883eee0a30cffffea7ea01f31599a343b9ef27e53c55569e9edf05b2197db296`
- Hash dihitung atas isi berakhiran baris LF (sama dengan blob git); clone Windows dengan `core.autocrlf` bisa memberi hash
  berbeda — cek dengan `git show HEAD:configs/params.yaml | sha256sum`.
- Dibekukan oleh: Danen (keputusan G6: varian, bobot pakan, grup fokus, koreksi Holm H5)
