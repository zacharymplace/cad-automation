# Z$ CAD Automation

Code-driven parametric CAD built with Python and CadQuery.

## Operating model

1. Put design parameters in `designs/*.json`.
2. Run the `zcad` command.
3. Validate the generated solid.
4. Export STEP and STL files.
5. Print only the smallest useful fit test first.

## Setup

```bash
source .venv/bin/activate
pip install -e ".[dev]"
```

## Generate a design

```bash
zcad designs/example-tray.json
```

## Validate

```bash
ruff check .
ruff format --check .
pytest
```

## Outputs

Generated manufacturing files are written to `exports/`.

- `STEP` is the authoritative exchange format.
- `STL` is the derived printing format.
- `JSON` is the authoritative design input.
## Architecture

This repository contains ZCAD product generators and CLI orchestration.
Reusable CAD infrastructure lives in the separate `zcad-core` repository.

See [docs/architecture.md](docs/architecture.md) for ownership boundaries and
local development setup.

Bootstrap both editable packages with:

```bash
./scripts/bootstrap-dev.sh
```


## Bundle export-binding preflight

Before copying each selected part into a gift bundle, the builder checks any
recorded `artifacts` bindings using zcad-core's read-only
`verify_artifact_bindings` API. Both STEP and STL must match their recorded
SHA-256, byte size and the filenames actually being packaged. Missing, malformed,
unsafe, unreadable or mismatched bound artifacts stop publication with a
part-specific error. The local zcad-core checkout must include this verifier
(commit `c3db1bf` or later) when packaging bound exports.

Legacy export metadata without an `artifacts` field remains supported. The bundle
guide explicitly labels those original export bindings **not checked**; existing
bundle-manifest verification still applies. A present but invalid or incomplete
`artifacts` field is an error, not a legacy fallback. This applies to both fresh
builds and reused exports; reused exports still do not establish freshness.

The check runs while original artifacts are siblings, before packaging separates
them into `step/`, `stl/` and `metadata/`. Bundle layout, manifest schema,
producer/consumer provenance and output-path rewriting are unchanged. Input
exports are read-only. Preflight failures retain the diagnostic stage and leave
an existing bundle and ZIP intact; publication rollback behavior is unchanged.
The preflight is not an atomic snapshot of concurrently edited inputs. Byte
identity does not establish authenticity, geometric validity or print suitability.
