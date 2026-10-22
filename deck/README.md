# The Cub Way: deck source

`../The_Cub_Way.pptx` is the 10-slide onboarding deck for new Social Media Interns.

## Rebuild

```bash
cd deck
npm install                                   # pptxgenjs, sharp, react-icons
python3 -I prep_assets.py <folder with the brand docx + 3 carousel PDFs> assets
PPTX_SKILL_DIR=<pptx skill dir> NODE_PATH=$PWD/node_modules node build.js
```

* `prep_assets.py` extracts everything from The Cub's own files: the logo (background keyed out), doodles,
  blob shapes, motifs and post renders. Nothing is redrawn.
* `build.js` lays out the deck (theme, three layouts, placeholders, sections, speaker notes).
* `assets/` holds the images the deck uses.

## Fonts

Slides name the brand fonts but do not embed them. Install **Playfair Display**, **Lexend** and
**Glacial Indifference** before presenting or editing, or PowerPoint will substitute them.
