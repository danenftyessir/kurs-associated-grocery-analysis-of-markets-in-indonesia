# Naskah video demo KAGAMI (tugas `[HUMAN]`)

Durasi sasaran 6–7 menit. Video wajib dikumpulkan bersama makalah dan zip (juknis §2e). Naskah ini mengikuti rambu klaim
CLAUDE.md §20: asosiasi historis, bukan sebab-akibat; hasil nol dibaca sebagai batas atas; KAGAMI adalah prototipe riset, bukan
sistem peringatan dini.

## Persiapan

- Rekam app lokal agar tidak bergantung pada jaringan: `python -m kagami app` (atau app daring https://kagami.streamlit.app
  sesudah perubahan terakhir di-push). Layar 1920×1080, zoom browser 100%, tutup tab dan notifikasi lain.
- Perekam layar: Xbox Game Bar (Win + G) atau OBS. Rekam suara terpisah bila mikrofon laptop berisik.
- Siapkan terminal di folder hasil ekstrak zip juri untuk adegan 7 (opsional, 20 detik).

## Adegan

| # | Waktu | Layar | Narasi (bacakan bebas, isi tetap) |
|---|---|---|---|
| 1 | 0:00–0:35 | Halaman Ringkasan, gulir pelan di kalimat judul | "Sepanjang 2026 rupiah melemah sampai sekitar Rp18.250 per dolar. Pertanyaan TPID sederhana: harga pangan mana yang ikut naik, di mana, dan berapa besar? KAGAMI, dari bahasa Jepang *kagami* yang berarti cermin, memeriksa sejauh mana harga pangan eceran mencerminkan rupiah." |
| 2 | 0:35–1:20 | Lampiran → Data & metode, bagian sumber dan pengolahan | "Kami membangun dataset turunan dari PIHPS Bank Indonesia: harga eceran mingguan 10 komoditas di 34 provinsi, 2018 sampai 2026, dengan status setiap minggu. Panel ini kami padukan dengan kurs JISDOR, harga dunia Pink Sheet dalam rupiah, dan riwayat HET/HAP. Hipotesis kami bekukan dalam praregistrasi sebelum hasil dilihat." |
| 3 | 1:20–2:10 | Rupiah dari waktu ke waktu: lini masa kurs, klik episode Mar–Mei 2020, lalu kipas episode | "Sejak 2018 ada 13 episode depresiasi. Untuk setiap episode kami melihat pergerakan harga 12 minggu sesudahnya dan membandingkannya dengan ratusan jendela tanpa episode. Hampir semua respons episode tidak dapat dibedakan dari kebetulan." |
| 4 | 2:10–3:10 | Respons harga: Komoditas = Minyak goreng, "Dibandingkan dengan" = harga dunia; lalu tab "Semua komoditas" | "Respons nasional terhadap kurs sebagian besar tidak terdeteksi. Asosiasi paling konsisten ada pada minyak goreng dan harga sawit dunia dalam rupiah: kenaikan 10% berasosiasi dengan kenaikan harga minyak goreng sekitar 1,5% dalam 4 minggu. Jadi untuk minyak goreng, yang lebih layak dipantau adalah harga sawit dunia dalam rupiah, bukan kurs itu sendiri." |
| 5 | 3:10–4:10 | Simulasi rupiah: beras, rupiah melemah 5%, minggu ke-8; lalu Profil provinsi untuk satu provinsi | "Hasil nol tetap berguna. Untuk beras, kenaikan harga 8 minggu yang konsisten dengan pelemahan rupiah 5% paling tinggi sekitar Rp89 per kilogram. Kalau harga beras naik Rp500, sisanya perlu ditelusuri ke pasokan, musim, atau kebijakan. Halaman profil provinsi memberi label harga seperti ini untuk setiap komoditas di provinsi pilihan." |
| 6 | 4:10–5:00 | Perbedaan antarprovinsi: peta, lalu grafik batas deteksi | "Apakah lokasi menentukan? Perbedaan antarprovinsi di atas derau hanya terdeteksi pada telur dan daging ayam, dan provinsi tidak membentuk kelompok. Uji struktur buatan menunjukkan dua atau tiga kelompok seimbang dengan selisih respons 0,2 akan terdeteksi, jadi struktur seperti itu dapat dikesampingkan." |
| 7 | 5:00–5:40 | Prediksi: rasio galat per komoditas | "Apakah kurs membantu memprediksi harga 4 dan 8 minggu ke depan? Dalam evaluasi rolling-origin pada 76 titik waktu, fitur kurs justru sedikit menambah galat. Pola harga sendiri lebih informatif daripada kurs." |
| 8 | 5:40–6:20 | Terminal: `python -m kagami status`, lalu `python -m pytest -q tests/test_app.py` (potong bagian menunggu) | "Semua hasil dapat dijalankan ulang. Paket proyek berisi kode, dataset turunan, artefak hasil, dan log eksekusi. Juri dapat membuka app dari hasil, menjalankan ulang semua tahap dari data turunan, atau mengunduh ulang data mentah." |
| 9 | 6:20–6:45 | Kembali ke Ringkasan | "KAGAMI adalah prototipe riset untuk mendukung keputusan, bukan sistem peringatan dini. Langkah berikutnya: memvalidasi kebutuhan TPID dan menambah data pasokan. Terima kasih." |

## Hal yang perlu dihindari

- Kata "menyebabkan", "memprediksi kenaikan harga", "sistem peringatan dini", atau "penelitian pertama".
- Menyebut angka tanpa batasnya ("±" untuk "sekitar" juga dihindari; ucapkan "sekitar").
- Menampilkan data mentah PIHPS atau halaman Riwayat eksekusi (alat pengembang).
