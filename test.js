const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const VIBE_DIR = __dirname;
const CONFIG_PATH = path.join(VIBE_DIR, 'whitelist_config.json');
const BACKUP_PATH = path.join(VIBE_DIR, 'whitelist_config.backup.json');

// Backup config before tests
if (fs.existsSync(CONFIG_PATH)) {
  fs.copyFileSync(CONFIG_PATH, BACKUP_PATH);
}

test.after(() => {
  // Restore config after tests
  if (fs.existsSync(BACKUP_PATH)) {
    fs.copyFileSync(BACKUP_PATH, CONFIG_PATH);
    fs.unlinkSync(BACKUP_PATH);
  }
});

test('Configuration Loading and Validation Tests', async (t) => {
  // Test local file reading
  await t.test('should read config successfully', () => {
    const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
    assert.ok(config);
    assert.ok(Array.isArray(config.allow_maintenance));
    assert.strictEqual(typeof config.prevent_deletion, 'boolean');
  });

  // Test server endpoints
  await t.test('Server API Integration Test', async () => {
    const testPort = 3399;
    
    // Spawn server process on testPort
    const serverProcess = spawn('node', [path.join(VIBE_DIR, 'dashboard', 'app.js')], {
      env: { ...process.env, PORT: testPort }
    });

    // Wait for server to start
    await new Promise((resolve) => setTimeout(resolve, 1000));

    try {
      // Test GET /api/config
      const getRes = await fetch(`http://localhost:${testPort}/api/config`);
      assert.strictEqual(getRes.status, 200);
      const config = await getRes.json();
      assert.ok(config.comet_api_base);
      
      // Test POST /api/config validation
      const invalidPayload = { cron_time: '99:99' };
      const postResInvalid = await fetch(`http://localhost:${testPort}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(invalidPayload)
      });
      assert.strictEqual(postResInvalid.status, 400); // Check validation failure
      
      // Test POST /api/config success
      const updatedConfig = { ...config, comet_api_base: 'https://api.testprovider.com/v1', cron_time: '12:34' };
      const postResValid = await fetch(`http://localhost:${testPort}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedConfig)
      });
      assert.strictEqual(postResValid.status, 200);
      const postResData = await postResValid.json();
      assert.strictEqual(postResData.config.comet_api_base, 'https://api.testprovider.com/v1');
      assert.strictEqual(postResData.config.cron_time, '12:34');
      
      // Verify file was written
      const fileConfig = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
      assert.strictEqual(fileConfig.comet_api_base, 'https://api.testprovider.com/v1');
      assert.strictEqual(fileConfig.cron_time, '12:34');

      // Test GET /api/state
      const stateRes = await fetch(`http://localhost:${testPort}/api/state`);
      assert.strictEqual(stateRes.status, 200);
      const state = await stateRes.json();
      assert.ok(state.state);

    } finally {
      // Kill the server process
      serverProcess.kill('SIGTERM');
    }
  });
});
