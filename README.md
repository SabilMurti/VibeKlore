# VibeKlore - Automated AI Developer Autopilot

VibeKlore adalah sistem pengembang autopilot berbasis AI yang berjalan secara otomatis setiap hari untuk merencanakan, memprogram, menguji, dan menyelaraskan proyek secara mandiri di WSL/Linux.

Sistem ini didesain tangguh untuk terus bekerja secara berkelanjutan melalui integrasi native **Antigravity CLI (`agy`)** dan mekanisme fallback pintar menggunakan **Aider + CometAPI** apabila kuota harian Antigravity habis.

---

## 🛠️ Fitur Utama

- **AI Planner Dinamis**: Secara otomatis membaca riwayat percakapan IDE, riwayat commit git, perintah shell, serta mendeteksi stack teknologi (WSL Toolchain) pengembang untuk menyusun rencana PRD, MVP, dan instruksi pengkodean yang presisi.
- **Quota-Aware State Machine**:
  - Menggunakan **Antigravity CLI** jika kuota aktif.
  - Secara otomatis beralih ke **Aider (`gpt-4o-mini` via CometAPI)** sebagai fallback saat kuota limit.
- **Sync & Resume Otomatis**: Saat kuota Antigravity pulih di pagi hari berikutnya, sistem akan mengumpulkan commit fallback lokal, merancang *gap report*, dan menyerahkannya kembali ke Antigravity CLI untuk diselesaikan secara native.
- **Real-Time Output Streaming**: Semua eksekusi subproses (agy/aider) di-stream secara langsung ke stdout untuk mencegah proses hang dan memudahkan monitoring.
- **Klore CLI**: Command-line interface yang intuitif untuk mengendalikan autopilot.
- **Jadwal Cron Dinamis**: Mengatur waktu pemicu autopilot harian langsung dari CLI.

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

## 📂 Struktur Berkas

- [bin/klore.js](file:///home/murtix/Projects/VibeKlore/bin/klore.js): Berkas logika utama untuk CLI tool `Klore`.
- [harvester.py](file:///home/murtix/Projects/VibeKlore/harvester.py): Mengumpulkan data aktivitas pengembang, logs percakapan, git commit terbaru, riwayat shell, dan WSL Toolchain.
- [sleeping_developer.py](file:///home/murtix/Projects/VibeKlore/sleeping_developer.py): File orkestrator autopilot yang memanggil AI Planner, mengecek kuota, menjalankan agy/aider, dan me-resume perubahan fallback.
- [whitelist_config.json](file:///home/murtix/Projects/VibeKlore/whitelist_config.json): Konfigurasi model AI, whitelist, token, dan pengaturan waktu cron.
- [autopilot_state.json](file:///home/murtix/Projects/VibeKlore/autopilot_state.json): Berkas pencatatan state machine autopilot.
