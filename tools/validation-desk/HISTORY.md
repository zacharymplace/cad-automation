# Run history

Open history.html locally and select a reports folder. Each folder containing
receipt.json is loaded independently through the shared comparison loader,
receipt validator, catalog validator, and SHA-256 verifier.

Original receipts and recorded repository snapshots remain unchanged.
Integrity and receipt-consistency concerns do not rewrite recorded outcomes.
Incomplete/rejected receipts remain visible as load errors; only accepted
completed receipts can be compared. Missing catalogs do not imply removed designs.
Cancel retains fully processed entries and discards late results.
Clear removes imported evidence from the page; source files remain unchanged.

Sample history and repository discovery are explicitly simulated. No real
repository discovery or command execution is implemented. Files stay in the tab;
there is no persistence or network access.

build.py generates both pages from shared sources; verify.py checks both outputs
and discovers history.test.cjs alongside the existing tests.
The standalone predecessor was manually exercised in Arc by the user.
Automated tests use a DOM stub, not a rendering engine; keyboard and responsive
browser verification remain incomplete.
