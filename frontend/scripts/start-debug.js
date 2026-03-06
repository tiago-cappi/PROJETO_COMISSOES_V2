const { spawn, execSync } = require('child_process');
const os = require('os');
const fs = require('fs');
const path = require('path');

// ── Carregar .env manualmente para garantir que as vars cheguem ao react-scripts ──
const envPath = path.resolve(__dirname, '..', '.env');
if (fs.existsSync(envPath)) {
  const lines = fs.readFileSync(envPath, 'utf-8').split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eqIdx = trimmed.indexOf('=');
    if (eqIdx === -1) continue;
    const key = trimmed.slice(0, eqIdx).trim();
    const val = trimmed.slice(eqIdx + 1).trim();
    if (!process.env[key]) {
      process.env[key] = val;
    }
  }
}

// ── Limitar memória do Node para evitar swap em máquinas com pouca RAM livre ──
const freeGB = os.freemem() / 1024 / 1024 / 1024;
if (!process.env.NODE_OPTIONS) {
  const maxOldSpace = freeGB < 2 ? 1024 : 2048;
  process.env.NODE_OPTIONS = `--max-old-space-size=${maxOldSpace}`;
}

const startTime = Date.now();

// ── Resolver react-scripts LOCAL (evita npx que instala globalmente e é lento) ──
const frontendDir = path.resolve(__dirname, '..');
const localBin = path.join(frontendDir, 'node_modules', '.bin',
  process.platform === 'win32' ? 'react-scripts.cmd' : 'react-scripts');

if (!fs.existsSync(localBin)) {
  console.error(`[DEBUG STARTUP] ERRO: react-scripts não encontrado em ${localBin}`);
  console.error('[DEBUG STARTUP] Execute "npm install" na pasta frontend primeiro.');
  process.exit(1);
}

const formatElapsed = () => `${((Date.now() - startTime) / 1000).toFixed(1)}s`;
const memUsage = () => {
  const used = process.memoryUsage();
  return `heap=${(used.heapUsed / 1024 / 1024).toFixed(0)}MB`;
};

console.log('');
console.log('╔══════════════════════════════════════════════════════╗');
console.log('║         [DEBUG STARTUP] Diagnóstico de Boot         ║');
console.log('╚══════════════════════════════════════════════════════╝');
console.log(`[DEBUG STARTUP] timestamp: ${new Date(startTime).toISOString()}`);
console.log(`[DEBUG STARTUP] plataforma: ${os.platform()} ${os.arch()}`);
console.log(`[DEBUG STARTUP] RAM livre: ${(os.freemem() / 1024 / 1024 / 1024).toFixed(1)}GB / ${(os.totalmem() / 1024 / 1024 / 1024).toFixed(1)}GB total`);
console.log(`[DEBUG STARTUP] CPUs: ${os.cpus().length}x ${os.cpus()[0]?.model || 'N/A'}`);
console.log(`[DEBUG STARTUP] NODE_OPTIONS: ${process.env.NODE_OPTIONS || '(não definido)'}`);
console.log(`[DEBUG STARTUP] GENERATE_SOURCEMAP: ${process.env.GENERATE_SOURCEMAP || '(não definido)'}`);
console.log(`[DEBUG STARTUP] DISABLE_ESLINT_PLUGIN: ${process.env.DISABLE_ESLINT_PLUGIN || '(não definido)'}`);
console.log(`[DEBUG STARTUP] react-scripts: ${localBin}`);
console.log('───────────────────────────────────────────────────────');

// ── Utilizar stdio 'inherit' para stdout/stderr (evita buffering de pipe) ──
// Em vez de capturar, vamos usar polling em localhost para detectar quando o server sobe
const child = spawn(localBin, ['start'], {
  stdio: 'inherit',
  cwd: frontendDir,
  env: process.env,
  shell: true,
});

// ── Polling: detectar quando o dev server fica disponível ──
const http = require('http');
const PORT = process.env.PORT || 3000;
let serverReady = false;

const checkServer = () => {
  if (serverReady) return;
  const req = http.get(`http://localhost:${PORT}`, (res) => {
    if (!serverReady) {
      serverReady = true;
      clearInterval(heartbeat);
      console.log('');
      console.log(`[DEBUG STARTUP] ✓ Servidor respondendo em localhost:${PORT}! (${formatElapsed()}) [${memUsage()}]`);
      console.log('═══════════════════════════════════════════════════════');
    }
  });
  req.on('error', () => { /* server not ready yet */ });
  req.setTimeout(1000, () => req.destroy());
};

const heartbeat = setInterval(() => {
  checkServer();
  if (!serverReady) {
    console.log(`[DEBUG STARTUP] aguardando compilação webpack... (${formatElapsed()}) [${memUsage()}]`);
  }
}, 10000);

// Checar a cada 3s sem logar (log só a cada 10s)
const fastPoll = setInterval(() => checkServer(), 3000);

child.on('close', (code) => {
  clearInterval(heartbeat);
  clearInterval(fastPoll);
  console.log(`[DEBUG STARTUP] processo finalizado com código ${code} (${formatElapsed()})`);
  process.exit(code ?? 0);
});

child.on('error', (error) => {
  clearInterval(heartbeat);
  clearInterval(fastPoll);
  console.error(`[DEBUG STARTUP] falha ao iniciar react-scripts: ${error.message}`);
  process.exit(1);
});
