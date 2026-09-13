"""Product-side Site and Site-template configuration package.

Everything in this package above `adapters/` is storage-agnostic: it speaks
domain records and port errors only. `tools/check-architecture.ps1` enforces
that, by banning the yaml, pathlib and sqlite3 modules and direct file
opening anywhere in this package outside `adapters/`, and by allowing imports
of `adapters/` from the single composition module only.

T005 scope: the shipped read-only Site Template catalog. No Site, no
`SiteRepository`, no writable store, and no write path exists here.
"""

__all__ = ["models", "ports", "parsing", "service"]
