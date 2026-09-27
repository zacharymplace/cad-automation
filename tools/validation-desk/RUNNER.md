# Runner integration v0.3

Open index.html. Extract the runner's output ZIP, then choose **Open runner folder** and select the directory containing receipt.json, catalog.json and logs. The installer ZIP is not an execution bundle.

Receipt schema follows the supplied zcad-local-ci-v1/files/src/zcad/local_ci.py. Execution-time timestamps, repository commits, dirty flags, commands, return codes and before/after snapshots are preserved. Original receipt JSON includes porcelain details. Failed and unfinished gates are expanded; passing gates and logs are collapsed. Catalog findings retain the v0.2 layout.

No current Git inspection, inferred freshness, rewritten provenance or hash attestation. The source runner records no artifact hashes. Companion files are associated by selected directory only. Inputs are displayed through textContent, never executed. Each text file is limited to 10 MiB. Unknown receipt schemas and malformed gate/snapshot structures are rejected. Checkpoint and error receipts can be viewed without catalog output.

Validation: six existing catalog tests plus three receipt tests and JavaScript syntax check. No completed execution receipt was supplied in this task; the attachment contains installer/source only. Real-run integration and interactive browser verification remain outstanding.
