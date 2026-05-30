#!/usr/bin/env bash

# VibeKlore Autopilot Setup Script
# Script ini akan mengonfigurasi CLI 'Klore' global dan mendaftarkan jadwal cron job.

VIBE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_BIN_DIR="/home/murtix/.local/bin"

echo "=== Memulai Setup VibeKlore Autopilot ==="

# 1. Pastikan folder bin lokal ada
if [ ! -d "$LOCAL_BIN_DIR" ]; then
    echo "[Setup] Membuat folder $LOCAL_BIN_DIR..."
    mkdir -p "$LOCAL_BIN_DIR"
fi

# 2. Buat symlink global untuk Klore CLI
echo "[Setup] Membuat symlink CLI 'Klore' ke $LOCAL_BIN_DIR/Klore..."
ln -sf "$VIBE_DIR/bin/klore.js" "$LOCAL_BIN_DIR/Klore"

# Pastikan file klore.js executable
chmod +x "$VIBE_DIR/bin/klore.js"

# 3. Periksa apakah local bin masuk PATH
if [[ ":$PATH:" == *":$LOCAL_BIN_DIR:"* ]]; then
    echo "[Setup] ✅ Folder $LOCAL_BIN_DIR sudah terdaftar di PATH Anda."
else
    echo "[Setup] ⚠️ Folder $LOCAL_BIN_DIR belum terdaftar di PATH Anda."
    echo "        Silakan tambahkan line ini ke file ~/.zshrc atau ~/.bashrc Anda:"
    echo "        export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# 4. Daftarkan Cron Job harian pukul 07:05 pagi
echo "[Setup] Mendaftarkan cron job harian pada pukul 07:05 pagi..."
CRON_JOB="5 7 * * * /usr/bin/python3 $VIBE_DIR/sleeping_developer.py >> $VIBE_DIR/autopilot.log 2>&1"

# Mengupdate crontab secara idempotent (aman dari duplikasi)
(crontab -l 2>/dev/null | grep -F -v "sleeping_developer.py" ; echo "$CRON_JOB") | crontab -

echo "[Setup] ✅ Cron job berhasil didaftarkan:"
crontab -l | grep "sleeping_developer.py"

echo "=== Setup VibeKlore Selesai! ==="
echo "Anda sekarang dapat menggunakan perintah 'Klore' dari folder mana saja."
echo "Silakan coba ketik: Klore help"
