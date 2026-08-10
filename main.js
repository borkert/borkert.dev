(() => {
  const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const FINE = matchMedia('(pointer: fine)').matches;

  /* ---------- custom cursor ---------- */
  const dot = document.getElementById('cur-dot');
  const ring = document.getElementById('cur-ring');
  let cursorOn = FINE && !REDUCED;
  if (!cursorOn) document.documentElement.classList.add('no-cursor');

  let mx = innerWidth / 2, my = innerHeight / 2, sx = mx, sy = my;
  addEventListener('mousemove', (e) => { mx = e.clientX; my = e.clientY; });

  document.addEventListener('mouseover', (e) => {
    if (e.target.closest('a, button, .dock a, [data-cursor]')) document.body.classList.add('cur-hover');
  });
  document.addEventListener('mouseout', (e) => {
    if (e.target.closest('a, button, .dock a, [data-cursor]')) document.body.classList.remove('cur-hover');
  });

  /* ---------- parallax layers ---------- */
  const layers = [...document.querySelectorAll('[data-depth]')].map((el) => ({
    el, d: +el.dataset.depth || 0, x: 0, y: 0,
  }));

  /* ---------- grid coordinate readout ---------- */
  const coord = document.getElementById('coord');
  const cellPx = () => parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--cell')) || 18;
  const pad = (n) => String(n).padStart(2, '0');

  function loop() {
    sx += (mx - sx) * 0.16;
    sy += (my - sy) * 0.16;

    if (cursorOn) {
      const t = (x, y) => `translate3d(${x}px,${y}px,0) translate(-50%,-50%)`;
      dot.style.transform = t(sx, sy);
      ring.style.transform = t(sx, sy);
    }

    if (!REDUCED) {
      const nx = (sx / innerWidth) * 2 - 1;
      const ny = (sy / innerHeight) * 2 - 1;
      for (const l of layers) {
        l.x += (nx * l.d * 26 - l.x) * 0.07;
        l.y += (ny * l.d * 26 - l.y) * 0.07;
        l.el.style.transform = `translate3d(${l.x}px,${l.y}px,0)`;
      }
    }

    if (coord) {
      const c = cellPx();
      coord.textContent = `${pad(Math.round(sx / c))},${pad(Math.round(sy / c))}`;
    }
    requestAnimationFrame(loop);
  }

  /* ---------- magnetic dock ---------- */
  if (FINE && !REDUCED) {
    document.querySelectorAll('.dock a').forEach((a) => {
      a.addEventListener('mousemove', (e) => {
        const r = a.getBoundingClientRect();
        const dx = e.clientX - (r.left + r.width / 2);
        const dy = e.clientY - (r.top + r.height / 2);
        a.style.transform = `translate3d(${dx * 0.22}px,${dy * 0.22}px,0)`;
      });
      a.addEventListener('mouseleave', () => { a.style.transform = ''; });
    });
  }

  /* ---------- split name into per-letter spans ---------- */
  const nameEl = document.getElementById('name');
  if (nameEl) {
    const text = nameEl.textContent;
    nameEl.textContent = '';
    [...text].forEach((ch, i) => {
      const s = document.createElement('span');
      s.className = 'letter';
      s.style.setProperty('--i', i);
      s.textContent = ch === ' ' ? '\u00A0' : ch;
      nameEl.appendChild(s);
    });
  }

  /* ---------- enter animation trigger ---------- */
  const go = () => document.body.classList.add('loaded');
  if (document.readyState === 'complete') setTimeout(go, 140);
  else addEventListener('load', () => setTimeout(go, 140));

  loop();
})();
