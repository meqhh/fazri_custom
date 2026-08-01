# Fazri Custom

**Versi:** 17.0.0.1  
**Author:** [Fazri Muhammad Yazid](https://github.com/meqhh)  
**NIM:** 3312311050  
**Jurusan:** Teknik Informatika  
**Program Studi:** [Teknik Informatika]  
**Lisensi:** LGPL-3  
**Kompatibel dengan:** Odoo 17 Community

---

## Tentang Modul Ini

Modul ini dibuat untuk menangani proses rekrutmen dari awal sampai akhir — mulai dari kandidat mengirim lamaran, tim HR mengirim penawaran gaji, kandidat menandatangani kontrak secara digital, sampai data karyawan baru tersimpan dengan rapi. Ada juga integrasi WhatsApp supaya komunikasi dengan kandidat bisa lebih cepat dan praktis.

---

## Fitur-fitur

### 1. Manajemen Lamaran Kerja (`hr.applicant`)

Dikembangkan dari modul rekrutmen bawaan Odoo dengan beberapa tambahan:

- **Cover Letter / Ringkasan** — Kandidat bisa melampirkan surat lamaran atau ringkasan profil mereka.
- **Tipe Kontrak** — Bisa pilih antara kontrak *Temporary* (Sementara) atau *Permanent* (Tetap).
- **Interviewer** — Setiap lamaran bisa langsung ditugaskan ke salah satu interviewer.
- **Riwayat Penawaran** — Lamaran terhubung ke semua penawaran gaji yang pernah dikirim ke kandidat tersebut.
- **Skill & Resume** — Data keahlian dan riwayat pengalaman kerja kandidat bisa diisi langsung di formulir lamaran.
- **Proteksi Data** — Kalau kandidat sudah berstatus *Hired*, datanya tidak bisa diubah lagi untuk menjaga integritas rekam jejak.

---

### 2. Penawaran Gaji (`salary.offer`)

Bagian utama yang mengatur seluruh proses penawaran gaji ke kandidat:

- **Alur Status** — Penawaran berjalan lewat alur: `Draft → Proposed → Accepted & Contract Signed / Rejected / Cancel`.
- **Tautan Unik per Kandidat** — Setiap penawaran punya *access token* unik yang menghasilkan tautan portal khusus untuk kandidat.
- **Kirim via WhatsApp** — Tautan penawaran bisa langsung dikirim ke WhatsApp kandidat lewat gateway yang sudah dikonfigurasi.
- **Template Kontrak** — Penawaran bisa dihubungkan ke template kontrak tertentu untuk generate dokumen kontrak secara otomatis.
- **Validasi Gaji** — Sistem tidak akan menerima nilai gaji yang nol atau negatif.
- **Catat Penolakan** — Kalau kandidat menolak, alasan penolakan tersimpan dengan rapi.

---

### 3. Portal Kandidat

Kandidat bisa berinteraksi dengan sistem lewat halaman web, tanpa perlu punya akun Odoo:

- **Halaman Penawaran Gaji** — Kandidat bisa lihat detail penawaran dan pilih *Terima* atau *Tolak*.
- **Halaman OTP** — Verifikasi identitas kandidat pakai kode OTP sebelum menerima penawaran.
- **Halaman Tanda Tangan Kandidat** — Kandidat menandatangani kontrak secara digital dari perangkat mereka sendiri.
- **Halaman Terima Kasih** — Konfirmasi otomatis setelah proses selesai.
- **Halaman Karir** — Portal publik untuk menampilkan lowongan yang sedang dibuka.
- **Halaman Formulir Lamaran** — Calon pelamar bisa kirim lamaran langsung lewat website.

---

### 4. Kontrak Kerja Digital (`hr.contract`)

Dikembangkan dari modul kontrak bawaan Odoo dengan fitur tanda tangan digital dua pihak:

- **Tanda Tangan Kandidat** — Kandidat menandatangani kontrak lewat tautan portal yang aman.
- **Tanda Tangan HR/Employer** — Tim HR atau perwakilan perusahaan menandatangani lewat tautan terpisah yang khusus.
- **Status Tanda Tangan** — Kontrak punya status progres: `Draft → Candidate Signed → Waiting HR Signature → Completed`.
- **Verifikasi Kontrak** — HR bisa memverifikasi data kontrak lewat sistem aktivitas Odoo.
- **Nomor Kontrak Otomatis** — Nomor kontrak dibuat otomatis dengan format `CTR\<Nama>\<Nomor Urut>`.

---

### 5. Jejak Tanda Tangan (`hr.contract.signature.trail`)

Setiap proses penandatanganan kontrak dicatat secara lengkap untuk keperluan audit:

- Nama, email, dan nomor telepon penandatangan.
- Waktu tepat saat tanda tangan dilakukan.
- Alamat IP dan *User Agent* perangkat yang dipakai.
- Gambar tanda tangan tersimpan sebagai lampiran.
- Mendukung dua tipe penandatangan: *Candidate* dan *HR*.

---

### 6. Template Kontrak (`hr.contract.template`)

Sistem pembuatan template kontrak yang cukup fleksibel, bisa disusun per-baris dengan berbagai tipe konten:

| Tipe | Keterangan |
|---|---|
| Text | Paragraf teks biasa, bisa pilih heading (H1, H2, H3) dan perataan teks |
| Listed List | Daftar berurutan (bernomor) |
| Unlisted List | Daftar tidak berurutan (bullet) |
| Table | Tabel dengan label dan nilai |
| Page Breaker | Pemisah halaman |
| Signature | Bagian tanda tangan |

Setiap baris juga bisa dikustomisasi ukuran font, padding, dan margin-nya. Ada fitur preview juga sebelum template dipakai beneran.

---

### 7. Manajemen Penolakan Penawaran (`offer.refuse`)

Khusus untuk menangani kandidat yang menolak penawaran gaji:

- Alasan penolakan dari kandidat tersimpan.
- Opsi **Postpone** untuk menangguhkan proses sementara.
- Opsi **Resend Offer** untuk buat salinan penawaran baru dan kirim ulang ke kandidat.

---

### 8. Integrasi WhatsApp

Pengiriman pesan WhatsApp via gateway pihak ketiga:

- **Konfigurasi Gateway** — URL dan API Key bisa diatur per perusahaan.
- **Wizard Pengiriman** — Antarmuka simpel untuk susun dan kirim pesan langsung dari formulir lamaran atau penawaran.
- **Pesan Otomatis** — Undangan interview dibuat otomatis berdasarkan data lamaran (nama, posisi, tanggal, dan lokasi).
- **Normalisasi Nomor** — Nomor format lokal (`08xx`) otomatis dikonversi ke format internasional (`62xx`).
- **Log Pengiriman** — Setiap percobaan kirim pesan dicatat untuk keperluan monitoring.

---

### 9. Log API (`api.log`)

Mencatat semua aktivitas yang melibatkan layanan eksternal:

- URL tujuan, header, dan body dari setiap permintaan tercatat.
- Kode respons dan isi respons dari layanan eksternal tersimpan.
- Status keberhasilan (*Success* / *Failed*) dihitung otomatis berdasarkan kode HTTP.

---

### 10. Data Karyawan yang Diperluas (`hr.employee`)

Beberapa field tambahan pada data karyawan:

| Field | Keterangan |
|---|---|
| Nama Ibu | Nama gadis ibu kandung karyawan |
| Agama | Agama yang dianut karyawan |
| Rekening Bank | Terhubung ke data rekening bank Odoo |
| Tanggal Bergabung | Tanggal mulai kerja di perusahaan |
| Nomor Karyawan | ID karyawan yang dibuat otomatis pakai prefix perusahaan |
| NPWP | Nomor Pokok Wajib Pajak karyawan |
| Tanda Tangan | Gambar tanda tangan digital karyawan |
| CV | File CV karyawan |
| Status Verifikasi | Status data: *Unverified* / *Verified* |

---

### 11. Data Master Tambahan

- **Agama (`hr.religion`)** — Daftar agama yang bisa dipilih di profil karyawan.
- **Sumber Lamaran (`utm.source`)** — Manajemen sumber lamaran (job portal, referral, dll.) dengan fitur aktif/nonaktif.
- **Data Bank** — Daftar bank yang sudah tersedia untuk memudahkan pemilihan.

---

## Dependensi

Modul ini butuh modul-modul Odoo berikut:

`mail`, `utm`, `calendar`, `base`, `web`, `hr`, `hr_recruitment`, `hr_contract`, `hr_recruitment_skills`, `contacts`, `main_menu`

---

## Informasi Pengembang

| | |
|---|---|
| Nama | Fazri Muhammad Yazid |
| NIM | 3312311050 |
| GitHub | [github.com/meqhh](https://github.com/meqhh) |
| Versi Odoo | 17.0 Community |
