const express = require('express');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const app = express();
const PORT = process.env.PORT || 3300;

const VIBE_DIR = path.resolve(__dirname, '..');
const CONFIG_PATH = path.join(VIBE_DIR, 'whitelist_config.json');
const STATE_PATH = path.join(VIBE_DIR, 'autopilot_state.json');
const PRE_INSTRUCTION_PATH = path.join(VIBE_DIR, 'pre_instruction.txt');
const LOG_PATH = path.join(VIBE_DIR, 'autopilot.log');
const ORCHESTRATOR_PATH = path.join(VIBE_DIR, 'sleeping_developer.py');

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// 1. Get configuration
app.get('/api/config', (req, res) => {
  try {
    if (!fs.existsSync(CONFIG_PATH)) {
      return res.status(404).json({ error: 'Config file not found' });
    }
    const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
    res.json(config);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// 2. Save configuration
app.post('/api/config', (req, res) => {
  try {
    const newConfig = req.body;
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(newConfig, null, 2), 'utf-8');
    res.json({ message: 'Configuration saved successfully', config: newConfig });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// 3. Get autopilot state
app.get('/api/state', (req, res) => {
  try {
    let state = { state: 'IDLE', current_project_path: '', active_task: '', last_run: '' };
    if (fs.existsSync(STATE_PATH)) {
      state = JSON.parse(fs.readFileSync(STATE_PATH, 'utf-8'));
    }
    res.json(state);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// 4. Get autopilot log
app.get('/api/logs', (req, res) => {
  try {
    if (!fs.existsSync(LOG_PATH)) {
      return res.json({ logs: 'No log file found yet.' });
    }
    const logs = fs.readFileSync(LOG_PATH, 'utf-8');
    res.json({ logs });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// 5. Trigger plan
app.post('/api/plan', (req, res) => {
  try {
    const { instruction } = req.body;
    if (!instruction || !instruction.trim()) {
      return res.status(400).json({ error: 'Instruction cannot be empty' });
    }
    fs.writeFileSync(PRE_INSTRUCTION_PATH, instruction.trim(), 'utf-8');
    res.json({ message: 'Pre-instruction saved successfully', instruction });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// 6. Trigger autopilot run
app.post('/api/run', (req, res) => {
  try {
    let state = { state: 'IDLE', current_project_path: '', active_task: '', last_run: '' };
    if (fs.existsSync(STATE_PATH)) {
      state = JSON.parse(fs.readFileSync(STATE_PATH, 'utf-8'));
    }

    if (state.state === 'RUNNING') {
      return res.status(400).json({ error: 'Autopilot is already running' });
    }

    // Set state to RUNNING in state file
    state.state = 'RUNNING';
    state.last_run = new Date().toISOString().replace('T', ' ').substring(0, 19);
    fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2), 'utf-8');

    // Kosongkan log sebelum mulai run
    fs.writeFileSync(LOG_PATH, `=== Memulai eksekusi manual via Web Dashboard pada ${new Date().toLocaleString()} ===\n`, 'utf-8');

    // Spawn python script in background
    const logStream = fs.createWriteStream(LOG_PATH, { flags: 'a' });
    
    // Siapkan environment dengan PATH ter-extend untuk cron/shell consistency
    const env = Object.assign({}, process.env);
    const userHome = require('os').homedir();
    const customPaths = [
      path.join(userHome, '.local/bin'),
      path.join(userHome, '.config/composer/vendor/bin'),
      '/usr/local/bin',
      '/usr/bin',
      '/bin'
    ];
    // Tambahkan NVM path secara dinamis jika ada
    const nvmNodeDir = path.join(userHome, '.nvm/versions/node');
    if (fs.existsSync(nvmNodeDir)) {
      const versions = fs.readdirSync(nvmNodeDir);
      versions.forEach(v => {
        customPaths.push(path.join(nvmNodeDir, v, 'bin'));
      });
    }
    env.PATH = customPaths.join(':') + ':' + (env.PATH || '');

    const child = spawn('python3', [ORCHESTRATOR_PATH], { 
      cwd: VIBE_DIR,
      env: env,
      detached: true,
      stdio: ['ignore', 'pipe', 'pipe'] 
    });

    child.stdout.pipe(logStream);
    child.stderr.pipe(logStream);

    child.unref();

    res.json({ message: 'Autopilot triggered successfully in background.' });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.listen(PORT, () => {
  console.log(`==================================================`);
  console.log(`  VibeKlore Premium Dashboard is running!`);
  console.log(`  Access it at: http://localhost:${PORT}`);
  console.log(`==================================================`);
});
