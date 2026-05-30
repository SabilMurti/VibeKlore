#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const VIBE_DIR = path.resolve(__dirname, '..');
const CONFIG_PATH = path.join(VIBE_DIR, 'whitelist_config.json');
const STATE_PATH = path.join(VIBE_DIR, 'autopilot_state.json');
const PRE_INSTRUCTION_PATH = path.join(VIBE_DIR, 'pre_instruction.txt');
const ORCHESTRATOR_PATH = path.join(VIBE_DIR, 'sleeping_developer.py');

function printHelp() {
  console.log(`
VibeKlore Autopilot CLI (Klore)
Usage:
  Klore <command> [args]

Commands:
  plan "<instruction>"     Tulis ide/instruksi proyek untuk autopilot malam ini
                           (Contoh: Klore plan "buat web kasir sederhana")
  mode <new|maintenance>   Ubah mode autopilot (membuat proyek baru / perbaikan proyek whitelist)
  cron <HH:MM>             Atur waktu eksekusi cron job harian autopilot (Contoh: Klore cron 07:05)
  state                    Tampilkan status autopilot saat ini
  whitelist add <path>     Tambahkan path proyek ke whitelist untuk mode maintenance
  run                      Jalankan autopilot secara manual sekarang juga
  help                     Tampilkan panduan ini
`);
}

const args = process.argv.slice(2);
if (args.length === 0 || args[0] === 'help') {
  printHelp();
  process.exit(0);
}

const command = args[0];

switch (command) {
  case 'plan':
    if (args.length < 2 || !args[1].trim()) {
      console.error('Error: Masukkan instruksi rencana Anda.');
      console.log('Contoh: Klore plan "buat web to-do list"');
      process.exit(1);
    }
    const instruction = args[1].trim();
    try {
      fs.writeFileSync(PRE_INSTRUCTION_PATH, instruction, 'utf-8');
      console.log(`✅ Pre-instruction berhasil dicatat: "${instruction}"`);
      console.log('AI Planner akan menggunakan rencana ini saat autopilot berjalan nanti pagi.');
    } catch (e) {
      console.error(`Gagal menulis file rencana: ${e.message}`);
      process.exit(1);
    }
    break;

  case 'mode':
    if (args.length < 2 || (args[1] !== 'new' && args[1] !== 'maintenance')) {
      console.error('Error: Pilih mode "new" atau "maintenance".');
      console.log('Contoh: Klore mode maintenance');
      process.exit(1);
    }
    const mode = args[1];
    try {
      const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
      config.mode = mode;
      fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2), 'utf-8');
      console.log(`✅ Mode autopilot berhasil diubah ke: "${mode}"`);
    } catch (e) {
      console.error(`Gagal mengubah konfigurasi: ${e.message}`);
      process.exit(1);
    }
    break;

  case 'state':
    try {
      if (!fs.existsSync(STATE_PATH)) {
        console.log('Status: IDLE (Tidak ada pengerjaan autopilot aktif)');
        break;
      }
      const state = JSON.parse(fs.readFileSync(STATE_PATH, 'utf-8'));
      console.log('=== STATUS VIBEKLORE AUTOPILOT ===');
      console.log(`State       : ${state.state}`);
      console.log(`Proyek Aktif: ${state.current_project_path || 'N/A'}`);
      console.log(`Tugas       : ${state.active_task || 'N/A'}`);
      console.log(`Jalan Terakhir: ${state.last_run || 'Belum pernah berjalan'}`);
    } catch (e) {
      console.error(`Gagal membaca status: ${e.message}`);
      process.exit(1);
    }
    break;

  case 'whitelist':
    if (args[1] !== 'add' || args.length < 3) {
      console.log('Usage: Klore whitelist add <absolute_path>');
      process.exit(1);
    }
    const targetPath = path.resolve(args[2]);
    try {
      const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
      if (!config.allow_maintenance.includes(targetPath)) {
        config.allow_maintenance.push(targetPath);
        fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2), 'utf-8');
        console.log(`✅ Path berhasil ditambahkan ke whitelist: ${targetPath}`);
      } else {
        console.log(`Path sudah ada di whitelist: ${targetPath}`);
      }
    } catch (e) {
      console.error(`Gagal memperbarui whitelist: ${e.message}`);
      process.exit(1);
    }
    break;

  case 'cron':
    if (args.length < 2 || !args[1].match(/^\d{1,2}:\d{2}$/)) {
      console.error('Error: Masukkan format waktu yang valid (HH:MM).');
      console.log('Contoh: Klore cron 07:05');
      process.exit(1);
    }
    const timeStr = args[1];
    const [hourStr, minStr] = timeStr.split(':');
    const hour = parseInt(hourStr, 10);
    const min = parseInt(minStr, 10);
    if (hour < 0 || hour > 23 || min < 0 || min > 59) {
      console.error('Error: Waktu tidak valid.');
      process.exit(1);
    }
    try {
      const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
      config.cron_time = timeStr;
      fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2), 'utf-8');
      
      const cronSchedule = `${min} ${hour} * * *`;
      const pythonPath = '/usr/bin/python3';
      const scriptPath = path.join(VIBE_DIR, 'sleeping_developer.py');
      const logPath = path.join(VIBE_DIR, 'autopilot.log');
      const cronCommand = `${cronSchedule} ${pythonPath} ${scriptPath} >> ${logPath} 2>&1`;
      
      const { exec } = require('child_process');
      exec(`(crontab -l 2>/dev/null | grep -F -v "sleeping_developer.py" ; echo "${cronCommand}") | crontab -`, (err, stdout, stderr) => {
        if (err) {
          console.error(`Gagal memperbarui crontab: ${stderr}`);
          process.exit(1);
        }
        console.log(`✅ Jadwal cron job harian berhasil diatur ke pukul: ${timeStr} (${cronSchedule})`);
      });
    } catch (e) {
      console.error(`Gagal memperbarui konfigurasi cron: ${e.message}`);
      process.exit(1);
    }
    break;

  case 'run':
    console.log('🚀 Menjalankan VibeKlore Autopilot...');
    const child = spawn('python3', [ORCHESTRATOR_PATH], { stdio: 'inherit' });
    child.on('close', (code) => {
      console.log(`Autopilot selesai dengan exit code: ${code}`);
      process.exit(code);
    });
    break;

  default:
    console.error(`Error: Perintah "${command}" tidak dikenal.`);
    printHelp();
    process.exit(1);
}
