"""Bounded, read-only Git discovery. JSON goes to stdout; no repo writes."""

import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def git(path, *args):
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("GIT_"):
            del env[key]
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    result = subprocess.run(
        ["git", "--no-optional-locks", "-c", "core.fsmonitor=false",
         "-c", "core.untrackedCache=false", "-C", str(path), *args],
        capture_output=True, timeout=15, env=env, check=False,
    )
    if result.returncode:
        raise ValueError(result.stderr.decode(errors="replace").strip()[:500])
    return result.stdout.decode(errors="replace").strip()


def observe(path):
    start = now()
    try:
        head = git(path, "rev-parse", "--verify", "HEAD")
        try:
            branch = git(path, "symbolic-ref", "--quiet", "--short", "HEAD")
        except ValueError:
            branch = None
        dirty = bool(git(path, "status", "--porcelain=v1", "-z", "--untracked-files=normal", "--ignore-submodules=none"))
        if head != git(path, "rev-parse", "--verify", "HEAD"):
            raise ValueError("HEAD changed during observation; retry when repository is stable")
        return dict(path=str(path), status="OBSERVED", started_at=start,
                    observed_at=now(), head=head, branch=branch, dirty=dirty)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        return dict(path=str(path), status="ERROR", started_at=start,
                    observed_at=now(), error=str(exc)[:500])


def discover(root, max_depth=2, max_directories=2000):
    root = Path(root).expanduser().absolute()
    result = dict(schema_version="zcad-repository-inventory/1", root=str(root),
                  started_at=now(), finished_at=None, max_depth=max_depth,
                  repositories=[], issues=[], visited_directories=0)
    pending = [(root, 0)]
    while pending:
        path, depth = pending.pop()
        if result["visited_directories"] >= max_directories:
            result["issues"].append(dict(path=str(root), reason="Directory limit reached; scan incomplete"))
            break
        if path.is_symlink():
            result["issues"].append(dict(path=str(path), reason="Symlink skipped"))
            continue
        result["visited_directories"] += 1
        try:
            entries = sorted(path.iterdir(), key=lambda p: p.name)
            if any(p.name == ".git" for p in entries):
                result["repositories"].append(observe(path))
                continue
            if depth == max_depth:
                continue
            for child in reversed(entries):
                if child.is_symlink():
                    result["issues"].append(dict(path=str(child), reason="Symlink skipped"))
                elif child.is_dir() and child.name not in {"node_modules", ".venv", ".git", "__pycache__"}:
                    pending.append((child, depth + 1))
        except OSError as exc:
            result["issues"].append(dict(path=str(path), reason=str(exc)[:500]))
    result["finished_at"] = now()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--max-depth", type=int, choices=range(0, 7), default=2)
    args = parser.parse_args()
    print(json.dumps(discover(args.root, args.max_depth), indent=2))


if __name__ == "__main__":
    main()
