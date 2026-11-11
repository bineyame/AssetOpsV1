"""UQ-6a (D-I18N.1): the server message contract.

A word the server sends is a `Message` - a catalogue `key` and typed `params` - and is rendered for the request's
locale at read (`i18n.render`), never stored as composed text. The catalogue holds one template per key per locale;
English is the complete reference locale. UQ-6b moves the existing server words into it; until then it holds the
keys converted so far.
"""
from __future__ import annotations

from typing import Mapping, TypedDict, Union

#: A typed message parameter. Formatting numbers, dates and money by locale (Babel) comes with UQ-4.
Param = Union[str, int, float]


class Message(TypedDict):
    key: str
    params: Mapping[str, Param]


def message(key: str, **params: Param) -> Message:
    return {"key": key, "params": dict(params)}


#: locale -> key -> `str.format` template over the message's params.
CATALOGUE: dict[str, dict[str, str]] = {
    "en": {
        "analytics.site_not_found": "No Site {site_id} is configured.",
    },
}
