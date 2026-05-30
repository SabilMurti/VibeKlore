#!/usr/bin/env python3
import os
import glob
import time
import json
import subprocess
import urllib.request
import urllib.error
import shutil

# Tambahkan path kustom untuk cron env
def setup_cron_path():
    user_home = os.path.expanduser("~")
    custom_paths = [
        os.path.join(user_home, ".local/bin"),
        os.path.join(user_home, ".config/composer/vendor/bin"),
        "/usr/local/bin",
        "/usr/bin",
        "/bin",
        "/usr/sbin",
        "/sbin"
    ]
    # Cari bin NVM secara dinamis
    node_nvm_dirs = glob.glob(os.path.join(user_home, ".nvm/versions/node/*/bin"))
    custom_paths.extend(node_nvm_dirs)
    
    current_path = os.environ.get("PATH", "")
    new_paths = []
    for p in custom_paths:
        if p not in current_path and os.path.exists(p):
            new_paths.append(p)
    if new_paths:
        os.environ["PATH"] = ":".join(new_paths) + ":" + current_path

setup_cron_path()

# Konfigurasi Path
PROJECTS_DIR = "/home/murtix/Projects"
VIBE_DIR = os.path.dirname(os.path.abspath(__file__))
BRAIN_DIR = os.path.expanduser("~/.gemini/antigravity-ide/brain")
MCP_CONFIG_PATH = os.path.expanduser("~/.gemini/config/mcp_config.json")
OUTPUT_FILE = os.path.join(VIBE_DIR, "latest_activity.md")
PRE_INSTRUCTION_FILE = os.path.join(VIBE_DIR, "pre_instruction.txt")


def get_latest_conversation_log():
    """Mencari folder brain terbaru (percakapan aktif) dan membaca transcript.jsonl"""
    print("[Harvester] Membaca log percakapan Antigravity...")
    try:
        if not os.path.exists(BRAIN_DIR):
            return "Folder brain Antigravity tidak ditemukan."
            
        folders = glob.glob(os.path.join(BRAIN_DIR, "*"))
        if not folders:
            return "Tidak ada folder percakapan yang ditemukan."
        
        # Urutkan berdasarkan waktu modifikasi folder terbaru
        folders.sort(key=os.path.getmtime, reverse=True)
        latest_folder = folders[0]
        
        transcript_path = os.path.join(latest_folder, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.exists(transcript_path):
            return f"Berkas transcript tidak ditemukan di: {transcript_path}"
            
        print(f"[Harvester] Membaca transcript dari: {transcript_path}")
        
        chat_turns = []
        with open(transcript_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    source = data.get("source")
                    step_type = data.get("type")
                    content = data.get("content", "")
                    
                    if not content:
                        continue
                        
                    # Deteksi input USER
                    if source == "USER_EXPLICIT" and step_type == "USER_INPUT":
                        chat_turns.append(f"**USER:** {content.strip()}")
                    # Deteksi respon AGENT/MODEL
                    elif source == "MODEL" and step_type == "PLANNER_RESPONSE":
                        chat_turns.append(f"**ANTIGRAVITY:** {content.strip()}")
                except Exception:
                    continue
        
        # Ambil maksimal 20 turn terakhir agar tidak terlalu panjang
        recent_chats = chat_turns[-20:]
        return "\n\n".join(recent_chats) if recent_chats else "Tidak ada percakapan aktif."
    except Exception as e:
        return f"Error membaca transcript: {str(e)}"

def get_git_logs(hours=14):
    """Mencari semua git repository di folder Projects dan mengambil log commit 14 jam terakhir"""
    print(f"[Harvester] Memindai commit git 14 jam terakhir di {PROJECTS_DIR}...")
    since_time = int(time.time()) - (hours * 3600)
    git_summaries = []
    
    try:
        if not os.path.exists(PROJECTS_DIR):
            return "Folder Projects tidak ditemukan."
            
        # Scan subdirectories
        for item in os.listdir(PROJECTS_DIR):
            item_path = os.path.join(PROJECTS_DIR, item)
            if os.path.isdir(item_path):
                git_dir = os.path.join(item_path, ".git")
                if os.path.exists(git_dir):
                    cmd = f"git log --since={since_time} --oneline --pretty=format:'%s (%h)'"
                    try:
                        output = subprocess.check_output(cmd, shell=True, cwd=item_path, stderr=subprocess.DEVNULL).decode('utf-8').strip()
                        if output:
                            git_summaries.append(f"### Proyek [{item}]:\n" + "\n".join([f"- {line}" for line in output.split('\n')]))
                    except Exception:
                        continue
    except Exception as e:
        return f"Error memindai Git log: {str(e)}"
        
    return "\n\n".join(git_summaries) if git_summaries else "Tidak ada commit git baru dalam 14 jam terakhir."

def get_shell_history():
    """Membaca riwayat command shell terakhir"""
    print("[Harvester] Membaca riwayat shell history...")
    history_files = [
        os.path.expanduser("~/.bash_history"),
        os.path.expanduser("~/.zsh_history")
    ]
    commands = []
    for h_file in history_files:
        if os.path.exists(h_file):
            try:
                with open(h_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    # Ambil 30 baris terakhir yang bukan kosong
                    commands.extend([l.strip() for l in lines[-40:] if l.strip()])
            except Exception:
                continue
    
    # Filter dan ambil 30 command terakhir secara global
    filtered_cmds = []
    for cmd in commands[-30:]:
        # Zsh history kadang menyimpan timestamp format ': 1700000000:0;cmd'
        if cmd.startswith(":"):
            parts = cmd.split(";", 1)
            if len(parts) > 1:
                cmd = parts[1]
        filtered_cmds.append(cmd)
        
    return "\n".join([f"- `{cmd}`" for cmd in filtered_cmds]) if filtered_cmds else "Riwayat shell tidak tersedia."

def fetch_github_repos():
    """Mengambil daftar repositori SabilMurti dari GitHub API menggunakan token jika tersedia"""
    print("[Harvester] Menghubungi GitHub API untuk memindai profil SabilMurti...")
    
    token = None
    if os.path.exists(MCP_CONFIG_PATH):
        try:
            with open(MCP_CONFIG_PATH, 'r') as f:
                config = json.load(f)
                token = config.get("mcpServers", {}).get("github-mcp-server", {}).get("env", {}).get("GITHUB_PERSONAL_ACCESS_TOKEN")
        except Exception as e:
            print(f"[Harvester] Gagal membaca token dari mcp_config.json: {e}")
            
    url = "https://api.github.com/users/SabilMurti/repos?per_page=100&sort=updated"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "VibeKlore-Autopilot")
    
    if token:
        print("[Harvester] Menggunakan GitHub Personal Access Token untuk otentikasi.")
        req.add_header("Authorization", f"token {token}")
        
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            repos_data = json.loads(response.read().decode('utf-8'))
            summary_list = []
            for r in repos_data:
                name = r.get("name", "")
                desc = r.get("description", "") or "Tidak ada deskripsi"
                lang = r.get("language", "") or "N/A"
                summary_list.append(f"- **{name}** ({lang}): {desc}")
            return "\n".join(summary_list) if summary_list else "Tidak ada repositori ditemukan."
    except urllib.error.URLError as e:
        print(f"[Harvester] Gagal mengakses GitHub API: {e}")
        return f"Gagal mengambil data dari GitHub: {str(e)} (Kemungkinan offline atau batas limit API tercapai)"
    except Exception as e:
        print(f"[Harvester] Terjadi kesalahan saat membaca data GitHub: {e}")
        return "Tidak dapat memuat repositori GitHub."

def read_pre_instruction():
    """Membaca berkas pre-instruction jika ada"""
    if os.path.exists(PRE_INSTRUCTION_FILE):
        try:
            with open(PRE_INSTRUCTION_FILE, 'r', encoding='utf-8') as f:
                instruction = f.read().strip()
                if instruction:
                    print(f"[Harvester] Ditemukan pre-instruction: '{instruction}'")
                    return instruction
        except Exception as e:
            print(f"[Harvester] Gagal membaca pre_instruction.txt: {e}")
    return None

def get_wsl_toolchain():
    """Memeriksa stack teknologi (toolchain) yang terpasang di WSL"""
    print("[Harvester] Memeriksa stack teknologi (toolchain) di WSL...")
    tools = {
        "Node.js": ["node", "--version"],
        "NPM": ["npm", "--version"],
        "PHP": ["php", "-v"],
        "Composer": ["composer", "--version"],
        "Git": ["git", "--version"],
        "MySQL": ["mysql", "--version"],
        "MongoDB": ["mongod", "--version"],
        "Docker": ["docker", "--version"],
    }
    
    results = []
    for name, cmd_args in tools.items():
        executable = cmd_args[0]
        exec_path = shutil.which(executable)
        if exec_path:
            try:
                res = subprocess.run(cmd_args, capture_output=True, text=True, timeout=5)
                version_str = (res.stdout or res.stderr).strip()
                # Ambil baris pertama saja agar ringkas
                first_line = version_str.split("\n")[0] if version_str else "Terpasang (versi tidak diketahui)"
                results.append(f"- **{name}**: {first_line} (`{exec_path}`)")
            except Exception as e:
                results.append(f"- **{name}**: Terpasang di `{exec_path}` tetapi gagal mendapatkan versi ({str(e)})")
        else:
            results.append(f"- **{name}**: Tidak terpasang / Tidak ditemukan di PATH")
            
    return "\n".join(results)

def main():
    print("[Harvester] Memulai pengumpulan data aktivitas...")
    
    pre_inst = read_pre_instruction()
    chats = get_latest_conversation_log()
    git_logs = get_git_logs()
    shell_hist = get_shell_history()
    github_repos = fetch_github_repos()
    toolchain = get_wsl_toolchain()
    
    markdown_content = f"""# VibeKlore - Laporan Aktivitas Developer

Laporan ini dibuat otomatis pada {time.strftime('%Y-%m-%d %H:%M:%S')} untuk memberikan konteks lengkap bagi AI Planner.

{"## ⚠️ PRE-INSTRUCTION UTAMA (HIGH PRIORITY)\n" + pre_inst + "\n\n" if pre_inst else ""}## 👤 Repositori GitHub Pengembang (SabilMurti)
{github_repos}

## 🛠️ Stack Teknologi (WSL Toolchain)
{toolchain}

## 💬 Transkrip Percakapan Terakhir (Antigravity IDE)
{chats}

## 📝 Commit Git (14 Jam Terakhir)
{git_logs}

## 💻 Riwayat Perintah Shell (Terakhir)
{shell_hist}
"""
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"[Harvester] Berhasil menulis laporan aktivitas ke: {OUTPUT_FILE}")
    except Exception as e:
        print(f"[Harvester] Gagal menulis berkas output: {e}")

if __name__ == "__main__":
    main()
