"""D-DD.42: Site document limits 10,000 nodes and 96 devices; a document at the limit parses, one over refuses."""
from __future__ import annotations

import copy

import pytest
from test_foundation_content_parsing import FAMILIES

from assetops_backend.document_bounds import reject_oversized
from assetops_backend.sites.foundation_parsing import MAX_DEVICES
from assetops_backend.sites.parsing import MAX_DOCUMENT_NODES
from assetops_backend.sites.ports import SiteConfigurationInvalid
from assetops_backend.sites.site_parsing import SITE_DOCUMENT_LIMITS


def _walk(document, limits):
    def invalid(message):
        raise SiteConfigurationInvalid(message)

    reject_oversized(document, source="t", limits=limits, invalid=invalid, document_kind="Site document")


def test_the_limits_are_the_ruled_values() -> None:
    assert (MAX_DOCUMENT_NODES, SITE_DOCUMENT_LIMITS.max_nodes, MAX_DEVICES) == (10_000, 10_000, 96)


def test_a_site_document_at_the_node_limit_is_read_and_one_over_is_refused() -> None:
    _walk(list(range(SITE_DOCUMENT_LIMITS.max_nodes - 1)), SITE_DOCUMENT_LIMITS)  # the list is the first node
    with pytest.raises(SiteConfigurationInvalid, match="more than 10000 nodes"):
        _walk(list(range(SITE_DOCUMENT_LIMITS.max_nodes)), SITE_DOCUMENT_LIMITS)


@pytest.mark.parametrize("foundation_of,parse,refusal", FAMILIES)
def test_a_foundation_with_96_devices_parses_and_97_names_the_device_cap(foundation_of, parse, refusal) -> None:
    def grown(n):
        foundation = copy.deepcopy(foundation_of())
        sample = foundation["devices"][0]
        foundation["devices"] = [{**copy.deepcopy(sample), "device_id": f"device-{i}"} for i in range(n)]
        foundation["signal_mappings"] = None
        return foundation

    assert len(parse(grown(MAX_DEVICES)).devices) == MAX_DEVICES
    with pytest.raises(refusal) as error:
        parse(grown(MAX_DEVICES + 1))
    assert "96" in str(error.value) and "has more than" not in str(error.value)


def test_the_operator_file_byte_bound_is_kept() -> None:
    from assetops_backend.onboarding.operator_file import MAX_BYTES

    assert MAX_BYTES == 256 * 1024
