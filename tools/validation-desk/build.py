import argparse
import base64
from pathlib import Path

parser = argparse.ArgumentParser(description="Build or check the standalone viewers")
parser.add_argument("--check", action="store_true", help="Check without writing")
args = parser.parse_args()
root = Path(__file__).resolve().parent

FONT_FACES = (
    ("Archivo Black", 400, "archivo-black-latin-400-normal.woff2"),
    ("Barlow Condensed", 500, "barlow-condensed-latin-500-normal.woff2"),
    ("Barlow Condensed", 700, "barlow-condensed-latin-700-normal.woff2"),
    ("Space Mono", 400, "space-mono-latin-400-normal.woff2"),
    ("Space Mono", 700, "space-mono-latin-700-normal.woff2"),
)


def font_css():
    # Embedded as data: URIs so each page stays a single file that makes no requests.
    rules = []
    for family, weight, filename in FONT_FACES:
        data = base64.b64encode((root / "fonts" / filename).read_bytes()).decode("ascii")
        rules.append(
            f'@font-face{{font-family:"{family}";font-style:normal;font-weight:{weight};'
            f'font-display:swap;src:url(data:font/woff2;base64,{data}) format("woff2")}}'
        )
    return "\n".join(rules)


for name in ("index", "history"):
    html = (root / f"{name}.template.html").read_text()
    for marker, filename in {
        "COMPARE": "compare.js",
        "MODEL": "model.js",
        "RUNNER": "runner.js",
        "INTEGRITY": "integrity.js",
        "HISTORY": "history.js",
        "REPOSITORIES": "repositories.js",
        "FIXTURE": "fixtures/historical-report.json",
        "FONTS": "fonts/",
        "HOUSE": "house-style.css",
    }.items():
        token = "/* " + marker + " */"
        if token in html:
            text = font_css() if marker == "FONTS" else (root / filename).read_text()
            if marker == "HOUSE":
                # Pages ship with a no-network CSP: drop the web-font @import.
                text = "\n".join(
                    line for line in text.splitlines() if not line.startswith("@import")
                )
            html = html.replace(token, text)
    target = root / f"{name}.html"
    expected = html.encode("utf-8")
    if args.check:
        if not target.is_file() or target.read_bytes() != expected:
            raise SystemExit(
                f"{target.name} is missing or stale. "
                "Run python3 tools/validation-desk/build.py"
            )
        print(f"{target.name} is current")
    else:
        target.write_bytes(expected)
