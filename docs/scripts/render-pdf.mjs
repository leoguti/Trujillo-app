// Renderiza ../index.html como PDF: 1 slide = 1 página, 2048×1280 px (horizontal).
// Output: ../MiRuta-Trujillo.pdf
// Intermedios: ./pages/page-NN.png
import puppeteer from 'puppeteer';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DOCS = path.resolve(__dirname, '..');
const OUT_DIR = path.resolve(__dirname, 'pages');
const PDF_OUT = path.resolve(DOCS, 'MiRuta-Trujillo.pdf');
const W = 2048;
const H = 1280;

fs.mkdirSync(OUT_DIR, { recursive: true });
for (const f of fs.readdirSync(OUT_DIR)) fs.unlinkSync(path.join(OUT_DIR, f));

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.json': 'application/json',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
};
const server = http.createServer((req, res) => {
  let urlPath = decodeURIComponent(req.url.split('?')[0]);
  if (urlPath === '/') urlPath = '/index.html';
  const filePath = path.join(DOCS, urlPath);
  if (!filePath.startsWith(DOCS) || !fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
    res.writeHead(404); res.end('not found'); return;
  }
  const ext = path.extname(filePath).toLowerCase();
  res.writeHead(200, { 'content-type': MIME[ext] || 'application/octet-stream' });
  fs.createReadStream(filePath).pipe(res);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const port = server.address().port;
const URL = `http://127.0.0.1:${port}/index.html`;
console.log(`server: ${URL}`);

const browser = await puppeteer.launch({
  headless: 'new',
  defaultViewport: { width: W, height: H, deviceScaleFactor: 1 },
  args: ['--no-sandbox', '--font-render-hinting=none'],
});
const page = await browser.newPage();
await page.setViewport({ width: W, height: H, deviceScaleFactor: 1 });

page.on('pageerror', (e) => console.warn('pageerror:', e.message));
page.on('console', (m) => { if (m.type() === 'error') console.warn('console error:', m.text()); });

await page.goto(URL, { waitUntil: 'networkidle0' });

const total = await page.$$eval('.slide', (els) => els.length);
console.log(`total slides: ${total}`);

await page.addStyleTag({
  content: `
    *, *::before, *::after {
      transition: none !important;
      animation: none !important;
    }
    .slide { transform: none !important; }
    .slide.is-active { transform: none !important; }
    .slide.is-prev { transform: none !important; }
    #prevBtn, #nextBtn, #counter, #progressBar,
    .nav-controls, .hint, .hint-keys, #fullscreenBtn,
    .keyboard-hint, .progress-bar, .slide-counter {
      display: none !important;
    }
  `,
});

await new Promise((r) => setTimeout(r, 800));

for (let n = 1; n <= total; n++) {
  await page.evaluate((n) => {
    document.querySelectorAll('.slide').forEach((s) => {
      const idx = parseInt(s.dataset.slide, 10);
      s.classList.remove('is-active', 'is-prev');
      if (idx === n) s.classList.add('is-active');
      else if (idx < n) s.classList.add('is-prev');
    });
    const active = document.querySelector('.slide.is-active');
    if (active) active.scrollTop = 0;
  }, n);

  await page.evaluate(async () => {
    const active = document.querySelector('.slide.is-active');
    if (!active) return;
    const imgs = Array.from(active.querySelectorAll('img'));
    await Promise.all(imgs.map((img) => img.complete ? null : new Promise((res) => {
      img.addEventListener('load', res, { once: true });
      img.addEventListener('error', res, { once: true });
    })));
    if (document.fonts && document.fonts.ready) await document.fonts.ready;
  });
  await new Promise((r) => setTimeout(r, 120));

  const file = path.join(OUT_DIR, `page-${String(n).padStart(2, '0')}.png`);
  await page.screenshot({ path: file, type: 'png', clip: { x: 0, y: 0, width: W, height: H } });
  process.stdout.write(`  ${n}/${total}\r`);
}
console.log(`\nPNGs guardados en ${OUT_DIR}`);

await browser.close();
server.close();

// --- Combinar PNGs en PDF con ImageMagick ---
console.log('Combinando PNGs en PDF...');
const pngs = fs.readdirSync(OUT_DIR).filter((f) => f.endsWith('.png')).sort()
  .map((f) => path.join(OUT_DIR, f));
const r = spawnSync('magick', [...pngs, '-density', '96', '-units', 'pixelsperinch', PDF_OUT], { stdio: 'inherit' });
if (r.status !== 0) {
  console.error('magick falló. ¿Está instalado ImageMagick? (brew install imagemagick)');
  process.exit(1);
}
console.log(`PDF: ${PDF_OUT}`);
