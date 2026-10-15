# huotianzhang.github.io

Personal homepage of Huotian Zhang, served by GitHub Pages from `main` (root).

The pages are generated from claude.ai artifacts (the editing source) by `build.py`:
`index.html` (homepage), `cv.html` (public CV) and `explainers/<key>.html` (paper explainers).
Do not edit the generated HTML by hand; edit the artifact and rebuild.

Share previews: `og/<key>.png` (1200 × 630) are made by `node tools/make_og.js` from the built pages
(set the signature story step for a new explainer in `STEP` there), then `build.py` is run again so the
page heads link them (Open Graph / Twitter card tags).
