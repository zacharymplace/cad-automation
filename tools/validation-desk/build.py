import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description="Build or check the standalone viewers")
parser.add_argument("--check", action="store_true", help="Check without writing")
args = parser.parse_args()
root = Path(__file__).resolve().parent
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
        "HOUSE": "house-style.css",
    }.items():
        token = "/* " + marker + " */"
        if token in html:
            text = (root / filename).read_text()
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
