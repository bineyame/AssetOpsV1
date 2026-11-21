"""DS4 T8: the bulk load's batch-cover rule, pure (spec §3.7, §5 T8; D-DS4.17). No database."""

from __future__ import annotations

import pytest

from assetops_backend.evidence.bulk_load import BatchTimeUnreadable, cover_gap, envelope_span

ADDIS = "Africa/Addis_Ababa"


def point(t: str):
    return envelope_span(t, None, None)


def interval(start: str, end: str):
    return envelope_span(start, start, end)


def test_a_local_gap_contiguous_in_utc_is_refused_on_the_local_grain():
    detail = cover_gap([point("2026-10-06T10:00:00Z"), point("2026-10-07T22:00:00Z")], ADDIS)
    assert detail is not None and detail.startswith("local ")
    assert detail.endswith("differs at 2026-10-07")


def test_b_contiguous_points_pass():
    assert cover_gap([point("2026-10-06T10:00:00Z"), point("2026-10-07T10:00:00Z")], ADDIS) is None


def test_c_one_point_passes_and_no_spans_pass():
    assert cover_gap([point("2026-10-06T10:00:00Z")], ADDIS) is None
    assert cover_gap([], ADDIS) is None


def test_d_a_multi_day_interval_covers_the_days_of_a_point_inside_and_after_it():
    spans = [interval("2026-10-05T21:00:00Z", "2026-10-08T21:00:00Z"), point("2026-10-09T10:00:00Z")]
    assert cover_gap(spans, ADDIS) is None


def test_e_an_interval_across_local_midnight_counts_both_days():
    spans = [interval("2026-10-06T20:45:00Z", "2026-10-06T21:15:00Z"), point("2026-10-07T22:00:00Z")]
    assert cover_gap(spans, ADDIS) is None


def test_f_a_point_at_local_midnight_as_the_last_instant_is_missed_by_the_cover():
    detail = cover_gap([point("2026-10-06T10:00:00Z"), point("2026-10-06T21:00:00Z")], ADDIS)
    assert detail is not None and detail.startswith("local ")
    assert detail.endswith("differs at 2026-10-07")


def test_g_contiguous_local_days_far_from_utc_can_open_a_utc_gap():
    detail = cover_gap([point("2026-10-05T10:30:00Z"), point("2026-10-07T09:30:00Z")], "Pacific/Kiritimati")
    assert detail is not None and detail.startswith("utc ")
    assert detail.endswith("differs at 2026-10-06")


def test_envelope_span_prefers_the_interval_over_source_time():
    start, end = envelope_span("2026-10-06T12:00:00Z", "2026-10-06T10:00:00Z", "2026-10-06T11:00:00+03:00")
    assert start.isoformat() == "2026-10-06T10:00:00+00:00"
    assert end.isoformat() == "2026-10-06T11:00:00+03:00"
    assert envelope_span("2026-10-06T12:00:00Z", None, None)[0] == envelope_span("2026-10-06T12:00:00Z", None, None)[1]


@pytest.mark.parametrize(
    ("args", "field"),
    [
        (("not a time", None, None), "source_time"),
        (("2026-10-06T10:00:00", None, None), "source_time"),
        ((None, None, None), "source_time"),
        ((1760000000, None, None), "source_time"),
        (("2026-10-06T10:00:00Z", "not a time", "2026-10-06T11:00:00Z"), "interval_start"),
        (("2026-10-06T10:00:00Z", "2026-10-06T10:00:00Z", "2026-10-06T11:00:00"), "interval_end"),
        (("2026-10-06T10:00:00Z", 5, "2026-10-06T11:00:00Z"), "interval_start"),
    ],
)
def test_envelope_span_unreadable_names_the_field(args, field):
    with pytest.raises(BatchTimeUnreadable) as caught:
        envelope_span(*args)
    assert type(caught.value) is BatchTimeUnreadable
    assert caught.value.field == field
