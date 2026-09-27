import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description="Build or check the standalone viewer")
parser.add_argument(
    "--check", action="store_true", help="Check generated HTML without writing"
)
args = parser.parse_args()

root = Path(__file__).resolve().parent
html = (root / "index.template.html").read_text()
html = html.replace("/* COMPARE */", (root / "compare.js").read_text())
html = html.replace("/* MODEL */", (root / "model.js").read_text())
html = html.replace("/* RUNNER */", (root / "runner.js").read_text())
html = html.replace("/* INTEGRITY */", (root / "integrity.js").read_text())
html = html.replace(
    "/* FIXTURE */", (root / "fixtures/historical-report.json").read_text()
)
target = root / "index.html"
expected = html.encode("utf-8")
if args.check:
    if not target.is_file() or target.read_bytes() != expected:
        raise SystemExit(
            "Viewer HTML is missing or stale. Run python3 tools/validation-desk/build.py"
        )
    print("Viewer generated HTML is current")
else:
    target.write_bytes(expected)
