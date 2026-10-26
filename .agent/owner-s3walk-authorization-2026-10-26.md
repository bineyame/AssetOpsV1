# Owner authorization: rebuild assetops_s3walk (2026-10-26)

Question asked: the demo-data tool for 22 mini-grid dispatch/analysis screens (batch-02 of the final recapture) can only run against the owner's walkthrough database `assetops_s3walk`: it drops and rebuilds it and has no test-copy option. Options: accept the gap / allow rebuilding s3walk / add a test-copy option.

Owner answer (verbatim selection): "Allow rebuilding s3walk".

Scope: run `tools/s3_dispatch_walkthrough.py` UNMODIFIED (no wrapper) so that it drops and recreates `assetops_s3walk` and uses its own work folder, for the final-recapture batch-02 dispatch/analysis pairs. This does not extend to any other non-test DB.
