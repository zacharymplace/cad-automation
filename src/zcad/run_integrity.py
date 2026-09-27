"""Bind local runner artifacts to a receipt; verify without executing gates."""

import argparse
import hashlib
import json
from pathlib import Path


def artifact_names(receipt):
    names = []
    for gate in receipt.get("gates", []):
        for stream in ("stdout", "stderr"):
            name = gate[stream]
            if (
                not isinstance(name, str)
                or not name
                or name in {".", "..", "receipt.json", "receipt.tmp"}
                or "/" in name
                or "\\" in name
            ):
                raise ValueError("Invalid artifact filename")
            names.append(name)
    if not names or len(names) != len(set(names)):
        raise ValueError("Expected nonempty, unique gate artifact names")
    return sorted(names)


def fingerprint(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Missing or nonregular artifact: {path.name}")
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return {"sha256": digest.hexdigest(), "size_bytes": size}


def bind_artifacts(folder, receipt):
    return {
        "schema_version": "1.0",
        "algorithm": "sha256",
        "files": {name: fingerprint(folder / name) for name in artifact_names(receipt)},
    }


def verify(folder):
    receipt_path = folder / "receipt.json"
    if receipt_path.is_symlink():
        raise ValueError("Receipt must not be a symlink")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    binding = receipt.get("artifact_integrity")
    if binding is None:
        return {"status": "UNBOUND", "reasons": ["Receipt has no artifact hashes"]}
    if receipt.get("status") not in {"PASS", "FAIL", "ERROR", "INTERRUPTED"}:
        raise ValueError("Receipt is not finalized")
    if binding.get("schema_version") != "1.0" or binding.get("algorithm") != "sha256":
        raise ValueError("Unsupported artifact integrity schema")
    names = artifact_names(receipt)
    files = binding["files"]
    if not isinstance(files, dict) or set(files) != set(names):
        raise ValueError("Hash inventory does not match gate artifact references")
    reasons = []
    for name in names:
        expected = files[name]
        if (
            not isinstance(expected, dict)
            or set(expected) != {"sha256", "size_bytes"}
            or type(expected["size_bytes"]) is not int
            or expected["size_bytes"] < 0
            or not isinstance(expected["sha256"], str)
            or len(expected["sha256"]) != 64
            or any(c not in "0123456789abcdef" for c in expected["sha256"])
        ):
            raise ValueError(f"Malformed hash record: {name}")
        try:
            if fingerprint(folder / name) != expected:
                reasons.append(f"Changed artifact: {name}")
        except (OSError, ValueError) as error:
            reasons.append(str(error))
    return {
        "status": "FAIL" if reasons else "PASS",
        "scope": "Artifact bytes match supplied receipt; "
        "receipt authenticity unverified",
        "run_status": receipt["status"],
        "file_count": len(names),
        "reasons": reasons,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.folder)
        code = 0 if result["status"] == "PASS" else 1
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        result = {"status": "ERROR", "reasons": [str(error)]}
        code = 2
    print(json.dumps(result, indent=2))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
