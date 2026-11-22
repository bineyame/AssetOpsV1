# DD1 readiness parity goldens (D-DD.45)

`readiness()` for COLD-LAB-001, COLD-KIRI (DD1 world conversion) and EV-LAB-001, captured from main `05be2b968`.
Serialisation: `json.dumps(x, sort_keys=True, indent=1)`, every UUID replaced by `uuid-<n>` in first-appearance order.

Capture: in a temporary worktree at `05be2b968` (`git worktree add --detach <dir> 05be2b968`), copy in
`backend/tests/test_dd1_readiness_parity_postgres.py`, `backend/conversions/world/`, and `backend/tests/fixtures/on1/`
from this branch. COLD-KIRI needs the onboarding file format, which main's `onboard_operator` refuses, so also copy this
branch's onboarding machinery (`evidence/provision_gateway.py`, `onboard_operator.py`, `onboarding/*`,
`sites/{ev_foundation,foundation_parsing,parsing,site_parsing}.py`). Keep main's `sites/binding_roles.py` and
`sites/binding_service.py`, which are the code under comparison. Then, from that worktree root:

    DD1_PARITY_CAPTURE_DIR=<dir>/backend/tests/fixtures/dd1_readiness_parity \
      tools/heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- backend/tests/test_dd1_readiness_parity_postgres.py

Note: on main both cold Sites read INCOMPLETE (policy controls not configured, Site-type gap); no channel role is
missing. The goldens record main as it is.
