"""UQ-6a (D-I18N.1): render a `Message` for a locale at read."""
from __future__ import annotations

from assetops_backend.i18n.locale import DEFAULT_LOCALE, current_locale
from assetops_backend.i18n.messages import CATALOGUE, Message


def render(msg: Message, locale: str | None = None) -> str:
    """The message's template for `locale` (the request's locale when None), else the English template, filled
    with its params. Params are inserted verbatim, never read as a template. An unknown key raises `KeyError`."""
    loc = current_locale() if locale is None else locale
    template = CATALOGUE.get(loc, {}).get(msg["key"])
    if template is None:
        template = CATALOGUE[DEFAULT_LOCALE][msg["key"]]
    return template.format_map(dict(msg["params"]))
