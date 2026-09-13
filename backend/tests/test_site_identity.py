"""Tests for `site_id` constraints, the first untrusted-input boundary.

`site_id` is the only Site identity and every later run, envelope, evidence
record, and analytic will be keyed on it. So these tests are about two things:
that a hostile or careless identity cannot escape the store or fork identity,
and that the rules are the same on every host rather than inherited from
whatever filesystem happens to be underneath.
"""

from __future__ import annotations

import pytest

from assetops_backend.sites.identity import (
    MAX_SITE_ID_LENGTH,
    site_id_key,
    validate_site_id,
)
from assetops_backend.sites.ports import SiteConfigurationInvalid


class TestAcceptedIdentities:
    @pytest.mark.parametrize(
        "site_id",
        ["MG-001", "mg-002", "CC-001", "site_1", "A1", "a" * MAX_SITE_ID_LENGTH],
    )
    def test_a_well_formed_site_id_is_accepted_unchanged(self, site_id: str) -> None:
        assert validate_site_id(site_id) == site_id


class TestRefusedIdentities:
    @pytest.mark.parametrize(
        ("site_id", "reason"),
        [
            pytest.param("MG/001", "separator", id="forward-slash"),
            pytest.param("MG\\001", "backslash", id="backslash"),
            pytest.param("..", "dot-dot", id="parent-directory"),
            pytest.param(".", "dot", id="current-directory"),
            pytest.param("../MG-001", "traversal", id="relative-traversal"),
            pytest.param("/MG-001", "absolute", id="absolute-posix"),
            pytest.param("C:\\MG-001", "drive", id="absolute-windows"),
            pytest.param("\\\\server\\share", "unc", id="unc-path"),
            pytest.param("", "empty", id="empty"),
            pytest.param("   ", "whitespace", id="whitespace"),
            pytest.param("M", "too-short", id="single-character"),
            pytest.param("a" * (MAX_SITE_ID_LENGTH + 1), "too-long", id="over-length"),
            pytest.param("MG 001", "space", id="inner-space"),
            pytest.param("-MG-001", "leading-hyphen", id="leading-hyphen"),
            pytest.param("MG-001-", "trailing-hyphen", id="trailing-hyphen"),
            pytest.param("MG.001", "dot", id="inner-dot"),
            pytest.param("MG%2F001", "percent", id="percent-encoded"),
            pytest.param("MG\u0000001", "nul", id="nul-byte"),
            pytest.param("MG\n001", "newline", id="newline"),
            pytest.param("Kalangala Mini-Grid", "display-name", id="display-name"),
        ],
    )
    def test_a_malformed_site_id_is_refused(self, site_id: str, reason: str) -> None:
        with pytest.raises(SiteConfigurationInvalid):
            validate_site_id(site_id)

    @pytest.mark.parametrize("site_id", ["CON", "con", "nul", "COM1", "LPT9", "AUX"])
    def test_a_windows_reserved_device_name_is_refused_on_every_host(
        self, site_id: str
    ) -> None:
        """Legal under the charset rule, but not a file name on Windows.

        Refused everywhere, so a document that can be created on one developer
        machine can be created on all of them.
        """
        with pytest.raises(SiteConfigurationInvalid, match="reserved device name"):
            validate_site_id(site_id)

    @pytest.mark.parametrize("value", [None, 1, True, ["MG-001"], {"site_id": "MG-001"}])
    def test_a_non_text_site_id_is_refused(self, value: object) -> None:
        with pytest.raises(SiteConfigurationInvalid):
            validate_site_id(value)

    def test_a_refusal_names_what_would_be_acceptable(self) -> None:
        """Refusal copy is product text: it must say what to do instead."""
        with pytest.raises(SiteConfigurationInvalid) as refusal:
            validate_site_id("MG 001")

        message = str(refusal.value)
        assert "MG 001" in message
        assert "letters, digits, hyphens, and underscores" in message
        assert "MG-002" in message
        assert "Traceback" not in message


class TestCaseInsensitiveIdentity:
    @pytest.mark.parametrize(
        ("left", "right"),
        [("MG-002", "mg-002"), ("Mg-002", "mG-002"), ("SITE_1", "site_1")],
    )
    def test_case_variants_share_one_identity_key(self, left: str, right: str) -> None:
        assert site_id_key(left) == site_id_key(right)

    def test_different_identities_do_not_share_a_key(self) -> None:
        assert site_id_key("MG-001") != site_id_key("MG-002")

    def test_the_key_is_a_comparison_key_and_not_the_identity(self) -> None:
        """The canonical spelling is what the record carries and what shows."""
        assert validate_site_id("MG-002") == "MG-002"
        assert site_id_key("MG-002") == "mg-002"
