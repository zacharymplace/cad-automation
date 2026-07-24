#!/usr/bin/env bash
set -euo pipefail

product_root="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
  pwd
)"

core_root="${ZCAD_CORE_ROOT:-$product_root/../zcad-core}"

run_repository_checks() {
  repository_name="$1"
  repository_root="$2"

  printf '\n=== %s ===\n' "$repository_name"

  if [[ ! -x "$repository_root/.venv/bin/python" ]]; then
    printf 'Virtual environment missing: %s/.venv\n' \
      "$repository_root" >&2
    exit 1
  fi

  "$repository_root/.venv/bin/ruff" \
    format --check \
    "$repository_root/src" \
    "$repository_root/tests"

  "$repository_root/.venv/bin/ruff" \
    check \
    "$repository_root/src" \
    "$repository_root/tests"

  (
    cd "$repository_root"
    .venv/bin/python -m pytest -q
  )
}

run_repository_checks \
  "zcad-core" \
  "$core_root"

run_repository_checks \
  "cad-automation" \
  "$product_root"

printf '\n=== PACKAGE BOUNDARY ===\n'

"$product_root/.venv/bin/python" - <<'PY'
from importlib.metadata import distribution

import zcad
import zcad_core

product = distribution("zcad")
core = distribution("zcad-core")

print("zcad:", product.version, zcad.__file__)
print("zcad-core:", core.version, zcad_core.__file__)

requirements = set(product.requires or [])

if not any(
    requirement.startswith("zcad-core<0.2,>=0.1")
    for requirement in requirements
):
    raise SystemExit(
        "cad-automation does not declare the expected "
        "zcad-core compatibility range"
    )

print("Compatibility contract: PASS")
PY

printf '\nLocal CI: PASS\n'
