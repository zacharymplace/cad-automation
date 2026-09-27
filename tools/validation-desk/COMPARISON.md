# Completed-run comparison

Open baseline A and comparison B independently. Neither is inferred to be newer.
Each slot retains its raw receipt, execution timestamps, repository snapshots, recorded outcome and independently checked artifact integrity. Only completed receipts with a valid finished_at are accepted.

Gates match by exact name and designs by exact path. Checks match by code plus part_name; duplicate identities are ambiguous and retain all records. Renames appear as added/removed. Missing checks never imply a fix. Full changed records expose dimensions, policy and coverage differences even when status is unchanged. Missing or invalid catalogs disable design comparison; gate evidence remains visible. Unbound or failed integrity is prominently labeled.

No source equivalence, causal improvement, current repository state or receipt authenticity is inferred. The comparison is read-only and session-local.

Run python3 tools/validation-desk/verify.py. Browser smoke check: load a failed baseline and completed comparison, inspect a changed design, then replace one slot and clear comparison.
