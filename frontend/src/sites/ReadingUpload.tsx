/**
 * UP-1 (rev 7 §7.5, D-UP.3/4): Kobo's "Upload readings" page and its Health entry panel, after
 * `frontend/mockups/v72/upload-readings.html` (owner provisional approval 2026-11-13).
 *
 * One page; the steps replace each other in place: choose a file (Part B) -> the check before saving (Part C, the
 * dry run, nothing saved) -> following the readings (Part D: Checked, Sent, Accepted n of m, Still processing,
 * Analysed with the board link; Held; Not analysed) or the refused file (Part E, nothing saved).
 *
 * MOCK DEVIATIONs (labelled where they apply):
 * - Part D: the tracker shows no per-step clock times; the server records one time (the save), shown in the head.
 * - Part E: the refusal is the server's one sentence plus the place the server names ("row 7 · timestamp_utc",
 *   "column 3" for a heading, the meter's role for an already-recorded file); the page never builds it from a path;
 *   the mock's separate explanation line and its "Every refusal" table are review aids, not page content.
 * - The drop zone's review-only state bar (Idle / Hover / Keyboard focus / Dragging) is not built; the states are.
 */
import { useCallback, useEffect, useRef, useState, type DragEvent } from "react";

import { RangeLink as Link } from "../ui/RangeLink";
import {
  createReadingUploadClient,
  readingTemplateHref,
  type ReadingUploadClient,
  type UploadChecked,
  type UploadRefusal,
  type UploadStatus,
} from "./readingUploadClient";
import { siteZoneOrUtc } from "./siteTime";
import "./readingUpload.css";

const DEFAULT_CLIENT = createReadingUploadClient();
export const UPLOAD_POLL_MS = 3000;
const SETTLED = new Set(["ANALYSED", "NOT_ANALYSED", "REFUSED"]);

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function localParts(value: string | null | undefined, timeZone: string | null | undefined) {
  if (!value) return null;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return null;
  const f = new Intl.DateTimeFormat("en-GB", {
    timeZone: siteZoneOrUtc(timeZone), year: "numeric", month: "numeric", day: "numeric",
    hour: "2-digit", minute: "2-digit", hourCycle: "h23",
  });
  const get = (type: string) => f.formatToParts(d).find((p) => p.type === type)?.value ?? "";
  return { y: get("year"), m: MONTHS[Number(get("month")) - 1], day: String(Number(get("day"))), hm: `${get("hour")}:${get("minute")}` };
}

/** `17 Nov, 03:00`, in the Site's time. */
export function siteDayTime(value: string | null | undefined, timeZone: string | null | undefined): string {
  const p = localParts(value, timeZone);
  return p === null ? "" : `${p.day} ${p.m}, ${p.hm}`;
}

/** `17 Nov 03:00 – 13:00` (or both days when the period crosses midnight), in the Site's time. */
export function sitePeriod(start: string | null | undefined, end: string | null | undefined, timeZone: string | null | undefined): string {
  const a = localParts(start, timeZone);
  const b = localParts(end, timeZone);
  if (a === null || b === null) return "";
  return a.day === b.day && a.m === b.m ? `${a.day} ${a.m}, ${a.hm} – ${b.hm}` : `${a.day} ${a.m}, ${a.hm} – ${b.day} ${b.m}, ${b.hm}`;
}

function siteDay(value: string | null | undefined, timeZone: string | null | undefined): string {
  const p = localParts(value, timeZone);
  return p === null ? "" : `${p.day} ${p.m}`;
}

/** Kobo **Health**: one panel with "Upload readings", shown only when the server's switch names the Site (D-UP.4). */
export function ReadingUploadEntry({ siteId, uploadsHref, client = DEFAULT_CLIENT }: {
  siteId: string;
  uploadsHref: string;
  client?: ReadingUploadClient;
}) {
  const [on, setOn] = useState(false);
  const [text, setText] = useState("");
  useEffect(() => {
    let live = true;
    void client.entry(siteId).then((entry) => {
      if (!live) return;
      setOn(entry.status === "on");
      if (entry.status === "on") setText(entry.healthText);
    });
    return () => {
      live = false;
    };
  }, [client, siteId]);
  if (!on) return null;
  return (
    <section className="upload-entry" aria-labelledby="upload-entry-heading" data-upload-entry="">
      <span className="upload-entry__tile" aria-hidden="true" />
      <div className="upload-entry__text">
        <h2 id="upload-entry-heading">Readings from a file</h2>
        <p>{text}</p>
      </div>
      <Link className="button primary" to={uploadsHref}>Upload readings</Link>
    </section>
  );
}

type Step =
  | { kind: "loading" }
  | { kind: "off" }
  | { kind: "choose"; note?: string | null }
  | { kind: "checking"; file: File }
  | { kind: "checked"; file: File; checked: UploadChecked; saving: boolean }
  | { kind: "refused"; fileName: string; refusal: UploadRefusal }
  | { kind: "following"; status: UploadStatus; lost: boolean };

function stateLabel(status: UploadStatus): [string, string] {
  if (status.state === "ANALYSED") return ["Analysed", "green"];
  if (status.state === "NOT_ANALYSED") return ["Not analysed", "red"];
  if (status.held && status.counts.accepted > 0) return ["Held", "amber"];
  if (status.state === "PROCESSING") return ["Still processing", "neutral"];
  if (status.state === "ACCEPTED") return ["Accepted", "neutral"];
  return ["Sent", "neutral"];
}

function Tracker({ status, siteName, timeZone }: { status: UploadStatus; siteName: string; timeZone: string | null | undefined }) {
  const s = status.state;
  const day = siteDay(status.period_start, timeZone);
  const failed = s === "NOT_ANALYSED";
  // Checked and Sent are done once saved; `current` is the step under way (5: every step done).
  const current = s === "SENT" || s === "ACCEPTED" ? 2 : s === "PROCESSING" || failed ? 3 : 5;
  const steps: { label: string; done: string; todo?: string }[] = [
    { label: "Checked", done: "The whole file passed." },
    { label: "Sent", done: "Handed to the site's data gateway." },
    { label: "Accepted", done: `${status.counts.accepted} of ${status.counts.accepted_of} readings.` },
    { label: failed ? "Not analysed" : "Still processing", done: "Finished." },
    { label: "Analysed", done: status.text, todo: `${siteName}'s board for ${day} will show these readings.` },
  ];
  return (
    <ol className="upload-track" aria-label="Where the readings are">
      {steps.map((step, i) => {
        const state = i < current ? "done" : i === current ? (failed ? "failed" : "now") : "todo";
        const words = state === "done" ? step.done : state === "todo" ? step.todo : status.text;
        return (
          <li key={i} className={`upload-track__step upload-track__step--${state}`} aria-current={state === "now" ? "step" : undefined}>
            <span className="upload-track__mark" aria-hidden="true" />
            <div>
              <b>{step.label}</b>
              {words ? <p>{words}</p> : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
}

function Following({ siteName, status, timeZone, lost, boardHref, onAgain }: {
  siteName: string;
  status: UploadStatus;
  timeZone: string | null | undefined;
  lost: boolean;
  boardHref: (day: string) => string;
  onAgain: () => void;
}) {
  const [label, tone] = stateLabel(status);
  const c = status.counts;
  const total = c.accepted + c.held;
  const entered = localParts(status.entered_at, timeZone);
  return (
    <section className="upload-panel" aria-labelledby="upload-follow-heading" data-upload-state={status.state}>
      <div className="upload-panel__head">
        <span className="upload-panel__file" aria-hidden="true" />
        <div>
          <h2 id="upload-follow-heading">{status.file_name}</h2>
          <p>
            {status.uploaded_by_text}
            {entered === null ? null : ` · ${entered.day} ${entered.m} ${entered.y}, ${entered.hm}`}
          </p>
        </div>
        <span className={`badge status-tone--${tone}`}>{label}</span>
      </div>
      <div className="upload-panel__body">
        {status.state === "ANALYSED" || (status.held && c.accepted > 0) ? (
          <div className="upload-result">
            <h3>{status.text}</h3>
            {total > 0 ? (
              <div className="upload-bar" role="img" aria-label={`${c.accepted} accepted, ${c.held === 0 ? "none" : c.held} held`}>
                <i className="upload-bar__ok" style={{ width: `${(100 * c.accepted) / total}%` }} />
                {c.held > 0 ? <i className="upload-bar__held" style={{ width: `${(100 * c.held) / total}%` }} /> : null}
              </div>
            ) : null}
            {status.state === "ANALYSED" && status.board_day ? (
              <p>
                <Link to={boardHref(status.board_day)} data-upload-board="">
                  Open {siteName}'s board for {siteDay(status.period_start, timeZone)}
                </Link>
              </p>
            ) : null}
          </div>
        ) : null}
        <Tracker status={status} siteName={siteName} timeZone={timeZone} />
        {lost ? <p className="upload-note" role="status">The page could not ask for the latest state just now; it will try again.</p> : null}
        {SETTLED.has(status.state) ? (
          <p><button type="button" className="button" onClick={onAgain}>Upload another file</button></p>
        ) : null}
      </div>
    </section>
  );
}

export function ReadingUploadPage({ siteId, siteName, timeZone, boardHref, client = DEFAULT_CLIENT, pollMs = UPLOAD_POLL_MS }: {
  siteId: string;
  siteName: string;
  timeZone: string | null | undefined;
  /** The Site board address for one Site-local day (`?date=`). */
  boardHref: (day: string) => string;
  client?: ReadingUploadClient;
  pollMs?: number;
}) {
  const [step, setStep] = useState<Step>({ kind: "loading" });
  const [templateNote, setTemplateNote] = useState("");
  const [templateStep, setTemplateStep] = useState("");
  const [drag, setDrag] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let live = true;
    void client.entry(siteId).then((entry) => {
      if (!live) return;
      if (entry.status === "on") {
        setTemplateNote(entry.templateNote);
        setTemplateStep(entry.templateStep);
        setStep({ kind: "choose" });
      } else {
        setStep({ kind: "off" });
      }
    });
    return () => {
      live = false;
    };
  }, [client, siteId]);

  const following = step.kind === "following" ? step.status : null;
  useEffect(() => {
    if (following === null || SETTLED.has(following.state)) return undefined;
    let live = true;
    const timer = setTimeout(() => {
      void client.status(siteId, following.upload_id).then((result) => {
        if (!live) return;
        if (result.status === "ok") setStep({ kind: "following", status: result.value, lost: false });
        else setStep({ kind: "following", status: following, lost: true });
      });
    }, pollMs);
    return () => {
      live = false;
      clearTimeout(timer);
    };
  }, [client, siteId, following, pollMs, step]);

  const choose = useCallback(async (file: File | undefined) => {
    if (!file) return;
    setStep({ kind: "checking", file });
    const result = await client.check(siteId, file);
    if (result.status === "ok") setStep({ kind: "checked", file, checked: result.value, saving: false });
    else if (result.status === "refused") setStep({ kind: "refused", fileName: file.name, refusal: result.refusal });
    else setStep({ kind: "choose", note: result.status === "unavailable" ? result.message ?? CHECK_LOST : null });
  }, [client, siteId]);

  const save = useCallback(async (file: File, checked: UploadChecked) => {
    setStep({ kind: "checked", file, checked, saving: true });
    const result = await client.save(siteId, file);
    if (result.status === "ok") setStep({ kind: "following", status: result.value, lost: false });
    else if (result.status === "refused") setStep({ kind: "refused", fileName: file.name, refusal: result.refusal });
    else setStep({ kind: "choose", note: result.status === "unavailable" ? result.message ?? CHECK_LOST : SAVE_LOST });
  }, [client, siteId]);

  const again = () => {
    if (input.current) input.current.value = "";
    setStep({ kind: "choose" });
  };
  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDrag(false);
    void choose(event.dataTransfer.files?.[0]);
  };

  if (step.kind === "loading") return <p className="upload-note" role="status">Loading the upload page.</p>;
  if (step.kind === "off") return <p className="upload-note">Uploading readings is not available for this site.</p>;

  return (
    <div className="upload-page">
      {step.kind === "choose" || step.kind === "checking" ? (
        <>
          <ol className="upload-stepper" aria-label="How it works">
            <li>
              <span className="upload-stepper__dot">1</span>
              <div>
                <h3>Get the template</h3>
                <p>{templateStep}</p>
                <a href={readingTemplateHref(siteId)} download data-upload-template="">Download the template (CSV)</a>
              </div>
            </li>
            <li>
              <span className="upload-stepper__dot">2</span>
              <div>
                <h3>Fill it in</h3>
                <p>{templateNote}</p>
              </div>
            </li>
            <li className="upload-stepper__current">
              <span className="upload-stepper__dot" aria-current="step">3</span>
              <div>
                <h3>Check, then save</h3>
                <p>AssetOps checks the whole file first and shows you what it found. Nothing is saved until you confirm.</p>
              </div>
            </li>
          </ol>
          <div
            className={`upload-drop${drag ? " upload-drop--drag" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={onDrop}
          >
            <span className="upload-drop__well" aria-hidden="true" />
            <h3>{drag ? "Drop the file to check it" : <>Drag a CSV file here, or <u>choose a file</u></>}</h3>
            <p>{step.kind === "checking" ? `Checking ${step.file.name}…` : `One file, up to 2 MB. Only ${siteName}, only the AssetOps template.`}</p>
            <input
              ref={input}
              type="file"
              accept=".csv,text/csv"
              aria-label={`Choose a CSV file of ${siteName}'s readings`}
              disabled={step.kind === "checking"}
              onChange={(e) => void choose(e.target.files?.[0])}
            />
          </div>
          {step.kind === "choose" && step.note ? <p className="upload-note" role="alert">{step.note}</p> : null}
          <div className="upload-attrib" role="note">
            <p>Readings you send here are recorded as <b>"Uploaded by site admin"</b>. Each reading keeps the file it came from.</p>
          </div>
        </>
      ) : null}

      {step.kind === "checked" ? (
        <section className="upload-panel" aria-labelledby="upload-check-heading" data-upload-state="CHECKED">
          <div className="upload-panel__head">
            <span className="upload-panel__file" aria-hidden="true" />
            <div>
              <h2 id="upload-check-heading">{step.file.name} · ready to save</h2>
              <p>{step.checked.text}</p>
            </div>
            <span className="badge status-tone--green">Checked</span>
          </div>
          <div className="upload-panel__body">
            <dl className="upload-facts">
              <div><dt>Period ({siteName} time)</dt><dd>{sitePeriod(step.checked.preview.period_start, step.checked.preview.period_end, timeZone)}</dd></div>
              <div><dt>Rows</dt><dd>{step.checked.preview.rows}</dd><small>one every 15 minutes</small></div>
              <div><dt>Readings</dt><dd>{step.checked.preview.cells}</dd><small>{step.checked.preview.rows} rows × {step.checked.preview.columns.length} meters</small></div>
              <div><dt>Empty cells</dt><dd>{step.checked.preview.blanks}</dd><small>saved as "no reading"</small></div>
            </dl>
            <div className="data-table__scroll">
              <table className="data-table upload-columns">
                <thead>
                  <tr>
                    <th scope="col">Column in your file</th>
                    <th scope="col">Matched to</th>
                    <th scope="col">Unit</th>
                    <th scope="col" className="upload-n">Readings</th>
                    <th scope="col" className="upload-n">Empty</th>
                  </tr>
                </thead>
                <tbody>
                  {step.checked.preview.columns.map((c) => (
                    <tr key={c.column ?? c.meter_text}>
                      <td className="upload-mono">{c.column}</td>
                      <td><span className="upload-match">{c.meter_text}</span><span className="upload-sub">{c.role_name_text}</span></td>
                      <td>{c.unit}{c.unit_matches === false ? <span className="upload-sub">this meter reports {c.profile_unit}; held</span> : null}</td>
                      <td className="upload-n">{c.readings + c.blanks}</td>
                      <td className="upload-n">
                        {c.blanks}
                        {c.blank_times && c.blank_times.length > 0 ? (
                          <span className="upload-sub">{c.blank_times.map((t) => siteDayTime(t, timeZone).split(", ")[1]).join(", ")}</span>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="upload-confirm">
            <button type="button" className="button primary" disabled={step.saving} onClick={() => void save(step.file, step.checked)}>
              {step.saving ? "Saving…" : `Save ${step.checked.preview.cells} readings`}
            </button>
            <button type="button" className="button" disabled={step.saving} onClick={again}>Choose another file</button>
            {step.checked.latest_saved ? (
              <p>{siteName}'s latest saved reading is {siteDayTime(step.checked.latest_saved, timeZone)}. This file starts after it.</p>
            ) : null}
          </div>
        </section>
      ) : null}

      {step.kind === "refused" ? (
        <div className="upload-refusal" role="alert" data-upload-state="REFUSED">
          <span className="badge status-tone--red">Refused</span>
          <h2>{step.refusal.message ?? NOT_SAVED}</h2>
          <p>Nothing from this file was saved; correct it and choose it again.</p>
          {step.refusal.where ? <span className="upload-where">{step.refusal.where}</span> : null}
          <div><button type="button" className="button" onClick={again}>Choose the corrected file</button></div>
        </div>
      ) : null}

      {step.kind === "following" ? (
        <Following siteName={siteName} status={step.status} timeZone={timeZone} lost={step.lost} boardHref={boardHref} onAgain={again} />
      ) : null}
    </div>
  );
}

const CHECK_LOST = "The file could not be checked just now. Nothing was saved; try again.";
const NOT_SAVED = "The file was not saved. Check it and try again.";
const SAVE_LOST =
  "The page lost contact while saving, so it cannot tell whether the readings were sent. Sending the same file again " +
  "is safe: readings already saved are refused, never doubled.";
