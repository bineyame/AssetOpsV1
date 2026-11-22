"""0K4b (spec `specs/0K4b-fuel-curve-taper/spec.md` section 2.6, D-0K4.19): a Foundation property's name, as a
statement over the `foundation_property` vocabulary. Pure literal data (D-SC1.3)."""
STATEMENTS = {
    "foundation.property_name": {
        "slots": {"property": {"type": "word", "vocabulary": "foundation_property", "form": "label"}},
        "variants": [{"id": "label", "text": "{property}"}],
        "rephrase": "never",
    },
    # DD3.2 (D-DD.17): where an equipment value comes from, read from a `-basis` property and the data-sheet slot
    # (`config/datasheets/kobo-equipment.json`): maker, model and revision for a sheet value, the slot's basis text for
    # a generic default.
    "component_property.basis": {
        "slots": {
            "basis": {"type": "state", "values": ["MANUFACTURER_DATASHEET", "DATASHEET_FIT", "GENERIC_DEFAULT"]},
            "maker": {"type": "name", "optional": True},
            "model": {"type": "name", "optional": True},
            "revision": {"type": "name", "optional": True},
            "reason": {"type": "name", "optional": True},
        },
        "variants": [
            {"id": "declared", "when": {"is": ["basis", "MANUFACTURER_DATASHEET"]},
             "text": "Declared, from the manufacturer data sheet ({maker} {model}, {revision})"},
            {"id": "fit", "when": {"is": ["basis", "DATASHEET_FIT"]},
             "text": "Assumed: fitted to the data sheet's stated points ({maker} {model}); the sheet states no value"},
            {"id": "generic", "when": {"is": ["basis", "GENERIC_DEFAULT"]}, "text": "Assumed: {reason}"},
        ],
        "exhaustive": "basis",
        "rephrase": "never",
    },
}
