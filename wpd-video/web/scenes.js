// Scene functions: (t = global time, lt = local time in scene, dur) -> SVG markup in 1080x1920 space.
const cam = (cx, cy, s, inner, dx = 0, dy = 0) => G(`translate(${f1(cx + dx)},${f1(cy + dy)}) scale(${s.toFixed(4)}) translate(${-cx},${-cy})`, inner);
function sceneBg(fill = C.bg, halo = [540, 800, 400], haloFill = C.halo) {
  return `<rect x="0" y="0" width="1080" height="1920" fill="${fill}"/>` + Ci(halo[0], halo[1], halo[2], haloFill, 0);
}
const W_ = i => WORDS[i].s; // word start time helper

// ===================================================================== 1
// Mother sitting beside her premature baby; gentle push-in; she strokes its head.
function scene1(t, lt) {
  const z = 1 + 0.10 * eio(prog(lt, 0, 4.6));
  let s = sceneBg(C.bg, [600, 860, 430]);
  const breathe = sin(lt, .3) * 3;
  const headTilt = 20 + sin(lt, .25) * 2.5;
  const mBody = G('translate(0,120) rotate(-22)', torso(250, 520, C.pink, C.pinkS, 'round'));
  s += G(T(300, 650 + breathe, 1.42, headTilt), adultHead({ kind: 'mother', turn: .7, lx: .7, ly: 1.5, blink: blink(lt + .7, 1), smile: .7 + .2 * prog(lt, 1.5, 2.5), body: mBody, neck: 128 }));
  // crib back panel + mattress
  s += P('M220,1060 C226,968 282,936 346,930 L940,914 C980,914 1004,940 1004,980 L1010,1060 Z', C.lav, SW, 'opacity="0.5"');
  s += L('M600,950 C720,944 830,940 930,940', C.white, 7, 'opacity="0.8"');
  s += P('M290,1040 C330,990 920,980 980,1030 L996,1120 L270,1126 Z', C.white, SW);
  // baby (head left, toward mother)
  s += G(`translate(690,1000) scale(-1.45,1.45)`, babyLying({ t: lt, armA: .8 * sin(lt, .7), armB: .6 * sin(lt, .55, 1), legA: .8 * sin(lt, .45, .3), legB: .6 * sin(lt, .5, 2), eyesOpen: (lt > 2.0 && lt < 3.8 && blink(lt, 2) < .5) ? 1 : 0 }));
  // front wall with portholes
  s += P('M190,1110 L1030,1110 Q1050,1110 1050,1130 L1050,1420 L170,1420 L170,1130 Q170,1110 190,1110 Z', C.lav);
  s += E(430, 1240, 74, 60, C.lavS, SW) + E(850, 1240, 74, 60, C.lavS, SW) + L('M394,1210 Q408,1190 434,1186 M814,1210 Q828,1190 854,1186', C.white, 5, 'opacity="0.8"');
  s += L('M190,1138 L1030,1138', C.lavS, 4);
  // other hand resting on the rim
  s += G(T(250, 1104 + sin(lt, .3) * 2, 1.25, -12), handSoft(C.skin)) + L('M180,1120 Q214,1090 252,1100', C.pinkS, 30) ;
  // front arm: hand gently strokes the baby's head
  const sweep = sin(lt, .45);
  const enter = 1 - eo(prog(lt, 0.1, 1.1));
  const hx = 430 + sweep * 14 - enter * 40, hy = 950 + Math.abs(sweep) * 6 - enter * 60;
  const shF = [340, 860];
  const [eF, HF] = ik(shF, [hx, hy], 110, 100, -1);
  s += arm2(shF, eF, HF, 54, 46, C.pink);
  s += G(T(HF[0], HF[1], 1.3, angOf(eF, HF) - 30), handSoft(C.skin));
  // love + sparkles
  const hp = pop(lt, 1.2, .6);
  s += heart(640 + sin(lt, .3) * 6, 790 - lt * 9, 1.6 * hp, C.pink, 3.4, hp);
  s += sparkle(860, 700, 1.2, .5 + .5 * sin(lt, .8)) + sparkle(920, 790, .8, .5 + .5 * sin(lt, .8, 2)) + dashes(520, 980, 100, 3, 1, .8 * fadeIn(lt, 1.6));
  return cam(560, 920, z, s);
}


// shoulder helper: head origin (hx,hy), scale k, local offset
const at = (hx, hy, k, lx, ly) => [hx + lx * k, hy + ly * k];
// smooth keyframe interpolation: keys = [[t,v],...]
function kf(t, keys) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) if (t < keys[i][0]) {
    const [a, va] = keys[i - 1], [b, vb] = keys[i];
    return lerp(va, vb, eio((t - a) / (b - a)));
  }
  return keys[keys.length - 1][1];
}

// ===================================================================== 2
// Both parents beside the incubator in the NICU; monitor ticking; concerned but hopeful.
function scene2(t, lt) {
  const z = 1.04 - 0.04 * eio(prog(lt, 0, 4.2));
  let s = sceneBg(C.bg, [700, 900, 420]);
  // NICU sign + lamps
  const sw = sin(lt, .5) * 1.5;
  s += L('M260,300 L270,352 M420,300 L410,352', C.ol, 3);
  s += G(`translate(340,400) rotate(${sw})`, `<rect x="-120" y="-48" width="240" height="96" rx="22" fill="${C.lav}" stroke="${C.ol}" stroke-width="4"/>` + txt(0, 20, 'NICU', 60, C.plum, 'Fredoka', 700));
  const glow = .35 + .1 * sin(lt, .6);
  s += Pn('M250,470 L180,760 L330,760 L290,470Z', C.cream, `opacity="${glow}"`) + Pn('M410,470 L370,760 L520,760 L450,470Z', C.cream, `opacity="${glow}"`);
  s += P('M246,452 L294,452 L300,478 L240,478Z', C.lavS, 3) + P('M406,452 L454,452 L460,478 L400,478Z', C.lavS, 3);
  // monitor on pole
  s += tube('M900,780 L900,1100', 12, C.lavS);
  s += `<rect x="770" y="560" width="250" height="190" rx="22" fill="${C.lavS}" stroke="${C.ol}" stroke-width="4"/><rect x="790" y="578" width="210" height="150" rx="14" fill="${C.plum}" stroke="${C.ol}" stroke-width="3"/>`;
  let ecg = 'M796,660';
  for (let x = 0; x <= 200; x += 4) {
    const ph = ((x / 200) * 2.2 + lt * 1.2) % 1;
    let y = 0;
    if (ph > .40 && ph < .44) y = -8; else if (ph > .46 && ph < .49) y = 18; else if (ph >= .49 && ph < .53) y = -42; else if (ph >= .53 && ph < .56) y = 16; else if (ph > .66 && ph < .72) y = -7;
    ecg += ` L${796 + x},${660 + y}`;
  }
  s += `<clipPath id="scr"><rect x="790" y="578" width="210" height="150" rx="14"/></clipPath><g clip-path="url(#scr)">${L(ecg, C.pink, 4)}</g>`;
  const beat = 1 + .25 * Math.max(0, Math.sin(lt * 2 * Math.PI * 1.2)) ** 6;
  s += heart(818, 604, .55 * beat, C.pink) + txt(890, 712, '148', 28, C.lav, 'Fredoka', 600, 'start');
  // incubator: cabinet + hood
  s += P('M520,1100 L1000,1100 L1000,1400 L520,1400Z', C.lav) + L('M540,1150 L980,1150', C.lavS, 4) + E(640, 1250, 34, 34, C.lavS, 3.5) + E(880, 1250, 34, 34, C.lavS, 3.5);
  s += P('M520,1100 L1000,1100 L1000,1076 L520,1076Z', C.cream, 3.5);
  s += G(`translate(770,1036) scale(0.92)`, babyLying({ t: lt, armA: .7 * sin(lt, .6), armB: .5 * sin(lt, .5, 1), legA: .6 * sin(lt, .4), legB: .5 * sin(lt, .45, 2), eyesOpen: 0 }));
  s += P('M536,1078 C536,930 560,860 640,856 L900,856 C970,860 990,930 990,1078 Z', C.lav, SW, 'opacity="0.42"');
  s += L('M580,1040 C580,950 600,904 650,898 M600,1052 L600,1000', C.white, 8, 'opacity="0.85"');
  s += E(640, 980, 40, 40, 'none', 3.5) + E(900, 980, 40, 40, 'none', 3.5);
  // parents
  const look = kf(lt, [[0, 1], [1.0, 1], [1.5, 0], [2.6, 0], [3.1, 1]]); // 1 = at baby, 0 = at each other
  const fTurn = lerp(-.1, .6, look), mTurn = lerp(-.45, .65, look);
  const nod = Math.max(0, Math.sin(prog(lt, 1.7, 2.4) * Math.PI)) * 8;
  // father (behind)
  const fh = [220, 640], fk = 1.12;
  s += G(T(fh[0], fh[1] + nod, fk, lerp(-4, 4, look)), adultHead({ kind: 'father', turn: fTurn, lx: lerp(.6, 1, look), ly: lerp(.6, 1, look), blink: blink(lt, 3), smile: lerp(.45, .05, look), concern: lerp(.25, .7, look), body: G('translate(0,128)', torso(280, 600, C.blue, C.blueS, 'v')) }));
  // mother (front)
  const mh = [412, 756], mk = 1.08;
  s += G(T(mh[0], mh[1], mk, lerp(-6, 6, look)), adultHead({ kind: 'mother', turn: mTurn, lx: lerp(-1, 1, look), ly: lerp(.2, 1, look), blink: blink(lt + 1.3, 1), smile: lerp(.5, .1, look), concern: lerp(.25, .75, look), body: G('translate(0,128)', torso(250, 600, C.pink, C.pinkS)) }));
  // father's hand on mother's shoulder
  const fs = at(fh[0], fh[1], fk, 120, 170), ms = at(mh[0], mh[1], mk, -96, 160);
  const [fe, fH] = ik(fs, [ms[0] - 6, ms[1] + 46 + sin(lt, .5) * 2], 120, 110, -1);
  s += arm2(fs, fe, fH, 48, 42, C.blue) + G(T(fH[0], fH[1], 1.15, angOf(fe, fH) + 30), handSoft(C.skin));
  // mother's hand on incubator hood
  const ms2 = at(mh[0], mh[1], mk, 104, 170);
  const [me, mH] = ik(ms2, [560 + sin(lt, .4) * 4, 970], 120, 110, 1);
  s += arm2(ms2, me, mH, 48, 42, C.pink) + G(T(mH[0], mH[1], 1.15, angOf(me, mH) - 40), handSoft(C.skin));
  s += sparkle(560, 820, 1, .4 + .4 * sin(lt, .7)) + heart(990, 1000, .9 * pop(lt, 2.8), C.pink, 3, pop(lt, 2.8));
  return cam(560, 860, z, s);
}

// ===================================================================== 3
// Close on the mother's face; thought bubbles pop in one after another.
function bubble(cx, cy, r, k, inner, trail) {
  if (k <= 0) return '';
  let s = '';
  if (trail) trail.forEach(([x, y, rr], i) => { const kk = clamp(k * 3 - i); if (kk > 0) s += Ci(x, y, rr * eob(kk), C.white, 3.5); });
  const kk = eob(clamp(k));
  s += G(T(cx, cy, kk), P(`M${-r},0 C${-r},${-r * .62} ${-r * .62},${-r * 1.02} 0,${-r * 1.0} C${r * .66},${-r * 1.04} ${r * 1.04},${-r * .6} ${r},0 C${r * 1.02},${r * .6} ${r * .6},${r} 0,${r * .98} C${-r * .64},${r * 1.02} ${-r * 1.02},${r * .6} ${-r},0 Z`, C.white) + inner);
  return s;
}
function scene3(t, lt) {
  const z = 1 + 0.07 * eio(prog(lt, 0, 6)) - 0.03 * eio(prog(lt, 7.5, 10.5));
  let s = sceneBg(C.bg, [540, 980, 400]);
  const qT = W_(32), cT = W_(36), gT = W_(40), oT = W_(46), lookT = W_(51);
  const sigh = Math.sin(prog(lt, .4, 2.2) * Math.PI) * 10;
  // gaze towards each bubble as it appears
  const lx = kf(t, [[0, 0], [qT, 0], [cT, -1], [gT - .1, -1], [gT + .3, 1], [oT - .1, 1], [oT + .3, 0], [99, 0]]);
  const ly = kf(t, [[0, .6], [qT, -.4], [cT, -1], [oT + .3, -1.2], [99, -1.2]]);
  const head = [540, 960 - sigh * .4], hk = 1.66;
  const handUp = eo(prog(lt, .6, 1.8));
  const tiltH = lerp(0, -7, handUp) + sin(lt, .2) * 1.5;
  s += G(T(head[0], head[1], hk, tiltH), adultHead({ kind: 'mother', turn: -.1, lx, ly, blink: blink(lt, 2), smile: -.35, concern: .9, body: G(`translate(0,${128 + sigh * .3})`, torso(300, 520, C.pink, C.pinkS)), neck: 128 }));
  // hand resting under the cheek
  const hand = [lerp(760, 676, handUp), lerp(1400, 1050, handUp) + sigh * .3];
  s += tube(limbPath([800, 1400], [lerp(820, 790, handUp), lerp(1360, 1200, handUp)], hand), 70, C.pink);
  s += G(T(hand[0], hand[1], 1.55, -110), handSoft(C.skin));
  // thought bubbles: calendar, growing baby, question mark
  const trailA = [[460, 700, 12], [420, 664, 16], [376, 630, 21]];
  const b1 = prog(t, cT - .15, cT + .35), b2 = prog(t, gT - .15, gT + .35), b3 = prog(t, oT - .1, oT + .4);
  const pre = prog(t, qT - .1, qT + .4); // little dots on "questions"
  if (pre > 0 && b1 <= 0) s += [[470, 640, 12], [500, 590, 16]].map(([x, y, r], i) => Ci(x, y + sin(lt, 1, i) * 3, r * eob(clamp(pre * 2 - i)), C.white, 3.4)).join('');
  const fl = i => sin(lt, .35, i * 2) * 8;
  s += bubble(260, 540 + fl(0), 118, b1, G(`translate(0,8) rotate(${sin(lt, .5) * 4})`, calendarIcon(130, 120, { ticks: Math.floor(prog(t, cT + .3, cT + 2) * 6) })), trailA);
  const grow = .55 + .45 * eo(prog(t, gT + .2, gT + 1.6));
  s += bubble(820, 540 + fl(1), 124, b2, G(`translate(0,${80 - 30 * grow}) scale(${(.48 * grow).toFixed(3)})`, kid({ pose: grow > .9 ? 'stand' : 'sit', t: lt, smile: .9, blink: blink(lt, 4), armL: [-80, -300 + sin(lt, 1) * 10], armR: [80, -300 - sin(lt, 1) * 10], shirt: grow > .9 })), [[620, 700, 12], [660, 664, 16], [706, 630, 21]]);
  const qb = Math.abs(Math.sin(lt * 3)) * 10 * prog(t, oT, oT + .2);
  s += bubble(540, 450 + fl(2), 98, b3, txt(0, 38 - qb, '?', 130, C.pinkS, 'Fredoka', 700, 'middle', `stroke="${C.ol}" stroke-width="4" paint-order="stroke"`), [[556, 680, 11], [550, 630, 15], [546, 584, 19]]);
  s += dashes(540, 460, 112, 3, 1, prog(t, lookT, lookT + .3) * .9 * (b3 > 0 ? 1 : 0));
  return cam(540, 820, z, s);
}

// ===================================================================== 4
// Gentle medical care; calendar highlighting "< 37 weeks".
function scene4(t, lt) {
  const z = 1.06 - 0.06 * eio(prog(lt, 0, 5.5));
  let s = sceneBg(C.bg, [540, 960, 420]);
  s += P('M90,1110 C200,1060 860,1050 990,1100 L1020,1400 L60,1400Z', C.cream, SW);
  s += L('M200,1150 C260,1140 320,1146 360,1140 M700,1160 C760,1150 820,1156 880,1150', C.whiteS, 4);
  // baby (head to the left)
  s += G(`translate(560,1040) scale(-1.55,1.55)`, babyLying({ t: lt, armA: .8 * sin(lt, .6), armB: .6 * sin(lt, .5, 1), legA: .8 * sin(lt, .4), legB: .6 * sin(lt, .45, 2), eyesOpen: (lt > 3.4 && blink(lt, 1) < .5) ? 1 : 0 }));
  // stethoscope tube from top-right
  const sx = 600 + sin(lt, .35) * 26, sy = 1000 + sin(lt, .5) * 8;
  s += tube(`M${sx},${sy} C${sx + 140},${sy - 40} 900,${720} 1080,640`, 7, C.plum);
  // glove 1: cradles the head from the left (rocking gently)
  const rock = sin(lt, .4) * 6;
  s += tube(`M-40,800 Q120,860 ${250 + rock},${930}`, 74, C.glove);
  s += G(T(258 + rock, 932, 1.9, 22 + rock * .4), handSoft(C.glove)) + L(`M${170 + rock},880 l20,40`, C.gloveS, 5);
  // glove 2: holds the stethoscope on the chest
  s += tube(`M1100,860 Q850,820 ${sx + 54},${sy - 30}`, 74, C.glove);
  s += G(T(sx, sy, 1), Ci(0, 0, 26, '#C4BDD6', 4) + Ci(0, 0, 14, C.lavS, 3));
  s += G(T(sx + 54, sy - 28, 1.8, 196), handSoft(C.glove));
  // heartbeat hearts
  const hb = 1 + .2 * Math.max(0, Math.sin(lt * Math.PI * 2 * 1.1)) ** 8;
  s += heart(370, 820, 1.3 * hb * pop(lt, .8), C.pink, 3.4, pop(lt, .8));
  s += sparkle(170, 700, 1, .5 + .5 * sin(lt, .7)) + sparkle(470, 760, .8, .5 + .5 * sin(lt, .7, 1));
  // calendar < 37 weeks
  const cT = W_(56), nT = W_(57);
  const ck = pop(t, cT - .1, .5);
  if (ck > 0) {
    let c = calendarIcon(330, 300, { dots: false });
    c += txt(0, 50, '&lt; 37', 104, C.ol, 'Fredoka', 700) + txt(0, 118, 'weeks', 50, C.ol, 'Fredoka', 600);
    // marker circle drawing around 37
    const mk = eo(prog(t, nT + .05, nT + .7));
    if (mk > 0) c += `<ellipse cx="40" cy="14" rx="74" ry="56" fill="none" stroke="${C.pinkS}" stroke-width="8" stroke-linecap="round" pathLength="100" stroke-dasharray="${f1(mk * 100)} 200" transform="rotate(-8 30 16)"/>`;
    s += G(T(790, 600 + sin(lt, .4) * 6, ck * .92, -5 + sin(lt, .3) * 1.5), c) + dashes(790, 470, 150, 3, 1, ck * fadeIn(t, nT + .4));
  }
  // "extra care" sparkle hearts
  const eT = W_(62);
  [0, 1, 2].forEach(i => { const k = prog(t, eT + i * .35, eT + i * .35 + 2.4); if (k > 0 && k < 1) s += heart(380 + i * 150, 900 - k * 200, 1 * Math.sin(k * Math.PI), [C.pink, C.lavS, C.pink][i], 3, Math.sin(k * Math.PI)); });
  return cam(560, 900, z, s);
}

// ===================================================================== 5
// Milestones: sitting -> first steps -> first words.
function scene5(t, lt) {
  const z = 1.0 + 0.04 * eio(prog(lt, 0, 6));
  let s = sceneBg(C.bg, [540, 980, 440]);
  const pT = W_(77), sT = W_(79), wT = W_(80), tT = W_(82), lT = W_(85);
  // winding milestone path
  const pk = eo(prog(lt, 0.2, 1.8));
  s += `<path d="M90,1220 C300,1250 380,1160 540,1210 C700,1260 800,1170 1000,1200" fill="none" stroke="${C.lav}" stroke-width="56" stroke-linecap="round" pathLength="100" stroke-dasharray="${f1(pk * 100)} 200"/>`;
  s += `<path d="M90,1220 C300,1250 380,1160 540,1210 C700,1260 800,1170 1000,1200" fill="none" stroke="${C.cream}" stroke-width="6" stroke-dasharray="14 18" pathLength="${f1(1000)}" opacity="${pk}"/>`;
  // stars on "milestones"
  [[230, 1196], [540, 1206], [860, 1196]].forEach(([x, y], i) => { const k = pop(t, pT + i * .12, .4); s += G(T(x, y - 300, k * .9), P('M0,-22 L6,-7 L22,-6 L10,4 L14,20 L0,11 L-14,20 L-10,4 L-22,-6 L-6,-7Z', C.yellow, 3.4), `opacity="${(k * (1 - prog(t, sT - .1, sT + .3) * (i === 0) - prog(t, wT - .1, wT + .3) * (i === 1) - prog(t, tT - .1, tT + .3) * (i === 2))).toFixed(2)}"`); });
  // kids
  const k1 = pop(t, sT - .05, .5), k2 = pop(t, wT - .05, .5), k3 = pop(t, tT - .05, .5);
  const wob1 = sin(lt, .9) * 5;
  s += k1 > 0 ? G(T(230, 1200, .78 * k1, wob1), kid({ pose: 'sit', t: lt, blink: blink(lt, 1), smile: .9, armL: [-92, -150 + sin(lt, .9) * 14], armR: [92, -150 - sin(lt, .9) * 14] })) : '';
  const ph = lt * 5.2;
  s += k2 > 0 ? G(T(540 + sin(lt, .4) * 10, 1210 - Math.abs(Math.sin(ph)) * 6, .84 * k2, Math.sin(ph) * 3), kid({ pose: 'walk', phase: ph, t: lt, blink: blink(lt, 2), smile: .9, shirt: true, armL: [-104, -300 + Math.sin(ph) * 10], armR: [104, -300 - Math.sin(ph) * 10] })) : '';
  const talk = Math.max(0, Math.sin(lt * 9)) * prog(t, tT, tT + .2) * (1 - prog(t, tT + 1.6, tT + 1.8));
  const wave = sin(lt, 1.6) * 16;
  s += k3 > 0 ? G(T(850, 1200, .92 * k3), kid({ pose: 'stand', t: lt, blink: blink(lt, 3), smile: .7, mouthOpen: talk, shirt: true, armL: [-90, -200], armR: [120 + wave * .3, -340 + wave] })) : '';
  // speech bubble
  const sb = pop(t, tT + .15, .45);
  if (sb > 0) s += G(T(880, 730, sb), P('M-120,-56 Q-120,-80 -96,-80 L96,-80 Q120,-80 120,-56 L120,30 Q120,54 96,54 L10,54 L-20,90 L-14,54 L-96,54 Q-120,54 -120,30Z', C.white) + txt(0, -2, 'Ma-ma!', 50, C.pinkD, 'Fredoka', 700));
  // arrows between milestones
  const arrow = (x, a) => a > 0 ? op(a, L(`M${x - 56},1000 Q${x},950 ${x + 56},990`, C.ol, 4.5) + L(`M${x + 38},968 L${x + 58},992 L${x + 30},1002`, C.ol, 4.5)) : '';
  s += arrow(385, fadeIn(t, wT - .1)) + arrow(700, fadeIn(t, tT - .1));
  // "a little later than we expect": soft clock
  const ck = pop(t, lT - .1, .5);
  if (ck > 0) {
    const a1 = (t - lT) * 120, a2 = (t - lT) * 24;
    s += G(T(540, 520 + sin(lt, .4) * 6, ck), Ci(0, 0, 84, C.white) + Ci(0, 0, 70, C.lav, 0) + Ci(0, 0, 70, C.cream, 3) +
      [0, 90, 180, 270].map(a => L(`M${f1(Math.cos(R(a)) * 56)},${f1(Math.sin(R(a)) * 56)} L${f1(Math.cos(R(a)) * 64)},${f1(Math.sin(R(a)) * 64)}`, C.ol, 4)).join('') +
      L(`M0,0 L${f1(Math.sin(R(a1)) * 50)},${f1(-Math.cos(R(a1)) * 50)}`, C.pinkS, 6) + L(`M0,0 L${f1(Math.sin(R(a2)) * 34)},${f1(-Math.cos(R(a2)) * 34)}`, C.ol, 7) + Ci(0, 0, 7, C.ol, 0)
      + tube('M-60,-66 L-44,-80', 14, C.pink) + tube('M60,-66 L44,-80', 14, C.pink));
  }
  return cam(540, 900, z, s);
}

// ===================================================================== 6
// Clipboard: Keeping Track of Development (4 icons highlighted in turn).
function iconMove() { return Ci(10, -34, 12, C.pink, 3.4) + L('M6,-20 L-2,10 M-2,10 L-20,30 M-2,10 L16,24 L14,40 M4,-12 L-18,-4 M4,-12 L26,-20', C.ol, 6) + L('M6,-20 L-2,10', C.pink, 0); }
function iconTalk() { return P('M-34,-30 Q-34,-42 -22,-42 L10,-42 Q22,-42 22,-30 L22,-8 Q22,4 10,4 L-12,4 L-24,16 L-22,4 Q-34,4 -34,-8Z', C.lav, 3.4) + P('M-6,-4 Q-6,-14 4,-14 L28,-14 Q38,-14 38,-4 L38,14 Q38,24 28,24 L26,24 L30,36 L16,24 L4,24 Q-6,24 -6,14Z', C.pink, 3.4); }
function iconBook() { return P('M0,-24 C-14,-34 -30,-34 -40,-28 L-40,24 C-30,18 -14,18 0,28 C14,18 30,18 40,24 L40,-28 C30,-34 14,-34 0,-24Z', C.yellow, 3.4) + L('M0,-24 L0,28 M-30,-16 Q-18,-20 -8,-14 M-30,-4 Q-18,-8 -8,-2 M30,-16 Q18,-20 8,-14 M30,-4 Q18,-8 8,-2', C.ol, 3); }
function iconSocial() { return Ci(-24, -12, 12, C.lav, 3.2) + Ci(24, -12, 12, C.lav, 3.2) + P('M-44,24 Q-44,4 -24,4 Q-4,4 -4,24Z', C.lavS, 3.2) + P('M4,24 Q4,4 24,4 Q44,4 44,24Z', C.lavS, 3.2) + Ci(0, -18, 14, C.pink, 3.4) + P('M-22,30 Q-22,4 0,4 Q22,4 22,30Z', C.pinkS, 3.4); }
function scene6(t, lt) {
  const ent = eob(prog(lt, 0, .7));
  let s = sceneBg(C.bg, [540, 860, 430]);
  const rows = [['Movement', iconMove, W_(91)], ['Communication', iconTalk, W_(95)], ['Learning', iconBook, W_(97)], ['Social Skills', iconSocial, W_(100)]];
  let b = '';
  b += `<rect x="-300" y="-450" width="600" height="890" rx="34" fill="${C.lavS}" stroke="${C.ol}" stroke-width="4"/>`;
  b += `<rect x="-262" y="-396" width="524" height="800" rx="16" fill="${C.white}" stroke="${C.ol}" stroke-width="4"/>`;
  b += P('M-80,-474 Q-80,-494 -60,-494 L60,-494 Q80,-494 80,-474 L90,-420 L-90,-420Z', C.lavD) + Ci(0, -470, 12, C.lav, 3.4);
  b += txt(0, -300, 'Keeping Track of', 50, C.ol, 'Itim', 400) + txt(0, -242, 'Development', 56, C.pinkD, 'Itim', 400);
  b += L('M-180,-216 Q0,-206 180,-220', C.pinkS, 5);
  rows.forEach(([label, ic, tt], i) => {
    const y = -140 + i * 140;
    const k = prog(t, tt - .1, tt + .3);
    const pk = eob(k);
    if (k > 0) b += `<rect x="-236" y="${y - 56}" width="${f1(472 * eo(k))}" height="112" rx="24" fill="${C.bg}"/>`;
    b += G(T(-196, y, 1 + .18 * Math.sin(k * Math.PI)), ic());
    b += txt(-136, y + 15, label, 42, C.ol, 'Fredoka', 600, 'start');
    b += `<rect x="172" y="${y - 24}" width="48" height="48" rx="10" fill="${C.cream}" stroke="${C.ol}" stroke-width="3.5"/>`;
    if (k > 0) b += `<path d="M180,${y} l12,14 l26,-32" fill="none" stroke="${C.pinkS}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" pathLength="100" stroke-dasharray="${f1(eo(k) * 100)} 200"/>`;
  });
  s += G(T(540, 860 + (1 - ent) * 500, 1, -3 + sin(lt, .3) * 1), b);
  // holding hand (left) + writing hand with pen (right)
  s += tube('M-40,1300 Q120,1220 220,1200', 80, C.pink) + G(T(236, 1190, 1.8, -50), handSoft(C.skin));
  const cur = rows.reduce((a, r, i) => t > r[2] - .3 ? i : a, 0);
  const tgt = [762 + sin(lt, 2) * 4, 720 + cur * 140 + Math.sin(lt * 14) * 3 * (t - rows[cur][2] < .4 ? 1 : 0)];
  const pen = [kf(lt, [[0, 1100], [.7, tgt[0]], [99, tgt[0]]]), lerp(1500, tgt[1], eo(prog(lt, 0, .7)))];
  s += tube(`M1120,1400 Q960,1240 ${pen[0] + 60},${pen[1] + 80}`, 80, C.blue);
  s += G(T(pen[0], pen[1], 1, 0), tube('M0,0 L70,70', 14, C.plum) + P('M-4,-4 L10,6 L6,10Z', C.ol, 2) + G(T(70, 84, 1.7, -130), handSoft(C.skin)));
  s += dashes(860, 560, 70, 3, 1, fadeIn(t, rows[3][2]));
  return s;
}

// ===================================================================== 7
// Parents with a friendly developmental psychologist.
function scene7(t, lt) {
  const z = 1 + 0.05 * eio(prog(lt, 0, 9.5));
  let s = sceneBg(C.bg, [540, 900, 440]);
  const ownT = W_(115), rT = W_(116), devT = W_(121), idT = W_(124), supT = W_(131);
  // plant + window doodle for a warm room
  
  // psychologist (right)
  const ph = [800, 690], pk = 1.06;
  const talking = Math.max(0, Math.sin(lt * 8.5)) * (0.5 + 0.5 * Math.sin(lt * 2.1)) * (1 - prog(t, ownT, ownT + .2) + prog(t, rT, rT + .2)) * (1 - prog(t, supT + .6, supT + .8));
  const pNod = sin(lt, .45) * 2;
  s += G(T(ph[0], ph[1] + pNod, pk, -4 + sin(lt, .3) * 2), adultHead({ kind: 'psych', turn: -.5, lx: -1, ly: .2, blink: blink(lt, 4), smile: .7, open: talking * .6, body: G('translate(0,128)', torso(300, 600, C.white, C.whiteS, 'none') + P('M-40,0 L0,80 L40,0 Z', C.lav, 3.4) + L('M-50,4 L-10,130 M50,4 L10,130', C.ol, 3.4) + `<rect x="58" y="120" width="44" height="12" rx="6" fill="${C.pink}" stroke="${C.ol}" stroke-width="2.6"/>`) }));
  // parents (left)
  const relax = eo(prog(t, ownT - .4, ownT + .6));
  const nodF = Math.max(0, Math.sin((lt - 1.2) * 2.6)) * 6 * (lt > 1.2 && lt < 5 ? 1 : 0);
  const nodM = Math.max(0, Math.sin((lt - 2.0) * 2.4)) * 6 * (lt > 2 && lt < 6.5 ? 1 : 0);
  const fh = [210, 690], fk = 1.0, mh = [400, 760], mk = .98;
  s += G(T(fh[0], fh[1] + nodF, fk, 3), adultHead({ kind: 'father', turn: .55, lx: 1, ly: .2, blink: blink(lt + .5, 3), smile: lerp(.25, .75, relax), concern: lerp(.5, 0, relax), body: G('translate(0,128)', torso(270, 600, C.blue, C.blueS, 'v')) }));
  s += G(T(mh[0], mh[1] + nodM, mk, 4), adultHead({ kind: 'mother', turn: .6, lx: 1, ly: .1, blink: blink(lt + 1.1, 1), smile: lerp(.25, .85, relax), concern: lerp(.55, 0, relax), raise: relax * .3, body: G('translate(0,128)', torso(250, 600, C.pink, C.pinkS)) }));
  // table
  s += P('M60,1120 L1020,1120 L1020,1180 L60,1180Z', C.lavS) + `<rect x="40" y="1170" width="1000" height="260" fill="${C.lav}" stroke="${C.ol}" stroke-width="4"/>`;
  // mother & father hands on the table; father holds mother's hand
  s += G(T(470, 1110, 1.2, -10), handSoft(C.skin)) + G(T(400, 1116, 1.2, -6), handSoft(C.skin));
  s += tube('M320,1000 Q330,1090 400,1112', 46, C.pink) + tube('M250,980 Q260,1090 330,1110', 46, C.blue) + G(T(340, 1106, 1.2, -16), handSoft(C.skin));
  // psychologist: tablet in one hand, gesturing with the other
  const gest = sin(lt, .55) * 18 + (talking > .2 ? 8 : 0);
  const pS = at(ph[0], ph[1], pk, -120, 170);
  const [pe, pH] = ik(pS, [620 + gest * .4, 970 - gest], 120, 110, -1);
  s += arm2(pS, pe, pH, 50, 44, C.white) + G(T(pH[0], pH[1], 1.3, angOf(pe, pH) - 50 + gest * .6), handOpen(C.skin));
  s += G(T(840, 1060, 1, -12), `<rect x="-90" y="-62" width="180" height="124" rx="14" fill="${C.plum}" stroke="${C.ol}" stroke-width="4"/><rect x="-76" y="-50" width="152" height="100" rx="8" fill="${C.lav}"/>` + L(`M-60,30 L-26,6 L4,16 L50,-30`, C.pinkS, 6));
  s += G(T(760, 1100, 1.3, -30), handSoft(C.skin));
  // idea bubble over the psychologist: calendar of check-ins, growth, support
  const bk = prog(t, rT - .15, rT + .35);
  const inner = G('translate(-130,4)', calendarIcon(110, 100, { ticks: Math.floor(prog(t, rT + .2, devT + .4) * 6) }))
    + G(`translate(0,4) scale(${eob(prog(t, devT - .05, devT + .4)).toFixed(3)})`, Ci(0, 0, 50, C.cream) + L('M-28,22 L-10,4 L6,12 L28,-18', C.pinkS, 6) + L('M18,-20 L30,-20 L30,-8', C.pinkS, 6))
    + G(`translate(130,4) scale(${(eob(prog(t, supT - .05, supT + .4)) * (1 + .1 * Math.max(0, Math.sin(lt * 7)))).toFixed(3)})`, heart(0, 0, 2.6, C.pink, 3.4));
  const mag = prog(t, idT, idT + 1.2);
  s += bubble(560, 470 + sin(lt, .4) * 6, 0, 0, '');
  if (bk > 0) {
    const kk = eob(clamp(bk));
    s += Ci(700, 640, 10 * kk, C.white, 3.4) + Ci(668, 606, 15 * kk, C.white, 3.4);
    s += G(T(540, 470 + sin(lt, .4) * 6, kk), `<rect x="-230" y="-100" width="460" height="200" rx="90" fill="${C.white}" stroke="${C.ol}" stroke-width="4"/>` + inner
      + (mag > 0 && mag < 1 ? G(T(lerp(-130, 130, eio(mag)), -10 + Math.sin(mag * Math.PI * 2) * 10, 1), Ci(0, 0, 26, 'rgba(255,255,255,0.5)', 5) + L('M18,18 L40,40', C.ol, 9)) : ''));
  }
  return cam(540, 860, z, s);
}

// ===================================================================== 8
// Early Support · Timely Guidance · Right Care
function scene8(t, lt) {
  let s = sceneBg(C.bg, [540, 820, 460]);
  const T1 = W_(135), T2 = W_(137), T3 = W_(141), T4 = W_(145);
  const items = [
    [T1, 'Early', 'Support', k => { const j = 1 - eo(prog(k, 0, .8)); return G(`translate(${-18 - j * 40},${-6})`, puzzle(C.pink)) + G(`translate(${22 + j * 40},${10}) rotate(90)`, puzzle(C.yellow)); }],
    [T2, 'Timely', 'Guidance', k => G('translate(0,4)', calendarIcon(130, 120, { ticks: Math.floor(clamp(k / 1.2) * 12) }))],
    [T3, 'Right', 'Care', k => { const b = 1 + .12 * Math.max(0, Math.sin(lt * 7)) ** 4; return heart(0, -16, 2.1 * b, C.pink, 4) + G('translate(-30,40) rotate(-12)', handSoft(C.skin)) + G('translate(30,40) scale(-1,1) rotate(-12)', handSoft(C.skin)); }],
  ];
  items.forEach(([tt, a, b, icon], i) => {
    const y = 520 + i * 300;
    const k = prog(t, tt - .12, tt + .5);
    const bounce = Math.max(0, Math.sin((t - T4 - i * .18) * 5)) * 18 * prog(t, T4, T4 + .2) * (1 - prog(t, T4 + 1.2, T4 + 1.5));
    if (k <= 0) { s += Ci(300, y, 128, 'none', 3, `stroke-dasharray="10 14" opacity="0.5"`); return; }
    const p = eob(k);
    s += G(T(300, y - bounce, p), Ci(0, 0, 128, C.cream) + Ci(0, 0, 112, i === 1 ? C.lav : C.halo, 0) + G('scale(1.25)', icon(t - tt)));
    const tx = eo(prog(t, tt, tt + .5));
    s += op(tx, txt(470 + (1 - tx) * 40, y - 6, a, 64, C.ol, 'Fredoka', 600, 'start') + txt(470 + (1 - tx) * 40, y + 62, b, 64, C.pinkD, 'Fredoka', 700, 'start'));
    s += dashes(300, y, 140, 3, 1, prog(t, tt + .2, tt + .5) * (1 - prog(t, tt + 1.4, tt + 1.8)));
  });
  // "reach their full potential": rising sparkles
  for (let i = 0; i < 7; i++) {
    const k = prog(t, T4 + i * .15, T4 + i * .15 + 1.6);
    if (k > 0 && k < 1) s += sparkle(160 + i * 130, 1260 - k * 900, 1.2, Math.sin(k * Math.PI));
  }
  return s;
}
function puzzle(fill) {
  return P('M-30,-30 L-8,-30 C-10,-44 10,-44 8,-30 L30,-30 L30,-8 C44,-10 44,10 30,8 L30,30 L-30,30 Z', fill, 3.6);
}

// ===================================================================== 9
// Toddler takes steps towards the parents; joy.
function scene9(t, lt, dur) {
  const z = 1.04 - 0.04 * eio(prog(lt, 0, 6));
  let s = sceneBg(C.bg, [560, 900, 450]);
  s += E(560, 1230, 470, 90, C.lav, SW) + E(560, 1222, 410, 66, C.halo, 0);
  const arrive = 4.7; // seconds into the scene when toddler reaches mum
  const wk = eio(prog(lt, .3, arrive));
  const tx = lerp(170, 560, wk);
  const walking = lt > .3 && lt < arrive;
  const ph = lt * 5.4;
  const hug = eo(prog(lt, arrive, arrive + .6));
  // parents kneeling on the right, arms open
  const happy = prog(lt, arrive + .1, arrive + .3) > .5 && lt < dur;
  const fh = [905, 690], fk = 1.0, mh = [760, 780], mk = 1.0;
  s += G(T(fh[0], fh[1] + sin(lt, .5) * 3, fk, -6), adultHead({ kind: 'father', turn: -.55, lx: -1, ly: .8, blink: blink(lt, 3), smile: 1, happy: happy ? 1 : 0, raise: .4, body: G('translate(0,128)', torso(270, 600, C.blue, C.blueS, 'v')) }));
  const encour = sin(lt, 1.2) * 10 * (1 - hug);
  // father's arm reaching / clapping
  const fS = at(fh[0], fh[1], fk, -110, 180);
  const [fe, fH] = ik(fS, [lerp(700, 640, hug) + encour, 1010 - encour], 140, 130, 1);
  s += arm2(fS, fe, fH, 48, 42, C.blue) + G(T(fH[0], fH[1], 1.25, angOf(fe, fH)), handOpen(C.skin));
  s += G(T(mh[0], mh[1] + sin(lt, .5, 1) * 3, mk, -8), adultHead({ kind: 'mother', turn: -.6, lx: -1, ly: .8, blink: blink(lt + .4, 1), smile: 1, open: lt < arrive ? .35 + .25 * Math.max(0, Math.sin(lt * 4)) : 0, happy: happy ? 1 : 0, raise: .5, body: G('translate(0,128)', torso(250, 600, C.pink, C.pinkS)) }));
  // toddler
  const bob = walking ? -Math.abs(Math.sin(ph)) * 10 : 0;
  const tilt = walking ? Math.sin(ph) * 4 : lerp(0, 6, hug);
  s += G(T(tx, 1220 + bob, .95, tilt), kid({ pose: walking ? 'walk' : 'stand', phase: ph, t: lt, blink: blink(lt, 2), smile: 1, happy: hug > .5 ? 1 : 0, mouthOpen: walking ? .5 : .8 * hug, shirt: true, armL: [-104 + hug * 30, -300 - hug * 30], armR: [104 + hug * 40, -300 - hug * 40 + Math.sin(ph) * 10 * (walking ? 1 : 0)] }));
  // mother's arms reaching out to the toddler
  const mS = at(mh[0], mh[1], mk, -100, 175), mS2 = at(mh[0], mh[1], mk, 60, 190);
  const reach = [lerp(560, tx + 110, .4 + .6 * wk) + encour * .6, lerp(1000, 1010, hug) - encour * .5];
  const [me, mH] = ik(mS, reach, 140, 140, -1);
  s += arm2(mS, me, mH, 48, 42, C.pink) + G(T(mH[0], mH[1], 1.25, angOf(me, mH)), handOpen(C.skin));
  const [me2, mH2] = ik(mS2, [reach[0] + 20, reach[1] + 60], 160, 150, 1);
  s += arm2(mS2, me2, mH2, 48, 42, C.pinkS) + G(T(mH2[0], mH2[1], 1.25, angOf(me2, mH2)), handOpen(C.skin));
  // footstep sparkles behind the toddler
  for (let i = 0; i < 4; i++) { const sx = lerp(170, 560, i / 4 + .05); if (tx > sx + 60) s += sparkle(sx, 1250, .7, .6); }
  // celebration: hearts + confetti
  if (lt > arrive - .2) {
    for (let i = 0; i < 9; i++) {
      const k = prog(lt, arrive - .2 + i * .12, arrive + 2.4 + i * .12);
      if (k <= 0 || k >= 1) continue;
      const ang = R(-160 + i * 17), r = 140 + 300 * eo(k);
      s += heart(640 + Math.cos(ang) * r, 860 + Math.sin(ang) * r * .8, (.8 + (i % 3) * .3) * Math.sin(k * Math.PI), [C.pink, C.lavS, C.yellow][i % 3], 3, Math.sin(k * Math.PI));
    }
  }
  [[200, 560], [380, 470], [980, 500], [140, 860]].forEach(([x, y], i) => { s += sparkle(x, y, 1.1, (.5 + .5 * sin(lt, .7, i)) * fadeIn(lt, .4 + i * .3)); });
  return cam(560, 900, z, s);
}

// ===================================================================== 10
// The Cub brand reveal + tagline.
function endCard(t) {
  const t0 = SCENES[9];
  const k = eio(prog(t, t0 - .5, t0 + .25));
  const r = k * 1300;
  let s = `<clipPath id="endc"><circle cx="540" cy="900" r="${f1(r)}"/></clipPath>`;
  let c = `<rect width="1080" height="1920" fill="${C.cream}"/>`;
  c += Ci(540, 880, 360, C.bg, 0);
  const lk = eo(prog(t, t0 + .1, t0 + 1.0));
  const ring = prog(t, t0 + .05, t0 + 1.1);
  if (ring > 0 && ring < 1) c += Ci(540, 880, 200 + 260 * eo(ring), 'none', 0, `stroke="${C.lavS}" stroke-width="${f1(10 * (1 - ring))}" opacity="${(1 - ring).toFixed(2)}"`);
  const ls = .86 + .14 * eob(prog(t, t0 + .1, t0 + 1.0));
  let logo;
  if (window.LOGO) {
    const maxW = 620, maxH = 460, sc = Math.min(maxW / LOGO.w, maxH / LOGO.h);
    const w = LOGO.w * sc, h = LOGO.h * sc;
    logo = `<image href="logo.png" x="${f1(-w / 2)}" y="${f1(-h / 2)}" width="${f1(w)}" height="${f1(h)}"/>`;
  } else {
    logo = txt(0, 50, 'The Cub', 150, C.ol, 'Fredoka', 700);   // placeholder until the official logo file is supplied
  }
  c += op(lk, G(T(540, 860, ls), logo));
  // tagline word by word
  const words = ['Everyone', 'Deserves', 'To', 'Be', 'Seen.'];
  meas.font = `600 62px Fredoka`;
  const sp = meas.measureText(' ').width, ws = words.map(w => meas.measureText(w).width);
  const tot = ws.reduce((a, b) => a + b, 0) + sp * (words.length - 1);
  let x = 540 - tot / 2;
  words.forEach((w, i) => {
    const a = eo(prog(t, t0 + .9 + i * .14, t0 + 1.3 + i * .14));
    c += op(a, txt(x, 1190 + (1 - a) * 22, w, 62, i === 4 ? C.pinkD : C.ol, 'Fredoka', 600, 'start'));
    x += ws[i] + sp;
  });
  const ul = eo(prog(t, t0 + 1.7, t0 + 2.3));
  c += L(`M${540 - tot / 2},1222 Q540,${1236} ${f1(540 - tot / 2 + tot * ul)},1222`, C.lavS, 6, `opacity="${ul.toFixed(2)}"`);
  const rb = fadeIn(t, t0 + 2.0, .6);
  c += op(rb, G(T(540, 1370, .8, sin(t, .4) * 4), ribbon()) + txt(540, 1470, 'World Prematurity Day', 40, C.lavD, 'Itim', 400));
  s += `<g clip-path="url(#endc)">${c}</g>`;
  return s;
}
