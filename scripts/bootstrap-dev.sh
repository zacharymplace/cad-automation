#!/usr/bin/env bash
set -euo pipefail

repository_root="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
  pwd
)"

core_root="${ZCAD_CORE_ROOT:-$repository_root/../zcad-core}"
venv_root="${VIRTUAL_ENV:-$repository_root/.venv}"

if [[ ! -f "$core_root/pyproject.toml" ]]; then
  printf 'zcad-core was not found at: %s\n' "$core_root" >&2
  printf 'Set ZCAD_CORE_ROOT to its repository path.\n' >&2
  exit 1
fi

if [[ ! -x "$venv_root/bin/python" ]]; then
  python3 -m venv "$venv_root"
fi

"$venv_root/bin/python" -m pip install --upgrade pip
"$venv_root/bin/python" -m pip install -e "$core_root"
"$venv_root/bin/python" -m pip install -e "$repository_root[dev]"

"$venv_root/bin/python" - <<'PY'
import zcad
import zcad_core

print("zcad:", zcad.__file__)
print("zcad_core:", zcad_core.__file__)
PY
