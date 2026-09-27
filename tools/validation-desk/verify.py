"""Read-only viewer verification for the local runner."""

import shutil
import subprocess
import sys
from pathlib import Path


def main():
    node = shutil.which("node")
    if node is None:
        print(
            "Viewer verification requires Node.js on PATH; no tests were run",
            file=sys.stderr,
        )
        return 2
    root = Path(__file__).resolve().parent
    result = subprocess.run(
        [sys.executable, str(root / "build.py"), "--check"], check=False
    )
    if result.returncode:
        return result.returncode
    result = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", str(root),
         "-p", "test_discover.py"], check=False
    )
    if result.returncode:
        return result.returncode
    tests = sorted(set(root.glob("*.test.cjs")) | {root / "test.cjs"})
    return subprocess.run(
        [node, "--test", *(str(p) for p in tests)], check=False
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
