#!/usr/bin/env python3
"""Build the static GitHub Pages site from claude.ai artifact sources.

Usage: python build.py SRC_DIR [OUT_DIR]

SRC_DIR holds the current live page source of each artifact (Artifact read,
path "index.html"), saved as:
  home.html          homepage artifact
  cv.html            public CV artifact
  explainers/<key>.html   one per explainer artifact
The artifact-id -> page map is in PAGES / EXPLAINERS below; add a line when a
new explainer is published. Share previews: og/<key>.png (made by
tools/make_og.js from the built page) is linked in the page head when present.
"""
import html, re, sys
from pathlib import Path

SITE = "https://huotianzhang.github.io/"
HOME = "1F4J2oRjASGFUQs4gHCh7N"
CV = "SBLZ4VGLwFyvvsp19NQXWG"
EXPLAINERS = {  # key -> artifact id
    "ff": "HTD5Rcb2vZqTYUu7fj1Fhv",
    "cocrystal": "Mg1ZTyz616gTjNQPD9SiYE",
    "lockring": "6caA5ERMgZarBczFBMwsxe",
    "barrierless": "S1tDbNHh3ZAneZWVF4ncT9",
    "vloss": "5abwCWpKQrD3MFEx4U5NZH",
    "ternary": "JH26x5yfAtpM4zrxjprGs3",
}
DESC = {
    "home": "Huotian Zhang - device physicist working on organic solar cells, University of Potsdam.",
    "cv": "Curriculum vitae of Huotian Zhang.",
}
ART = re.compile(r"https://claude\.ai/(?:code/)?artifact/([A-Za-z0-9-]+)")
CARD = re.compile(r"\['(\w+)','([^']*)','([^']*)','([^']*)','([^']*)',\d\]")


def fragment(src):
    """Strip the publishing shell (<!doctype ... <body>) and closing tags."""
    i = src.find("<body>")
    body = src[i + len("<body>"):] if i >= 0 else src
    body = re.sub(r"\s*</body>\s*</html>\s*$", "", body)
    m = re.search(r"<title>(.*?)</title>\s*", body, re.S)
    title = html.unescape(m.group(1).strip()) if m else "Huotian Zhang"
    if m:
        body = body[:m.start()] + body[m.end():]
    return title, body.strip() + "\n"


def relink(body, where):
    """Rewrite claude.ai artifact links to site-relative paths."""
    def sub(m):
        aid = m.group(1)
        if aid == HOME:
            return "../index.html" if where == "explainer" else "index.html"
        if aid == CV:
            return "../cv.html" if where == "explainer" else "cv.html"
        for k, v in EXPLAINERS.items():
            if aid == v:
                return f"{k}.html" if where == "explainer" else f"explainers/{k}.html"
        raise SystemExit(f"unknown artifact link {m.group(0)}")
    return ART.sub(sub, body)


def share_meta(out, path, title, desc, image):
    """Open Graph / Twitter card tags; image is og/<name>.png, used only if it exists."""
    url = SITE + ("" if path == "index.html" else path)
    tags = [f'<link rel="canonical" href="{url}">',
            '<meta property="og:type" content="article">' if path.startswith("explainers/") else '<meta property="og:type" content="website">',
            '<meta property="og:site_name" content="Huotian Zhang">',
            f'<meta property="og:title" content="{html.escape(title)}">',
            f'<meta property="og:description" content="{html.escape(desc)}">',
            f'<meta property="og:url" content="{url}">']
    if image and (out / image).exists():
        tags += [f'<meta property="og:image" content="{SITE}{image}">',
                 '<meta property="og:image:width" content="1200">', '<meta property="og:image:height" content="630">',
                 '<meta name="twitter:card" content="summary_large_image">']
    else:
        tags.append('<meta name="twitter:card" content="summary">')
    return "".join(tags)


def heading(body, fallback):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else fallback


def wrap(title, desc, body, meta=""):
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(title)}</title>"
            "<style>html,body{margin:0;padding:0}img{max-width:100%}</style>"
            f'<meta name="description" content="{html.escape(desc)}">'
            f"{meta}</head><body>\n{body}</body></html>\n")


def main():
    src = Path(sys.argv[1])
    out = Path(sys.argv[2] if len(sys.argv) > 2 else Path(__file__).parent)
    (out / "explainers").mkdir(parents=True, exist_ok=True)

    home = (src / "home.html").read_text()
    cards = {m.group(1): html.unescape(m.group(3)) for m in CARD.finditer(home)}  # homepage card blurbs
    t, b = fragment(home)
    (out / "index.html").write_text(wrap(t, DESC["home"], relink(b, "root"),
        share_meta(out, "index.html", "Huotian Zhang", DESC["home"], "og/home.png")))

    t, b = fragment((src / "cv.html").read_text())
    b = relink(b, "root")
    b, n = re.subn(r'(<div class="run">)',
                   r'\1<a href="index.html" style="color:inherit">← Homepage</a> · ', b, count=1)
    if not n:
        raise SystemExit('cv: class="run" line not found')
    (out / "cv.html").write_text(wrap(t, DESC["cv"], b, share_meta(out, "cv.html", "Huotian Zhang · CV", DESC["cv"], None)))

    for k in EXPLAINERS:
        t, b = fragment((src / "explainers" / f"{k}.html").read_text())
        d = cards.get(k) or f"{t}: an interactive explainer of a paper by Huotian Zhang and co-authors."
        (out / "explainers" / f"{k}.html").write_text(
            wrap(t, d, relink(b, "explainer"),
                 share_meta(out, f"explainers/{k}.html", heading(b, t), d, f"og/{k}.png")))
    (out / ".nojekyll").write_text("")

    left = [str(p) for p in out.rglob("*.html") if ".git" not in p.parts and "claude.ai" in p.read_text()]
    if left:
        raise SystemExit(f"claude.ai links remain in {left}")


if __name__ == "__main__":
    main()
