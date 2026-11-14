// Frame compositor: background, header, illustration card w/ iris transitions, captions, end card.
const CARD = { x: 60, y: 300, w: 960, h: 1040, r: 52 };
const CX = CARD.x + CARD.w / 2, CY = CARD.y + CARD.h / 2;
const TOTAL = SCENES[SCENES.length - 1];
const FPS = 30;

// ---- logo (optional brand asset: web/logo.png) ----
window.LOGO = null;
window.assetsReady = new Promise(res => {
  const img = new Image();
  img.onload = () => { window.LOGO = { w: img.naturalWidth, h: img.naturalHeight }; res(); };
  img.onerror = () => res();
  img.src = 'logo.png';
}).then(() => Promise.all(['800 60px Nunito','900 60px Nunito','600 60px Nunito','400 40px Itim','500 40px Fredoka','600 40px Fredoka','700 40px Fredoka'].map(f => document.fonts.load(f)))).then(() => document.fonts.ready);

// ---- caption layout (measured with the real font so highlights fit exactly) ----
const CAP = { size: 60, lh: 82, y0: 1478, font: 'Nunito', wN: 800, wE: 900 };
const meas = document.createElement('canvas').getContext('2d');
function wordW(w, emph) { meas.font = `${emph ? CAP.wE : CAP.wN} ${CAP.size}px ${CAP.font}`; return meas.measureText(w).width; }
let capLayout = null;
function layoutCaptions() {
  meas.font = `${CAP.wN} ${CAP.size}px ${CAP.font}`;
  const sp = meas.measureText(' ').width;
  capLayout = CHUNKS.map((lines, ci) => {
    const first = lines[0][0], last = lines[lines.length - 1].slice(-1)[0];
    const nextFirst = CHUNKS[ci + 1] ? CHUNKS[ci + 1][0][0] : null;
    const t0 = WORDS[first].s - 0.12;
    let t1 = WORDS[last].e + 0.75;
    if (nextFirst !== null) t1 = Math.min(t1, WORDS[nextFirst].s - 0.18);
    if (nextFirst !== null && WORDS[nextFirst].s - WORDS[last].e < 1.1) t1 = WORDS[nextFirst].s - 0.18;
    const L = lines.map((ids, li) => {
      const ws = ids.map(i => wordW(WORDS[i].w, EMPH.includes(i)));
      const tot = ws.reduce((a, b) => a + b, 0) + sp * (ids.length - 1);
      let x = 540 - tot / 2;
      return ids.map((i, k) => { const o = { i, x, w: ws[k] }; x += ws[k] + sp; return o; });
    });
    const yBase = CAP.y0 + (lines.length === 1 ? CAP.lh / 2 : 0);
    return { t0, t1, L, yBase };
  });
}
function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;'); }
function captions(t) {
  if (!capLayout) layoutCaptions();
  let out = '';
  for (const c of capLayout) {
    if (t < c.t0 - 0.01 || t > c.t1) continue;
    const ia = eo(prog(t, c.t0, c.t0 + 0.22));
    const oa = 1 - prog(t, c.t1 - 0.14, c.t1);
    const a = Math.min(ia, oa);
    if (a <= 0) continue;
    const dy = (1 - ia) * 18;
    let g = '';
    c.L.forEach((line, li) => {
      const y = c.yBase + li * CAP.lh;
      for (const o of line) {
        const W = WORDS[o.i], em = EMPH.includes(o.i);
        const k = prog(t, W.s - 0.06, W.s + 0.12);
        const alpha = 0.34 + 0.66 * k;
        if (em) {
          const hk = eo(prog(t, W.s, W.s + 0.28));
          if (hk > 0) g += `<rect x="${f1(o.x - 8)}" y="${f1(y - 44)}" width="${f1((o.w + 16) * hk)}" height="58" rx="14" fill="${C.lav}" opacity="0.95"/>`;
        }
        const lift = (1 - eo(k)) * 4;
        g += `<text x="${f1(o.x)}" y="${f1(y + lift)}" font-family="${CAP.font}" font-weight="${em ? CAP.wE : CAP.wN}" font-size="${CAP.size}" fill="${em ? C.pinkD : C.ol}" opacity="${alpha.toFixed(3)}">${esc(W.w)}</text>`;
      }
    });
    out += `<g transform="translate(0,${f1(dy)})" opacity="${a.toFixed(3)}">${g}</g>`;
  }
  return out;
}

// ---- header ----
function header(t) {
  const a = fadeIn(t, 0.15, 0.6) * (1 - prog(t, SCENES[9] - 0.3, SCENES[9] + 0.2));
  if (a <= 0) return '';
  const rb = sin(t, .4) * 3;
  return op(a, G(`translate(540,214)`,
    `<rect x="-262" y="-42" width="524" height="74" rx="37" fill="${C.cream}" stroke="${C.ol}" stroke-width="3"/>` +
    G(`translate(-214,-5) rotate(${rb}) scale(0.62)`, ribbon()) +
    txt(18, 12, 'World Prematurity Day', 40, C.ol, 'Itim', 400)));
}
function ribbon(fill = C.lavD) {
  return P('M-6,-28 C-26,-28 -30,-4 -16,12 L-38,40 L-26,46 L-6,20 L14,46 L26,40 L4,12 C18,-4 14,-28 -6,-28 Z', fill, 3.4)
    + Pn('M-6,-18 C-14,-18 -16,-6 -6,6 C4,-6 2,-18 -6,-18Z', C.bg);
}

// ---- scene compositing with iris transitions ----
const SCENE_FNS = [scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8, scene9];
const TR = 0.32; // half-length of a transition
function cardScene(i, t) {
  const t0 = SCENES[i];
  return SCENE_FNS[i](t, t - t0, SCENES[i + 1] - t0);
}
function cardContent(t) {
  let idx = 0;
  for (let i = 0; i < SCENE_FNS.length; i++) if (t >= SCENES[i]) idx = i;
  let out = cardScene(idx, t);
  // incoming next scene during transition window
  const nb = SCENES[idx + 1];
  if (idx + 1 < SCENE_FNS.length && t > nb - TR) {
    const k = eio(prog(t, nb - TR, nb + TR));
    out += irisIn(idx + 1, t, k);
  }
  // still finishing previous transition (we are just past boundary)
  if (idx > 0 && t < SCENES[idx] + TR) {
    const k = eio(prog(t, SCENES[idx] - TR, SCENES[idx] + TR));
    out = cardScene(idx - 1, t) + irisIn(idx, t, k);
  }
  return out;
}
let clipN = 0;
function irisIn(i, t, k) {
  const r = 30 + k * 760;
  const id = 'iris' + (clipN++);
  return `<clipPath id="${id}"><circle cx="${CX}" cy="${CY}" r="${f1(r)}"/></clipPath>` +
    `<g clip-path="url(#${id})">${cardScene(i, t)}</g>` +
    (k < 1 ? `<circle cx="${CX}" cy="${CY}" r="${f1(r)}" fill="none" stroke="${C.cream}" stroke-width="${f1(18 * (1 - k) + 4)}" opacity="${(1 - k).toFixed(2)}"/>` : '');
}

function frame(t) {
  clipN = 0;
  let s = `<rect width="1080" height="1920" fill="${C.bg}"/>`;
  // faint doodle dots on the page background
  s += pageDecor(t);
  s += header(t);
  // card enter (first 0.5s) and exit into end card
  const enter = eo(prog(t, 0, 0.55));
  const cs = 0.94 + 0.06 * enter;
  let card = `<clipPath id="card"><rect x="${CARD.x}" y="${CARD.y}" width="${CARD.w}" height="${CARD.h}" rx="${CARD.r}"/></clipPath>`;
  card += `<rect x="${CARD.x}" y="${CARD.y + 10}" width="${CARD.w}" height="${CARD.h}" rx="${CARD.r}" fill="${C.bg2}"/>`;
  card += `<g clip-path="url(#card)">${cardContent(t)}</g>`;
  card += `<rect x="${CARD.x}" y="${CARD.y}" width="${CARD.w}" height="${CARD.h}" rx="${CARD.r}" fill="none" stroke="${C.ol}" stroke-width="4"/>`;
  s += op(enter, G(`translate(${CX},${CY}) scale(${cs.toFixed(4)}) translate(${-CX},${-CY})`, card));
  s += captions(t);
  if (t > SCENES[9] - 0.6) s += endCard(t);
  // gentle fade from/to page colour at the very start / end
  const fin = 1 - prog(t, 0, 0.35), fout = prog(t, TOTAL - 0.25, TOTAL);
  if (fin > 0) s += `<rect width="1080" height="1920" fill="${C.bg}" opacity="${fin.toFixed(3)}"/>`;
  return s;
}
function pageDecor(t) {
  let s = '';
  const pts = [[110, 1730, 0], [960, 1700, 1], [980, 150, 2], [96, 130, 3], [540, 1810, 4]];
  for (const [x, y, k] of pts) s += sparkle(x, y, 0.9, 0.35 + 0.25 * sin(t, .35, k));
  s += heart(160, 1820, 0.9, C.pink, 0, 0.35) + heart(930, 1830, 0.7, C.lavS, 0, 0.45);
  return s;
}

window.renderAt = function (t) {
  document.getElementById('stage').innerHTML = frame(t);
};
window.TOTAL = TOTAL; window.FPS = FPS;
