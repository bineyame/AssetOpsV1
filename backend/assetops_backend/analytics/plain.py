"""The plain reading of a stored dispatch assessment and of readiness.

Presentation projection under `D-2026-10-04-plain-language-analysis-views`:
the default views and the Analysis views describe a site and its operation in
plain words. Every sentence here is generated at read time from the stored,
structured assessment (classifications, constraint ids, quantities, input
names, alternative ids and statuses); nothing is persisted, so no revision is
added and `dispatch-2` / `readiness-3` semantics are unchanged. Stored text is
never rewritten; where a stored list is a fixed template (confidence basis,
missing-input lines) it is read by template and restated, and an unknown line
becomes an explicit "detail unavailable" rather than being passed through.

The projection interprets nothing the assessment does not already state: it
names the same bounds, the same uncertainty and the same limits.
"""
from __future__ import annotations

import re
from typing import Any

from . import dispatch

CANDIDATE, NECESSARY, INDETERMINATE = dispatch.CANDIDATE, dispatch.NECESSARY, dispatch.INDETERMINATE

#: Display labels for the three backend classifications (not new states).
OUTCOMES = {
    CANDIDATE: "Possibly avoidable",
    NECESSARY: "Needed",
    INDETERMINATE: "Cannot determine",
}

#: Plain names of the assessment's inputs, keyed by the stored input labels.
INPUT_NAMES = {
    dispatch.INPUT_LABELS["load"]: "Site demand",
    dispatch.INPUT_LABELS["pv_available"]: "Available solar power",
    dispatch.INPUT_LABELS["soc"]: "Battery charge",
    dispatch.INPUT_LABELS["reserve"]: "Minimum battery reserve",
    dispatch.INPUT_LABELS["discharge_capability"]: "Available battery output",
    "Generator state (status or output)": "Generator operation",
}

#: Plain names of the evidence roles a declaration and readiness name.
ROLE_NAMES = {
    "Generator state": "Generator operation",
    "Generator state and output": "Generator operation and output",
    "Load": "Site demand",
    "PV capability": "Available solar power",
    "Battery state": "Battery charge",
    "Battery capability": "Available battery output",
    "Reserve policy": "Minimum battery reserve setting",
    "Minimum runtime policy": "Minimum operating time setting",
    "Stop threshold policy (context)": "Generator stop setting",
    "Operator override": "Operator instruction",
    **INPUT_NAMES,
}

_PROBLEMS = {
    "no record": "no record received",
    "no GOOD record": "no record of usable quality",
    "conflicting records": "conflicting records",
    "no effective record": "no record in effect",
}

#: Why the generator was needed, per stored constraint id: a short name and a
#: sentence fragment.
CONSTRAINTS = {
    "OPERATOR_OVERRIDE": ("Operator instruction",
                          "an operator instruction kept the generator on"),
    "MINIMUM_RUNTIME": ("Minimum operating time",
                        "the generator was within its minimum operating time after starting"),
    "BATTERY_AT_RESERVE": ("Battery at minimum reserve",
                           "battery charge was at or below its minimum reserve"),
    "BATTERY_NEAR_RESERVE": ("Battery close to minimum reserve",
                             "battery charge was close to its minimum reserve"),
    "CAPABILITY_SHORTFALL": ("Not enough solar and battery supply",
                             "site demand was more than the available solar power and "
                             "battery output together"),
}

ALTERNATIVE_LABELS = {
    "OPERATOR_OVERRIDE": "Recorded operator instruction",
    "UNOBSERVED_OVERRIDE": "Unrecorded operator instruction",
    "POLICY_CONSTRAINT": "Generator stop setting",
    "PCS_CAPABILITY_UNAVAILABLE": "Battery output not reported",
    "UNMEASURED_PV_VARIATION": "Solar changes between reports",
}
ALTERNATIVE_STATUS = {
    "OBSERVED": "Supported by records",
    "NOT_EXCLUDED": "Still possible",
    "CONTRADICTED_BY_EVIDENCE": "Not supported by the available records",
}

CONFIDENCE_WORDS = {"HIGH": "High", "MEDIUM": "Medium", "LOW": "Low",
                    "NOT_APPLICABLE": "Not stated"}

MEANINGS = {
    CANDIDATE: "Possibly avoidable means that, for that time, the reported solar power and "
               "available battery output were more than the site demand, and no reason the "
               "generator was needed was recorded. It is not proof of wasted fuel and not a "
               "judgement of how the generator should have been operated.",
    NECESSARY: "Needed means a recorded reason required the generator to operate. It does not "
               "judge whether that setting or limit is right.",
    INDETERMINATE: "Cannot determine means the records needed to decide are missing or "
                   "conflicting. It says neither that the generator was needed nor that it "
                   "was avoidable.",
}

FRAMING = (
    "These are checks to make before considering any change. They are not an instruction "
    "to stop the generator or to change a setting."
)

UNAVAILABLE = "Detail not available for this part of the assessment."


def _num(text: str | None) -> float | None:
    return None if text is None else float(text)


def duration(hours: str | None) -> str:
    """'4.17' -> '4 h 10 min'; '0.5' -> '30 min'."""
    if hours is None:
        return "unknown"
    minutes = round(float(hours) * 60)
    h, m = divmod(minutes, 60)
    if h and m:
        return f"{h} h {m} min"
    return f"{h} h" if h else f"{m} min"


def bound(b: dict[str, Any]) -> str:
    """A stored low/high bound in words; an absent high is an open end."""
    low, high = b.get("low"), b.get("high")
    if "high" in b and high is None:
        return f"at least {duration(low)} (the start or end was not recorded)"
    if high is None or high == low:
        return duration(low)
    return f"{duration(low)} to {duration(high)}"


def missing_text(line: str) -> str:
    """A stored 'Input label: problem' line, in plain words."""
    label, sep, problem = line.partition(": ")
    name = INPUT_NAMES.get(label)
    if not sep or name is None:
        return UNAVAILABLE
    return f"{name}: {_PROBLEMS.get(problem, problem)}"


def _sentence(text: str) -> str:
    return text[:1].upper() + text[1:]


def _constraint_names(ids: list[str]) -> list[str]:
    return [CONSTRAINTS[i][0] if i in CONSTRAINTS else "Recorded operating limit" for i in ids]


def _because(ids: list[str]) -> str:
    parts = [CONSTRAINTS[i][1] for i in ids if i in CONSTRAINTS] or ["a recorded operating limit applied"]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


def _headline(a: dict[str, Any]) -> tuple[str, str]:
    level = a["claim_level"]
    portions = a["portions_hours"]
    if level == CANDIDATE:
        return (
            "The generator may have operated longer than needed.",
            f"For {bound(portions[CANDIDATE])} of this period, the reported solar power and "
            "available battery output were more than the site demand, and no reason the "
            "generator was needed was recorded.",
        )
    if level == NECESSARY:
        return ("The generator was needed during this period.",
                f"{_sentence(_because(a['binding_constraints']))}.")
    missing = [missing_text(m) for m in a.get("missing_evidence", [])]
    if missing:
        reason = "Records needed to decide are missing or conflicting: " + "; ".join(missing) + "."
    elif any(not s["observed"] for s in a["segments"]):
        reason = "Generator operation was not recorded for part of this period."
    else:
        reason = ("The available solar power and battery output were too close to the site "
                  "demand to decide.")
    return "We cannot determine whether the generator was needed during this period.", reason


_BASIS = (
    (re.compile(r"^Every evaluated segment reached a classification\.$"),
     lambda m: "Every part of the period could be assessed."),
    (re.compile(r"^(\d+) min of the interval is Indeterminate \(lowers one level\)\.$"),
     lambda m: f"{m[1]} min of the period cannot be determined, which lowers confidence."),
    (re.compile(r"^Smallest candidate margin is (\d+) % of load, below the (\d+) % strong "
                r"margin \(lowers one level\)\.$"),
     lambda m: f"At its closest, the available solar power and battery output exceeded site "
               f"demand by only {m[1]} % (less than {m[2]} %), which lowers confidence."),
    (re.compile(r"^Smallest candidate margin is (\d+) % of load\.$"),
     lambda m: f"At its closest, the available solar power and battery output exceeded site "
               f"demand by {m[1]} %."),
    (re.compile(r"^Start or stop time is not bracketed by evidence \(lowers one level\)\.$"),
     lambda m: "The records do not show both when the generator started and when it stopped, "
               "which lowers confidence."),
    (re.compile(r"^Start/stop uncertainty is (\d+) min \(lowers one level\)\.$"),
     lambda m: f"The start and stop times are uncertain by up to {m[1]} min, which lowers "
               "confidence."),
    (re.compile(r"^Start/stop uncertainty is (\d+) min\.$"),
     lambda m: f"The start and stop times are known to within {m[1]} min."),
    (re.compile(r"^No classification could be reached"),
     lambda m: "No conclusion was reached, so no confidence is stated."),
)


def _basis_line(line: str) -> tuple[str, bool]:
    for pattern, render in _BASIS:
        match = pattern.match(line)
        if match:
            return render(match), "lowers one level" in line
    return UNAVAILABLE, False


def _confidence(a: dict[str, Any]) -> dict[str, Any]:
    lines = [_basis_line(line) for line in a["confidence"]["basis"]]
    lowering = [text for text, lowers in lines if lowers]
    return {
        "word": CONFIDENCE_WORDS.get(a["confidence"]["level"], "Not stated"),
        "explanation": [text for text, _ in lines],
        "principal_limitation": lowering[0] if lowering else None,
    }


def _limits(a: dict[str, Any]) -> list[str]:
    level = a["claim_level"]
    portions = a["portions_hours"]
    ids = {alt["id"]: alt for alt in a["alternatives"]}
    out = [{
        CANDIDATE: "This is an assessment of the reported values, not proof of wasted fuel and "
                   "not a judgement of how the generator should have been operated.",
        NECESSARY: "This shows the generator was needed for the reason given. It does not "
                   "judge whether that setting or limit is right.",
        INDETERMINATE: "This says neither that the generator was needed nor that it was "
                       "avoidable.",
    }[level]]
    if "OPERATOR_OVERRIDE" in ids:
        out.append("An operator instruction is recorded during this period.")
    if "UNOBSERVED_OVERRIDE" in ids:
        out.append("No operator instruction was recorded for this period, but that does not "
                   "prove none was given.")
    if level != INDETERMINATE and float(portions[INDETERMINATE]["low"]) > 0:
        out.append(f"{_sentence(duration(portions[INDETERMINATE]['low']))} of this period "
                   "cannot be determined"
                   + (" and is not part of the possibly avoidable time." if level == CANDIDATE
                      else "."))
    if level == CANDIDATE and float(portions[NECESSARY]["low"]) > 0:
        out.append(f"{_sentence(duration(portions[NECESSARY]['low']))} of this period was "
                   "needed and is not part of the possibly avoidable time.")
    return out


def _fuel(a: dict[str, Any]) -> dict[str, Any]:
    fuel = a["fuel"]
    if fuel["status"] == "BOUNDED":
        inputs = fuel.get("inputs") or {}
        hours = inputs.get("duration_hours")
        return {
            "label": "Estimated fuel associated with possibly avoidable operation",
            "text": f"{fuel['low_litres']} to {fuel['high_litres']} litres",
            "note": ("This is an estimate, not confirmed fuel savings"
                     + ("" if hours is None else
                        f", for {bound(hours)} of possibly avoidable operation") + "."),
        }
    if fuel["status"] == "NOT_APPLICABLE":
        reason = "No fuel estimate: no possibly avoidable operation was found in this period."
    else:
        stored = fuel.get("reason") or ""
        reason = (
            "No fuel estimate: the generator's output was not reported for the possibly "
            "avoidable time." if stored.startswith("No generator output")
            else "No fuel estimate: the end of the possibly avoidable time was not recorded."
            if "upper bound is open" in stored
            else "No fuel estimate: the generator's fuel consumption is not set in the site's "
                 "equipment details." if "specific fuel consumption" in stored
            else "No fuel estimate is available for this period."
        )
    return {"label": "Estimated fuel associated with possibly avoidable operation",
            "text": None, "note": reason}


def _segment(s: dict[str, Any]) -> dict[str, Any]:
    level = s["classification"]
    missing = [missing_text(m) for m in s.get("missing", [])]
    if not s["observed"]:
        reason = "Generator operation was not recorded between these times."
    elif level == NECESSARY:
        reason = f"{_sentence(_because([s['binding_constraint']] if s['binding_constraint'] else []))}."
    elif level == CANDIDATE:
        reason = ("The available solar power and battery output were more than the site "
                  "demand, with battery charge above its minimum reserve; no reason the "
                  "generator was needed was recorded.")
    elif missing:
        reason = "Records needed to decide are missing or conflicting: " + "; ".join(missing) + "."
    else:
        reason = ("The available solar power and battery output were too close to the site "
                  "demand to decide.")
    return {"outcome": OUTCOMES[level], "reason": reason, "missing": missing}


def _policy_statement(stored: str) -> str:
    if stored.startswith("Conflicting"):
        return ("The site's records give conflicting generator stop settings for this period, "
                "so which setting applied is not known.")
    if stored.startswith("No generator stop policy"):
        return "No generator stop setting was recorded, so the setting in use is not known."
    match = re.match(r"The published generator stop threshold is ([\d.]+) %", stored)
    if match is None:
        return UNAVAILABLE
    text = (f"The recorded generator stop setting is {match[1]} % battery charge. Keeping the "
            "generator on below that level is consistent with the setting, so the question is "
            "the setting, not an equipment fault.")
    if "does not explain this stop" in stored:
        text += (" The generator stopped at a battery charge below that level, so the setting "
                 "in use may differ; no record of a change was received.")
    return text


def _alternative(alt: dict[str, Any]) -> dict[str, Any]:
    kind, status = alt["id"], alt["status"]
    if kind == "OPERATOR_OVERRIDE":
        statement = ("An operator instruction is recorded during this period. Its records are "
                     "listed below.")
    elif kind == "UNOBSERVED_OVERRIDE":
        statement = ("No operator instruction was recorded for this period. That does not "
                     "prove none was given.")
    elif kind == "POLICY_CONSTRAINT":
        statement = _policy_statement(alt["statement"])
    elif kind == "PCS_CAPABILITY_UNAVAILABLE":
        minutes = sum(int(g["minutes"]) for g in alt.get("gaps", []))
        statement = (
            f"Available battery output was not reported for {minutes} min of this period, so "
            "battery support there is unknown and that time is not counted as possibly "
            "avoidable." if status == "NOT_EXCLUDED"
            else "Available battery output was reported for every assessed part of this period."
        )
    elif kind == "UNMEASURED_PV_VARIATION":
        statement = ("Solar power is reported every 15 minutes as a 5-minute average, so "
                     "changes between reports are not seen.")
    else:
        statement = UNAVAILABLE
    return {
        "id": kind,
        "label": ALTERNATIVE_LABELS.get(kind, "Other possible explanation"),
        "status": ALTERNATIVE_STATUS.get(status, "Still possible"),
        "statement": statement,
    }


def _next_steps(a: dict[str, Any]) -> list[dict[str, Any]]:
    level = a["claim_level"]
    alternatives = {alt["id"]: alt for alt in a.get("alternatives", [])}
    steps: list[dict[str, Any]] = []
    if level in (CANDIDATE, INDETERMINATE):
        if level == CANDIDATE and "UNOBSERVED_OVERRIDE" in alternatives:
            steps.append({
                "id": "CONFIRM_OPERATOR_INSTRUCTION",
                "text": "Confirm whether an operator instruction kept the generator on during "
                        "this period. No instruction was recorded, and that absence is not "
                        "proof that none was given.",
                "target": {"kind": "alternative", "id": "UNOBSERVED_OVERRIDE"},
            })
        if "OPERATOR_OVERRIDE" in alternatives:
            steps.append({
                "id": "REVIEW_RECORDED_OVERRIDE",
                "text": "Review the recorded operator instruction and how much of this period "
                        "it covers.",
                "target": {"kind": "alternative", "id": "OPERATOR_OVERRIDE"},
            })
    capability = alternatives.get("PCS_CAPABILITY_UNAVAILABLE")
    capability_open = capability is not None and capability.get("status") == "NOT_EXCLUDED"
    if capability_open:
        minutes = sum(int(g["minutes"]) for g in capability.get("gaps", []))
        steps.append({
            "id": "CHECK_BATTERY_CAPABILITY",
            "text": f"Check why available battery output was not reported for {minutes} min of "
                    "this period; battery support there is unknown, so that time cannot be "
                    "assessed.",
            "target": {"kind": "alternative", "id": "PCS_CAPABILITY_UNAVAILABLE"},
        })
    other = [missing_text(m) for m in a.get("missing_evidence", [])
             if not (capability_open and m.startswith(dispatch.INPUT_LABELS["discharge_capability"]))]
    if other:
        steps.append({
            "id": "CHECK_MISSING_EVIDENCE",
            "text": "Check the site's records for the missing or conflicting information: "
                    + "; ".join(other) + ".",
            "target": {"kind": "site_evidence"},
        })
    policy = alternatives.get("POLICY_CONSTRAINT")
    if level != NECESSARY and policy is not None and policy["statement"].startswith(
        ("Conflicting", "No generator stop policy")
    ):
        steps.append({
            "id": "CONFIRM_STOP_POLICY",
            "text": "Confirm which generator stop setting was in use during this period.",
            "target": {"kind": "alternative", "id": "POLICY_CONSTRAINT"},
        })
    if level == NECESSARY:
        steps.append({
            "id": "CHECK_CONSTRAINT_IF_UNEXPECTED",
            "text": "No possibly avoidable operation was found. If the reason shown is "
                    "unexpected, check how that setting or limit is configured; this "
                    "assessment does not judge the setting.",
            "target": {"kind": "none"},
        })
    return steps


def reading(a: dict[str, Any]) -> dict[str, Any]:
    """The plain reading of one stored assessment, generated at read time.

    Served beside the assessment wherever it is read (index, Dispatch, detail,
    card), never persisted.
    """
    headline, reason = _headline(a)
    interval = a["interval"]
    return {
        "outcome": OUTCOMES[a["claim_level"]],
        "headline": headline,
        "reason": reason,
        "meaning": MEANINGS[a["claim_level"]],
        "generator": "Generator",
        "operating_time": bound(interval["duration_hours"]),
        "portions": {
            "possibly_avoidable": bound(a["portions_hours"][CANDIDATE]),
            "needed": duration(a["portions_hours"][NECESSARY]["low"]),
            "cannot_determine": duration(a["portions_hours"][INDETERMINATE]["low"]),
        },
        "reasons_needed": _constraint_names(a["binding_constraints"]),
        "missing": [missing_text(m) for m in a.get("missing_evidence", [])],
        "confidence": _confidence(a),
        "limits": _limits(a),
        "fuel": _fuel(a),
        "duration_note": (
            "The shorter figure counts only the times the generator was recorded as operating. "
            "The longer figure spans from the last record showing it off before the period to "
            "the first record showing it off after. Gaps in the records count only toward the "
            "longer figure."
            + (" No record shows the generator off before this period, so its start is open."
               if interval.get("open_start") else "")
            + (" No record shows the generator off after this period, so its end is open."
               if interval.get("open_end") else "")
        ),
        "coverage_note": ("Each assessed part of the period is checked for a usable record of "
                          "each input; a part without one cannot be determined."),
        "segments": [_segment(s) for s in a["segments"]],
        "alternatives": [_alternative(alt) for alt in a["alternatives"]],
        "next_steps": _next_steps(a),
        "framing": FRAMING,
    }


def card(level: str | None, lead: dict[str, Any] | None, others: int) -> dict[str, str]:
    """The Overview Dispatch card's plain label and reason."""
    if lead is None:
        return {"label": "No generator operation",
                "reason": "No generator operation was recorded in this window."}
    headline, reason = _headline(lead)
    text = f"{headline} {reason}"
    if others:
        text += f" ({others} other assessed period{'s' if others > 1 else ''} in this window.)"
    return {"label": OUTCOMES[lead["claim_level"]], "reason": text}


# --- readiness (read time; readiness-3 scoring unchanged) -----------------------

READINESS_QUESTION = "What can we assess from this site's records?"
READINESS_MEANINGS = {
    "FULL": "The records needed are there: every required input has usable records, and no "
            "assessed period was left undetermined by a gap. This is about the records, not "
            "whether the site is operating well, and not uninterrupted coverage.",
    "LIMITED": "Assessments are possible but limited: the missing records named below limit "
               "the conclusion or leave parts of periods undetermined.",
    "NONE": "Nothing can be assessed yet: no records of generator operation have been "
            "received and accepted.",
}
READINESS_SCOPE = (
    "Based on all of this site's accepted records, not only the selected window. It is not a "
    "rating of the site's health and not permission to act."
)
READINESS_METHOD = (
    "How this is scored: Full means every required input has at least one usable accepted "
    "record and no assessed part of a period was left undetermined by a missing record. "
    "Gaps that did not affect any conclusion are listed as not limiting. Limited means "
    "conclusions are possible but limited by the missing records named. None means no "
    "period can be assessed because no record of generator operation is accepted. Full "
    "does not mean the site is healthy, or that records are uninterrupted, current or "
    "present in every selected window."
)


def role(name: str) -> str:
    return ROLE_NAMES.get(name, name)


def _gap(gap: dict[str, Any]) -> str:
    who = role(gap["role"])
    if gap["kind"] == "NOT_ACCEPTED":
        return f"{who}: no usable record has been accepted."
    if gap["role"] == "Generator state":
        minutes = re.search(r"not observed for (\d+) min", gap.get("statement", ""))
        n = len(gap["assessment_ids"])
        return (f"Generator operation: not recorded for {minutes[1] if minutes else 'some'} "
                f"min in {n} assessed period{'' if n == 1 else 's'}; that time cannot be "
                "determined.")
    n = len(gap["assessment_ids"])
    consequence = (
        f"{gap['limiting_segments']} part(s) that needed it cannot be determined."
        if gap["limits_claim"] else "no conclusion depended on it there."
    )
    return (f"{who}: no usable record for {gap['missing_segments']} of "
            f"{gap['evaluated_segments']} assessed parts in {n} assessed "
            f"period{'' if n == 1 else 's'}; {consequence}")


def readiness(level: str, ceiling: dict[str, Any], missing: list[dict[str, Any]],
              capped_roles: list[str]) -> dict[str, Any]:
    """Plain fields for one readiness row: its meaning, scope, method, the
    conclusion available and each gap."""
    if level == "NONE":
        conclusion = ("No conclusion: with no record of generator operation, no period can be "
                      "assessed.")
    elif capped_roles:
        conclusion = ("Possibly avoidable operation cannot be identified without "
                      + " and ".join(role(r) for r in capped_roles)
                      + ". Needed can be shown only where a recorded reason required the "
                        "generator; other time cannot be determined.")
    elif level == "LIMITED":
        conclusion = ("Possibly avoidable operation can be identified only where the required "
                      "records exist; other time cannot be determined.")
    else:
        conclusion = ("Possibly avoidable operation can be identified, with the limits stated "
                      "on each assessment.")
    return {
        "question": READINESS_QUESTION,
        "meaning": READINESS_MEANINGS[level],
        "scope": READINESS_SCOPE,
        "method": READINESS_METHOD,
        "conclusion": conclusion,
        "gaps": [_gap(g) for g in missing],
    }
