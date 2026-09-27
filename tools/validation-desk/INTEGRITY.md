# Artifact integrity — v0.4

Uses artifact_integrity schema 1.0 from zcad-run-integrity-v1: algorithm sha256 and files keyed by stdout/stderr filename, with sha256 and size_bytes. Inventory must exactly match gate references. Web Crypto hashes raw file bytes, never reserialized JSON.

Integrity is separate from run status. PASS: referenced bytes match supplied receipt. FAIL: missing or changed bytes. ERROR: malformed binding or unable to verify. UNBOUND: no hashes. Extra files are outside the binding. Receipts remain unchanged; old runs are never retroactively bound. Authenticity and freshness remain unverified. Browser selection cannot inspect filesystem symlink metadata; use the runner CLI for that check. Per-file limit: 10 MiB.

Open index.html, choose Open runner folder, select an extracted run directory. Unverified findings remain available with a prominent warning.

Build: python3 tools/validation-desk/build.py

Tests: node --test tools/validation-desk/*.test.cjs tools/validation-desk/test.cjs

This supersedes the no-hash limitation in RUNNER.md. Real completed hashed-run and interactive browser verification remain pending.
