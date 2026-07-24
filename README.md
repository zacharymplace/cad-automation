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
