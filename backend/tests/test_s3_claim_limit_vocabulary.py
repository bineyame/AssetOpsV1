"""The claim-limit read maps dispatch-3.2 problem text to coverage statuses by substring. This ties that table to
the model, so a wording change without a model bump fails here instead of silently reading as COVERED."""

from assetops_backend.analytics import claim_limit_read as read
from assetops_backend.analytics import dispatch_v3


EXPECTED = {"UNBOUND": read.MISSING, "MULTIPLE_BINDINGS": read.MISSING, "MISSING": read.MISSING,
            "NOT_GOOD": read.POOR, "CONFLICTING": read.CONFLICTED, "AMBIGUOUS_SERIES": read.CONFLICTED,
            "NOT_CONFIGURED": read.MISSING}


def test_every_dispatch_problem_text_maps_to_its_status_by_a_table_needle() -> None:
    assert dispatch_v3.MODEL_VERSION == "dispatch-3.2", "model changed: re-derive claim_limit_read._PROBLEM_STATUS"
    assert set(dispatch_v3._PROBLEM_TEXT) == set(EXPECTED), "new/removed problem code: extend the table"
    for code, text in dispatch_v3._PROBLEM_TEXT.items():
        matched = [status for needle, status in read._PROBLEM_STATUS if needle in text]
        # The fail-closed default (MISSING) must not be what carries a POOR or CONFLICTED problem.
        assert matched and matched[0] == EXPECTED[code], (code, text, matched)


def test_labels_map_to_roles() -> None:
    for role, label in dispatch_v3.LABELS.items():
        if role in read.REQUIRED_ROLES:
            assert read._LABEL_ROLE[label] == role
