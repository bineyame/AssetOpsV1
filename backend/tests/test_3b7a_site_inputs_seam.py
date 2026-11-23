"""3B7a unit 0: the shared seam `StructureRead.site_inputs` (spec §2.1, §6 test 1; D-3B7A.7, D-3B7A.10). No database."""

from __future__ import annotations

from types import MappingProxyType

import pytest
from test_3a4_commercial_months import READ_AT
from test_4b_money_leaves import fallback, money_world, site

from assetops_backend.structure import registry as _registry
from assetops_backend.structure.check import StructureError
from assetops_backend.structure.evaluate import evaluate
from assetops_backend.structure.money import CommercialLeafSource
from assetops_backend.structure.read import SiteInputs, StructureRead, evaluate_inputs

OCT = "2026-10"
AS_OF = READ_AT
SITES = ("KOBO-001", "KISIWA-001", "MTO-001")


def counting_read(w, stated: bool = True):
    calls = {"site_month": 0}

    class Months:
        def site_month(self, *a, **k):
            calls["site_month"] += 1
            return w["months"].site_month(*a, **k)

    source = CommercialLeafSource(Months(), w["store"], fallback())
    return StructureRead(source, stated=source if stated else None), calls


@pytest.mark.parametrize("code", SITES)
def test_1_evaluate_inputs_equals_site(code):
    w = money_world()
    read, _ = counting_read(w)
    s = site(w, code)
    inputs = read.site_inputs(s, OCT, AS_OF)
    assert isinstance(inputs, SiteInputs)
    assert evaluate_inputs(inputs) == read.site(s, OCT, AS_OF)
    reg = _registry.REGISTRIES[inputs.structure_key]
    assert list(inputs.leaves) == [r.factor_id for r in reg.rows if r.is_leaf]
    assert len(inputs.leaves) == 31
    assert evaluate_inputs(inputs).values == evaluate(reg, inputs.leaves, inputs.stated)
    if code == "KOBO-001":  # the stated rows change the answer, so dropping them is seen
        assert evaluate_inputs(inputs).values != evaluate(reg, inputs.leaves)
    assert list(inputs.stated) == [r.factor_id for r in reg.rows if r.stated_by is not None]
    assert list(inputs.stated) == ["metered_kwh", "billed_kwh", "revenue"]  # 4a: stated kWh nodes; DD3d.4: fuel cost is not stated
    assert (inputs.site_code, inputs.month, inputs.structure_version) == (code, OCT, reg.version)
    assert isinstance(inputs.leaves, MappingProxyType) and isinstance(inputs.stated, MappingProxyType)


def test_1_no_stated_source_gives_empty_stated():
    w = money_world()
    read, _ = counting_read(w, stated=False)
    inputs = read.site_inputs(site(w, "KOBO-001"), OCT, AS_OF)
    assert inputs.stated == {} and isinstance(inputs.stated, MappingProxyType)
    assert evaluate_inputs(inputs) == read.site(site(w, "KOBO-001"), OCT, AS_OF)


def test_1_one_site_month_call_each():
    w = money_world()
    read, calls = counting_read(w)
    s = site(w, "KOBO-001")
    read.site_inputs(s, OCT, AS_OF)
    assert calls["site_month"] == 1
    read.site(s, OCT, AS_OF)
    assert calls["site_month"] == 2


def test_1_version_mismatch_is_compose_error():
    from dataclasses import replace

    w = money_world()
    read, _ = counting_read(w)
    inputs = read.site_inputs(site(w, "KOBO-001"), OCT, AS_OF)
    with pytest.raises(StructureError) as e:
        evaluate_inputs(replace(inputs, structure_version=inputs.structure_version + 1))
    assert e.value.code == "STRUCTURE_COMPOSE"
