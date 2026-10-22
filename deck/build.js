/**
 * The Cub Way — Social Media Intern onboarding deck (10 slides, 16:9).
 * Brand sources: Brand Elements & Description (docx) + the three Instagram carousels.
 * Run:  node build.js   (after  python3 -I prep_assets.py <uploads> assets )
 */
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const sharp = require("sharp");
const React = require("react");
const RDS = require("react-dom/server");
const fi = require("react-icons/fi");
const { applyTheme } = require(process.env.PPTX_SKILL_DIR + "/scripts/apply_theme.js");

const A = (f) => path.join(__dirname, "assets", f);
const OUT = process.env.OUT || path.join(__dirname, "..", "The_Cub_Way.pptx");

// ------------------------------------------------------------------ brand
const ORANGE = "F0853E", CHARCOAL = "2B2B2B", CREAM = "FDF6EE", WHITE = "FFFFFF";
const THEME = {
  name: "The Cub",
  headFontFace: "Playfair Display",
  bodyFontFace: "Glacial Indifference",
  colors: {
    dk1: CHARCOAL, lt1: WHITE, dk2: CHARCOAL, lt2: CREAM,
    accent1: ORANGE, accent2: CHARCOAL, accent3: CREAM, accent4: ORANGE, accent5: CHARCOAL, accent6: CREAM,
    hlink: ORANGE, folHlink: CHARCOAL,
  },
};
const LABEL = "Lexend"; // third brand font: small labels, tags, counters
const HEAD = "+mj-lt"; // theme heading font (Playfair Display) for non-title text

const W = 13.333, H = 7.5, MX = 0.6, RIGHT = W - MX;

// ---------------------------------------------------------------- helpers
async function icon(name, color, px = 256) {
  let svg = RDS.renderToStaticMarkup(React.createElement(fi[name], { size: String(px), strokeWidth: 2 }));
  svg = svg.replace(/currentColor/g, "#" + color);
  const buf = await sharp(Buffer.from(svg), { density: 300 }).resize(px, px).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
async function variant(src, dst, { flop = false, flip = false } = {}) {
  let s = sharp(A(src));
  if (flop) s = s.flop();
  if (flip) s = s.flip();
  await s.toFile(A(dst));
}
async function plate(dst, w, h, r, fill) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><rect width="${w}" height="${h}" rx="${r}" fill="#${fill}"/></svg>`;
  await sharp(Buffer.from(svg)).png().toFile(A(dst));
}
const POST_AR = 855 / 1069;

async function main() {
  // derived images
  await variant("blob_cream_d.png", "blob_cream_d_tr.png", { flop: true });
  await plate("plate_white.png", 940, 250, 70, WHITE);

  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.title = "The Cub Way";
  pres.subject = "Social Media Intern onboarding";
  pres.author = "The Cub";
  pres.company = "The Cub";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;
  const RR = pres.shapes.ROUNDED_RECTANGLE;

  const ic = {};
  for (const [k, n, col] of [
    ["usersW", "FiUsers", WHITE], ["smileW", "FiSmile", WHITE], ["heartW", "FiHeart", WHITE], ["eyeW", "FiEye", WHITE],
    ["homeW", "FiHome", WHITE], ["briefW", "FiBriefcase", WHITE],
    ["sunW", "FiSun", WHITE], ["msgW", "FiMessageCircle", WHITE], ["shieldW", "FiUserCheck", WHITE], ["awardW", "FiAward", WHITE],
    ["checkW", "FiCheck", WHITE], ["xW", "FiX", WHITE], ["playW", "FiPlay", WHITE], ["imageW", "FiImage", WHITE],
  ]) ic[k] = await icon(n, col);

  // ----------------------------------------------------------- layouts
  const counter = [
    { image: { x: 11.85, y: 6.28, w: 1.483, h: 1.22, path: A("quarter.png") } },
    { text: { text: "/10", options: { x: 12.62, y: 6.76, w: 0.6, h: 0.4, fontFace: LABEL, fontSize: 16, bold: true, color: WHITE, valign: "middle", margin: 0 } } },
    { line: { x: 12.15, y: 7.2, w: 0.75, h: 0, line: { color: WHITE, width: 1.25, endArrowType: "arrow" } } },
  ];
  const slideNum = { x: 11.95, y: 6.76, w: 0.67, h: 0.4, fontFace: LABEL, fontSize: 16, bold: true, color: WHITE, align: "right", valign: "middle", margin: 0 };
  const titleBox = (color) => ({
    placeholder: {
      options: { name: "title", type: "title", x: 0.62, y: 0.5, w: 8.7, h: 1.4, fontSize: 36, bold: true, color, align: "left", valign: "top", margin: 0, lineSpacingMultiple: 0.95 },
      text: "",
    },
  });

  pres.defineSlideMaster({
    title: "Cover", background: { color: C.background1 },
    objects: [
      { image: { x: 0, y: 5.05, w: 4.7, h: 2.45, path: A("blob_cream_a.png") } },
      { image: { x: 6.95, y: 0, w: 7.715, h: 7.5, path: A("blob_orange_b.png") } },
      { text: { text: "/10", options: { x: 12.62, y: 6.76, w: 0.6, h: 0.4, fontFace: LABEL, fontSize: 16, bold: true, color: WHITE, valign: "middle", margin: 0 } } },
      { line: { x: 12.15, y: 7.2, w: 0.75, h: 0, line: { color: WHITE, width: 1.25, endArrowType: "arrow" } } },
      {
        placeholder: {
          options: { name: "title", type: "title", x: 0.7, y: 2.1, w: 5.7, h: 3.0, fontSize: 84, bold: true, color: C.text1, align: "left", valign: "top", margin: 0, lineSpacingMultiple: 0.88 },
          text: "",
        },
      },
    ],
    slideNumber: slideNum,
  });
  pres.defineSlideMaster({
    title: "Light", background: { color: C.background1 },
    objects: [
      { image: { x: 0.2, y: 0.4, w: 0.36, h: 0.39, path: A("spark.png") } },
      ...counter,
      { image: { x: 0.6, y: 6.86, w: 1.95, h: 0.366, path: A("logo_horizontal.png") } },
      titleBox(C.text1),
    ],
    slideNumber: slideNum,
  });
  pres.defineSlideMaster({
    title: "Orange", background: { color: C.accent1 },
    objects: [
      { image: { x: 0.2, y: 0.4, w: 0.36, h: 0.39, path: A("spark.png") } },
      { text: { text: "/10", options: { x: 12.62, y: 6.76, w: 0.6, h: 0.4, fontFace: LABEL, fontSize: 16, bold: true, color: WHITE, valign: "middle", margin: 0 } } },
      { line: { x: 12.15, y: 7.2, w: 0.75, h: 0, line: { color: WHITE, width: 1.25, endArrowType: "arrow" } } },
      { image: { x: 0.45, y: 6.72, w: 2.25, h: 0.6, path: A("plate_white.png") } },
      { image: { x: 0.65, y: 6.855, w: 1.85, h: 0.347, path: A("logo_horizontal.png") } },
      titleBox(C.background1),
    ],
    slideNumber: slideNum,
  });

  // ------------------------------------------------------ small builders
  const T = (extra) => ({ isTextBox: true, margin: 0, valign: "top", color: C.text1, fontSize: 16, ...extra });
  const pill = (s, text, { x, y, w, h = 0.36, fill = C.accent1, color = C.background1, size = 11, name = "Tag", body = false }) =>
    s.addText(text, {
      shape: RR, rectRadius: h / 2, x, y, w, h, fill: { color: fill }, color, ...(body ? { bold: false } : { fontFace: LABEL, bold: true, charSpacing: 1.2 }), fontSize: size,
      align: "center", valign: "middle", margin: 0, objectName: name,
    });
  const tag = (s, text, { onOrange = false } = {}) => {
    const w = 0.55 + 0.118 * text.length;
    pill(s, text, { x: RIGHT - w, y: 0.55, w, fill: onOrange ? C.background1 : C.accent1, color: onOrange ? C.text1 : C.background1, name: "Section tag" });
  };
  const card = (s, x, y, w, h, fill, name, r = 0.22) =>
    s.addShape(RR, { x, y, w, h, fill: { color: fill }, rectRadius: r, objectName: name });
  const badge = (s, img, x, y, d, name, fill = C.accent1, pad = 0.27) => {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, objectName: name + " circle" });
    const p = d * pad;
    s.addImage({ data: img, x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, altText: name });
  };
  const numDot = (s, n, x, y, d = 0.34, fill = C.accent1) =>
    s.addText(String(n), { shape: pres.shapes.OVAL, x, y, w: d, h: d, fill: { color: fill }, color: C.background1, fontFace: LABEL, fontSize: 12, bold: true, align: "center", valign: "middle", margin: 0, objectName: "Number " + n });
  const setTitle = (s, l1, l2, onOrange = false) =>
    s.addText(
      [
        { text: l1, options: { color: onOrange ? C.background1 : C.text1, breakLine: true } },
        { text: l2, options: { color: onOrange ? C.text1 : C.accent1 } },
      ],
      { placeholder: "title" }
    );
  const small = (s, text, x, y, w, extra = {}) =>
    s.addText(text, T({ x, y, w, h: 0.3, fontFace: LABEL, fontSize: 11, bold: true, charSpacing: 1.4, ...extra }));

  // =====================================================================
  // 1 — Cover
  pres.addSection({ title: "Welcome" });
  let s = pres.addSlide({ masterName: "Cover", sectionTitle: "Welcome" });
  s.addImage({ path: A("dots_cream.png"), x: 5.2, y: 0.55, w: 1.0, h: 0.947, altText: "Dot pattern" });
  s.addShape(RR, { x: 8.55, y: 1.45, w: 4.3, h: 4.55, fill: { color: C.background1 }, rectRadius: 0.4, objectName: "Logo plate" });
  s.addImage({ path: A("logo_full.png"), x: 8.9, y: 2.05, w: 3.6, h: 3.085, altText: "The Cub logo: tiger cub face and wordmark" });
  s.addImage({ path: A("spark.png"), x: 0.22, y: 1.95, w: 0.5, h: 0.54, altText: "Spark" });
  pill(s, "SOCIAL MEDIA INTERN ONBOARDING", { x: 0.7, y: 1.1, w: 4.6, h: 0.4, name: "Cover tag" });
  s.addText([{ text: "The Cub", options: { color: C.text1, breakLine: true } }, { text: "Way", options: { color: C.accent1 } }], { placeholder: "title" });
  s.addText([{ text: "How we look, sound and feel", options: { breakLine: true } }, { text: "on social media." }], T({ x: 0.7, y: 5.2, w: 5.4, h: 0.9, fontSize: 22 }));
  s.addNotes(
    "Welcome the intern. 'The Cub Way' is our short guide to how The Cub looks, sounds and feels online. " +
      "Everything here comes from our brand guide and our own Instagram posts. Use it as a reference while you create content. " +
      "Walk-through order: who we are, our voice, how we write, our language, colours and fonts, design style, visuals and reels, do's and don'ts, examples."
  );

  // =====================================================================
  // 2 — Who we are & who we talk to
  pres.addSection({ title: "Who we are" });
  s = pres.addSlide({ masterName: "Light", sectionTitle: "Who we are" });
  s.addImage({ path: A("blob_cream_d_tr.png"), x: 8.55, y: 0, w: 4.78, h: 2.65, altText: "Soft cream blob" });
  tag(s, "ABOUT THE CUB");
  setTitle(s, "We see the child", "before the label.");
  small(s, "WHO WE ARE", MX, 2.05, 3);
  s.addText("A multidisciplinary centre for children and adolescents.", T({ x: MX, y: 2.4, w: 5.6, h: 0.75, fontSize: 18 }));
  const who = [
    [ic.usersW, "Experts, together", "Psychology, speech & language, OT and special education."],
    [ic.smileW, "The whole child", "Communication, learning, emotions and daily life."],
    [ic.heartW, "Parents are partners", "Families know their child best. We help them feel confident."],
    [ic.eyeW, "Restraint over labels", "A diagnosis is a last resort, used only when it truly helps."],
  ];
  who.forEach(([img, h1, d1], i) => {
    const y = 3.25 + i * 0.86;
    badge(s, img, MX, y + 0.02, 0.56, h1);
    s.addText(h1, T({ x: 1.4, y, w: 4.8, h: 0.3, fontSize: 17, bold: true }));
    s.addText(d1, T({ x: 1.4, y: y + 0.3, w: 5.2, h: 0.45, fontSize: 14 }));
  });
  small(s, "WHO WE TALK TO", 6.95, 2.05, 3);
  const aud = [
    [ic.homeW, "Parents & caregivers", "They want clear, kind answers. We help them feel understood and confident."],
    [ic.briefW, "Clinicians & professionals", "SLPs, OTs, paediatricians. They want practical, clinical detail."],
  ];
  aud.forEach(([img, h1, d1], i) => {
    const y = 2.45 + i * 2.0;
    card(s, 6.95, y, 5.78, 1.85, C.background2, h1 + " card");
    badge(s, img, 7.25, y + 0.32, 0.72, h1);
    s.addText(h1, T({ x: 8.2, y: y + 0.3, w: 4.35, h: 0.4, fontFace: HEAD, fontSize: 22, bold: true }));
    s.addText(d1, T({ x: 8.2, y: y + 0.82, w: i === 0 ? 3.2 : 4.3, h: 0.9, fontSize: 16 }));
  });
  s.addImage({ path: A("doodle_parent_child.png"), x: 11.5, y: 2.85, w: 1.1, h: 1.052, altText: "Hand-drawn doodle of a parent crouching to talk with a child" });
  s.addNotes(
    "We are a multidisciplinary centre for children and adolescents. Our big idea: look at the whole child before reaching for a label. " +
      "Two audiences. Parents and caregivers: they want clear, kind answers and often feel judged. Clinicians and professionals: they want practical detail (see our OSIT workshop posts). " +
      "Ask the intern: who is this post for? That answer decides the words you choose."
  );

  // =====================================================================
  // 3 — Voice & tone
  s = pres.addSlide({ masterName: "Orange", sectionTitle: "Who we are" });
  tag(s, "VOICE & TONE", { onOrange: true });
  setTitle(s, "Warm. Clear.", "Never judging.", true);
  const traits = [
    [ic.sunW, "Warm", "We lead with care, never with fear.", "“A little understanding can go a long way.”"],
    [ic.msgW, "Clear", "Simple words. One idea at a time.", "“Give clear, simple instructions.”"],
    [ic.shieldW, "Respectful", "We never blame a child or a parent.", "“Struggling doesn’t mean not trying.”"],
    [ic.awardW, "Expert", "We know the science and explain it simply.", "“Look beyond the presenting concern.”"],
  ];
  const cw = 2.85, gap = (12.133 - 4 * cw) / 3;
  traits.forEach(([img, name, d1, q], i) => {
    const x = MX + i * (cw + gap), y = 2.05;
    card(s, x, y, cw, 3.7, C.background1, name + " card");
    badge(s, img, x + 0.3, y + 0.3, 0.72, name);
    s.addText(name, T({ x: x + 0.3, y: y + 1.17, w: 2.3, h: 0.45, fontFace: HEAD, fontSize: 24, bold: true }));
    s.addText(d1, T({ x: x + 0.3, y: y + 1.68, w: 2.3, h: 0.75, fontSize: 15.5 }));
    s.addShape(pres.shapes.LINE, { x: x + 0.3, y: y + 2.55, w: cw - 0.6, h: 0, line: { color: C.accent1, width: 1.25, dashType: "sysDot" } });
    s.addText("SOUNDS LIKE", T({ x: x + 0.3, y: y + 2.7, w: 2.3, h: 0.22, fontFace: LABEL, fontSize: 10, bold: true, charSpacing: 1.4 }));
    s.addText(q, T({ x: x + 0.3, y: y + 2.98, w: 2.3, h: 0.65, fontFace: HEAD, italic: true, fontSize: 14.5 }));
  });
  pill(s, "Sound like a kind expert, not a textbook.", { x: MX, y: 6.0, w: 5.9, h: 0.5, fill: C.text1, color: C.background1, size: 15, name: "Voice reminder" });
  s.addNotes(
    "Four words to remember: warm, clear, respectful, expert. Each quote on the cards is taken or adapted from our own posts. " +
      "The test: would a worried parent feel judged by this line? If yes, rewrite it. Would a clinician trust it? It should still be accurate and evidence-informed."
  );

  // =====================================================================
  // 4 — Hooks, headlines, captions
  pres.addSection({ title: "How we write" });
  s = pres.addSlide({ masterName: "Light", sectionTitle: "How we write" });
  s.addImage({ path: A("blob_cream_d_tr.png"), x: 8.55, y: 0, w: 4.78, h: 2.65, altText: "Soft cream blob" });
  tag(s, "HOOKS · HEADLINES · CAPTIONS");
  setTitle(s, "Challenge the label.", "Then offer help.");
  const cy = 2.1, chh = 4.15, cwid = 3.85, cgap = (12.133 - 3 * cwid) / 2;
  const cx = (i) => MX + i * (cwid + cgap);
  // hooks
  card(s, cx(0), cy, cwid, chh, C.background2, "Hooks card");
  s.addText("Hooks", T({ x: cx(0) + 0.25, y: cy + 0.22, w: 3.3, h: 0.4, fontFace: HEAD, fontSize: 24, bold: true }));
  s.addText("Open with a myth or a question.", T({ x: cx(0) + 0.25, y: cy + 0.7, w: 3.4, h: 0.3, fontSize: 15 }));
  [
    ["QUESTION A LABEL", "“Struggling Doesn’t Mean Not Trying.”"],
    ["WIDEN THE VIEW", "“ADHD is more than just being ‘Hyper’”"],
    ["ASK SIMPLY", "“What can help?”"],
  ].forEach(([lab, q], i) => {
    const y = cy + 1.15 + i * 1.0;
    card(s, cx(0) + 0.25, y, cwid - 0.5, 0.88, C.background1, "Hook example " + (i + 1), 0.16);
    s.addText(lab, T({ x: cx(0) + 0.45, y: y + 0.12, w: 3.0, h: 0.2, fontFace: LABEL, fontSize: 10, bold: true, charSpacing: 1.2 }));
    s.addText(q, T({ x: cx(0) + 0.45, y: y + 0.37, w: 3.1, h: 0.5, fontFace: HEAD, italic: true, fontSize: 14 }));
  });
  // headlines
  card(s, cx(1), cy, cwid, chh, C.background2, "Headlines card");
  s.addText("Headlines", T({ x: cx(1) + 0.25, y: cy + 0.22, w: 3.3, h: 0.4, fontFace: HEAD, fontSize: 24, bold: true }));
  s.addText("Two lines: setup, then payoff.", T({ x: cx(1) + 0.25, y: cy + 0.7, w: 3.4, h: 0.3, fontSize: 15 }));
  card(s, cx(1) + 0.25, cy + 1.15, cwid - 0.5, 1.6, C.background1, "Headline example", 0.16);
  s.addImage({ path: A("spark.png"), x: cx(1) + 0.33, y: cy + 1.23, w: 0.26, h: 0.28, altText: "Spark" });
  s.addText(
    [
      { text: "Understanding Comes", options: { color: C.text1, fontSize: 20, breakLine: true } },
      { text: "Before Labelling.", options: { color: C.accent1, fontSize: 26 } },
    ],
    T({ x: cx(1) + 0.55, y: cy + 1.5, w: 3.0, h: 1.1, fontFace: HEAD, bold: true, lineSpacingMultiple: 0.95 })
  );
  [
    ["Charcoal setup, orange payoff"],
    ["2–5 words a line"],
    ["Playfair Display Bold"],
  ].forEach(([t1], i) => {
    const y = cy + 3.0 + i * 0.37;
    badge(s, ic.checkW, cx(1) + 0.25, y, 0.3, "Rule " + (i + 1), C.accent1, 0.2);
    s.addText(t1, T({ x: cx(1) + 0.7, y: y + 0.02, w: 2.95, h: 0.28, fontSize: 14.5 }));
  });
  // captions
  card(s, cx(2), cy, cwid, chh, C.background2, "Captions card");
  s.addText("Captions", T({ x: cx(2) + 0.25, y: cy + 0.22, w: 3.3, h: 0.4, fontFace: HEAD, fontSize: 24, bold: true }));
  s.addText("Short, kind, one next step.", T({ x: cx(2) + 0.25, y: cy + 0.7, w: 3.4, h: 0.3, fontSize: 15 }));
  [
    ["Hook", "One line that names the myth or feeling."],
    ["Explain", "Two or three short lines, plain words."],
    ["Reassure", "End with hope: “Every child deserves to be understood.”"],
    ["Next step", "One action, e.g. thecub.co.in."],
  ].forEach(([h1, d1], i) => {
    const y = cy + 1.15 + i * 0.76;
    numDot(s, i + 1, cx(2) + 0.25, y + 0.02, 0.4);
    s.addText(h1, T({ x: cx(2) + 0.8, y, w: 2.8, h: 0.26, fontSize: 16, bold: true }));
    s.addText(d1, T({ x: cx(2) + 0.8, y: y + 0.27, w: 2.85, h: 0.46, fontSize: 14 }));
  });
  s.addNotes(
    "Hooks and headlines follow one pattern in our posts: question the label, then offer help. " +
      "Examples are real: 'Struggling Doesn't Mean Not Trying.', 'ADHD is more than just being Hyper', 'What can help?'. " +
      "Headline recipe: line one sets up (charcoal), line two pays off (orange). " +
      "Caption recipe is based on how our ADHD and Learning Disability carousels flow: hook, explain, reassure, one next step."
  );

  // =====================================================================
  // 5 — Language & sentences
  s = pres.addSlide({ masterName: "Orange", sectionTitle: "How we write" });
  tag(s, "LANGUAGE & SENTENCES", { onOrange: true });
  setTitle(s, "Short sentences.", "Soft, simple words.", true);
  card(s, MX, 2.05, 6.55, 3.75, C.background1, "Sentence rules card");
  s.addText("How our sentences sound", T({ x: MX + 0.3, y: 2.27, w: 5.9, h: 0.4, fontFace: HEAD, fontSize: 22, bold: true }));
  [
    ["Short and plain", "“Give clear, simple instructions.”"],
    ["Soft, not absolute (use may and can)", "“…may sometimes reflect difficulties with attention.”"],
    ["About needs, not faults", "“What they often need is the right kind of support.”"],
    ["Lists of 4–6 short points", "“Attention · Impulse control · Organisation”"],
  ].forEach(([h1, ex], i) => {
    const y = 2.92 + i * 0.7;
    numDot(s, i + 1, MX + 0.3, y + 0.06, 0.38);
    s.addText(h1, T({ x: MX + 0.9, y, w: 5.4, h: 0.28, fontSize: 16.5, bold: true }));
    s.addText(ex, T({ x: MX + 0.9, y: y + 0.29, w: 5.4, h: 0.3, fontFace: HEAD, italic: true, fontSize: 14 }));
  });
  // words we use
  card(s, 7.4, 2.05, 5.33, 1.8, C.background1, "Words we use card");
  s.addText("Words we use", T({ x: 7.7, y: 2.25, w: 4.7, h: 0.4, fontFace: HEAD, fontSize: 20, bold: true }));
  const chip = (txt, x, y, w, fill, color, name) =>
    s.addText(txt, { shape: RR, rectRadius: 0.17, x, y, w, h: 0.34, fill: { color: fill }, color, fontSize: 14, align: "center", valign: "middle", margin: 0, objectName: name });
  [["understand", 1.3, 7.7, 2.8], ["support", 1.05, 9.15, 2.8], ["strengths", 1.2, 10.35, 2.8], ["every child", 1.4, 7.7, 3.27], ["“What would help them?”", 2.95, 9.25, 3.27]]
    .forEach(([t1, w1, x1, y1]) => chip(t1, x1, y1, w1, C.background2, C.text1, "Word " + t1));
  // words we only quote
  card(s, 7.4, 4.0, 5.33, 1.8, C.text1, "Words we quote card");
  s.addText("Words we only quote", T({ x: 7.7, y: 4.2, w: 4.7, h: 0.4, fontFace: HEAD, fontSize: 20, bold: true, color: C.background1 }));
  [["“lazy”", 0.85, 7.7], ["“careless”", 1.2, 8.7], ["“not trying”", 1.4, 10.05], ["“hyper”", 0.95, 11.6]]
    .forEach(([t1, w1, x1]) => chip(t1, x1, 4.75, w1, C.accent1, C.text1, "Quoted " + t1));
  s.addText("Only to challenge them, never to describe a child.", T({ x: 7.7, y: 5.22, w: 4.8, h: 0.3, fontSize: 14, color: C.background1 }));
  // style details
  [
    [MX, 4.3, "British spelling: organisation, labelling"],
    [5.1, 4.9, "Dates and prices: 5th & 6th Dec. 2026 · ₹17,499"],
    [10.2, 2.1, "Web: thecub.co.in"],
  ].forEach(([x, w, t1], i) => pill(s, t1, { x, y: 6.0, w, h: 0.46, fill: C.background1, color: C.text1, size: 14, name: "Style detail " + (i + 1), body: true }));
  s.addNotes(
    "Short sentences, simple words. Notice how often our posts say 'may' and 'can': 'may sometimes reflect', 'may struggle with'. We never state things as absolute facts about a child. " +
      "Words like lazy, careless and not trying only appear inside quote marks, to challenge them. " +
      "Spelling is British (organisation, labelling, individualised, paediatricians). Dates and prices follow the workshop posts. Parent posts explain terms simply; clinician posts can use clinical terms."
  );

  // =====================================================================
  // 6 — Colours & fonts
  pres.addSection({ title: "How we look" });
  s = pres.addSlide({ masterName: "Light", sectionTitle: "How we look" });
  s.addImage({ path: A("blob_cream_d_tr.png"), x: 8.55, y: 0, w: 4.78, h: 2.65, altText: "Soft cream blob" });
  tag(s, "COLOURS & FONTS");
  setTitle(s, "Warm orange.", "Calm charcoal.");
  const sw = [
    ["The Cub Orange", "#F0853E", "Accents, labels, icons, CTAs", C.accent1, false],
    ["Charcoal", "#2B2B2B", "Headlines, backgrounds, wordmark", C.text1, false],
    ["Cream", "#FDF6EE", "Backgrounds, cards, panels", C.background2, true],
    ["White", "#FFFFFF", "Cards, digital UI, breathing space", C.background1, true],
  ];
  const swW = 1.65, swG = 0.18;
  sw.forEach(([n, hex, use, fill, border], i) => {
    const x = MX + i * (swW + swG);
    s.addShape(RR, { x, y: 2.1, w: swW, h: 2.2, fill: { color: fill }, line: border ? { color: "E3D9CF", width: 1 } : undefined, rectRadius: 0.2, objectName: n + " swatch" });
    s.addText(n, T({ x, y: 4.45, w: swW, h: 0.28, fontSize: 15, bold: true }));
    s.addText(hex, T({ x, y: 4.76, w: swW, h: 0.25, fontFace: LABEL, fontSize: 12 }));
    s.addText(use, T({ x, y: 5.08, w: swW, h: 0.6, fontSize: 13.5 }));
  });
  s.addText("Orange leads. Charcoal is for text. Cream and white give space.", T({ x: MX, y: 5.95, w: 7.1, h: 0.4, fontSize: 16, bold: true }));
  const fonts = [
    ["Playfair Display", "Headlines", "Understanding Comes", { fontFace: HEAD, bold: true, fontSize: 26 }],
    ["Glacial Indifference", "Body text and lists", "Give clear, simple instructions.", { fontSize: 20 }],
    ["Lexend", "Labels and tags", "AWARENESS SERIES", { fontFace: LABEL, bold: true, fontSize: 16, charSpacing: 1.5 }],
  ];
  fonts.forEach(([n, role, sample, st], i) => {
    const y = 2.1 + i * 1.38;
    card(s, 8.1, y, 4.63, 1.24, C.background2, n + " card", 0.18);
    s.addText([{ text: n, options: { bold: true } }, { text: "  ·  " + role, options: {} }], T({ x: 8.35, y: y + 0.17, w: 4.2, h: 0.28, fontSize: 14 }));
    s.addText(sample, T({ x: 8.35, y: y + 0.52, w: 4.2, h: 0.55, valign: "middle", ...st }));
  });
  s.addNotes(
    "Four colours: The Cub Orange (#F0853E) for accents, labels, icons and calls to action; Charcoal (#2B2B2B) for headlines, backgrounds and the wordmark; Cream (#FDF6EE) for backgrounds, cards and panels; White for cards, digital UI and breathing space. " +
      "Three fonts: Playfair Display for headlines, Glacial Indifference for body text, Lexend for small labels and tags. Do not add other colours or fonts."
  );

  // =====================================================================
  // 7 — Design style (anatomy of a post)
  s = pres.addSlide({ masterName: "Light", sectionTitle: "How we look" });
  tag(s, "DESIGN STYLE");
  setTitle(s, "Every post", "looks like us.");
  const ph = 4.2, pw = ph * POST_AR, px1 = 5.7, px2 = px1 + pw + 0.3, py = 1.95;
  s.addImage({ path: A("post_c5_1.png"), x: px1, y: py, w: pw, h: ph, altText: "The Cub Awareness Series cover slide" });
  s.addImage({ path: A("post_c5_2.png"), x: px2, y: py, w: pw, h: ph, altText: "The Cub Awareness Series content slide on orange" });
  const mk = (n, fx, fy) => numDot(s, n, px1 + fx * pw - 0.17, py + fy * ph - 0.17, 0.34);
  mk(1, 0.2, 0.075); mk(2, 0.6, 0.09); mk(3, 0.1, 0.3); mk(4, 0.04, 0.63); mk(5, 0.93, 0.5); mk(6, 0.8, 0.95);
  s.addText("Cover slide: white", T({ x: px1, y: 6.27, w: pw, h: 0.3, fontSize: 13, align: "center" }));
  s.addText("Content slide: orange", T({ x: px2, y: 6.27, w: pw, h: 0.3, fontSize: 13, align: "center" }));
  [
    ["Logo", "Top-left on cover slides, on white."],
    ["Tag pill", "Names the series, e.g. Awareness Series."],
    ["Rounded photo", "Soft corners. One calm picture."],
    ["Two-tone headline", "Playfair Bold. Charcoal setup, orange payoff."],
    ["Warm extras", "Blobs, dots and sparks. Keep them light."],
    ["Page counter", "Orange corner and arrow on every slide."],
  ].forEach(([h1, d1], i) => {
    const y = 2.0 + i * 0.73;
    numDot(s, i + 1, MX, y + 0.04, 0.36);
    s.addText(h1, T({ x: MX + 0.55, y, w: 4.2, h: 0.28, fontSize: 16, bold: true }));
    s.addText(d1, T({ x: MX + 0.55, y: y + 0.29, w: 4.35, h: 0.4, fontSize: 14 }));
  });
  s.addNotes(
    "Anatomy of a Cub post, using our ADHD Awareness carousel. Walk through the six numbered parts. " +
      "Rhythm: a white cover slide, then alternate between white and orange slides so the swipe feels lively. Every slide has the page counter in the bottom-right corner. " +
      "Special days (like Learning Disability Month) use a textured paper background, big numbers and hand-drawn doodles, but the same colours, fonts and voice."
  );

  // =====================================================================
  // 8 — Visuals, reels & multimedia
  s = pres.addSlide({ masterName: "Orange", sectionTitle: "How we look" });
  tag(s, "VISUALS · REELS · MORE", { onOrange: true });
  setTitle(s, "Same look.", "Every format.", true);
  const vy = 2.05, vh = 3.85, vw = 3.85, vg = (12.133 - 3 * vw) / 2;
  const vx = (i) => MX + i * (vw + vg);
  // photos
  card(s, vx(0), vy, vw, vh, C.background1, "Photos card");
  s.addImage({ path: A("photo_blocks.png"), x: vx(0) + 0.45, y: vy + 0.3, w: 1.5, h: 2.248, altText: "Photo in a rounded frame, as used in our posts" });
  s.addImage({ path: A("doodle_question.png"), x: vx(0) + 2.15, y: vy + 0.38, w: 1.37, h: 2.157, altText: "Hand-drawn doodle of a puzzled child with a question mark" });
  s.addText("Photos and drawings", T({ x: vx(0) + 0.25, y: vy + 2.62, w: 3.4, h: 0.32, fontFace: HEAD, fontSize: 19, bold: true }));
  s.addText("Calm photos in rounded frames. Hand-drawn doodles for tender topics. White line icons on orange.", T({ x: vx(0) + 0.25, y: vy + 3.0, w: 3.35, h: 0.8, fontSize: 14 }));
  // carousels
  card(s, vx(1), vy, vw, vh, C.background1, "Carousels card");
  const mw = 1.05, mh = mw / POST_AR;
  ["post_c5_1.png", "post_c5_2.png", "post_c5_3.png"].forEach((f, i) =>
    s.addImage({ path: A(f), x: vx(1) + 0.25 + i * (mw + 0.1), y: vy + 0.25 + 0.4, w: mw, h: mh, altText: "Carousel slide " + (i + 1) })
  );
  s.addText("Carousels", T({ x: vx(1) + 0.25, y: vy + 2.62, w: 3.4, h: 0.32, fontFace: HEAD, fontSize: 19, bold: true }));
  s.addText("5–6 slides, one idea each. Alternate white and orange. Counter and arrow on every slide.", T({ x: vx(1) + 0.25, y: vy + 3.0, w: 3.35, h: 0.8, fontSize: 14 }));
  // reels
  card(s, vx(2), vy, vw, vh, C.background1, "Reels card");
  s.addShape(pres.shapes.OVAL, { x: vx(2) + 1.25, y: vy + 0.45, w: 1.35, h: 1.35, fill: { color: C.accent1 }, objectName: "Play circle" });
  s.addImage({ data: ic.playW, x: vx(2) + 1.62, y: vy + 0.82, w: 0.6, h: 0.6, altText: "Play icon" });
  [[C.accent1, "Orange"], [C.text1, "Charcoal"], [C.background2, "Cream"]].forEach(([c1, n1], i) =>
    s.addShape(pres.shapes.OVAL, { x: vx(2) + 1.1 + i * 0.55, y: vy + 2.0, w: 0.4, h: 0.4, fill: { color: c1 }, line: { color: "E3D9CF", width: 1 }, objectName: n1 + " dot" })
  );
  s.addText("Reels and video", T({ x: vx(2) + 0.25, y: vy + 2.62, w: 3.4, h: 0.32, fontFace: HEAD, fontSize: 19, bold: true }));
  s.addText("Same colours, fonts and calm voice. Logo on white. End with thecub.co.in.", T({ x: vx(2) + 0.25, y: vy + 3.0, w: 3.35, h: 0.8, fontSize: 14 }));
  // events & collabs strip
  s.addText("Event posts:", T({ x: MX, y: 6.08, w: 1.4, h: 0.4, fontSize: 15, bold: true, valign: "middle" }));
  [["Price tags in charcoal pills", 2.95], ["QR code to register", 2.3], ["Partner logos on a white plate", 3.3]].forEach(([t1, w1], i) =>
    pill(s, t1, { x: 2.0 + [0, 3.1, 5.55][i], y: 6.08, w: w1, h: 0.4, fill: C.text1, color: C.background1, size: 12, name: "Event detail " + (i + 1) })
  );
  s.addNotes(
    "Photos: soft rounded frames, calm and simple; hand-drawn doodles for sensitive topics; white line icons on orange. " +
      "Carousels are our main format: five or six slides, one idea each, alternating white and orange. " +
      "Our references do not include a reel, so apply the same system in motion: same colours and fonts, same calm voice, logo on white, finish with thecub.co.in. Check new reel ideas with the team lead until we have a reel template. " +
      "Event posts add charcoal price pills with orange labels, a QR code to register, and partner logos on a white plate (as in the OSIT workshop posts)."
  );

  // =====================================================================
  // 9 — Do's and don'ts
  pres.addSection({ title: "Put it into practice" });
  s = pres.addSlide({ masterName: "Light", sectionTitle: "Put it into practice" });
  s.addImage({ path: A("blob_cream_d_tr.png"), x: 8.55, y: 0, w: 4.78, h: 2.65, altText: "Soft cream blob" });
  tag(s, "DO'S & DON'TS");
  setTitle(s, "What to do,", "what to avoid.");
  const dw = 5.95, dy = 2.05, dh = 4.15;
  card(s, MX, dy, dw, dh, C.background2, "Do card");
  card(s, MX + dw + 0.233, dy, dw, dh, C.text1, "Don't card");
  s.addText("Do", T({ x: MX + 0.3, y: dy + 0.2, w: 2, h: 0.4, fontFace: HEAD, fontSize: 24, bold: true }));
  s.addText("Don’t", T({ x: MX + dw + 0.533, y: dy + 0.2, w: 2, h: 0.4, fontFace: HEAD, fontSize: 24, bold: true, color: C.background1 }));
  const dos = [
    "Open with a myth or a question",
    "Use short, plain sentences",
    "Say “may” and “can”",
    "End with reassurance and thecub.co.in",
    "Use our colours, fonts and the real logo",
    "Proofread every slide before posting",
  ];
  const donts = [
    "Blame a child or a parent",
    "Label or diagnose in a post",
    "Use scary hooks: “5 signs you can’t ignore!”",
    "Use jargon in parent posts",
    "Add new colours, fonts or a redrawn logo",
    "Crowd a slide or copy old text across",
  ];
  dos.forEach((t1, i) => {
    const y = dy + 0.8 + i * 0.54;
    badge(s, ic.checkW, MX + 0.3, y, 0.4, "Do " + (i + 1), C.accent1, 0.2);
    s.addText(t1, T({ x: MX + 0.9, y, w: 4.85, h: 0.4, fontSize: 16.5, valign: "middle" }));
  });
  donts.forEach((t1, i) => {
    const y = dy + 0.8 + i * 0.54;
    badge(s, ic.xW, MX + dw + 0.533, y, 0.4, "Don't " + (i + 1), C.accent1, 0.2);
    s.addText(t1, T({ x: MX + dw + 1.133, y, w: 4.7, h: 0.4, fontSize: 16.5, valign: "middle", color: C.background1 }));
  });
  s.addNotes(
    "The quick reference. Do: open with a myth or question, short plain sentences, may and can, end with reassurance and our website, use the brand colours, fonts and the real logo, proofread. " +
      "Don't: blame, label or diagnose, use scary or clickbait hooks, use jargon in parent posts, add new colours or fonts or redraw the logo, crowd slides or copy old text across posts. " +
      "Always proofread: reused text from an old post is easy to miss, and overlapping elements show up only when you look at the finished slide."
  );

  // =====================================================================
  // 10 — Examples that feel like The Cub
  s = pres.addSlide({ masterName: "Orange", sectionTitle: "Put it into practice" });
  tag(s, "EXAMPLES", { onOrange: true });
  setTitle(s, "Content that", "feels like us.", true);
  const ew = 2.15, eh = ew / POST_AR, ey = 2.0;
  [
    ["post_ldm_5.png", "Flips the question. Kind and hopeful."],
    ["post_c5_5.png", "Two-tone headline. Warm close."],
    ["post_c4_5.png", "Event details, easy to scan."],
  ].forEach(([f, why], i) => {
    const x = MX + i * (ew + 0.22);
    s.addImage({ path: A(f), x, y: ey, w: ew, h: eh, altText: "Example post: " + why });
    s.addText(why, T({ x, y: ey + eh + 0.1, w: ew, h: 0.5, fontSize: 13.5 }));
  });
  const rx = 7.75, rw = RIGHT - rx;
  s.addText("Not us  →  The Cub way", T({ x: rx, y: 2.0, w: rw, h: 0.3, fontFace: LABEL, fontSize: 11, bold: true, charSpacing: 1.4 }));
  [
    ["Is your child lazy? 5 signs you can’t ignore!", "“Struggling Doesn’t Mean Not Trying.”"],
    ["Why can’t they just focus?!", "“What would help them?”"],
    ["BOOK NOW!!! Hurry, seats going fast!!!", "“Limited Spots Available!”"],
  ].forEach(([bad, good], i) => {
    const y = 2.4 + i * 1.12;
    card(s, rx, y, rw, 1.0, C.background1, "Rewrite " + (i + 1), 0.16);
    s.addText(bad, T({ x: rx + 0.25, y: y + 0.14, w: rw - 0.5, h: 0.3, fontSize: 14, strike: "sngStrike" }));
    s.addText(good, T({ x: rx + 0.25, y: y + 0.5, w: rw - 0.5, h: 0.4, fontFace: HEAD, bold: true, fontSize: 17, color: C.accent1 }));
  });
  s.addText("Before you post:", T({ x: MX, y: 6.05, w: 1.9, h: 0.4, fontSize: 16, bold: true, valign: "middle" }));
  [["Kind?", 1.0], ["Clear?", 1.05], ["Sounds like us?", 1.85], ["Looks like us?", 1.8], ["Proofread?", 1.5]].reduce((x, [t1, w1], i) => {
    pill(s, t1, { x, y: 6.05, w: w1 + 0.2, h: 0.4, fill: C.text1, color: C.background1, size: 12, name: "Checklist " + (i + 1) });
    return x + w1 + 0.2 + 0.12;
  }, 2.45);
  s.addNotes(
    "Three real posts from our feed and why they feel like us: the Learning Disability Month post flips a blaming question into a helpful one; the ADHD carousel closes with a two-tone headline and warm line; the OSIT workshop post makes event details easy to scan. " +
      "On the right, the 'Not us' lines are examples of what we would never publish; the orange lines are how we say the same thing. " +
      "Close with the five-question check before every post: kind, clear, sounds like us, looks like us, proofread."
  );

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
}
main().catch((e) => { console.error(e); process.exit(1); });
