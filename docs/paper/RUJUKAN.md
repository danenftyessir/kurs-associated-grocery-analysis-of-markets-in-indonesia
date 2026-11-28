# Verifikasi rujukan makalah (U12)

Catatan bertanggal 2026-11-28 (Danen, dengan agent). Setiap rujukan di `kagami_makalah.tex` dicocokkan identitasnya (penulis,
tahun, judul, terbitan, volume, halaman) dengan sumber resmi sebelum dikutip. Cara verifikasi:

- **DOI** — metadata dari API Crossref (`https://api.crossref.org/works/<DOI>`), dibandingkan dengan entri di makalah.
- **arXiv** — metadata dari API arXiv (`export.arxiv.org/api/query?id_list=...`).
- **Halaman resmi** — halaman penerbit atau lembaga diambil langsung (judul, penulis, tanggal).
- **Teks lengkap** — untuk klaim kuantitatif yang dikutip dari studi lain, angka dicek pada teks lengkap artikel (akses terbuka).

Kajian pustaka makalah bersifat tematik, bukan tinjauan sistematis (tanpa protokol PRISMA), dan ditulis demikian di makalah.

## 1. Rujukan yang dikutip (55)

| Kunci | Rujukan | Cara verifikasi | Catatan |
|---|---|---|---|
| aginta2022 | Aginta & Someya (2022), J. Economic Structures 11, Art. 1 | DOI 10.1186/s40008-021-00260-6 | – |
| almuzara2024 | Almuzara & Sancibrián (2024), FRBNY Staff Report 1090 | DOI 10.59576/sr.1090 | Proposal mengutip versi IGIER WP 732 (2026) yang tidak ditemukan di Crossref; dikutip versi FRBNY yang terverifikasi |
| amatullah2025 | Amatullah dkk. (2025), JAIC 9(1) 121–130 | DOI 10.30871/jaic.v9i1.8840 | studi data mining harga gula per provinsi (baru, menggantikan "studi DM PIHPS" yang belum terverifikasi) |
| amiti2014 | Amiti, Itskhoki & Konings (2014), AER 104(7) 1942–1978 | DOI 10.1257/aer.104.7.1942 | – |
| apaitan2024 | Apaitan dkk. (2024), JIMF 149, 103196 | DOI 10.1016/j.jimonfin.2024.103196 | – |
| arintoko2024 | Arintoko dkk. (2024), Ekonomika 103(2) 66–89 | DOI 10.15388/Ekon.2024.103.2.4 | – |
| bapanas2026 | Badan Pangan Nasional, Panel Harga Pangan | halaman resmi (`configs/sources.yaml`) | sumber data |
| bps2026 | BPS, data ekspor impor | halaman resmi | sumber data |
| bijisdor2026 | Bank Indonesia, JISDOR | halaman resmi | sumber data |
| bipihps2026 | Bank Indonesia, PIHPS Nasional | halaman resmi | sumber data |
| bh1995 | Benjamini & Hochberg (1995), JRSS-B 57(1) 289–300 | DOI 10.1111/j.2517-6161.1995.tb02031.x | – |
| burstein2003 | Burstein, Neves & Rebelo (2003), JME 50(6) 1189–1214 | DOI 10.1016/S0304-3932(03)00075-8 | – |
| campa2010 | Campa & Goldberg (2010), REStat 92(2) 392–407 | DOI 10.1162/rest.2010.11459 | – |
| chen2023 | Chen dkk. (2023), TSMixer, TMLR | arXiv 2303.06053 (journal_ref TMLR 09/2023) | – |
| clark2026 | Clark & Huber (2026), arXiv 2608.04631 | arXiv | penulis: Todd Clark, Florian Huber |
| das2024 | Das dkk. (2024), TimesFM, arXiv 2310.10688 | arXiv | dikutip sebagai preprint |
| dl1986 | DerSimonian & Laird (1986), Controlled Clinical Trials 7(3) 177–188 | DOI 10.1016/0197-2456(86)90046-2 | – |
| dm1995 | Diebold & Mariano (1995), JBES 13(3) 253–263 | DOI 10.1080/07350015.1995.10524599 | sebelumnya "belum diverifikasi" di proposal |
| fao2026 | FAO, FAOSTAT SUA | halaman resmi | sumber data, CC BY 4.0 |
| fred2026 | FRED, DCOILBRENTEU & DTWEXBGS | halaman resmi | sumber data |
| friedman2001 | Friedman (2001), Annals of Statistics 29(5) 1189–1232 | DOI 10.1214/aos/1013203451 | – |
| gebru2021 | Gebru dkk. (2021), CACM 64(12) 86–92 | DOI 10.1145/3458723 | daftar 7 penulis dicocokkan |
| gopinath2020 | Gopinath dkk. (2020), AER 110(3) 677–719 | DOI 10.1257/aer.20171201 | daftar 6 penulis dicocokkan |
| gopinath2010 | Gopinath & Itskhoki (2010), QJE 125(2) 675–727 | DOI 10.1162/qjec.2010.125.2.675 | – |
| google2026 | Google Research (2026), TimesFM 3.0 di Hugging Face | API Hugging Face (`google/timesfm-3.0-pytorch`, repo dibuat 2026-08-24, lisensi "other") | bobot tidak ikut paket juri |
| hln1997 | Harvey, Leybourne & Newbold (1997), IJF 13(2) 281–291 | DOI 10.1016/S0169-2070(96)00719-4 | koreksi HLN pada uji DM |
| hennig2007 | Hennig (2007), CSDA 52(1) 258–271 | DOI 10.1016/j.csda.2006.11.025 | – |
| hoerl1970 | Hoerl & Kennard (1970), Technometrics 12(1) 55–67 | DOI 10.1080/00401706.1970.10488634 | – |
| holm1979 | Holm (1979), Scand. J. Statistics 6(2) 65–70 | URL stabil JSTOR 4615733 | tidak punya DOI (Crossref 404 untuk 10.2307/4615733); halaman JSTOR ada tetapi menolak akses bot |
| hubert1985 | Hubert & Arabie (1985), J. Classification 2(1) 193–218 | DOI 10.1007/BF01908075 | – |
| ibrahim2025 | Ibrahim & Nghiem (2025), Australian Economic Papers 65(2) 149–163 | DOI 10.1111/1467-8454.70018 | nama lengkap: Mansor Ibrahim, Xuan-Hoa Nghiem (catatan lama U12) |
| jorda2005 | Jordà (2005), AER 95(1) 161–182 | DOI 10.1257/0002828053828518 | – |
| kohlscheen2026 | Kohlscheen & Mehrotra (2026), BIS WP 1371 | halaman resmi BIS (22 Juli 2026) | – |
| kunsch1989 | Künsch (1989), Annals of Statistics 17(3) 1217–1241 | DOI 10.1214/aos/1176347265 | – |
| montiel2021 | Montiel Olea & Plagborg-Møller (2021), Econometrica 89(4) 1789–1823 | DOI 10.3982/ECTA18756 | – |
| nie2023 | Nie dkk. (2023), PatchTST, arXiv 2211.14730 | arXiv | dikutip sebagai preprint |
| nosek2018 | Nosek dkk. (2018), PNAS 115(11) 2600–2606 | DOI 10.1073/pnas.1708274114 | – |
| pedregosa2011 | Pedregosa dkk. (2011), JMLR 12 2825–2830 | halaman resmi JMLR | – |
| persada2026 | Persada, Subagyo & Wibowo (2026), Front. Sustain. Food Syst. 10, 1844670 | DOI + teks lengkap | **klaim dikoreksi**, lihat §3 |
| plagborg2021 | Plagborg-Møller & Wolf (2021), Econometrica 89(2) 955–980 | DOI 10.3982/ECTA17813 | – |
| pustejovsky2018 | Pustejovsky & Tipton (2018), JBES 36(4) 672–683 | DOI 10.1080/07350015.2016.1247004 | rujukan CR2; menggantikan Bell & McCaffrey (2002) yang halaman resminya menolak akses (HTTP 403) |
| rahkmawati2023 | Rahkmawati & Annisa (2023), TIERS IT Journal 4(2) 115–121 | DOI 10.38043/tiers.v4i2.5081 | studi DM PIHPS yang di proposal "belum diverifikasi" |
| rousseeuw1987 | Rousseeuw (1987), J. Comput. Appl. Math. 20, 53–65 | DOI 10.1016/0377-0427(87)90125-7 | – |
| runfola2020 | Runfola dkk. (2020), PLOS ONE 15(4) e0231866 | DOI 10.1371/journal.pone.0231866 | geometri peta app (ODbL); daftar 19 penulis dicocokkan |
| saputra2026 | Saputra dkk. (2026), JASKS 18(1) 115–129 | DOI 10.34123/jurnalasks.v18i1.973 | – |
| schroer2021 | Schröer, Kruse & Gómez (2021), Procedia CS 181, 526–534 | DOI 10.1016/j.procs.2021.01.199 | rujukan CRISP-DM |
| solorzano2023 | Solórzano (2023), LAJCB 4(4) 100100 | DOI 10.1016/j.latcb.2023.100100 | – |
| suarsih2016 | Suarsih, Achsani & Nuryartono (2016), JEPI 17(1) 1–14 | DOI 10.21002/jepi.v17i1.548 | – |
| sumertajaya2024 | Sumertajaya dkk. (2024), Sains Malaysiana 53(11) 3779–3789 | DOI 10.17576/jsm-2024-5311-20 | studi "Sains Malaysiana 2024" di proposal |
| un2015 | Majelis Umum PBB (2015), A/RES/70/1 | simbol dokumen resmi PBB | target SDG 2.c |
| unuvar2026 | Unuvar (2026), Front. Sustain. Food Syst. 10, 1960606 | DOI + teks lengkap | angka Indonesia diverifikasi, lihat §3 |
| varela2013 | Varela, Aldaz-Carroll & Iacovone (2013), 30(1) 19–44 | DOI 10.1355/ae30-1b | Crossref mencatat nama jurnal lama *ASEAN Economic Bulletin*; makalah menulis keduanya |
| ward1963 | Ward (1963), JASA 58(301) 236–244 | DOI 10.1080/01621459.1963.10500845 | – |
| widarjono2023 | Widarjono dkk. (2023), BMEB 26(1) 105–124 | DOI 10.59091/1410-8046.2047 | – |
| worldbank2026 | World Bank, Pink Sheet rilis 3 Nov 2026 | halaman resmi | sumber data, CC BY 4.0 |

## 2. Rujukan proposal yang tidak dikutip

| Rujukan | Alasan |
|---|---|
| Hidayah & Askar (2026), Policy Note CELIOS | tidak ditemukan di situs CELIOS; tidak dapat diverifikasi |
| "Sistemasi, 2026" (studi DM PIHPS) | tidak ditemukan di Crossref |
| IMF (2019), Indonesia: Selected Issues | DOI terverifikasi, tetapi isi bab yang relevan tidak dicek; tidak diperlukan untuk klaim makalah |
| Kaufman & Rousseeuw (1990) | DOI terverifikasi; silhouette cukup dirujuk ke Rousseeuw (1987) |
| Bell & McCaffrey (2002) | halaman Statistics Canada menolak akses (403); CR2 dirujuk ke Pustejovsky & Tipton (2018) |

## 3. Klaim yang dikoreksi setelah membaca teks lengkap

- **Unuvar (2026)** — benar: 17 negara berkembang, rerata penerusan kumulatif ke inflasi pangan 0,213, rentang −0,012 (Indonesia)
  sampai 0,807 (Turki); Indonesia −0,012 (SE 0,150; interval −0,306..0,281); ambang inflasi pangan tahunan 6,8–7,6%.
- **Persada dkk. (2026)** — proposal dan dokumen hidup menyebutnya bukti bahwa penerusan kurs ke harga pangan lemah. Teks lengkapnya
  tidak memuat estimasi penerusan kurs: studi itu memakai panel bulanan 26 provinsi (wilayah operasi Bulog) 2018–2022, membagi
  provinsi surplus–harga rendah dan defisit–harga tinggi, dan menemukan HPP hanya berasosiasi dengan harga eceran di provinsi defisit,
  stok CBP hanya berasosiasi dengan harga lebih rendah di provinsi surplus, harga BBM (lag 3 bulan) sebagai pendorong biaya terkuat.
  Di makalah, Persada dkk. hanya dikutip untuk heterogenitas harga beras antarprovinsi. `docs/PROJECT_OVERVIEW.md` §1 dan CLAUDE.md
  §1.2 ikut dikoreksi (D-177).
