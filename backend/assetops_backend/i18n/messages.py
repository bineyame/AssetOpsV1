"""UQ-6a (D-I18N.1): the server message contract.

A word the server sends is a `Message` - a catalogue `key` and typed `params` - and is rendered for the request's
locale at read (`i18n.render`), never stored as composed text. The catalogue holds one template per key per locale;
English is the complete reference locale. UQ-6b moves the existing server words into it; until then it holds the
keys converted so far.
"""
from __future__ import annotations

from typing import Mapping, TypedDict, Union

#: A typed message parameter. Formatting numbers, dates and money by locale (Babel) comes with UQ-4.
Param = Union[str, int, float]


class Message(TypedDict):
    key: str
    params: Mapping[str, Param]


def message(key: str, **params: Param) -> Message:
    return {"key": key, "params": dict(params)}


#: locale -> key -> `str.format` template over the message's params.
CATALOGUE: dict[str, dict[str, str]] = {
    "en": {
        "analytics.site_not_found": "No Site {site_id} is configured.",
        # UP-1 (rev 7 section 7.5): the reading-upload page's words (drafted in frontend/mockups/v72).
        "reading_upload.uploaded_by_site_admin": "Uploaded by site admin",
        "reading_upload.off": "Uploading readings is switched off.",
        "reading_upload.not_this_site": "Uploading readings is not available for this site.",
        "reading_upload.not_found": "No upload with this reference for this site.",
        "reading_upload.bad_request": "The upload request is not valid: {detail}.",
        "reading_upload.gateway_unavailable": (
            "The readings could not be sent just now, so nothing was saved. Try again in a minute."),
        "reading_upload.checked": "Checked the whole file: {readings} readings. Nothing is saved until you confirm.",
        "reading_upload.state.sent": "Sent to the site's data gateway. Waiting for AssetOps to accept the readings.",
        "reading_upload.state.accepted": "Accepted {accepted} of {total} readings.",
        "reading_upload.state.processing": (
            "All {total} readings accepted. AssetOps is working out what they mean for these days."),
        "reading_upload.state.analysed": "{accepted} of {total} readings accepted and analysed.",
        "reading_upload.state.sent_with_held": (
            "Sent. {held} readings are held: their unit is not the unit this meter reports. They are kept aside "
            "and not used."),
        "reading_upload.state.processing_with_held": (
            "{accepted} of {total} sent readings accepted; {held} held because their unit is not the unit this "
            "meter reports. AssetOps is working out what the accepted readings mean."),
        "reading_upload.state.analysed_with_held": (
            "{accepted} of {total} sent readings accepted and analysed; {held} held because their unit is not the "
            "unit this meter reports."),
        "reading_upload.refused.encoding": (
            "The file was not saved: it is not plain CSV text. In Excel, save as 'CSV (Comma delimited)', not "
            "'CSV UTF-8', and try again."),
        "reading_upload.refused.empty_file": "The file was not saved: it has no readings in it.",
        "reading_upload.refused.header_mismatch": (
            "The file was not saved: the column headings do not match the template ({field})."),
        "reading_upload.refused.invalid_timing": (
            "The file was not saved: a time is not written like 2026-11-17T03:15:00Z (UTC, ending in Z). "
            "Row {row}."),
        "reading_upload.refused.span_mismatch": (
            "The file was not saved: a time is not on a 15-minute step (:00, :15, :30, :45). Row {row}."),
        "reading_upload.refused.duplicate_row": "The file was not saved: the same time appears twice. Row {row}.",
        "reading_upload.refused.unsorted_rows": (
            "The file was not saved: the rows are not in time order. Row {row} is earlier than the row before it."),
        "reading_upload.refused.invalid_value": (
            "The file was not saved: a reading is not a plain number (a dot for decimals, no thousands separator, "
            "at most 3 decimals), or the row has the wrong number of cells. Row {row} ({field})."),
        "reading_upload.refused.already_recorded": (
            "The file was not saved: this site already has {role} readings up to {latest} (UTC). Only readings "
            "after that can be uploaded."),
        "reading_upload.role.pv_power": "solar",
        "reading_upload.role.feeder_demand": "feeder meter",
        "reading_upload.refused.file_too_large": "The file was not saved: it is larger than {limit_mb} MB.",
        # D-UP.5 (raw text/csv body) and D-UP.6 (the BOM fix named in the template words).
        "reading_upload.unsupported_type": "The file was not saved: send it as a CSV file (text/csv).",
        "reading_upload.template_note": (
            "One row per 15 minutes, times in UTC ending in Z, power in kW. Leave a cell empty when there is no "
            "reading. In Excel, save as 'CSV (Comma delimited)', not 'CSV UTF-8'."),
        "reading_upload.template_unavailable": "The upload template is not available for this site just now.",
    },
}
