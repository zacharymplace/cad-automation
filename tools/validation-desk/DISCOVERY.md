# Read-only repository discovery

From cad-automation:

```sh
python3 -B tools/validation-desk/discover.py "$HOME/dev" --max-depth 2 > "$HOME/Downloads/zcad-repositories.json"
open tools/validation-desk/history.html
```

Import that JSON under Repository observations. Each import replaces only the
repository snapshot; rejected imports retain the previous snapshot. Clear removes
it from the tab. Run imports, A/B selections, receipts and integrity are independent.

The scanner emits schema `zcad-repository-inventory/1`. Depth zero examines only
the supplied root. Discovery stops at repository roots; nested repositories,
bare repositories and excluded dependency directories are outside its coverage.
Git worktrees with a .git file are supported. Symlinks are skipped, scanning is
bounded to 2000 directories, and each Git invocation has a 15-second timeout.
Unborn HEADs and inaccessible repositories appear as errors, not clean states.

Git optional locks are disabled; no fetch, checkout, hooks or configuration writes
are requested. Dirty includes tracked and untracked changes and submodule status.
Ignored files are excluded. No remote URLs or credentials are collected. Absolute
paths are present in the export. The shell writes only the chosen output JSON.

Observations are sequential, not atomic. HEAD is checked again after status, but
other concurrent edits can still occur. Imported snapshots are unauthenticated
and may be stale; they never attest to current state or rewrite run provenance.
Rescan when a fresh observation is needed. Use a quiet workspace while scanning.

verify.py checks the scanner with temporary Git fixtures as well as the viewer
tests. Browser layout verification remains separate.
