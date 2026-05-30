#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import time
import glob
from openai import OpenAI
import dotenv

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

# Load .env
VIBE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv.load_dotenv(os.path.join(VIBE_DIR, ".env"))


# Path Konfigurasi
CONFIG_PATH = os.path.join(VIBE_DIR, "whitelist_config.json")
STATE_PATH = os.path.join(VIBE_DIR, "autopilot_state.json")
ACTIVITY_PATH = os.path.join(VIBE_DIR, "latest_activity.md")
PLAN_PATH = os.path.join(VIBE_DIR, "latest_plan.md")
PRE_INSTRUCTION_PATH = os.path.join(VIBE_DIR, "pre_instruction.txt")
REPORT_PATH = os.path.join(VIBE_DIR, "morning_report.md")
MCP_CONFIG_PATH = os.path.expanduser("~/.gemini/config/mcp_config.json")

def load_config():
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[Orchestrator] Gagal membaca config: {e}")
        return {
            "allow_maintenance": [VIBE_DIR],
            "prevent_deletion": True,
            "git_auto_commit": True,
            "max_iterations_per_run": 20,
            "project_generation_path": "/home/murtix/Projects",
            "comet_api_base": "https://api.cometapi.com/v1",
            "comet_api_key": "sk-Qj16IMAHsC5yWkjja2yCoFWA3ESRGI3YOdhILopqGjZOKfl2",
            "planner_model": "gpt-4o-mini",
            "fallback_model": "gpt-4o-mini",
            "mode": "new",
            "discord_webhook_url": "",
            "github_username": "SabilMurti"
        }

def load_state():
    try:
        if os.path.exists(STATE_PATH):
            with open(STATE_PATH, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"[Orchestrator] Gagal membaca state: {e}")
    return {
        "state": "IDLE",
        "current_project_path": "",
        "active_task": "",
        "last_run": ""
    }

def save_state(state):
    try:
        with open(STATE_PATH, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"[Orchestrator] Gagal menulis state: {e}")

def get_github_token():
    """Mengambil GITHUB_PERSONAL_ACCESS_TOKEN dari mcp_config.json"""
    if os.path.exists(MCP_CONFIG_PATH):
        try:
            with open(MCP_CONFIG_PATH, 'r') as f:
                config = json.load(f)
                return config.get("mcpServers", {}).get("github-mcp-server", {}).get("env", {}).get("GITHUB_PERSONAL_ACCESS_TOKEN")
        except Exception as e:
            print(f"[Orchestrator] Gagal membaca token dari mcp_config.json: {e}")
    return None

def send_discord_notification(webhook_url, message):
    if not webhook_url:
        return
    import urllib.request
    payload = {
        "content": message
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            pass
        print("[Orchestrator] Notifikasi Discord terkirim.")
    except Exception as e:
        print(f"[Orchestrator] Gagal mengirim notifikasi Discord: {e}")

def check_agy_quota():
    """Memeriksa apakah Antigravity CLI ('agy') memiliki kuota aktif"""
    print("[Orchestrator] Memeriksa kuota Antigravity CLI...")
    try:
        # Jalankan perintah cepat untuk tes respon
        result = subprocess.run(
            ["agy", "--dangerously-skip-permissions", "--print", "Hello, are you ready? Just answer with 'ready'"],
            capture_output=True,
            text=True,
            timeout=45
        )
        output = result.stdout.lower() + result.stderr.lower()
        if result.returncode != 0 or "quota exceeded" in output or "rate limit" in output or "resource exhausted" in output:
            print("[Orchestrator] ⚠️ Kuota Antigravity CLI limit atau terhambat.")
            return False
        print("[Orchestrator] ✅ Kuota Antigravity CLI aktif!")
        return True
    except subprocess.TimeoutExpired:
        print("[Orchestrator] ⚠️ Timeout saat menghubungi Antigravity CLI. Menganggap limit.")
        return False
    except Exception as e:
        print(f"[Orchestrator] ⚠️ Gagal menjalankan check agy: {e}")
        return False

def run_harvester():
    print("[Orchestrator] Menjalankan harvester.py...")
    try:
        subprocess.run(["python3", os.path.join(VIBE_DIR, "harvester.py")], check=True)
        print("[Orchestrator] Harvester selesai.")
    except Exception as e:
        print(f"[Orchestrator] Gagal menjalankan harvester: {e}")

def run_ai_planner(config):
    """Menjalankan AI Planner menggunakan CometAPI untuk merancang latest_plan.md"""
    print("[Orchestrator] Menjalankan AI Planner untuk menyusun spesifikasi proyek...")
    
    api_key = os.getenv("COMET_API_KEY") or config.get("comet_api_key")
    api_base = os.getenv("COMET_API_BASE") or config.get("comet_api_base")
    model = config.get("planner_model", "gpt-4o-mini")
    mode = config.get("mode", "new")
    github_user = config.get("github_username", "SabilMurti")
    
    if not api_key:
        print("[Orchestrator] Error: COMET_API_KEY tidak ditemukan di environment/config. Keluar.")
        return False
        
    if not os.path.exists(ACTIVITY_PATH):
        print(f"[Orchestrator] Error: latest_activity.md tidak ditemukan. Jalankan harvester dulu.")
        return False
        
    with open(ACTIVITY_PATH, 'r', encoding='utf-8') as f:
        activity_content = f.read()
        
    client = OpenAI(api_key=api_key, base_url=api_base)
    
    system_prompt = f"""You are VibeKlore's AI Planner, a world-class Product Owner and Software Architect.
Your task is to analyze the developer's raw activity logs (transcripts, git commits, shell history, pre-instructions, and their existing GitHub profile) and compile a detailed implementation plan in Markdown format.

Determine the optimal project/enhancement using this logic:
1. If there is a PRE-INSTRUCTION UTAMA (HIGH PRIORITY), you MUST strictly build/enhance what is requested there.
2. Otherwise, check the configuration mode: '{mode}'.
   - If '{mode}' is 'maintenance', recommend an enhancement/bug fix for one of the whitelisted projects.
   - If '{mode}' is 'new', brainstorm a brand new project. Analyze the developer's GitHub repos (for user {github_user}) to see what they are missing (e.g. web portfolio, SaaS utility, etc.) and suggest a highly relevant premium project.

IMPORTANT STACK GUIDELINES:
- The developer's machine does NOT have MongoDB or Docker installed. Do NOT suggest or use them.
- The developer has Node.js (v24), NPM (v11), PHP (v8.5), and MySQL installed.
- Unless explicitly requested, keep the application as a premium frontend-only Single Page Application (HTML, CSS, JS) with glassmorphism styles and micro-interactions, utilizing `localStorage` for state persistence (avoiding complex backend/database structures and heavy authentication).
- "VibeKlore" is the name of this orchestrator tool. The generated projects must be named specific to their function (e.g. "simple-todo-list", "web-cashier") and placed in '/home/murtix/Projects/[project-name]'. Do not use "vibeklore" as the generated project's name.

Your output must be structured precisely in JSON format containing two keys:
1. "plan_markdown": The complete Markdown configuration and spec that will be saved to `latest_plan.md`.
2. "metadata": A JSON object containing:
   - "type": "new" or "enhance"
   - "project_name": The recommended folder-safe project name specific to the task (e.g. "todo-list", "web-cashier")
   - "target_path": The absolute target project path (e.g. "/home/murtix/Projects/todo-list")
   - "task_description": A short 1-line summary of the feature/project.

Within "plan_markdown", compile a premium, state-of-the-art software specification including:
- Project Name & Description
- Product Requirements Document (PRD)
- Core Features Checklist (MVP scope)
- Coding Instructions: specific prompt instructions for the coding agent (describing visual guidelines, styling, tech stack, and safety).

Respond ONLY with the raw JSON object. Do not wrap it in markdown code fences.
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": activity_content}
            ],
            temperature=0.2
        )
        
        raw_res = response.choices[0].message.content.strip()
        # Bersihkan pembungkus json markdown jika ada
        if raw_res.startswith("```json"):
            raw_res = raw_res.split("```json", 1)[1]
        if raw_res.endswith("```"):
            raw_res = raw_res.rsplit("```", 1)[0]
        raw_res = raw_res.strip()
        
        parsed = json.loads(raw_res)
        plan_markdown = parsed.get("plan_markdown", "")
        metadata = parsed.get("metadata", {})
        
        # Simpan latest_plan.md
        with open(PLAN_PATH, 'w', encoding='utf-8') as f:
            f.write(plan_markdown)
            
        print(f"[Orchestrator] AI Planner berhasil merumuskan rencana untuk: {metadata.get('project_name')}")
        return metadata
    except Exception as e:
        print(f"[Orchestrator] Gagal menjalankan AI Planner: {e}")
        return False

def execute_antigravity(project_path, task_desc):
    """Menjalankan Antigravity CLI ('agy') untuk menulis kode"""
    print(f"[Orchestrator] Menjalankan Antigravity CLI di: {project_path}...")
    
    # Prompt instruksi untuk agy
    instruction = (
        f"Tolong buat/tingkatkan kode di workspace {project_path} berdasarkan spesifikasi lengkap di file {PLAN_PATH}. "
        f"Ikuti seluruh teknologi stack, arsitektur, dan struktur file yang direncanakan di berkas tersebut. "
        f"Jika proyek memiliki antarmuka (frontend), pastikan didesain secara premium (misalnya dengan skema warna yang harmonis, "
        f"layout responsif, efek hover/transisi yang mulus, dan micro-interactions). Tulis README.md yang representatif. "
        f"Pastikan jalankan pengujian dan selesaikan semuanya."
    )
                  
    cmd = [
        "agy",
        "--dangerously-skip-permissions",
        "--print",
        instruction
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            cwd=project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1
        )
        
        output_lines = []
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            output_lines.append(line)
            
        process.wait(timeout=600)
        output = "".join(output_lines)
        output_lower = output.lower()
        
        # Cek ketersediaan kuota/error
        if process.returncode != 0 or "quota exceeded" in output_lower or "rate limit" in output_lower or "resource exhausted" in output_lower:
            print("[Orchestrator] ⚠️ Antigravity CLI menemui limit kuota saat eksekusi.")
            return False, output
            
        print("[Orchestrator] ✅ Antigravity CLI sukses menulis kode!")
        return True, output
    except Exception as e:
        print(f"[Orchestrator] Gagal memanggil Antigravity CLI: {e}")
        return False, str(e)

def execute_aider_fallback(project_path, task_desc, config):
    """Menjalankan Aider fallback menggunakan CometAPI"""
    print(f"[Orchestrator] Menjalankan Aider Fallback dengan CometAPI di: {project_path}...")
    
    api_key = os.getenv("COMET_API_KEY") or config.get("comet_api_key")
    api_base = os.getenv("COMET_API_BASE") or config.get("comet_api_base")
    model = config.get("fallback_model", "gpt-4o-mini")
    github_token = get_github_token()
    
    # Siapkan Environment
    env = os.environ.copy()
    env["OPENAI_API_KEY"] = api_key
    env["OPENAI_API_BASE"] = api_base
    if github_token:
        env["GITHUB_TOKEN"] = github_token
        env["GITHUB_PERSONAL_ACCESS_TOKEN"] = github_token
        
    instruction = (
        f"Tolong buat/tingkatkan kode di workspace ini berdasarkan spesifikasi lengkap di file {PLAN_PATH}. "
        f"Ikuti seluruh teknologi stack, arsitektur, dan struktur file yang direncanakan di berkas tersebut. "
        f"Jika proyek memiliki antarmuka (frontend), pastikan didesain secara premium (misalnya dengan skema warna yang harmonis, "
        f"layout responsif, efek hover/transisi yang mulus, dan micro-interactions). Tulis README.md yang representatif."
    )
                  
    cmd = [
        "aider",
        "--model", f"openai/{model}",
        "--yes",
        "--message",
        instruction
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            cwd=project_path,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1
        )
        
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            
        process.wait(timeout=600)
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)
        
        # Lakukan git commit fallback
        if config.get("git_auto_commit", True):
            subprocess.run(["git", "init"], cwd=project_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "add", "."], cwd=project_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "commit", "-m", "[Fallback-CometAPI] Autopilot coding fallback update"], cwd=project_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        print("[Orchestrator] ✅ Aider Fallback sukses menulis kode!")
        return True
    except Exception as e:
        print(f"[Orchestrator] Gagal menjalankan Aider Fallback: {e}")
        return False

def run_resume_sync(project_path, config):
    """Menjalankan proses resume: mengumpulkan commit fallback dan menyuapkannya ke agy"""
    print(f"[Orchestrator] Mendeteksi perubahan fallback di {project_path} untuk di-resume ke Antigravity...")
    
    # Cari commit [Fallback-CometAPI] terakhir
    try:
        commits = subprocess.check_output(
            ["git", "log", "--grep=\\[Fallback-CometAPI\\]", "--oneline", "-n", "5"],
            cwd=project_path,
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        
        diff = subprocess.check_output(
            ["git", "diff", "HEAD~5..HEAD", "--stat"],
            cwd=project_path,
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
    except Exception:
        commits = "Tidak ada commit fallback terdeteksi."
        diff = "Tidak ada diff yang tersedia."
        
    gap_report = f"### COMMIT LOG FALLBACK:\n{commits}\n\n### STATS PERUBAHAN BERKAS:\n{diff}"
    
    print("[Orchestrator] Mengirim laporan gap ke Antigravity CLI untuk me-resume pengerjaan...")
    instruction = f"Resume pengerjaan di workspace {project_path}. Selama kuota Anda limit kemarin, " \
                  f"model fallback lokal (Ollama/CometAPI) telah melakukan modifikasi berikut:\n{gap_report}\n\n" \
                  f"Tolong review semua perubahan file tersebut, lakukan penyesuaian gaya premium, jalankan verifikasi pengujian, " \
                  f"dan pastikan seluruh fitur berjalan dengan sempurna sesuai specs di {PLAN_PATH}."
                  
    cmd = [
        "agy",
        "--dangerously-skip-permissions",
        "--print",
        instruction
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            cwd=project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1
        )
        
        output_lines = []
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            output_lines.append(line)
            
        process.wait(timeout=600)
        output = "".join(output_lines)
        output_lower = output.lower()
        
        if process.returncode != 0 or "quota exceeded" in output_lower or "rate limit" in output_lower or "resource exhausted" in output_lower:
            print("[Orchestrator] ⚠️ Gagal me-resume: Antigravity CLI masih limit.")
            return False
            
        print("[Orchestrator] ✅ Resume sukses! Antigravity telah memverifikasi perubahan fallback.")
        return True
    except Exception as e:
        print(f"[Orchestrator] Gagal me-resume ke Antigravity CLI: {e}")
        return False


def setup_git_branch(project_path, project_name):
    """Memastikan repositori git terinisialisasi dan membuat branch baru untuk autopilot"""
    print(f"[Orchestrator] Menyiapkan branch Git untuk {project_name}...")
    try:
        # Init git jika belum ada
        if not os.path.exists(os.path.join(project_path, ".git")):
            subprocess.run(["git", "init"], cwd=project_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Create initial commit if empty
            subprocess.run(["git", "checkout", "-b", "main"], cwd=project_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            with open(os.path.join(project_path, ".gitignore"), "w") as f:
                f.write("node_modules/\n.env\nmcp.db\n")
            subprocess.run(["git", "add", "."], cwd=project_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "commit", "-m", "Initial commit from autopilot"], cwd=project_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Dapatkan nama branch baru
        branch_name = f"feature/autopilot-{project_name}-{int(time.time())}"
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=project_path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[Orchestrator] ✅ Branch baru dibuat: {branch_name}")
        return branch_name
    except Exception as e:
        print(f"[Orchestrator] Gagal menyiapkan branch Git: {e}")
        return "main"

def run_project_tests(project_path, config):
    """Mencari test suite dan menjalankannya. Mengembalikan (success, error_output)"""
    print("[Orchestrator] Menjalankan test suite verifikasi...")
    
    # Pilih test command secara cerdas
    test_command = config.get("test_command")
    if not test_command:
        if os.path.exists(os.path.join(project_path, "run-tests.js")):
            test_command = "node run-tests.js"
        elif os.path.exists(os.path.join(project_path, "package.json")):
            # Cek apakah package.json memiliki test script
            try:
                with open(os.path.join(project_path, "package.json"), "r") as f:
                    pkg = json.load(f)
                    if "test" in pkg.get("scripts", {}):
                        test_command = "npm test"
            except:
                pass
        elif os.path.exists(os.path.join(project_path, "phpunit.xml")):
            test_command = "vendor/bin/phpunit"
               
    if not test_command:
        print("[Orchestrator] Tidak ada test suite terdeteksi. Melewati verifikasi.")
        return True, ""
           
    print(f"[Orchestrator] Menjalankan perintah tes: `{test_command}`")
    try:
        res = subprocess.run(
            test_command,
            shell=True,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        stdout_stderr = (res.stdout or "") + "\n" + (res.stderr or "")
        if res.returncode == 0:
            print("[Orchestrator] ✅ Seluruh pengujian lolos!")
            return True, stdout_stderr
        else:
            print(f"[Orchestrator] ❌ Pengujian gagal dengan exit code {res.returncode}.")
            return False, stdout_stderr
    except Exception as e:
        print(f"[Orchestrator] ⚠️ Error saat menjalankan tes: {e}")
        return False, str(e)

def get_github_repo_info(project_path):
    """Mendapatkan owner dan repo dari git remote origin"""
    try:
        remotes = subprocess.check_output(["git", "remote", "-v"], cwd=project_path).decode('utf-8')
        for line in remotes.split("\n"):
            if "origin" in line and "(push)" in line:
                parts = line.split()
                if len(parts) >= 2:
                    url = parts[1]
                    if "github.com" in url:
                        url = url.replace("git@github.com:", "").replace("https://github.com/", "")
                        url = url.replace(".git", "")
                        owner_repo = url.split("/")
                        if len(owner_repo) == 2:
                            return owner_repo[0], owner_repo[1]
    except Exception as e:
        print(f"[Orchestrator] Gagal mendapatkan remote GitHub: {e}")
    return None

def create_github_pr(project_path, branch_name, project_name, config):
    """Membuat Pull Request di GitHub menggunakan GitHub API"""
    print(f"[Orchestrator] Mencoba membuat Pull Request untuk branch {branch_name}...")
    
    repo_info = get_github_repo_info(project_path)
    if not repo_info:
        print("[Orchestrator] Tidak dapat mendeteksi remote repo GitHub. Melewati pembuatan PR.")
        return False
        
    owner, repo = repo_info
    github_token = get_github_token() or (os.getenv("GITHUB_TOKEN") or config.get("github_token"))
    if not github_token:
        print("[Orchestrator] GITHUB_TOKEN tidak ditemukan. Melewati pembuatan PR.")
        return False
        
    # Deskripsi PR
    description = "Autopilot code generated by VibeKlore.\n\n"
    if os.path.exists(PLAN_PATH):
        try:
            with open(PLAN_PATH, "r") as f:
                description += f.read()[:2000]
        except:
            pass
            
    payload = {
        "title": f"Autopilot: scaffold/enhance {project_name}",
        "head": branch_name,
        "base": "main",
        "body": description
    }
    
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "VibeKlore-Autopilot"
    }
    
    try:
        import urllib.request
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            pr_url = res_data.get("html_url")
            print(f"[Orchestrator] ✅ Pull Request berhasil dibuat: {pr_url}")
            return pr_url
    except Exception as e:
        print(f"[Orchestrator] Gagal membuat Pull Request di GitHub: {e}")
        return False

def execute_with_self_healing(project_path, task_desc, config, agy_active, used_fallback):
    """Menjalankan coding agent (Antigravity atau Aider) dengan loop perbaikan jika tes gagal"""
    max_healing_tries = 3
    current_try = 1
    current_task_desc = task_desc
    active_fallback = used_fallback
    
    while current_try <= max_healing_tries:
        if current_try > 1:
            print(f"\n[Orchestrator] 🔄 Memulai Iterasi Self-Healing #{current_try - 1}...")
            
        success = False
        log_or_err = ""
        
        if agy_active and not active_fallback:
            success, log_or_err = execute_antigravity(project_path, current_task_desc)
            if not success:
                print("[Orchestrator] Gagal mengeksekusi dengan Antigravity. Mencoba Aider...")
                active_fallback = True
                success = execute_aider_fallback(project_path, current_task_desc, config)
        else:
            success = execute_aider_fallback(project_path, current_task_desc, config)
            
        if not success:
            print(f"[Orchestrator] Agent gagal menulis kode pada percobaan #{current_try}.")
            return False, active_fallback
            
        # Jalankan test suite
        test_passed, test_output = run_project_tests(project_path, config)
        if test_passed:
            print("[Orchestrator] ✅ Proyek berhasil diselesaikan dan terverifikasi!")
            return True, active_fallback
            
        # Jika gagal, siapkan feedback error untuk iterasi berikutnya
        current_try += 1
        if current_try <= max_healing_tries:
            current_task_desc = (
                f"Hasil pengujian sebelumnya GAGAL. Tolong perbaiki kode Anda agar seluruh tes lolos.\n\n"
                f"### PERINTAH TES:\n{config.get('test_command') or 'Otomatis'}\n\n"
                f"### ERROR OUTPUT:\n{test_output}\n\n"
                f"Tinjau kode yang rusak dan lakukan perbaikan. Jangan merusak fungsionalitas lain yang sudah benar."
            )
        else:
            print(f"[Orchestrator] ❌ Batas iterasi self-healing ({max_healing_tries}) tercapai.")
            return False, active_fallback


def main():
    config = load_config()
    state = load_state()
    
    # Argument parsing untuk testing
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--test-planner":
            print("[Orchestrator] Running test-planner mode...")
            run_harvester()
            plan_meta = run_ai_planner(config)
            if plan_meta:
                print(f"[Orchestrator] ✅ AI Planner sukses! Metadata: {plan_meta}")
                if os.path.exists(PLAN_PATH):
                    with open(PLAN_PATH, 'r') as f:
                        print("=== LATEST PLAN ===")
                        print(f.read()[:500] + "\n... (truncated)")
            else:
                print("[Orchestrator] ❌ AI Planner gagal.")
            sys.exit(0)
        elif arg == "--simulate-fallback":
            print("[Orchestrator] Simulating quota limit fallback...")
            run_harvester()
            plan_meta = run_ai_planner(config)
            if plan_meta:
                project_name = plan_meta.get("project_name")
                project_path = os.path.join(config.get("project_generation_path", "/home/murtix/Projects"), project_name)
                os.makedirs(project_path, exist_ok=True)
                print("[Orchestrator] Memulai eksekusi fallback Aider + CometAPI...")
                success = execute_aider_fallback(project_path, plan_meta.get("task_description"), config)
                if success:
                    state["state"] = "FALLBACK_LOCAL"
                    state["current_project_path"] = project_path
                    state["active_task"] = plan_meta.get("task_description")
                    state["last_run"] = time.strftime('%Y-%m-%d %H:%M:%S')
                    save_state(state)
                    print("[Orchestrator] ✅ Simulasi fallback sukses. State saat ini: FALLBACK_LOCAL")
                else:
                    print("[Orchestrator] ❌ Eksekusi fallback Aider gagal.")
            sys.exit(0)

    webhook_url = config.get("discord_webhook_url")
    
    # Jalankan harvester
    run_harvester()
    
    # Cek State Machine
    if state.get("state") == "FALLBACK_LOCAL":
        print("[Orchestrator] Terdeteksi status FALLBACK_LOCAL. Mencoba me-resume ke Antigravity...")
        # Cek apakah agy sudah bangun/quota reset
        agy_active = check_agy_quota()
        if agy_active:
            project_path = state.get("current_project_path")
            success = run_resume_sync(project_path, config)
            if success:
                # Bersihkan status
                state["state"] = "IDLE"
                state["current_project_path"] = ""
                state["active_task"] = ""
                state["last_run"] = time.strftime('%Y-%m-%d %H:%M:%S')
                save_state(state)
                
                # Hapus pre_instruction jika ada
                if os.path.exists(PRE_INSTRUCTION_PATH):
                    try: os.remove(PRE_INSTRUCTION_PATH)
                    except: pass
                    
                # Kirim laporan selesai
                report_text = f"🌅 **Morning Report: Autopilot Resumed & Completed!**\n" \
                              f"Antigravity CLI berhasil bangun, meninjau pengerjaan model fallback di `{project_path}`, dan menyelesaikan proyek!"
                send_discord_notification(webhook_url, report_text)
                
                with open(REPORT_PATH, 'w') as f:
                    f.write(f"# 🌅 Morning Report\n\nAutopilot sukses resume dan pengerjaan diselesaikan di [{project_path}](file://{project_path}) pada {time.strftime('%Y-%m-%d %H:%M:%S')}.")
            else:
                print("[Orchestrator] Kuota Antigravity CLI aktif namun resume gagal. Tetap di FALLBACK_LOCAL.")
        else:
            print("[Orchestrator] Antigravity CLI masih limit. Tetap di FALLBACK_LOCAL.")
        sys.exit(0)
        
    # State: IDLE - Mulai Pekerjaan Baru
    print("[Orchestrator] Memulai alur kerja Autopilot Baru...")
    
    # Jalankan AI Planner
    plan_meta = run_ai_planner(config)
    if not plan_meta:
        print("[Orchestrator] Planner gagal merumuskan rencana. Keluar.")
        sys.exit(1)
        
    project_name = plan_meta.get("project_name")
    task_desc = plan_meta.get("task_description")
    
    # Jika mode adalah new, buat folder baru di project_generation_path
    if plan_meta.get("type") == "new":
        project_path = os.path.join(config.get("project_generation_path", "/home/murtix/Projects"), project_name)
    else:
        # Jika enhance, pastikan ada di whitelist
        project_path = plan_meta.get("target_path")
        if project_path not in config.get("allow_maintenance", []):
            print(f"[Orchestrator] ⚠️ Proyek '{project_path}' tidak terdaftar di whitelist pengerjaan. Menggunakan folder default VibeKlore.")
            project_path = VIBE_DIR
            
    os.makedirs(project_path, exist_ok=True)
    
    # Siapkan branch git sebelum menulis kode
    branch_name = setup_git_branch(project_path, project_name)
    
    # Cek kuota agy
    agy_active = check_agy_quota()
    
    success = False
    used_fallback = False
    
    # Jalankan pengerjaan dengan loop self-healing
    success, used_fallback = execute_with_self_healing(
        project_path, task_desc, config, agy_active, used_fallback
    )
        
    if success:
        # Commit sisa perubahan di branch (jika ada yang terlewat)
        if config.get("git_auto_commit", True):
            subprocess.run(["git", "add", "."], cwd=project_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "commit", "-m", "[Autopilot] Auto-commit changes and fixes"], cwd=project_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        # PUSH & PULL REQUEST CREATION
        pr_url = ""
        try:
            print(f"[Orchestrator] Pushing branch {branch_name} ke GitHub...")
            subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=project_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            pr_url = create_github_pr(project_path, branch_name, project_name, config)
        except Exception as e:
            print(f"[Orchestrator] Gagal mendorong branch / membuat PR: {e}")

        pr_info = f"\n- **Pull Request**: {pr_url}" if pr_url else ""

        if used_fallback:
            # Set status ke FALLBACK_LOCAL agar cron berikutnya me-resume ke agy
            state["state"] = "FALLBACK_LOCAL"
            state["current_project_path"] = project_path
            state["active_task"] = task_desc
            state["last_run"] = time.strftime('%Y-%m-%d %H:%M:%S')
            save_state(state)
            
            # Kirim Discord Notif Fallback
            msg = f"⚠️ **Autopilot Warning: Running in Fallback Mode**\n" \
                  f"Proyek `{project_name}` sedang dikerjakan menggunakan model fallback lokal (CometAPI `gpt-4o-mini`) karena kuota Antigravity CLI sedang habis/limit.\n" \
                  f"Branch: `{branch_name}`\nPR URL: {pr_url or 'N/A'}"
            send_discord_notification(webhook_url, msg)
        else:
            # Sukses penuh dengan agy
            state["state"] = "IDLE"
            state["current_project_path"] = ""
            state["active_task"] = ""
            state["last_run"] = time.strftime('%Y-%m-%d %H:%M:%S')
            save_state(state)
            
            # Hapus pre_instruction jika ada
            if os.path.exists(PRE_INSTRUCTION_PATH):
                try: os.remove(PRE_INSTRUCTION_PATH)
                except: pass
                
            # Kirim Discord Notif Sukses
            msg = f"🌅 **Morning Report: Autopilot Success!**\n" \
                  f"Proyek baru `{project_name}` berhasil dibuat di `{project_path}` menggunakan Antigravity CLI secara native!\n" \
                  f"Branch: `{branch_name}`\nPR URL: {pr_url or 'N/A'}"
            send_discord_notification(webhook_url, msg)
            
            # Tulis Morning Report markdown
            report_text = f"# 🌅 Morning Report: Autopilot Selesai!\n\n" \
                          f"Pagi Murtix! Autopilot telah membuat proyek baru untukmu:\n\n" \
                          f"- **Nama**: {project_name}\n" \
                          f"- **Lokasi**: [Folder Project](file://{project_path})\n" \
                          f"- **Branch**: `{branch_name}`{pr_info}\n" \
                          f"- **Deskripsi**: {task_desc}\n" \
                          f"- **Status**: ✅ Sukses Ter-Scaffold via Antigravity CLI!\n\n" \
                          f"*Laporan dibuat pada {time.strftime('%Y-%m-%d %H:%M:%S')}.*"
            with open(REPORT_PATH, 'w') as f:
                f.write(report_text)
                
        print("[Orchestrator] Proses autopilot selesai!")
    else:
        print("[Orchestrator] Autopilot gagal mengeksekusi tugas.")

if __name__ == "__main__":
    main()
