# Local validation runner

From cad-automation, run:

```bash
.venv/bin/python -m zcad.local_ci --output-parent ~/Downloads/zcad-ci-reports
```

Use the existing development environment with Ruff, pytest, and zcad-core installed
editable from its Git checkout. The runner discovers the core actually imported by
this Python interpreter, rather than assuming the adjacent folder is in use.
No dependencies are installed and no network or Git write operations are performed.

The gates run sequentially: automation formatting, lint, full automation tests,
then the example catalog and its committed policy using the Prusa profile.
This does not run the core repository's own test suite. Ordinary gate failures
do not skip later gates. Each gate defaults to a 1800-second timeout; set
`--timeout SECONDS` to change that limit.

Every run creates a fresh directory outside both repositories containing
`receipt.json`, stdout/stderr logs, and `catalog.json`. The catalog keeps its
existing schema so existing report viewers can read it. Provenance is in the
receipt alongside it. The runner checkpoints after each gate; interruption
retains available logs. Machine termination or storage failure can leave a
RUNNING receipt, which must never be interpreted as PASS.

Exit codes: 0 all gates passed; 1 one or more gates failed or errored;
2 setup/provenance/runner error; 130 interrupted. Dirty trees are allowed and
explicitly recorded. A changed observed Git state prevents an overall PASS.
SHA plus porcelain status does not freeze dirty contents or detect every
concurrent edit. Avoid editing during a run. These records are not source
attestations, clean-room builds, or product-readiness evidence.

Reports contain local paths, Git status filenames, commands, and tool output.
Review them before sharing. Retention is local and manual; choose a durable
output parent rather than the default system temporary directory.

The GitHub workflow has no push or pull-request triggers. Its optional manual
entry only displays instructions; local validation does not depend on Actions.
