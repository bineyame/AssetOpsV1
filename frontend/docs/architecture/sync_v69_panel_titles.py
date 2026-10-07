"""Refresh panel display titles from the rendered mock inventory without changing decisions."""

import json
from pathlib import Path

here = Path(__file__).resolve().parent
inventory = json.loads((here / "v69-rendered-panels.json").read_text(encoding="utf-8"))["panels"]
path = here / "v69-panel-contracts.json"
ledger = json.loads(path.read_text(encoding="utf-8"))
for row in ledger["panels"]:
    row["panel_title"] = inventory[row["screen_id"]][row["panel_index"] - 1]["title"]
    row["tier_approval"] = "pending owner review"
path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
