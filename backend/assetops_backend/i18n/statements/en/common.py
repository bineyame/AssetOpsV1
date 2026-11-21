"""SC-1 (spec section 5.3): shared statements every screen may use. Pure literal data (D-SC1.3)."""
STATEMENTS = {
    # The honesty rule in data: "Not analysed yet" only while `pending` (system work) is true.
    "common.not_available": {
        "slots": {"needs": {"type": "items", "of": {"type": "word", "vocabulary": "record", "form": "in_sentence"},
                            "order": "vocabulary", "optional": True},
                  "pending": {"type": "flag"}},
        "variants": [{"id": "analysing", "when": {"is": ["pending", True]}, "text": "Not analysed yet."},
                     {"id": "needs", "when": {"present": "needs"}, "text": "Not available yet: it needs {needs}."},
                     {"id": "plain", "text": "Not available yet."}],
    },
    "common.budget_lines": {
        "slots": {"factors": {"type": "items", "of": {"type": "word", "vocabulary": "factor", "form": "in_sentence"},
                              "order": "vocabulary"}},
        "variants": [{"id": "one", "when": {"cmp": ["factors.count", "==", {"const": 1}]},
                      "text": "a budget line for {factors}"},
                     {"id": "many", "text": "budget lines for {factors}"}],
    },
}
