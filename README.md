# Pinjem Aja

**Topik Utama:** Sustainable Consumption

🔗 **Deployment PWS:** [PinjemAja - Pinjam Barang, Jangan Beli](https://khanyfatul-muflikhat-pinjemaja.pws.cs.ui.ac.id/)

🎨 **Desain Figma:** [Wireframe PinjemAja – Figma](https://www.figma.com/design/6dKz48JAYCguCmL9fVptaa/Wireframe-PinjemAja?node-id=0-1&p=f&t=ZN2o0JN1opeWuIMw-0)

---

## Anggota Kelompok

| NPM | Nama |
|---|---|
| 2506656614 | Della Permata Prasilda |
| 2506656835 | Joceline Nadine Immanuella |
| 2506533614 | Fatma Widya Rachma |
| 2506589755 | Khanyfatul Muflikhat |
| 2506604573 | Nafeeza Arwatabina |

---

## Deskripsi Aplikasi

Pinjem Aja adalah platform berbasis komunitas yang memungkinkan pengguna untuk meminjam dan meminjamkan barang. Pengguna dapat mengunggah barang yang sedang tidak dipakai dalam kurun waktu tertentu, lalu memasukkan informasi barang dan harga, lalu pengguna lain yang membutuhkan dapat mencari barang berdasarkan kategori, lokasi, ketersediaan, dan kondisi barang untuk kemudian mengajukan peminjaman.

**Masalah yang Diselesaikan:**
- Barang sering dibeli meski hanya digunakan sesekali (calculator, speaker, penyedot debu, dll).
- Banyak barang yang dimiliki orang lain belum dimanfaatkan secara maksimal.
- Sulit menemukan barang yang bisa dipinjam dari orang di sekitar (tetangga, teman, komunitas).

Dengan Pinjem Aja, masyarakat bisa saling memanfaatkan barang yang sudah dimiliki alih-alih membeli barang baru yang hanya dipakai sesekali dan mendorong pola konsumsi yang lebih berkelanjutan sekaligus mempererat kebiasaan berbagi di tingkat komunitas (kampus, lingkungan tempat tinggal, organisasi).

---

## Jenis/Peran Pengguna

- **Primary User** - Mahasiswa dan individu yang sedang membutuhkan suatu barang secepatnya, baik untuk meminjam maupun meminjamkan barangnya sendiri.
- **Secondary User** - Komunitas, organisasi, atau lingkungan tempat tinggal yang memiliki barang untuk digunakan bersama (misal komunitas kampus dengan tenda, kompor portable, speaker, cooler, dsb).

---

## Public API / Mock API

**OpenStreetMap / Overpass API** - digunakan untuk fitur lokasi (menampilkan lokasi barang/pemilik melalui peta, pencarian berdasarkan jarak).
Dokumentasi: [https://wiki.openstreetmap.org/wiki/Overpass_API](https://wiki.openstreetmap.org/wiki/Overpass_API)

---

## Daftar Modul & Pembagian Kerja

Modul dibuat sesederhana mungkin di tahap awal, fokus pada alur pinjam dan barter. Pengembangan lanjutan (gamifikasi, challenge, dsb) menyusul setelah alur inti selesai.

| No | Modul | Deskripsi | Anggota |
|----|-------|-----------|---------|
| 1 | **Modul Barang (Item Listing)** | CRUD listing barang: upload barang, kategori, foto, deskripsi, harga, dan status ketersediaan. | Della Permata Prasilda |
| 2 | **Modul Transaksi Pinjam & Barter** | Pengajuan peminjaman/barter, approve/reject oleh pemilik, jadwal ambil-kembali, status transaksi (dipinjam/ditukar/dikembalikan/telat). | Nafeeza Arwatabina |
| 3 | **Modul Pencarian, Filter & Lokasi** | Pencarian barang berdasarkan kategori, lokasi, jarak, dan ketersediaan; integrasi dengan Overpass API untuk menampilkan lokasi di peta. | Joceline Nadine Immanuella |
| 4 | **Modul Profil** | Profil pengguna dan riwayat transaksi setelah transaksi selesai. | Khanyfatul Muflikhat |
| 5 | **Chat** | Fitur komunikasi teks secara langsung (real-time) antar-pengguna di dalam platform. | Fatma Widya Rachma |

---

## Checkpoint Progress

### ✅ Checkpoint 2 — Design System & Deployment Pertama
- Template dasar dan design system (palet warna, komponen UI bersama) sudah disepakati dan mulai diimplementasikan.
- Situs web kelompok sudah berhasil di-deploy ke PWS untuk pertama kali (belum lengkap semua modul).
- Link deployment: [https://khanyfatul-muflikhat-pinjemaja.pws.cs.ui.ac.id/](https://khanyfatul-muflikhat-pinjemaja.pws.cs.ui.ac.id/)
- Link desain Figma: [Wireframe PinjemAja](https://www.figma.com/design/6dKz48JAYCguCmL9fVptaa/Wireframe-PinjemAja?node-id=0-1&p=f&t=ZN2o0JN1opeWuIMw-0)