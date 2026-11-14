// ---------------------------------------------------------------------------
// World Prematurity Day | The Cub — drawing + animation helpers
// Everything is a pure function of time so frames render deterministically.
// ---------------------------------------------------------------------------

// Palette (sampled from the storyboard / doodle references — swap here for official brand values)
const C = {
  ol: '#4A2C23',        // dark-brown outline
  bg: '#FBE3E7',        // blush background
  bg2: '#F6D3DA',       // deeper blush
  halo: '#FDEFF1',      // soft circle behind subjects
  cream: '#FFF7F3',
  pink: '#F28FA8', pinkS: '#DE6F8D', pinkD: '#C9577A',
  lav: '#DCD3F1', lavS: '#BBAEE0', lavD: '#9C86CF', plum: '#5D4777',
  blue: '#8FB2DD', blueS: '#7096C8',
  glove: '#A9CFEF', gloveS: '#83B4E0',
  yellow: '#F8D97F', yellowS: '#EBC25C',
  skin: '#F5CFB4', skinS: '#E7B193',
  baby: '#F4C2A6', babyS: '#E3A487',
  blush: '#F3A1A6',
  hairM: '#8D5A3B', hairMS: '#6E432B', hairMH: '#B27D58',
  hairF: '#5A3A2A', hairFS: '#43291D',
  hairP: '#A3613F', hairPS: '#844A2F',
  white: '#FFFCFA', whiteS: '#EEE6EC',
  tube: '#D7D0E4', eye: '#3A2219', mouth: '#B4566E'
};
const SW = 4; // default outline width

// ---------- math / easing ----------
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const lerp = (a, b, k) => a + (b - a) * k;
const prog = (t, a, b) => clamp((t - a) / (b - a));
const eio = k => k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;      // easeInOutCubic
const eo = k => 1 - Math.pow(1 - k, 3);                                          // easeOutCubic
const ei = k => k * k * k;
const eob = k => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(k - 1, 3) + c1 * Math.pow(k - 1, 2); }; // easeOutBack
const eel = k => k === 0 ? 0 : k === 1 ? 1 : Math.pow(2, -10 * k) * Math.sin((k * 10 - .75) * (2 * Math.PI) / 3) + 1; // elastic
const sin = (t, f = 1, ph = 0) => Math.sin(2 * Math.PI * f * t + ph);
const R = d => d * Math.PI / 180;
const f1 = v => (Math.round(v * 10) / 10);
const pt = p => `${f1(p[0])},${f1(p[1])}`;
// pop-in: 0..1 with overshoot, from time a over dur
const pop = (t, a, dur = .45) => eob(prog(t, a, a + dur));
const fadeIn = (t, a, dur = .35) => eo(prog(t, a, a + dur));

// natural blinking: closes for ~0.14s at pseudo-random intervals
function blink(t, seed = 0) {
  const period = 2.9 + (seed % 3) * .55;
  const ph = ((t + seed * 1.37) % period);
  const d = 0.16;
  if (ph < d) return Math.sin(Math.PI * ph / d);
  return 0;
}
// smooth noise-ish wobble
const wob = (t, s = 0) => .55 * Math.sin(t * 1.3 + s) + .3 * Math.sin(t * 2.7 + s * 2.1) + .15 * Math.sin(t * 4.9 + s * 3.3);

// ---------- svg builders ----------
const P = (d, fill = 'none', sw = SW, x = '') => `<path d="${d}" fill="${fill}" stroke="${sw ? C.ol : 'none'}" stroke-width="${sw}" stroke-linejoin="round" stroke-linecap="round" ${x}/>`;
const Pn = (d, fill, x = '') => `<path d="${d}" fill="${fill}" ${x}/>`; // no outline
const L = (d, col = C.ol, sw = 3.5, x = '') => `<path d="${d}" fill="none" stroke="${col}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round" ${x}/>`;
const E = (cx, cy, rx, ry, fill, sw = SW, x = '') => `<ellipse cx="${f1(cx)}" cy="${f1(cy)}" rx="${f1(rx)}" ry="${f1(ry)}" fill="${fill}" stroke="${sw ? C.ol : 'none'}" stroke-width="${sw}" ${x}/>`;
const Ci = (cx, cy, r, fill, sw = SW, x = '') => E(cx, cy, r, r, fill, sw, x);
const G = (tr, inner, x = '') => `<g transform="${tr}" ${x}>${inner}</g>`;
const T = (x, y, s = 1, r = 0) => `translate(${f1(x)},${f1(y)}) rotate(${f1(r)}) scale(${s})`;
const op = (o, inner) => o >= 0.999 ? inner : (o <= 0.001 ? '' : `<g opacity="${o.toFixed(3)}">${inner}</g>`);
const txt = (x, y, s, size, fill, fam = 'Fredoka', wgt = 600, anchor = 'middle', extra = '') =>
  `<text x="${f1(x)}" y="${f1(y)}" font-family="${fam}" font-weight="${wgt}" font-size="${size}" fill="${fill}" text-anchor="${anchor}" ${extra}>${s}</text>`;

// smooth limb through shoulder S, elbow E, hand H (quadratic passing near E)
function limbPath(S, E, H) {
  const c = [2 * E[0] - (S[0] + H[0]) / 2, 2 * E[1] - (S[1] + H[1]) / 2];
  return `M${pt(S)} Q${pt(c)} ${pt(H)}`;
}
function tube(d, w, fill) {
  return L(d, C.ol, w + 2 * SW) + L(d, fill, w);
}
// tapered arm: upper w1, fore w2 (two tubes, joint hidden by overlap)
function arm2(S, E, H, w1, w2, fill) {
  const m = [(S[0] + E[0]) / 2, (S[1] + E[1]) / 2], n = [(E[0] + H[0]) / 2, (E[1] + H[1]) / 2];
  const up = `M${pt(S)} Q${pt(E)} ${pt(n)}`, fo = `M${pt(m)} Q${pt(E)} ${pt(H)}`;
  return L(up, C.ol, w1 + 2 * SW) + L(fo, C.ol, w2 + 2 * SW) + L(up, fill, w1) + L(fo, fill, w2);
}
// two-bone IK: returns [elbow, hand]
function ik(S, H, l1, l2, bend = 1) {
  let dx = H[0] - S[0], dy = H[1] - S[1];
  let d = Math.hypot(dx, dy);
  const dm = Math.min(Math.max(d, Math.abs(l1 - l2) + 1), l1 + l2 - 0.5);
  const a = Math.atan2(dy, dx);
  const cb = (l1 * l1 + dm * dm - l2 * l2) / (2 * l1 * dm);
  const b = Math.acos(clamp(cb, -1, 1));
  const ang = a + bend * b;
  const Eb = [S[0] + l1 * Math.cos(ang), S[1] + l1 * Math.sin(ang)];
  const Hh = [S[0] + dm * Math.cos(a), S[1] + dm * Math.sin(a)];
  return [Eb, Hh];
}
const angOf = (A, B) => Math.atan2(B[1] - A[1], B[0] - A[0]) * 180 / Math.PI;

// ---------- hands ----------
// open hand pointing along +x, wrist at origin
function handOpen(fill = C.skin, shade = C.skinS) {
  return P('M-4,-15 C6,-21 20,-21 30,-19 C39,-18 47,-16 47,-11 C47,-6 40,-6 33,-7 C42,-6 51,-3 51,2 C51,7 42,7 34,5 C42,8 48,11 47,16 C45,21 37,18 30,14 C35,17 39,21 36,25 C32,28 25,23 18,18 C10,20 0,18 -4,13 Z', fill)
    + P('M4,-16 C0,-28 9,-36 16,-31 C21,-27 18,-21 15,-18', fill)
    + L('M33,-7 C27,-8 22,-7 18,-6 M34,5 C28,4 23,3 19,2 M30,14 C25,12 21,10 18,8', C.ol, 2.4);
}
// relaxed cupped hand (gentle touch)
function handSoft(fill = C.skin) {
  return P('M-4,-16 C8,-22 26,-22 38,-16 C48,-11 52,-2 48,6 C44,14 30,18 16,18 C6,18 -2,16 -4,12 Z', fill)
    + P('M6,-17 C2,-27 10,-33 17,-29 C21,-26 20,-21 17,-18', fill)
    + L('M44,-6 C36,-5 30,-4 24,-3 M46,4 C38,5 31,5 25,5', C.ol, 2.4);
}
const fist = (fill = C.baby, r = 13) => Ci(0, 0, r, fill, 3.5) + L(`M${-r * .4},${-r * .55} Q0,${-r * .2} ${r * .45},${-r * .5}`, C.ol, 2.2);

// ---------- faces ----------
// generic eye
function eye(x, y, o) {
  const k = 1 - clamp(o.blink || 0);
  const lx = (o.lx || 0) * 5.5, ly = (o.ly || 0) * 4.5;
  const s = o.es || 1;
  if (o.happy > .5) return L(`M${x - 11 * s},${y + 3} Q${x},${y - 9 * s} ${x + 11 * s},${y + 3}`, C.ol, 4);
  if (k < .18) return L(`M${x - 11 * s},${y} Q${x},${y + 6 * s} ${x + 11 * s},${y}`, C.ol, 3.6);
  let out = E(x + lx, y + ly, 7.2 * s, 9.2 * s * k, C.eye, 0);
  if (k > .5) out += Ci(x + lx + 2.4 * s, y + ly - 3.4 * s, 2.5 * s, '#FFFFFF', 0);
  const lid = y - 9.5 * s * k - 1;
  out += L(`M${x - 12 * s},${lid + 5} Q${x},${lid - 4} ${x + 12 * s},${lid + 5}`, C.ol, 3.4);
  if (o.lash) {
    const sx = o.lash > 0 ? 1 : -1; // outer side
    out += L(`M${x + sx * 11 * s},${lid + 4} l${sx * 6},-5`, C.ol, 3);
  }
  return out;
}
function brow(x, y, side, concern = 0, raise = 0, col = C.hairMS, w = 1) {
  // side: -1 left eye, +1 right eye ; inner end is toward centre
  const inner = [x - side * 12 * w, y - concern * 7 - raise * 5];
  const outer = [x + side * 13 * w, y + concern * 3 - raise * 4];
  const mid = [(inner[0] + outer[0]) / 2, Math.min(inner[1], outer[1]) - 5 - raise * 2];
  return L(`M${pt(outer)} Q${pt(mid)} ${pt(inner)}`, col, 5);
}
function mouth(x, y, smile = .5, open = 0, w = 1) {
  if (open > .05) {
    const h = 4 + 16 * open;
    return P(`M${x - 13 * w},${y - 1} Q${x},${y + h * 1.3 + smile * 6} ${x + 13 * w},${y - 1} Q${x},${y + 2 - smile * 2} ${x - 13 * w},${y - 1} Z`, C.mouth, 3.2)
      + (open > .4 ? Pn(`M${x - 6 * w},${y + h * .9} Q${x},${y + h * 1.05} ${x + 6 * w},${y + h * .9} Q${x},${y + h * .6} ${x - 6 * w},${y + h * .9}Z`, '#E58C9D') : '');
  }
  return L(`M${x - 15 * w},${y - smile * 3} Q${x},${y + smile * 13} ${x + 15 * w},${y - smile * 3}`, C.ol, 3.8);
}

/* Adult head. o = {kind:'mother'|'father'|'psych', turn, lx, ly, blink, smile, open, concern, happy, raise}
   Local coords: face centre (0,0); chin ~ y=100 */
function adultHead(o) {
  const tn = o.turn || 0, k = o.kind;
  const fx = tn * 16;
  const skin = C.skin;
  let back = '', front = '', face = '';
  // ---- back hair ----
  if (k === 'mother') {
    back = P(`M${-112 - tn * 8},-40 C-130,-160 130,-160 ${112 - tn * 8},-40 C126,30 122,92 150,152 C162,192 152,232 128,252 C108,266 78,252 68,236 L-68,236 C-78,252 -108,266 -128,252 C-152,232 -162,192 -150,152 C-122,92 ${-126 - tn * 8},30 ${-112 - tn * 8},-40 Z`, C.hairM)
      + L('M-130,150 C-138,190 -128,222 -112,240 M130,150 C138,190 128,222 112,240 M-118,60 C-126,110 -118,140 -130,170', C.hairMS, 3);
  } else if (k === 'psych') {
    const px = 102 - tn * 30;
    back = P(`M${px},-30 C${px + 40},-20 ${px + 52},40 ${px + 40},96 C${px + 30},128 ${px + 4},140 ${px - 8},126 C${px + 10},80 ${px + 6},20 ${px - 14},-10 Z`, C.hairP)
      + P(`M-102,-30 C-110,-150 110,-150 102,-30 C100,10 92,30 86,40 L-86,40 C-92,30 -100,10 -102,-30Z`, C.hairP);
  }
  // ---- neck + face ----
  const chin = fx * .9;
  face += P(`M-30,70 L-30,${o.neck || 132} L30,${o.neck || 132} L30,70 Z`, skin, SW) + Pn('M-30,72 L30,72 L29,98 Q0,112 -29,98 Z', C.skinS)+(o.collar||'');
  // ears (father / psych)
  if (k !== 'mother') {
    if (tn > -.7) face += E(-90 + tn * 14, 10, 15, 22, skin) + L(`M${-92 + tn * 14},2 Q${-98 + tn * 14},12 ${-90 + tn * 14},20`, C.ol, 2.6);
    if (tn < .7) face += E(90 + tn * 14, 10, 15, 22, skin) + L(`M${92 + tn * 14},2 Q${98 + tn * 14},12 ${90 + tn * 14},20`, C.ol, 2.6);
  }
  const jaw = k === 'father' ? 12 : 0;
  face += P(`M${-88 + tn * 10},-14 C${-92 + tn * 8},-104 ${92 + tn * 8},-104 ${88 + tn * 10},-14 C${86 + tn * 6 + jaw},48 ${44 + chin + jaw},98 ${chin},102 C${-44 + chin - jaw},98 ${-86 + tn * 6 - jaw},48 ${-88 + tn * 10},-14 Z`, skin);
  // cheeks
  face += E(-50 + tn * 20, 42, 17, 11, C.blush, 0, 'opacity="0.75"') + E(50 + tn * 12, 42, 17 * (1 - tn * .3), 11, C.blush, 0, 'opacity="0.75"');
  // eyes
  const exL = -34 + tn * 22, exR = 34 + tn * 14, ey = 8;
  const fem = k !== 'father';
  const eo_ = { blink: o.blink, lx: o.lx, ly: o.ly, happy: o.happy };
  face += eye(exL, ey, { ...eo_, lash: fem ? -1 : 0, es: 1 - Math.max(0, tn) * .15 });
  face += eye(exR, ey, { ...eo_, lash: fem ? 1 : 0, es: 1 + Math.min(0, tn) * .15 });
  const bc = k === 'mother' ? C.hairMS : k === 'father' ? C.hairFS : C.hairPS;
  face += brow(exL, ey - 24, -1, o.concern || 0, o.raise || 0, bc, k === 'father' ? 1.1 : 1);
  face += brow(exR, ey - 24, 1, o.concern || 0, o.raise || 0, bc, k === 'father' ? 1.1 : 1);
  // nose + mouth
  face += L(`M${fx * 1.3 + 2},26 Q${fx * 1.3 + 9},40 ${fx * 1.3 - 3},43`, C.ol, 3.2);
  face += mouth(fx * 1.1, 66, o.smile ?? .5, o.open || 0, 1);
  if (k === 'psych') { // round glasses
    face += Ci(exL, ey, 20, 'rgba(255,255,255,0.18)', 3.4) + Ci(exR, ey, 20 * (1 - Math.max(0, tn) * .1), 'rgba(255,255,255,0.18)', 3.4) + L(`M${exL + 20},${ey - 2} Q${(exL + exR) / 2},${ey - 8} ${exR - 20},${ey - 2}`, C.ol, 3.2);
  }
  // ---- front hair ----
  if (k === 'mother') {
    front = P(`M-96,-14 C-106,-112 -26,-134 26,-124 C82,-114 108,-66 98,-8 C86,-52 52,-80 6,-82 C-32,-80 -72,-58 -96,-14 Z`, C.hairM)
      + P(`M-94,-34 C-108,30 -104,110 -122,172 C-100,152 -86,96 -82,20 Z`, C.hairM)
      + P(`M98,-24 C110,40 102,112 122,172 C100,152 90,92 86,22 Z`, C.hairM)
      + L('M-46,-104 C-14,-118 26,-114 54,-98', C.hairMH, 9, 'opacity="0.8"')
      + L('M-60,-84 C-40,-96 -10,-100 14,-96', C.hairMS, 3);
  } else if (k === 'father') {
    front = P(`M-94,-12 C-104,-100 -40,-136 10,-134 C72,-132 106,-92 96,-8 C90,-40 74,-62 44,-68 C14,-58 -26,-72 -58,-58 C-78,-48 -88,-32 -94,-12 Z`, C.hairF)
      + L('M-40,-100 C-20,-112 10,-114 40,-104', C.hairFS, 3) + L('M-88,-20 L-90,20 M88,-20 L90,20', C.hairF, 10);
  } else if (k === 'psych') {
    front = P(`M-98,-16 C-108,-118 -10,-140 40,-124 C90,-110 110,-60 100,-6 C80,-60 40,-86 -10,-62 C-40,-50 -74,-40 -98,-16 Z`, C.hairP)
      + L('M-30,-110 C0,-122 40,-116 66,-98', '#C07A55', 8, 'opacity="0.8"');
  }
  return back + (o.body || '') + face + front;
}

// ---------- torsos ----------
// neck base at origin, body extends down. w = shoulder width
function torso(w, h, fill, shade, neck = 'round') {
  const a = w / 2;
  let s = P(`M${-a},${h} C${-a - 6},${h * .35} ${-a + 8},18 ${-a * .5},4 Q0,-4 ${a * .5},4 C${a - 8},18 ${a + 6},${h * .35} ${a},${h} Z`, fill);
  s += Pn(`M${-a + 6},${h} C${-a + 2},${h * .45} ${-a + 14},40 ${-a * .55},20 L${-a * .45},${h}Z`, shade, 'opacity="0.55"');
  if (neck === 'round') s += L(`M-34,4 Q0,34 34,4`, C.ol, 3.4);
  if (neck === 'v') s += L(`M-30,2 L0,46 L30,2`, C.ol, 3.4);
  return s;
}

// ---------- babies ----------
/* Preterm baby lying on its back, seen from above. Head to the RIGHT (flip with scale(-1,1)).
   origin = belly centre. o: {t, armA, armB, legA, legB, eyesOpen, cannula} */
function babyLying(o) {
  const t = o.t || 0;
  const br = 1 + .03 * sin(t, .55);
  const a1 = o.armA || 0, a2 = o.armB || 0, l1 = o.legA || 0, l2 = o.legB || 0;
  let s = '';
  // legs (frog position)
  const leg = (side, k) => {
    const hip = [-62, side * 30], knee = [-104 - k * 6, side * (78 + k * 6)], foot = [-150 + k * 10, side * (40 - k * 6)];
    return tube(limbPath(hip, knee, foot), 30, C.baby) + G(T(foot[0] - 6, foot[1], 1, side * 20), E(0, 0, 13, 17, C.baby, 3.4) + L(`M-8,${side * -10} l-4,${side * -3} M-2,${side * -13} l-2,${side * -4}`, C.ol, 2));
  };
  s += leg(-1, l1) + leg(1, l2);
  // body + diaper
  s += G(`scale(1,${br.toFixed(3)})`, E(8, 0, 70, 54, C.baby) + Pn('M-30,40 C10,56 50,52 70,26 C56,48 10,58 -30,40Z', C.babyS, 'opacity="0.55"'));
  s += Ci(-4, 6, 3, 'none', 2.3) + L('M40,-30 Q48,-24 46,-14', C.babyS, 3) ;
  s += P('M-34,-50 C-60,-52 -92,-40 -96,-6 C-98,30 -66,54 -34,50 C-24,24 -24,-24 -34,-50 Z', C.white) + L('M-60,-40 Q-50,0 -60,40', C.whiteS, 3);
  if (o.cannula !== false) s += tube('M118,52 C90,90 40,100 -20,96 C-80,92 -140,104 -200,120', 5, C.tube);
  // arms: fists up by the cheeks
  const arm = (side, k) => {
    const sh = [44, side * 44], el = [10 - k * 4, side * (78 + k * 4)], hd = [74 + k * 10, side * (64 - k * 4)];
    return tube(limbPath(sh, el, hd), 23, C.baby) + G(T(hd[0], hd[1]), fist(C.baby, 13));
  };
  // head (face up; top of head points +x)
  let h = '';
  h += E(-62, 6, 12, 16, C.baby, 3.2) + E(62, 6, 12, 16, C.baby, 3.2);
  h += Ci(0, 0, 62, C.baby) + Pn('M-50,34 C-26,62 26,62 50,34 C26,52 -26,52 -50,34Z', C.babyS, 'opacity="0.5"');
  h += L('M-14,-58 Q-6,-68 2,-60 M8,-60 Q14,-68 20,-58', C.babyS, 3);
  const ok = o.eyesOpen > .5;
  h += ok ? (E(-22, 0, 5.5, 7, C.eye, 0) + Ci(-20.5, -2.5, 1.8, '#fff', 0) + E(22, 0, 5.5, 7, C.eye, 0) + Ci(23.5, -2.5, 1.8, '#fff', 0))
          : L('M-30,0 Q-22,7 -14,0 M14,0 Q22,7 30,0', C.ol, 3.2);
  h += E(-34, 20, 11, 7, C.blush, 0, 'opacity="0.75"') + E(34, 20, 11, 7, C.blush, 0, 'opacity="0.75"');
  h += L('M-3,12 Q1,17 -2,20', C.ol, 2.6) + L('M-7,36 Q0,40 7,36', C.ol, 3);
  if (o.cannula !== false) {
    h += tube('M-58,18 C-40,30 -16,26 -4,26 M4,26 C16,26 40,30 58,18', 4.5, C.tube);
    h += P('M-34,20 l14,-3 l2,11 l-14,3 Z', C.white, 2.4) + P('M20,17 l14,3 l-2,11 l-14,-3 Z', C.white, 2.4);
  }
  s += G(`translate(104,0) rotate(90)`, h);
  s += arm(-1, a1) + arm(1, a2);
  return s;
}

/* Front-view child (baby -> toddler -> child). Origin at ground between feet.
   o: {pose:'sit'|'stand'|'walk', t, phase, shirt, armL, armR (hand target offsets), mouthOpen, happy, blink, bob} */
function kid(o) {
  const t = o.t || 0;
  let s = '';
  const sit = o.pose === 'sit';
  const ph = o.phase || 0;
  const bob = o.bob || 0;
  const hipY = sit ? -60 : -112 + bob;
  const bodyTop = hipY - 104;
  const headY = bodyTop - 64 + (o.headBob || 0);
  const tilt = o.tilt || 0;
  // legs
  if (sit) {
    s += tube(limbPath([-30, hipY + 6], [-74, -30], [-88, -16]), 36, C.baby) + E(-100, -18, 16, 22, C.baby, 3.5, 'transform="rotate(-30 -100 -18)"');
    s += tube(limbPath([30, hipY + 6], [74, -30], [88, -16]), 36, C.baby) + E(100, -18, 16, 22, C.baby, 3.5, 'transform="rotate(30 100 -18)"');
  } else {
    const swing = o.pose === 'walk' ? Math.sin(ph) : 0;
    const liftL = o.pose === 'walk' ? Math.max(0, Math.sin(ph)) * 22 : 0;
    const liftR = o.pose === 'walk' ? Math.max(0, -Math.sin(ph)) * 22 : 0;
    const fL = [-30 - swing * 6, -12 - liftL], fR = [30 + swing * 6, -12 - liftR];
    s += tube(limbPath([-26, hipY + 10], [-32 - swing * 2, (hipY + fL[1]) / 2], fL), 38, C.baby) + E(fL[0] - 6, fL[1] + 6, 24, 13, C.baby, 3.5);
    s += tube(limbPath([26, hipY + 10], [32 + swing * 2, (hipY + fR[1]) / 2], fR), 38, C.baby) + E(fR[0] + 6, fR[1] + 6, 24, 13, C.baby, 3.5);
  }
  // diaper
  s += P(`M-62,${hipY - 30} C-64,${hipY + 10} -40,${hipY + 36} 0,${hipY + 38} C40,${hipY + 36} 64,${hipY + 10} 62,${hipY - 30} Z`, C.white) + L(`M-30,${hipY + 6} Q0,${hipY + 18} 30,${hipY + 6}`, C.whiteS, 3);
  // body
  const shirt = o.shirt;
  const bodyFill = shirt ? C.yellow : C.baby;
  s += P(`M-62,${hipY - 20} C-70,${bodyTop + 40} -52,${bodyTop} 0,${bodyTop - 2} C52,${bodyTop} 70,${bodyTop + 40} 62,${hipY - 20} C40,${hipY - 6} -40,${hipY - 6} -62,${hipY - 20} Z`, bodyFill);
  if (shirt) { // little bear face on tee
    const by = bodyTop + 52;
    s += Ci(-14, by - 16, 8, C.yellowS, 2.6) + Ci(14, by - 16, 8, C.yellowS, 2.6) + Ci(0, by, 18, C.yellowS, 2.6) + Ci(-6, by - 3, 2.2, C.ol, 0) + Ci(6, by - 3, 2.2, C.ol, 0) + E(0, by + 5, 4, 3, C.ol, 0);
    s += L(`M-36,${bodyTop + 10} Q0,${bodyTop + 26} 36,${bodyTop + 10}`, C.ol, 3);
  } else s += Ci(0, hipY - 34, 3, 'none', 2.4);
  // arms
  const shL = [-50, bodyTop + 22], shR = [50, bodyTop + 22];
  const hL = o.armL || [-86, bodyTop + 90], hR = o.armR || [86, bodyTop + 90];
  const [eL, HL] = ik(shL, hL, 52, 52, -1), [eR, HR] = ik(shR, hR, 52, 52, 1);
  const sleeve = shirt ? C.yellow : C.baby;
  s += tube(limbPath(shL, eL, HL), 28, C.baby) + G(T(HL[0], HL[1]), fist(C.baby, 15));
  s += tube(limbPath(shR, eR, HR), 28, C.baby) + G(T(HR[0], HR[1]), fist(C.baby, 15));
  if (shirt) { s += tube(`M${pt(shL)} L${pt([lerp(shL[0], eL[0], .45), lerp(shL[1], eL[1], .45)])}`, 34, C.yellow) + tube(`M${pt(shR)} L${pt([lerp(shR[0], eR[0], .45), lerp(shR[1], eR[1], .45)])}`, 34, C.yellow); }
  // head
  let h = '';
  h += E(-64, 6, 14, 18, C.baby, 3.5) + E(64, 6, 14, 18, C.baby, 3.5);
  h += Ci(0, 0, 66, C.baby) + Pn('M-52,30 C-30,62 30,62 52,30 C30,52 -30,52 -52,30Z', C.babyS, 'opacity="0.55"');
  h += L('M-8,-66 C-14,-84 6,-92 12,-80 C16,-72 6,-68 2,-74', C.ol, 3.6); // curl
  if (o.pose !== 'sit' || o.hair) h += P('M-40,-50 C-30,-70 30,-72 44,-48 C24,-60 -20,-60 -40,-50Z', C.hairM, 3);
  h += E(-34, 24, 14, 9, C.blush, 0, 'opacity="0.75"') + E(34, 24, 14, 9, C.blush, 0, 'opacity="0.75"');
  h += eye(-24, 0, { blink: o.blink, happy: o.happy, es: 1.05, lx: o.lx || 0, ly: o.ly || 0 }) + eye(24, 0, { blink: o.blink, happy: o.happy, es: 1.05, lx: o.lx || 0, ly: o.ly || 0 });
  h += L('M-2,14 Q2,20 -1,22', C.ol, 2.8);
  h += mouth(0, 34, o.smile ?? .8, o.mouthOpen || 0, .85);
  s += G(`translate(0,${headY}) rotate(${tilt})`, h);
  return s;
}

// ---------- props / decor ----------
function sparkle(x, y, s, o = 1) {
  if (o <= 0) return '';
  return G(T(x, y, s), L('M0,-14 L0,-5 M0,5 L0,14 M-14,0 L-5,0 M5,0 L14,0', C.ol, 3), `opacity="${o.toFixed(2)}"`);
}
function heart(x, y, s, fill = C.pink, sw = 0, o = 1) {
  if (o <= 0 || s <= 0) return '';
  return G(T(x, y, s), P('M0,14 C-24,-2 -26,-20 -14,-26 C-6,-30 0,-24 0,-18 C0,-24 6,-30 14,-26 C26,-20 24,-2 0,14 Z', fill, sw), `opacity="${o.toFixed(2)}"`);
}
function dashes(x, y, r, n, s = 1, o = 1) { // little emphasis ticks radiating
  let d = '';
  for (let i = 0; i < n; i++) {
    const a = R(-150 + i * (120 / Math.max(1, n - 1)));
    d += `M${f1(x + Math.cos(a) * r)},${f1(y + Math.sin(a) * r)} L${f1(x + Math.cos(a) * (r + 22 * s))},${f1(y + Math.sin(a) * (r + 22 * s))} `;
  }
  return op(o, L(d, C.ol, 3.4));
}
function calendarIcon(w, h, opts = {}) {
  let s = P(`M${-w / 2},${-h / 2 + 18} Q${-w / 2},${-h / 2} ${-w / 2 + 18},${-h / 2} L${w / 2 - 18},${-h / 2} Q${w / 2},${-h / 2} ${w / 2},${-h / 2 + 18} L${w / 2},${h / 2 - 14} Q${w / 2},${h / 2} ${w / 2 - 14},${h / 2} L${-w / 2 + 14},${h / 2} Q${-w / 2},${h / 2} ${-w / 2},${h / 2 - 14} Z`, C.white);
  s += P(`M${-w / 2},${-h / 2 + 18} Q${-w / 2},${-h / 2} ${-w / 2 + 18},${-h / 2} L${w / 2 - 18},${-h / 2} Q${w / 2},${-h / 2} ${w / 2},${-h / 2 + 18} L${w / 2},${-h / 2 + h * .26} L${-w / 2},${-h / 2 + h * .26} Z`, C.pink);
  s += tube(`M${-w * .25},${-h / 2 - 12} L${-w * .25},${-h / 2 + 10}`, 8, C.lavS) + tube(`M${w * .25},${-h / 2 - 12} L${w * .25},${-h / 2 + 10}`, 8, C.lavS);
  if (opts.dots !== false) {
    const rows = 3, cols = 4;
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      const x = -w / 2 + w * (c + 0.75) / (cols + .5), y = -h / 2 + h * .38 + r * h * .19;
      s += L(`M${x - 5},${y - 3} l5,6 l7,-9`, (r * cols + c) < (opts.ticks ?? 0) ? C.pinkS : C.lavS, 3.6);
    }
  }
  return s;
}
