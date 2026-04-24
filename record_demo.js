/**
 * AgentFlow Hackathon Demo Recording
 * Uses Playwright recordVideo — no external screen recorder needed.
 * Output: demo-video/agentflow-demo.webm
 *
 * Run: node record_demo.js
 */
// Playwright from npx cache; chromium-1208 binary (what's installed on this machine)
const PLAYWRIGHT_PATH = 'C:/Users/ASFAR/AppData/Local/npm-cache/_npx/9833c18b2d85bc59/node_modules/playwright';
const CHROMIUM_EXE = 'C:/Users/ASFAR/AppData/Local/ms-playwright/chromium-1208/chrome-win64/chrome.exe';
const { chromium } = require(PLAYWRIGHT_PATH);
const path = require('path');
const fs = require('fs');

const VIDEO_DIR = path.join(__dirname, 'demo-video');
const DASHBOARD_URL = 'http://localhost:3000';
const BACKEND_URL = 'http://localhost:8000';

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

(async () => {
  if (!fs.existsSync(VIDEO_DIR)) fs.mkdirSync(VIDEO_DIR, { recursive: true });

  console.log('Launching browser with video recording...');
  const browser = await chromium.launch({
    headless: false,
    executablePath: CHROMIUM_EXE,
    args: ['--start-maximized'],
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: {
      dir: VIDEO_DIR,
      size: { width: 1280, height: 720 },
    },
  });

  const page = await context.newPage();

  // ─── SCENE 1: Dashboard Intro ──────────────────────────────────────
  console.log('Scene 1: Dashboard intro...');
  await page.goto(DASHBOARD_URL, { waitUntil: 'networkidle' });
  await sleep(3000); // Hold on title — "AgentFlow — Autonomous AI Agent Economy on Arc"

  // Scroll slowly to show agent cards
  await page.evaluate(() => window.scrollTo({ top: 200, behavior: 'smooth' }));
  await sleep(2000);

  // Scroll back to top
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(1500);

  // ─── SCENE 2: Margin Analysis ──────────────────────────────────────
  console.log('Scene 2: Margin analysis...');
  await page.evaluate(() => window.scrollTo({ top: 500, behavior: 'smooth' }));
  await sleep(4000); // Hold on Gas vs Arc comparison: -$997 LOSS vs +$2.999 PROFIT

  // Scroll to live feed (empty, about to run)
  await page.evaluate(() => window.scrollTo({ top: 900, behavior: 'smooth' }));
  await sleep(2000);

  // ─── SCENE 3: Clear + Run Demo ─────────────────────────────────────
  console.log('Scene 3: Clearing data and running demo...');
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(1000);

  // Clear all data
  await page.getByRole('button', { name: /Clear All Data/ }).click();
  await sleep(2000);

  // Run demo
  console.log('Clicking Run Demo...');
  await page.getByRole('button', { name: /Run Demo/ }).click();
  await sleep(3000); // Show initial burst of transactions

  // ─── SCENE 4: Watch transactions arrive (concurrent demo ~30s) ─────
  console.log('Scene 4: Watching transactions stream in...');
  for (let i = 0; i < 3; i++) {
    await sleep(10000);
    const count = await page.locator('p:has-text("Total Transactions") + p').textContent().catch(() => '?');
    const usdc = await page.locator('p:has-text("USDC Settled") + p').textContent().catch(() => '?');
    console.log(`  Progress: ${count} txns | ${usdc} settled`);
  }

  // ─── SCENE 5: Scroll to Live Feed ──────────────────────────────────
  console.log('Scene 5: Live transaction feed...');
  await page.evaluate(() => window.scrollTo({ top: 800, behavior: 'smooth' }));
  await sleep(10000); // Watch real CONFIRMED transactions in the table

  // ─── SCENE 6: Wait for all 55 to complete ──────────────────────────
  console.log('Scene 6: Waiting for all 55 Circle confirmations...');
  try {
    await page.waitForFunction(() => {
      const btn = document.querySelector('button');
      return btn && btn.textContent.includes('Run Demo');
    }, { timeout: 90000 });
    console.log('Demo complete!');
  } catch {
    console.log('90s timeout — proceeding with what we have...');
  }

  await sleep(2000);

  // ─── SCENE 7: Final Stats ───────────────────────────────────────────
  console.log('Scene 7: Final stats...');
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(3000);

  // Get final numbers
  const finalCount = await page.locator('p:has-text("Total Transactions") + p').textContent().catch(() => '?');
  const finalUsdc = await page.locator('p:has-text("USDC Settled") + p').textContent().catch(() => '?');
  console.log(`Final: ${finalCount} transactions | ${finalUsdc} USDC settled`);

  await sleep(4000); // Hold on final stats

  // ─── SCENE 8: Live Tx Feed with Real Hashes ────────────────────────
  console.log('Scene 8: Transaction feed with tx hashes...');
  await page.evaluate(() => window.scrollTo({ top: 800, behavior: 'smooth' }));
  await sleep(5000);

  // ─── SCENE 9: Arc Explorer — MAIN PAGE navigate (same tab = recorded) ─
  console.log('Scene 9: Arc Explorer on MAIN PAGE...');

  // Get first real tx hash link from the dashboard
  const txLink = page.locator('a[href*="testnet.arcscan.app"]').first();
  const linkCount = await txLink.count();
  let explorerUrl = 'https://testnet.arcscan.app/tx/0x4079460fb8c9fe20c015a07d5b101700e47cb5e0918844c61fa9f4739259903b';

  if (linkCount > 0) {
    explorerUrl = await txLink.getAttribute('href');
    console.log(`Using live tx hash: ${explorerUrl}`);
  } else {
    console.log('Using known real tx hash...');
  }

  // Navigate MAIN PAGE to Arc Explorer (stays in same recording)
  await page.goto(explorerUrl, { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(() => {});
  await sleep(8000); // Hold on Arc Explorer — show Success, block, confirmations

  // ─── SCENE 10: Circle Console — MAIN PAGE navigate ─────────────────
  console.log('Scene 10: Circle Developer Console on MAIN PAGE...');
  await page.goto('https://console.circle.com', {
    waitUntil: 'domcontentloaded',
    timeout: 20000,
  }).catch(() => {});
  await sleep(5000); // Hold on Circle Console — show Circle branding + dashboard

  // ─── SCENE 11: Back to AgentFlow Dashboard — Outro ──────────────────
  console.log('Scene 11: Back to AgentFlow dashboard outro...');
  await page.goto(DASHBOARD_URL, { waitUntil: 'networkidle', timeout: 20000 }).catch(() => {});
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(3000);
  // Scroll to show final stats
  await page.evaluate(() => window.scrollTo({ top: 200, behavior: 'smooth' }));
  await sleep(3000); // Final hold — 55 txns, $0.3110 USDC, all CONFIRMED

  // ─── Finalize ────────────────────────────────────────────────────────
  console.log('Closing context to finalize video...');
  await context.close();
  await browser.close();

  // Find the recorded video — main page file (largest file = main page recording)
  const files = fs.readdirSync(VIDEO_DIR).filter(f => f.endsWith('.webm') && !f.includes('agentflow-demo'));
  if (files.length > 0) {
    // Pick the LARGEST file — that's the main page (longest recording)
    const withSize = files.map(f => ({ f, size: fs.statSync(path.join(VIDEO_DIR, f)).size }));
    withSize.sort((a, b) => b.size - a.size);
    const best = withSize[0].f;
    const finalPath = path.join(VIDEO_DIR, 'agentflow-demo.webm');
    if (fs.existsSync(finalPath)) fs.unlinkSync(finalPath);
    fs.renameSync(path.join(VIDEO_DIR, best), finalPath);
    console.log(`\n✅ Video saved: ${finalPath}`);
    console.log(`   Size: ${(fs.statSync(finalPath).size / 1024 / 1024).toFixed(1)} MB`);
  } else {
    console.log('No new .webm file found — check demo-video/ folder');
  }
})();
