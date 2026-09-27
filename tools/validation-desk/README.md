# ZCAD Validation Desk — prototype v0.2

The detail view now shows failures and warnings, then unchecked areas, then a dimensions table. Passing checks and policy JSON start collapsed. Policy reasons remain visible. Dimension values retain the report's original precision; missing values are labeled. Commit provenance remains a separate integration step.

Open `index.html` in a modern browser. No install, service, account, or network access is required. Choose **Open catalog JSON**, or explore the clearly labeled historical report. Nothing is uploaded or persisted by the app; clear or close the tab to discard imported data.

## Use with your repository

From your actual cad-automation checkout, generate a fresh report using the existing CLI:

```bash
cd ~/dev/cad-automation || exit 1
.venv/bin/python -m zcad.cli validate-catalog \
  designs/validation-catalog.example.json \
  --policy designs/validation-policy.example.json \
  --printer-profile profiles/printers/prusa-mk4.json \
  --json > /tmp/zcad-catalog-report.json
```

Open `/tmp/zcad-catalog-report.json` through the viewer. Nonzero CLI exits can represent failed validation; inspect the report and terminal errors. Empty or malformed output is rejected. In CI, download the JSON artifact and open it the same way.

These command paths come from the supplied successful terminal transcript. The current checkout and CI workflow were unavailable for verification. This package does not modify your repository or install itself.

## Evidence and limits

- Supported input: schema 1.0 catalog JSON as observed in the September 26, 2026 saved terminal transcript. The fixture is extracted from that actual output, not synthetic results.
- Displays catalog and design status, coverage, policy reasons, per-part checks, dimensions, and raw JSON. Search and status filtering work locally.
- Invalid counts, duplicate paths, unsupported versions/statuses, missing checks, and contradictory catalog PASS are rejected. This is structural sanity checking, not independent geometry validation or a replacement for the producer's policy evaluator.
- The observed catalog format does not record commit, timestamp, input hashes, profile identity, or exported artifact links. The viewer marks those fields unavailable and never infers freshness from file modification times. Original JSON preserves additional fields but they are not authenticated.
- Historical PASS means the recorded pre-export checks passed. Physical fit, manufacturing, artifact integrity, and current repository state remain unverified.
- No run button, repository scanning, server, persistence, external requests, or executable artifact links. Imported strings render as text.
- File limit: 10 MiB. Browser performance for very large catalogs is unqualified.

## Develop

Edit `index.template.html` and `model.js`, then run `python3 build.py`. Run `node --test test.cjs` for model tests. `index.html` is the self-contained distribution.

## Next integration gate

Inspect the live repository and catalog producer before adding a provenance envelope. Capture commit, dirty state, run time, catalog/policy/profile and input hashes at execution time. Add repo integration only after those fields are bound to the same validation run. No current-state or product-ready claim is justified by this prototype.
