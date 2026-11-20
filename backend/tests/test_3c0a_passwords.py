"""3C0a (spec §3, §9): the password hash, its policy and the email rule. No database."""
from __future__ import annotations

import re

import pytest

from assetops_backend.accounts.model import AccountRefused
from assetops_backend.accounts.passwords import (DUMMY_HASH, check_policy, hash_password, normalise_email,
                                                 verify_password)

#: The migration's CHECK on `account_credential.password_hash` (spec §2), as a Python pattern.
HASH_CHECK = re.compile(r"^scrypt\$32768\$8\$1\$[A-Za-z0-9_-]{22}\$[A-Za-z0-9_-]{43}$")
PW = "correct horse battery"


def test_hash_form_matches_the_database_check_and_verifies() -> None:
    stored = hash_password(PW)
    assert HASH_CHECK.fullmatch(stored), stored
    assert HASH_CHECK.fullmatch(DUMMY_HASH), DUMMY_HASH
    assert verify_password(PW, stored) is True
    assert verify_password(PW + "x", stored) is False
    assert hash_password(PW) != stored  # a fresh salt each time


def test_a_tampered_or_foreign_hash_fails_and_never_raises() -> None:
    stored = hash_password(PW)
    _, n, r, p, salt, digest = stored.split("$")
    flip = lambda s: ("B" if s[0] == "A" else "A") + s[1:]  # noqa: E731
    for bad in (f"scrypt${n}${r}${p}${flip(salt)}${digest}",       # salt
                f"scrypt${n}${r}${p}${salt}${flip(digest)}",       # hash
                f"scrypt$16384${r}${p}${salt}${digest}",           # parameter
                f"scrypt${n}$9${p}${salt}${digest}",
                f"bcrypt${n}${r}${p}${salt}${digest}",
                stored[:-1], "", "scrypt$$$$$", "not a hash"):
        assert verify_password(PW, bad) is False, bad


@pytest.mark.parametrize("length, ok", [(11, False), (12, True), (128, True), (129, False)])
def test_policy_length(length: int, ok: bool) -> None:
    pw = "p" * length
    if ok:
        check_policy(pw)
    else:
        with pytest.raises(AccountRefused) as refused:
            check_policy(pw)
        assert (refused.value.code, refused.value.status) == ("PASSWORD_POLICY", 422)


def test_policy_refuses_all_whitespace_and_keeps_the_password_as_typed() -> None:
    with pytest.raises(AccountRefused):
        check_policy(" " * 12)
    with pytest.raises(AccountRefused):
        check_policy("\t \n" * 5)
    check_policy("  spaced out  ")  # surrounding spaces are part of the password
    stored = hash_password("  spaced out  ")
    assert verify_password("  spaced out  ", stored) and not verify_password("spaced out", stored)


@pytest.mark.parametrize("text, expected", [
    ("Amina@Kobo.Example", ("Amina@Kobo.Example", "amina@kobo.example")),
    ("  joseph@example.org\t", ("joseph@example.org", "joseph@example.org")),
    ("a@b", ("a@b", "a@b")),
])
def test_normalise_email_trims_and_keys_lower_case(text: str, expected: tuple[str, str]) -> None:
    assert normalise_email(text) == expected


@pytest.mark.parametrize("text", [
    "no-at-sign.example",
    "two@at@signs.example",
    "a" * 64 + "@" + "b" * 256,          # 321 characters
    "x" * 65 + "@example.org",            # local part over 64
    "josé@example.org",              # a non-ASCII letter
    "nul\x00@example.org",                # a NUL
    "inner space@example.org",            # an inner space
    "@example.org", "local@", "", "   ",
])
def test_normalise_email_refuses(text: str) -> None:
    with pytest.raises(AccountRefused) as refused:
        normalise_email(text)
    assert (refused.value.code, refused.value.status) == ("BAD_EMAIL", 422)


def test_normalise_email_accepts_320_characters() -> None:
    email = "a" * 64 + "@" + "b" * 255
    assert len(email) == 320 and normalise_email(email)[1] == email
