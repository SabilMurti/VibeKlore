# VibeKlore - Automated AI Developer Autopilot

VibeKlore adalah sistem pengembang autopilot berbasis AI yang berjalan secara otomatis setiap hari untuk merencanakan, memprogram, menguji, dan menyelaraskan proyek secara mandiri di WSL/Linux.

Sistem ini didesain tangguh untuk terus bekerja secara berkelanjutan melalui integrasi native **Antigravity CLI (`agy`)** dan mekanisme fallback pintar menggunakan **Aider + CometAPI** apabila kuota harian Antigravity habis.

---

## 🛠️ Fitur Utama

- **AI Planner Dinamis**: Secara otomatis membaca riwayat percakapan IDE, riwayat commit git, perintah shell, serta mendeteksi stack teknologi (WSL Toolchain) pengembang untuk menyusun rencana PRD, MVP, dan instruksi pengkodean yang presisi.
- **Web Dashboard Premium**: Antarmuka berbasis web dengan desain *glassmorphism* modern dan gelap, lengkap dengan monitor log aktivitas *live* yang terwarnai secara otomatis (*colorized*).
- **Konfigurasi Dynamic API & Provider**: Atur API Key dan API Base URL secara langsung dari Web Dashboard. Input API Key terlindungi secara visual dengan opsi tombol Tampilkan/Sembunyikan (Show/Hide).
- **Sinkronisasi Cron Otomatis**: Menyimpan setelan waktu cron harian dari dashboard secara otomatis memperbarui file konfigurasi dan menjadwalkan ulang cron job di sistem operasi.
- **Quota-Aware State Machine**:
  - Menggunakan **Antigravity CLI** jika kuota aktif.
  - Secara otomatis beralih ke **Aider (`gpt-4o-mini` via CometAPI)** sebagai fallback saat kuota limit.
- **Sync & Resume Otomatis**: Saat kuota Antigravity pulih di pagi hari berikutnya, sistem akan mengumpulkan commit fallback lokal, merancang *gap report*, dan menyerahkannya kembali ke Antigravity CLI untuk diselesaikan secara native.
- **Real-Time Output Streaming**: Semua eksekusi subproses (agy/aider) di-stream secara langsung ke stdout untuk mencegah proses hang dan memudahkan monitoring.
- **Klore CLI**: Command-line interface yang intuitif untuk mengendalikan autopilot.

---

## 🚀 Panduan Instalasi

Jalankan skrip instalasi untuk meregistrasikan perintah global `Klore` dan cron job harian:

```bash
./setup_autopilot.sh
```

Pastikan folder `/home/murtix/.local/bin` telah terdaftar di berkas `~/.zshrc` atau `~/.bashrc` Anda:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

---

## 💻 Penggunaan Klore CLI

Gunakan perintah `Klore` dari folder mana saja:

- **Membuka Web Dashboard**:
  ```bash
  Klore dashboard
  ```
  atau jalankan server dashboard secara langsung melalui NPM:
  ```bash
  npm start
  ```
  Lalu buka [http://localhost:3300](http://localhost:3300) di browser Anda.

- **Merencanakan Ide Proyek**:
  ```bash
  Klore plan "buat website to do list sederhana dengan localStorage"
  ```
- **Mengubah Mode Autopilot**:
  ```bash
  Klore mode <new | maintenance>
  ```
- **Mengatur Waktu Cron Job Secara Dinamis**:
  ```bash
  Klore cron <HH:MM>  # Contoh: Klore cron 07:05
  ```
- **Memeriksa Status Autopilot**:
  ```bash
  Klore state
  ```
- **Menambahkan Whitelist Proyek (Mode Maintenance)**:
  ```bash
  Klore whitelist add <path_absolute_proyek>
  ```
- **Menjalankan Autopilot Manual Sekarang**:
  ```bash
  Klore run
  ```

---

## 🧪 Pengujian Integrasi

Proyek ini dilengkapi dengan suite pengujian integrasi otomatis untuk memverifikasi keakuratan pemuatan konfigurasi, validasi data masukan di sisi server (*server-side validation*), serta integritas API endpoint.

Jalankan pengujian menggunakan:
```bash
npm test
```

---

## 📂 Struktur Berkas

- [bin/klore.js](file:///home/murtix/Projects/VibeKlore/bin/klore.js): Berkas logika utama untuk CLI tool `Klore`.
- [dashboard/app.js](file:///home/murtix/Projects/VibeKlore/dashboard/app.js): Server Express yang melayani API konfigurasi, status, log, dan sinkronisasi crontab.
- [dashboard/public/index.html](file:///home/murtix/Projects/VibeKlore/dashboard/public/index.html): Antarmuka Web Dashboard dengan gaya desain Glassmorphism premium.
- [harvester.py](file:///home/murtix/Projects/VibeKlore/harvester.py): Mengumpulkan data aktivitas pengembang, logs percakapan, git commit terbaru, riwayat shell, dan WSL Toolchain.
- [sleeping_developer.py](file:///home/murtix/Projects/VibeKlore/sleeping_developer.py): File orkestrator autopilot yang memanggil AI Planner, mengecek kuota, menjalankan agy/aider, dan me-resume perubahan fallback.
- [whitelist_config.json](file:///home/murtix/Projects/VibeKlore/whitelist_config.json): Konfigurasi model AI, whitelist, token, dan pengaturan waktu cron.
- [autopilot_state.json](file:///home/murtix/Projects/VibeKlore/autopilot_state.json): Berkas pencatatan state machine autopilot.
- [test.js](file:///home/murtix/Projects/VibeKlore/test.js): Berkas pengujian integrasi otomatis menggunakan test runner bawaan Node.js.
