"""IA-P P3a and P4a (`spec-period.md` P.5 and P.8; D-IAP.9, D-IAP.20, D-IAP.26): the Sites rows' words for the same
months as the Overview (E1), and the month row's contribution and driver E2 shares with them.

Pure literal data (D-SC1.3), the 1a pattern. A driver is its factor's label and its signed amount, each already a
statement's text (`deep_dive.label`, `deep_dive.money`); a period is `portfolio_period.span`'s text.
"""
STATEMENTS = {
    "portfolio_sites.headline": {
        "slots": {"sites": {"type": "k_of_n"}, "period": {"type": "name"},
                  "below": {"type": "state", "values": ["SOME", "NONE"]}},
        "variants": [
            {"id": "some", "when": {"is": ["below", "SOME"]}, "text": "{sites} are below target in {period}"},
            {"id": "none", "text": "Every Site is on or above target in {period}"},
        ],
        "rephrase": "never",
    },
    "portfolio_sites.months": {
        "slots": {"months": {"type": "k_of_n"}},
        "variants": [{"id": "months", "text": "Compared in {months}"}],
        "rephrase": "never",
    },
    "portfolio_sites.contribution": {
        "evidence": "served",
        "slots": {"actual": {"type": "money"}, "target": {"type": "money"}},
        "variants": [{"id": "contribution", "text": "{actual} against a target of {target}"}],
        "rephrase": "never",
    },
    "portfolio_sites.driver": {
        "slots": {"factor": {"type": "name"}, "effect": {"type": "name"}},
        "variants": [{"id": "driver", "text": "{factor} {effect}"}],
        "rephrase": "never",
    },
    "portfolio_sites.no_driver": {
        "variants": [{"id": "no_driver", "text": "No driver widens the gap"}],
        "rephrase": "never",
    },
    "portfolio_sites.no_figures": {
        "slots": {"domain": {"type": "state", "values": ["COLDCHAIN", "EV_CHARGING"]}},
        "variants": [
            {"id": "coldchain", "when": {"is": ["domain", "COLDCHAIN"]},
             "text": "No monthly figures for cold-chain Sites yet"},
            {"id": "ev_charging", "text": "No monthly figures for EV charging Sites yet"},
        ],
        "rephrase": "never",
    },
    "portfolio_sites.without_target": {
        "slots": {"count": {"type": "count"}, "number": {"type": "state", "values": ["ONE", "SEVERAL"]}},
        "variants": [
            {"id": "one", "when": {"is": ["number", "ONE"]}, "text": "{count} without a target is not in this figure"},
            {"id": "several", "text": "{count} without a target are not in this figure"},
        ],
        "rephrase": "never",
    },
    "portfolio_sites.group": {
        "slots": {"domain": {"type": "state", "values": ["MINIGRID", "COLDCHAIN", "EV_CHARGING"]}},
        "variants": [
            {"id": "minigrid", "when": {"is": ["domain", "MINIGRID"]}, "text": "Mini-grid"},
            {"id": "coldchain", "when": {"is": ["domain", "COLDCHAIN"]}, "text": "Cold-chain"},
            {"id": "ev_charging", "text": "EV charging"},
        ],
        "rephrase": "never",
    },
    "portfolio_sites.text": {
        "slots": {"piece": {"type": "state", "values": ["GROUP", "WAITING"]}},
        "variants": [
            {"id": "group", "when": {"is": ["piece", "GROUP"]}, "text": "Group"},
            {"id": "waiting", "text": "Waiting for a choice"},
        ],
        "rephrase": "never",
    },
}
