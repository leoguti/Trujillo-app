// =====================================================
// MiRuta Trujillo · presentación slide-based
// =====================================================

const deck = document.getElementById('deck');
const slides = Array.from(deck.querySelectorAll('.slide'));
const total = slides.length;
const counter = document.getElementById('counter');
const progressBar = document.getElementById('progressBar');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const overview = document.getElementById('overview');
const overviewGrid = document.getElementById('overviewGrid');
const overviewClose = document.getElementById('overviewClose');
const fullscreenBtn = document.getElementById('fullscreenBtn');

let current = 1;

// ---- Theme ----
// Forzamos light always; limpiamos cualquier preferencia previa del localStorage.
document.documentElement.setAttribute('data-theme', 'light');
try { localStorage.removeItem('miruta-theme'); } catch (e) {}

// ---- Slide navigation ----
function go(n) {
  n = Math.max(1, Math.min(total, n));
  if (n === current) return;
  slides.forEach((s) => {
    const idx = parseInt(s.dataset.slide, 10);
    s.classList.remove('is-active', 'is-prev');
    if (idx === n) s.classList.add('is-active');
    else if (idx < n) s.classList.add('is-prev');
  });
  current = n;
  updateChrome();
  history.replaceState(null, '', '#' + n);
}
function next() { go(current + 1); }
function prev() { go(current - 1); }

function updateChrome() {
  counter.textContent = current + ' / ' + total;
  progressBar.style.width = ((current - 1) / (total - 1) * 100) + '%';
  prevBtn.disabled = current === 1;
  nextBtn.disabled = current === total;
}

// inicial
slides[0].classList.add('is-active');

// hash inicial (#3 → slide 3)
(function initFromHash() {
  const m = location.hash.match(/^#(\d+)$/);
  if (m) {
    const n = parseInt(m[1], 10);
    if (n >= 1 && n <= total) {
      slides[0].classList.remove('is-active');
      current = 0;
      go(n);
      return;
    }
  }
  updateChrome();
})();

// ---- Controls ----
nextBtn.addEventListener('click', next);
prevBtn.addEventListener('click', prev);

// ---- Keyboard ----
document.addEventListener('keydown', (e) => {
  if (overview.hidden === false) {
    if (e.key === 'Escape') closeOverview();
    return;
  }
  switch (e.key) {
    case 'ArrowRight':
    case 'ArrowDown':
    case 'PageDown':
    case ' ':
      e.preventDefault(); next(); break;
    case 'ArrowLeft':
    case 'ArrowUp':
    case 'PageUp':
      e.preventDefault(); prev(); break;
    case 'Home': e.preventDefault(); go(1); break;
    case 'End': e.preventDefault(); go(total); break;
    case 'Escape': openOverview(); break;
    case 'f': case 'F': toggleFullscreen(); break;
  }
  // teclas numéricas → ir a slide
  if (/^[0-9]$/.test(e.key)) {
    const n = parseInt(e.key, 10);
    if (n >= 1 && n <= total) go(n);
  }
});

// ---- Touch / swipe ----
let touchStartX = 0;
deck.addEventListener('touchstart', (e) => { touchStartX = e.touches[0].clientX; }, { passive: true });
deck.addEventListener('touchend', (e) => {
  const dx = e.changedTouches[0].clientX - touchStartX;
  if (Math.abs(dx) > 50) { dx > 0 ? prev() : next(); }
}, { passive: true });

// ---- Hash sync ----
window.addEventListener('hashchange', () => {
  const m = location.hash.match(/^#(\d+)$/);
  if (m) go(parseInt(m[1], 10));
});

// ---- Idle / hint ----
let idleTimer;
function bumpActivity() {
  document.body.classList.remove('is-idle');
  clearTimeout(idleTimer);
  idleTimer = setTimeout(() => document.body.classList.add('is-idle'), 4000);
}
['mousemove', 'keydown', 'touchstart'].forEach((ev) => window.addEventListener(ev, bumpActivity, { passive: true }));
bumpActivity();

// ---- Overview ----
function buildOverview() {
  overviewGrid.innerHTML = '';
  slides.forEach((s) => {
    const num = s.dataset.slide;
    const title = s.dataset.title || (s.querySelector('h1, h2')?.textContent || '').trim() || ('Slide ' + num);
    const card = document.createElement('button');
    card.className = 'overview-card';
    card.dataset.target = num;
    card.innerHTML = '<span class="overview-card-num">Slide ' + num + ' / ' + total + '</span>' +
                     '<h4 class="overview-card-title">' + title + '</h4>';
    card.addEventListener('click', () => {
      go(parseInt(num, 10));
      closeOverview();
    });
    overviewGrid.appendChild(card);
  });
}

function openOverview() {
  buildOverview();
  overview.hidden = false;
  // marcar el actual
  const cards = overviewGrid.querySelectorAll('.overview-card');
  cards.forEach((c) => c.classList.toggle('is-current', parseInt(c.dataset.target, 10) === current));
}
function closeOverview() { overview.hidden = true; }
overviewClose.addEventListener('click', closeOverview);
overview.addEventListener('click', (e) => { if (e.target === overview) closeOverview(); });

// ---- Fullscreen ----
function toggleFullscreen() {
  if (!document.fullscreenElement) document.documentElement.requestFullscreen?.();
  else document.exitFullscreen?.();
}
fullscreenBtn.addEventListener('click', toggleFullscreen);

// ---- Mermaid ----
(function initMermaid() {
  if (!window.mermaid) return;
  const themeFor = (t) => (t === 'light' ? 'default' : 'dark');
  function render() {
    const theme = document.documentElement.getAttribute('data-theme') || 'dark';
    window.mermaid.initialize({
      startOnLoad: false,
      theme: themeFor(theme),
      themeVariables: theme === 'dark'
        ? {
            background: 'transparent',
            primaryColor: '#1a1d2e',
            primaryTextColor: '#f4f5f9',
            primaryBorderColor: '#818cf8',
            lineColor: '#6c7186',
            secondaryColor: '#0e1019',
            tertiaryColor: '#0a0c14',
            clusterBkg: 'rgba(99, 102, 241, 0.06)',
            clusterBorder: 'rgba(129, 140, 248, 0.25)',
          }
        : {
            background: 'transparent',
            primaryColor: '#ffffff',
            primaryTextColor: '#0f172a',
            primaryBorderColor: '#6366f1',
            lineColor: '#94a3b8',
            secondaryColor: '#f8f9fc',
            clusterBkg: 'rgba(99, 102, 241, 0.04)',
            clusterBorder: 'rgba(99, 102, 241, 0.2)',
          },
      flowchart: { curve: 'basis', padding: 20 },
    });
    document.querySelectorAll('.mermaid').forEach((el) => {
      if (!el.dataset.source) el.dataset.source = el.textContent.trim();
      el.removeAttribute('data-processed');
      el.innerHTML = el.dataset.source;
    });
    window.mermaid.run({ querySelector: '.mermaid' });
  }
  window.__renderMermaid = render;
  render();
})();
