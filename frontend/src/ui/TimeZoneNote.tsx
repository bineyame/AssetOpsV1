import "./time-zone-note.css";

/** POLISH §3 / Addendum 6 Q7 (D-4, R650): one note per page instead of a "UTC" suffix on every time. */
export const TIME_ZONE_NOTE = "Times in UTC";
/** Switched on by PB-3 (Addendum 7 Q6) once a page shows Site-local due dates. */
export const TIME_ZONE_NOTE_WITH_DUE_DATES = "Times in UTC · due dates in each site's local date";

export function TimeZoneNote({ dueDates = false }: { dueDates?: boolean }) {
  return (
    <span className="time-zone-note" data-time-zone-note={dueDates ? "due-dates" : "utc"}>
      {dueDates ? TIME_ZONE_NOTE_WITH_DUE_DATES : TIME_ZONE_NOTE}
    </span>
  );
}
