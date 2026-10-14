#!/usr/bin/env python3
"""Build the static GitHub Pages site from claude.ai artifact sources.

Usage: python build.py SRC_DIR [OUT_DIR]

SRC_DIR holds the current live page source of each artifact (Artifact read,
path "index.html"), saved as:
  home.html          homepage artifact
  cv.html            public CV artifact
  explainers/<key>.html   one per explainer artifact
The artifact-id -> page map is in PAGES / EXPLAINERS below; add a line when a
new explainer is published.
"""
import html, re, sys
from pathlib import Path

HOME = "1F4J2oRjASGFUQs4gHCh7N"
CV = "SBLZ4VGLwFyvvsp19NQXWG"
EXPLAINERS = {  # key -> artifact id
    "ff": "HTD5Rcb2vZqTYUu7fj1Fhv",
    "cocrystal": "Mg1ZTyz616gTjNQPD9SiYE",
    "lockring": "6caA5ERMgZarBczFBMwsxe",
    "barrierless": "S1tDbNHh3ZAneZWVF4ncT9",
    "vloss": "5abwCWpKQrD3MFEx4U5NZH",
}
DESC = {
    "home": "Huotian Zhang - device physicist working on organic solar cells, University of Potsdam.",
    "cv": "Curriculum vitae of Huotian Zhang.",
}
ART = re.compile(r"https://claude\.ai/(?:code/)?artifact/([A-Za-z0-9-]+)")


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


def wrap(title, desc, body):
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(title)}</title>"
            "<style>html,body{margin:0;padding:0}img{max-width:100%}</style>"
            f'<meta name="description" content="{html.escape(desc)}">'
            f"</head><body>\n{body}</body></html>\n")


def main():
    src = Path(sys.argv[1])
    out = Path(sys.argv[2] if len(sys.argv) > 2 else Path(__file__).parent)
    (out / "explainers").mkdir(parents=True, exist_ok=True)

    t, b = fragment((src / "home.html").read_text())
    (out / "index.html").write_text(wrap(t, DESC["home"], relink(b, "root")))

    t, b = fragment((src / "cv.html").read_text())
    b = relink(b, "root")
    b, n = re.subn(r'(<div class="run">)',
                   r'\1<a href="index.html" style="color:inherit">← Homepage</a> · ', b, count=1)
    if not n:
        raise SystemExit('cv: class="run" line not found')
    (out / "cv.html").write_text(wrap(t, DESC["cv"], b))

    for k in EXPLAINERS:
        t, b = fragment((src / "explainers" / f"{k}.html").read_text())
        (out / "explainers" / f"{k}.html").write_text(
            wrap(t, f"{t}: an interactive explainer of a paper by Huotian Zhang and co-authors.",
                 relink(b, "explainer")))
    (out / ".nojekyll").write_text("")

    left = [str(p) for p in out.rglob("*.html") if ".git" not in p.parts and "claude.ai" in p.read_text()]
    if left:
        raise SystemExit(f"claude.ai links remain in {left}")


if __name__ == "__main__":
    main()
