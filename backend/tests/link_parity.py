"""CH-5a2a test helper: every legacy link on a body equals `href_for` of its sibling Ref (CH5a2-R4(a)).

`checked(body)` walks a body, asserts `href == href_for(link_ref)`, `destination == href_for(link_ref)` and
`links[k] == href_for(link_refs[k])` wherever the Ref sibling is present, and returns the body without the Ref
siblings, so the pre-CH-5a2 equality assertions keep pinning the legacy shape."""
from __future__ import annotations

from typing import Any

from assetops_backend.chain.refs import href_for


def checked(body: Any) -> Any:
    if isinstance(body, list):
        return [checked(x) for x in body]
    if not isinstance(body, dict):
        return body
    if "link_ref" in body:
        legacy = "href" if "href" in body else "destination"
        assert body[legacy] == href_for(body["link_ref"]), (body[legacy], body["link_ref"])
    if "link_refs" in body:
        for key, ref in body["link_refs"].items():
            assert body["links"][key] == href_for(ref), (key, body["links"][key], ref)
    return {k: checked(v) for k, v in body.items() if k not in ("link_ref", "link_refs")}
