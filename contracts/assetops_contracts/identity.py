"""Canonical encoding and the BLAKE2b-256 identity domain, v4 section 9.

Two rules from v4 and one consequence.

**The hash family is named and fixed.** `hashlib.blake2b(payload,
digest_size=32)`. Python's `hash()` is never used: it is salted per process, so
two runs of the same inputs in two processes would disagree about their own
identity.

**The identity domain is separated from the RNG domain.**
`assetops-sim-identity-v1` prefixes every identity digest. v4 reserves
`assetops-sim-rng-v1` for stochastic draws, and this build declares no
stochastic mechanism, so that prefix is not spelled here: a domain constant with
no consumer is a promise, and T022 adds it with the first stream that consumes
one.

**The encoding is length-prefixed rather than concatenated.** `("a", "bc")` and
`("ab", "c")` join to the same string and must not hash to the same digest.
Every field is written as its byte length followed by its bytes, so a boundary
between two fields is part of the payload rather than a convention about how to
read it.

A `Fraction` is encoded as `numerator/denominator` in lowest terms, which is the
form `Fraction` normalizes to, so the exact rational a step produced is what the
digest sees. A float never reaches this module: a trajectory that hashed a
binary approximation of its own exact arithmetic would have an identity the
arithmetic does not determine.
"""

from __future__ import annotations

import hashlib
from fractions import Fraction

#: The domain separator every identity digest in this product carries.
IDENTITY_DOMAIN = "assetops-sim-identity-v1"

#: The named hash family, so a record can say which one produced its digest.
DIGEST_NAME = "BLAKE2b-256"
DIGEST_SIZE = 32


def encode_field(value: object) -> bytes:
    """One field as length-prefixed bytes.

    `int`, `str`, `Fraction`, `bool` and `None` are the value kinds a frozen
    input or a trajectory holds. Anything else is refused rather than coerced:
    a `repr` in a digest payload is an identity that changes when a dataclass
    gains a field.
    """
    if value is None:
        token = "\x00none"
    elif isinstance(value, bool):
        token = f"\x00bool:{'1' if value else '0'}"
    elif isinstance(value, int):
        token = f"\x00int:{value}"
    elif isinstance(value, Fraction):
        token = f"\x00rat:{value.numerator}/{value.denominator}"
    elif isinstance(value, str):
        token = f"\x00str:{value}"
    else:
        raise TypeError(
            f"{type(value).__name__} has no canonical encoding, so it cannot "
            "enter an identity digest. A float cannot: exact rational "
            "arithmetic whose identity was taken over a binary approximation "
            "would not be determined by the arithmetic."
        )

    encoded = token.encode("utf-8")
    return f"{len(encoded)}:".encode("ascii") + encoded


def canonical_payload(fields: object) -> bytes:
    """A nested structure of fields as one canonical byte string.

    Lists and tuples are written with their length first, so a sequence of two
    items and the concatenation of its members are different payloads.
    Mappings are refused: an iteration order would decide the digest, and a
    caller that means an ordered sequence of pairs can write one.
    """
    if isinstance(fields, (list, tuple)):
        parts = [f"seq:{len(fields)}".encode("ascii")]
        parts.extend(canonical_payload(item) for item in fields)
        body = b"".join(parts)
        return f"{len(body)}:".encode("ascii") + body
    if isinstance(fields, dict):
        raise TypeError(
            "A mapping has no canonical order, so it cannot enter a digest. "
            "Write an ordered sequence of pairs and say what the order is."
        )
    return encode_field(fields)


def identity_digest(fields: object) -> str:
    """The hexadecimal identity of a canonically encoded structure.

    The domain separator is the first field rather than a string prepended to
    the payload, so it is length-prefixed like every other field and cannot be
    confused with the beginning of the content.
    """
    payload = canonical_payload([IDENTITY_DOMAIN, fields])
    return hashlib.blake2b(payload, digest_size=DIGEST_SIZE).hexdigest()
