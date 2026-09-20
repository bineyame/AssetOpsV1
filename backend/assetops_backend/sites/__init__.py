"""Product-side Site and Site-template configuration package.

Everything in this package above `adapters/` is storage-agnostic: it speaks
domain records and port errors only. `tools/check-architecture.ps1` enforces
that, by banning the yaml, pathlib and sqlite3 modules and direct file
opening anywhere in this package outside `adapters/`, and by allowing imports
of `adapters/` from the single composition module only.

Two identity spaces live here and never merge: templates (`template_id`,
`template_version`) and Sites (`site_id`). Two ports serve them and stay
separate, with parallel error vocabularies rather than one shared family.

Sites live in one globally unique identity space spread over two stores: a
shipped read-only store that ships empty, and a writable user store. There is
no overlay and no precedence between them. The only write in the package is
create-if-absent on the user store; there is no update and no delete, because
M1 has decided configuration is fixed at creation and removal is a developer
action on the store.
"""

__all__ = [
    "identity",
    "models",
    "ports",
    "parsing",
    "service",
    "site_parsing",
]
