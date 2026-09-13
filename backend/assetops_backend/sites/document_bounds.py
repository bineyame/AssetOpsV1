"""Document bounds, shared by the template parser and the Site parser.

Both parsers refuse a pathological document before doing any field-level work
on it, and both must refuse it the same way. A user-authored Site document is
untrusted input; a shipped template document is trusted only in the sense that
somebody reviewed it. Neither is allowed to exhaust memory, nest without limit,
or fill a screen with ten thousand rows, and an oversized document must not be
able to make the Sites index unopenable.

This module walks an already-loaded structure. It opens nothing, decodes
nothing, and locates nothing, so it needs no exemption from the
storage-technology guard in `tools/check-architecture.ps1`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, NoReturn


@dataclass(frozen=True)
class DocumentLimits:
    """Bounds for one document family."""

    max_nodes: int
    max_text_length: int
    max_nesting_depth: int


def reject_oversized(
    document: Any,
    *,
    source: str,
    limits: DocumentLimits,
    invalid: Callable[[str], NoReturn],
    document_kind: str,
) -> None:
    """Refuse a document that is too large, too deep, or too wordy.

    Args:
        document: the already-loaded structure. Never a path or handle.
        source: a human-readable name for the document, used in messages only.
        limits: the bounds for this document family.
        invalid: raises the caller's configuration-invalid error. Passing the
            raiser rather than the exception class is what lets the two
            parsers keep their own error vocabularies while sharing one
            implementation of the rule.
        document_kind: how the message names the document, so a refusal reads
            as product text rather than as a generic parser message.
    """
    nodes = 0
    text_length = 0
    pending: list[tuple[Any, int]] = [(document, 0)]

    while pending:
        value, depth = pending.pop()

        nodes += 1
        if nodes > limits.max_nodes:
            invalid(
                f"{document_kind} in {source} has more than "
                f"{limits.max_nodes} nodes"
            )
        if depth > limits.max_nesting_depth:
            invalid(
                f"{document_kind} in {source} is nested deeper than "
                f"{limits.max_nesting_depth} levels"
            )

        if isinstance(value, str):
            text_length += len(value)
            if text_length > limits.max_text_length:
                invalid(
                    f"{document_kind} in {source} holds more than "
                    f"{limits.max_text_length} characters of text"
                )
        elif isinstance(value, Mapping):
            for key, child in value.items():
                pending.append((key, depth + 1))
                pending.append((child, depth + 1))
        elif isinstance(value, (list, tuple)):
            for child in value:
                pending.append((child, depth + 1))
