import pytest
from test_w302_w1_claim_limit_on_postgres import *  # noqa
from test_w302_w1_claim_limit_on_postgres import SPEC, runner, engine, store  # noqa

@pytest.mark.parametrize("cid", ["F02","F06","F04","F08","F03","F01","F05"])
def test_x(cid, runner):
    case = next(c for c in SPEC["cases"] if c["case_id"] == cid)
    for st in case["steps"]:
        if st["do"] in ("deliver","release","assess","reserve","runtime"):
            runner.step(st)
    with runner.engine.connect() as c:
        rows = c.execute(text("SELECT assessment_revision_id, count(DISTINCT run_id) n FROM analytic_run_assessment WHERE site_id=:s AND scope='INTERVAL' GROUP BY 1 HAVING count(DISTINCT run_id)>1"),{"s":runner.site}).all()
    print("RESULT", cid, len(rows))
