"""Storage adapters for Site configuration.

This is the only package in `sites/` allowed to know a storage technology.
`tools/check-architecture.ps1` permits imports that resolve in here from the
single composition module only, so replacing the store stays one new adapter
module plus one composition change, with no change to any caller.
"""
