"""D-0K4.19: a field of a legacy text family holds a legacy `str` or an SC-1 `Message`; its serving read calls this.

The migration seam for legacy text families (Foundation property names, model-profile statements). A `str` is the
legacy, baselined text and passes through unchanged; a `Message` is rendered at read for the request's locale. This
module is deleted when the last family is migrated (queue Q9).
"""
from assetops_backend.i18n import Message, render


def served_text(value: str | Message) -> str:
    return value if isinstance(value, str) else render(value)
