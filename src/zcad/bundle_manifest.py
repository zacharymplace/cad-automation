"""Portable bundle integrity checks; no CAD runtime or authenticity claim."""

import hashlib
import json
from pathlib import Path, PurePosixPath

MANIFEST_NAME = "bundle-manifest.json"
SCHEMA = "zcad.bundle/1"
PROVENANCE_SCOPE = "design-inputs-and-artifacts; implementation-source-not-attested"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inventory(root: Path) -> dict[str, Path]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Bundle must be a real directory")
    files = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Bundle contains a symlink: {path.name}")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path
        elif not path.is_dir():
            raise ValueError(f"Bundle contains a non-regular entry: {path.name}")
    return files


def _safe_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Invalid manifest path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        raise ValueError(f"Invalid manifest path: {value}")
    return value


def _unique_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_json)


def write_manifest(root: Path, designs: list[dict], *, fresh: bool) -> None:
    """Hash every payload file; the manifest's own hash is reported separately."""
    files = _inventory(root)
    if MANIFEST_NAME in files:
        raise ValueError("Manifest already exists")
    document = {
        "schema": SCHEMA,
        "mode": "fresh" if fresh else "reused",
        "provenance_scope": PROVENANCE_SCOPE,
        "designs": designs,
        "files": {
            name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for name, path in sorted(files.items())
        },
    }
    (root / MANIFEST_NAME).write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def verify_bundle(root: Path, *, expected_manifest_sha256: str | None = None) -> dict:
    """Verify exact file inventory, bytes, and design/part relationships.

    A trusted expected_manifest_sha256 pins this manifest. Without it, the
    check establishes internal integrity only, not origin or authenticity.
    """
    files = _inventory(root)
    manifest_path = files.pop(MANIFEST_NAME, None)
    if manifest_path is None:
        raise ValueError("Bundle manifest is missing; rebuild with manifest support")
    manifest_hash = sha256_file(manifest_path)
    if expected_manifest_sha256 is not None:
        if manifest_hash != expected_manifest_sha256:
            raise ValueError("Manifest SHA-256 does not match the trusted value")
    document = _load(manifest_path)
    if not isinstance(document, dict) or document.get("schema") != SCHEMA:
        raise ValueError("Unsupported bundle manifest schema")
    if document.get("mode") not in ("fresh", "reused"):
        raise ValueError("Invalid bundle mode")
    if document.get("provenance_scope") != PROVENANCE_SCOPE:
        raise ValueError("Unsupported provenance scope")
    records = document.get("files")
    if not isinstance(records, dict) or not records:
        raise ValueError("Missing file inventory")
    for name in records:
        _safe_path(name)
    if set(files) != set(records):
        raise ValueError("Bundle file inventory differs from manifest")
    for name, record in records.items():
        if (
            not isinstance(record, dict)
            or type(record.get("size_bytes")) is not int
            or record["size_bytes"] != files[name].stat().st_size
            or record.get("sha256") != sha256_file(files[name])
        ):
            raise ValueError(f"Bundle file hash/size mismatch: {name}")
    designs = document.get("designs")
    if not isinstance(designs, list) or not designs:
        raise ValueError("Missing design inventory")
    referenced = {"README.md"}
    if "guide.html" in records:
        referenced.add("guide.html")
    names = set()
    part_count = 0
    for design in designs:
        if not isinstance(design, dict):
            raise ValueError("Invalid design record")
        name, kind = design.get("name"), design.get("type")
        if not isinstance(name, str) or not name or name in names:
            raise ValueError("Invalid or duplicate design name")
        if not isinstance(kind, str) or not kind:
            raise ValueError("Invalid design type")
        names.add(name)
        source = _safe_path(design.get("source"))
        if (
            not source.startswith("designs/")
            or source not in files
            or source in referenced
        ):
            raise ValueError("Invalid or duplicate design source")
        referenced.add(source)
        source_json = _load(files[source])
        if not isinstance(source_json, dict) or (
            source_json.get("name"),
            source_json.get("type"),
        ) != (name, kind):
            raise ValueError("Design source identity differs from manifest")
        parts = design.get("parts")
        if not isinstance(parts, list) or not parts:
            raise ValueError("Missing part inventory")
        actual = []
        for part in parts:
            if not isinstance(part, dict) or not isinstance(part.get("name"), str):
                raise ValueError("Invalid part record")
            part_name = part["name"]
            if not part_name or part_name in actual:
                raise ValueError("Invalid or duplicate part name")
            actual.append(part_name)
            for field, folder, suffix in (
                ("stl", "stl/", ".stl"),
                ("step", "step/", ".step"),
                ("metadata", "metadata/", ".metadata.json"),
            ):
                path = _safe_path(part.get(field))
                if (
                    not path.startswith(folder)
                    or not path.endswith(suffix)
                    or path not in files
                    or path in referenced
                ):
                    raise ValueError("Missing, duplicate, or invalid part artifact")
                referenced.add(path)
            metadata = _load(files[part["metadata"]])
            if not isinstance(metadata, dict) or not isinstance(
                metadata.get("part"), dict
            ):
                raise ValueError("Invalid export metadata")
            if metadata.get("design") != {"name": name, "type": kind}:
                raise ValueError("Metadata design identity differs from manifest")
            if metadata["part"].get("name") != part_name:
                raise ValueError("Metadata part identity differs from manifest")
            if metadata.get("bundle_output_path_base") != "bundle_root" or metadata.get(
                "outputs"
            ) != {"step": part["step"], "stl": part["stl"]}:
                raise ValueError("Metadata output paths differ from manifest")
        expected = design.get("expected_parts")
        if document["mode"] == "fresh":
            if (
                not isinstance(expected, list)
                or not expected
                or any(not isinstance(n, str) or not n for n in expected)
                or len(set(expected)) != len(expected)
                or set(expected) != set(actual)
            ):
                raise ValueError("Exported parts differ from expected generated parts")
        elif expected is not None:
            raise ValueError("Reused exports cannot claim generated-part completeness")
        part_count += len(actual)
    if referenced != set(records):
        raise ValueError("Manifest contains missing or unreferenced payload files")
    return {
        "status": "PASS",
        "mode": document["mode"],
        "design_count": len(designs),
        "part_count": part_count,
        "file_count": len(files),
        "manifest_sha256": manifest_hash,
        "trusted_manifest_pinned": expected_manifest_sha256 is not None,
        "completeness": (
            "generated-part-set-verified"
            if document["mode"] == "fresh"
            else "unverified"
        ),
        "provenance_scope": PROVENANCE_SCOPE,
    }
