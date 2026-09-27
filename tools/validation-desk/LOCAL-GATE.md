# Local runner viewer gate

The local runner executes a separate viewer gate after Python tests and before catalog validation:

    python tools/validation-desk/verify.py

It checks generated index.html byte-for-byte against the template, scripts and fixture, without writing it, then runs test.cjs and all *.test.cjs with Node.js on PATH. Node must support the viewer's node:test and Blob APIs (Node 18 or later). Missing Node, stale/missing HTML, or failed tests produce a nonzero gate result. Later runner gates still execute.

Repair stale HTML explicitly with python3 tools/validation-desk/build.py. Verification never repairs it silently.

viewer.stdout.log and viewer.stderr.log are recorded and hashed by the existing runner. A five-gate completed run references ten artifact files. Old receipts remain unchanged. Artifact integrity and gate outcomes stay separate.
