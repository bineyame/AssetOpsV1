"""0K4b (spec `specs/0K4b-fuel-curve-taper/spec.md` section 2.6, D-0K4.19): a Foundation property's name, as a
statement over the `foundation_property` vocabulary. Pure literal data (D-SC1.3)."""
STATEMENTS = {
    "foundation.property_name": {
        "slots": {"property": {"type": "word", "vocabulary": "foundation_property", "form": "label"}},
        "variants": [{"id": "label", "text": "{property}"}],
        "rephrase": "never",
    },
}
