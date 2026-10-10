"""Build every preset and print one table. Run: uv run --no-project --with cadquery build_all.py"""
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

root = Path(__file__).parent
sizes = list(tomllib.loads((root / "config.toml").read_text())["sizes"])
rows = []
for size in sizes:
    env = {**os.environ, "FESTIVAL_YOKE_SIZE": size}
    out = subprocess.run([sys.executable, "build.py"], cwd=root, env=env, capture_output=True, text=True)
    text = out.stdout + out.stderr
    grams = re.search(r"upper bound: (\d+) g", text)
    bad = "TOO BIG" in text
    overlap = re.search(r"overlap ([\d.]+) mm3", text)
    crumbs = re.search(r"crumbs: (.*)", text)
    warn = [l.strip() for l in text.splitlines() if "WARN" in l]
    rows.append((size, grams.group(1) if grams else "FAILED", "no" if bad else "yes", overlap.group(1) if overlap else "?", crumbs.group(1) if crumbs else "?", warn))
print(f"{'size':<6}{'solid g':>8}  {'fits bed':<9}{'joint overlap':<15}crumbs")
for size, g, fits, ov, cr, warn in rows:
    print(f"{size:<6}{g:>8}  {fits:<9}{ov:<15}{cr}")
    for w in warn:
        print(f"      {w}")
