"""6a (spec section 3.4, D-P6.7): the cases of `decision.refused`, one per variant. The English is section 3.4's
sentence, written by hand (W2), never computed."""
from __future__ import annotations

from assetops_backend.i18n import Count, State

from statement_cases import Case

#: The facts every refusal sentence is rendered with (`records.refusal_sentence`): the code and the bounds.
_FACTS = {"least": Count(1, "month"), "most": Count(60, "month"), "places": Count(2, "character"),
          "letters": Count(3, "character"), "chars": Count(200, "character"),
          "value_places": Count(6, "character")}


def _refused(code: str, english: str) -> Case:
    return Case("decision.refused", code.lower(), {"code": State(code), **_FACTS}, english)


CASES = [
    _refused("UNKNOWN_TENANT", "No operator has that name."),
    _refused("PERSON_NOT_FOUND", "The person is not an active person of this operator."),
    _refused("PERSON_ROLE_REQUIRED", "This person's role does not allow this step."),
    _refused("BAD_PERIOD", "Write the month as YYYY-MM, like 2026-10."),
    _refused("BAD_HORIZON", "Write the horizon as 1 to 60 months."),
    _refused("SITE_NOT_FOUND", "This operator has no Site with that code."),
    _refused("LEVER_UNKNOWN", "No change of that kind is known."),
    _refused("LEVER_SITE_TYPE", "That kind of change does not apply to this Site's type."),
    _refused("FINDING_NOT_FOUND", "This Site has no finding with that reference."),
    _refused("FINDING_NOT_ON_LEVER", "That finding is not about what this change acts on."),
    _refused("BAD_CURRENT", "Give today's value for each setting of this change."),
    _refused("ALREADY_PREPARED_OTHER", "This decision was prepared with other current settings."),
    _refused("DECISION_NOT_FOUND", "This operator has no decision with that reference."),
    _refused("OPTION_NOT_FOUND", "This decision has no option with that name."),
    _refused("NO_ACTION_ONE_OFF", "Doing nothing costs nothing to put in place."),
    _refused("BAD_AMOUNT", "Write the amount as a number with at most 2 decimals, like 90.00."),
    _refused("BAD_CURRENCY", "Write the currency as 3 capital letters, like USD."),
    _refused("BAD_CREW_VISITS", "Write the crew visits as a whole number."),
    _refused("BAD_BASIS", "Say in up to 200 characters what the cost is based on."),
    _refused("ALREADY_CHOSEN", "This decision already has a recorded choice."),
    _refused("NOT_EVALUATED", "The options have not been valued yet."),
    _refused("CHOOSE_NONE_INSTEAD", "To keep things as they are, choose none."),
    _refused("OPTION_REJECTED", "This option was rejected and cannot be chosen."),
    _refused("ACTION_NOT_FOUND", "This operator has no agreed Action with that reference."),
    _refused("ACTION_SITE_MISMATCH", "That Action is for another Site."),
    _refused("BAD_UUID", "Write the reference as it was printed."),
    _refused("NO_DATABASE", "Set DATABASE_URL to the operator's database."),
    _refused("RECORD_INVALID", "This record does not fit the decision it names, so nothing was stored."),
    _refused("DECISIONS_UNAVAILABLE", "The decisions store cannot be reached right now."),
    _refused("STUDY_REQUIRED", "Give the simulation for this kind of change (--study)."),
    _refused("STUDY_UNREADABLE", "The simulation file cannot be read."),
    _refused("STUDY_NOT_CALIBRATED", "The simulation did not match the Site's own run, so it cannot value anything."),
    _refused("STUDY_LABELS_INVALID", "The simulation is not labelled as a model on simulated, emulated or recorded readings."),
    _refused("STUDY_BASELINE_MISMATCH", "The simulation starts from other settings than this decision's."),
    _refused("STUDY_GRID_MISMATCH", "The simulation does not hold exactly this decision's settings."),
    _refused("STUDY_ADMISSION_MISMATCH", "The simulation's service checks do not match the rule."),
    _refused("STUDY_FRAME_MISMATCH", "The simulation is of another Site's record."),
    _refused("STUDY_MONTH_NOT_COVERED", "The simulation does not cover the whole of this decision's month."),
    _refused("NO_ACTION_RECORD", "Doing nothing has no records to state."),
    _refused("RECORD_NOT_ON_OPTION", "That option does not change that figure, or its change comes from a simulation."),
    _refused("BAD_RECORD_UNIT", "The unit does not match that figure's unit."),
    _refused("BAD_VALUE", "Give a number with at most 6 decimal places."),
    _refused("BAD_DOCUMENT", "Name the document, in 1 month to 200 characters."),
    _refused("STUDY_NOT_FOR_LEVER", "This kind of change is not valued from a simulation file."),
    _refused("STRUCTURE_UNAVAILABLE", "The month's figures cannot be read right now."),
]
