import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import type { PriceEntryBlock, PriceRowBody } from "./pricePageClient";
import {
  freshPriceEntryKey,
  type PriceBasis,
  type PriceEntryClient,
  type PriceEntryDryRun,
  type PriceEntryRequest,
} from "./priceEntryClient";

/**
 * PR-3 (D-PRICE.1, rev 5 §5.3, owner defaults 6-9): the inline "Set a new price" form under one price row.
 *
 * Two steps: Continue sends the dry run and shows the server's one change-kind sentence (default 8: no figure count);
 * Save price posts with the same idempotency key, reused on every retry. A dry run that says `reason_required`
 * (today or earlier over an existing price: a correction) shows the Reason field. After a save the page stays, the
 * server's summary is the success note (it already says figures read "Updating…" for a few minutes) and the page is
 * re-read. MOCK DEVIATION (D-PRICE.3): v7.1 `price-it.html` has no form (Part B is read-only, Part D lists the form
 * as "Comes with sign-in"); the layout follows rev 5 §5.3 inside Part B's table.
 */
export const PRICE_ENTRY_WORDS = {
  open: "Set a new price",
  title: "Set a new price",
  amount: "Amount",
  currency: "Currency",
  basis: "Basis",
  source: "Where this price comes from",
  appliesFrom: "Applies from",
  reason: "Reason",
  reasonHint: "This date changes figures already shown. Say why.",
  continue: "Continue",
  checking: "Checking…",
  cancel: "Cancel",
  change: "Change",
  save: "Save price",
  saving: "Saving…",
  confirmTitle: "What this does",
  nothingSaved: "Nothing was saved.",
  check: "Check:",
  unavailable: "Prices cannot be saved right now. Nothing was saved.",
  lost: "We could not confirm the save. Saving again is safe.",
  keyReused:
    "An earlier save from this form may already have been recorded. Reload the page and check History before saving again.",
} as const;

const BASES: [PriceBasis, string][] = [
  ["AUTHORED_ESTIMATE", "An estimate"],
  ["CONTRACT_RATE", "A contract rate"],
  ["RECORDED_PURCHASE", "A recorded purchase"],
];

const FIELD_WORDS: Record<string, string> = {
  value: PRICE_ENTRY_WORDS.amount,
  currency: PRICE_ENTRY_WORDS.currency,
  basis: PRICE_ENTRY_WORDS.basis,
  source: PRICE_ENTRY_WORDS.source,
  applies_from: PRICE_ENTRY_WORDS.appliesFrom,
  reason: PRICE_ENTRY_WORDS.reason,
};

type Phase = "editing" | "checking" | "confirm" | "saving";

export interface PriceEntrySlotProps {
  siteId: string;
  row: PriceRowBody;
  entry: PriceEntryBlock;
  client: PriceEntryClient;
  /** `?key=` named this row: its form is open on arrival. */
  openOnArrival: boolean;
  /** The server's saved summary for this row, kept by the page across its re-read. */
  savedSummary: string | null;
  onSaved: (key: string, summary: string) => void;
  /** The safe `return` path, repeated in the success note. */
  back: string | null;
  backWords: string;
}

export function PriceEntrySlot(props: PriceEntrySlotProps) {
  const { row, savedSummary, back, backWords } = props;
  const [open, setOpen] = useState(props.openOnArrival && savedSummary === null);
  const noteRef = useRef<HTMLDivElement>(null);
  const showNote = savedSummary !== null && !open;
  // After a save the form unmounts: keyboard focus moves to the success note.
  useEffect(() => {
    if (showNote) noteRef.current?.focus();
  }, [showNote]);
  return (
    <div className="price-entry" data-price-entry={row.key}>
      {!showNote ? null : (
        <div className="price-entry__saved" role="status" tabIndex={-1} ref={noteRef} data-price-entry-saved>
          <p>{savedSummary}</p>
          {back ? (
            <Link to={back} data-price-entry-back>
              {backWords}
            </Link>
          ) : null}
        </div>
      )}
      {open ? (
        <PriceEntryForm
          {...props}
          onClose={() => setOpen(false)}
          onSaved={(key, summary) => {
            setOpen(false);
            props.onSaved(key, summary);
          }}
        />
      ) : (
        <button type="button" className="button" data-price-entry-open onClick={() => setOpen(true)}>
          {PRICE_ENTRY_WORDS.open}
        </button>
      )}
    </div>
  );
}

function PriceEntryForm({
  siteId,
  row,
  entry,
  client,
  onSaved,
  onClose,
}: PriceEntrySlotProps & { onClose: () => void }) {
  const id = useId();
  // One idempotency key per opened form, reused on every retry (rev 5 §5.3).
  // "Change" starts a new key (an edited request must not reuse the key of a save that may have landed).
  const keyRef = useRef(freshPriceEntryKey());
  const idempotencyKey = keyRef.current;
  const formRef = useRef<HTMLFormElement>(null);
  const [focusOn, setFocusOn] = useState<{ what: "amount" | "confirm" | "problem" } | null>({ what: "amount" });
  // Focus follows the step: Amount on open, the summary (or Reason) on confirm, the first invalid field on a refusal.
  useEffect(() => {
    const root = formRef.current;
    if (focusOn === null || root === null) return;
    let target: HTMLElement | null = null;
    if (focusOn.what === "amount") target = root.querySelector<HTMLElement>('input[name="value"]');
    else if (focusOn.what === "confirm") {
      target = root.querySelector<HTMLElement>('textarea[name="reason"]') ?? root.querySelector<HTMLElement>("[data-price-entry-summary]");
    } else {
      const bad = root.querySelector<HTMLElement>('[aria-invalid="true"]');
      target = bad instanceof HTMLFieldSetElement ? bad.querySelector<HTMLElement>("input") : bad;
    }
    target?.focus();
  }, [focusOn]);
  const fixedCurrency = row.current?.currency ?? null;
  const [value, setValue] = useState("");
  const [currency, setCurrency] = useState(
    fixedCurrency ?? (entry.currencies.includes("USD") ? "USD" : entry.currencies[0] ?? ""),
  );
  const [basis, setBasis] = useState<PriceBasis | null>(null);
  const [source, setSource] = useState("");
  const [appliesFrom, setAppliesFrom] = useState(entry.today ?? "");
  const [reason, setReason] = useState("");
  const [phase, setPhase] = useState<Phase>("editing");
  const [dry, setDry] = useState<PriceEntryDryRun | null>(null);
  const [reasonRequired, setReasonRequired] = useState(false);
  const [problem, setProblem] = useState<{ text: string; fields: string[] } | null>(null);

  const request = (): PriceEntryRequest => ({
    key: row.key,
    value: value.trim(),
    currency,
    basis,
    source: source.trim(),
    applies_from: appliesFrom,
    reason: reason.trim() === "" ? null : reason.trim(),
    dry_run: false,
    idempotency_key: idempotencyKey,
  });

  function refusedText(message: string | null, fields: string[]): string {
    const named = fields.map((f) => FIELD_WORDS[f]).filter((w): w is string => w !== undefined);
    const check = named.length === 0 ? "" : ` ${PRICE_ENTRY_WORDS.check} ${named.join(", ")}.`;
    return `${message ?? ""}${check} ${PRICE_ENTRY_WORDS.nothingSaved}`.trim();
  }

  async function onContinue(event: FormEvent) {
    event.preventDefault();
    setPhase("checking");
    setProblem(null);
    const result = await client.dryRun(siteId, request());
    if (result.status === "ok") {
      setDry(result.value);
      setReasonRequired(result.value.reason_required);
      setPhase("confirm");
      setFocusOn({ what: "confirm" });
      return;
    }
    setPhase("editing");
    if (result.status === "refused") setProblem({ text: refusedText(result.message, result.fields), fields: result.fields });
    else setProblem({ text: PRICE_ENTRY_WORDS.unavailable, fields: [] });
    setFocusOn({ what: "problem" });
  }

  async function onSave(event: FormEvent) {
    event.preventDefault();
    setPhase("saving");
    setProblem(null);
    const result = await client.save(siteId, request());
    if (result.status === "ok") {
      onSaved(row.key, result.value.summary);
      return;
    }
    if (result.status === "lost") {
      setPhase("confirm");
      setProblem({ text: PRICE_ENTRY_WORDS.lost, fields: [] });
      return;
    }
    if (result.status === "unavailable") {
      setPhase("confirm");
      setProblem({ text: PRICE_ENTRY_WORDS.unavailable, fields: [] });
      return;
    }
    if (result.code === "IDEMPOTENCY_KEY_REUSED") {
      // The store's own words carry the key and a revision id, and "nothing was written" may be false for the
      // earlier save: say what is honest instead.
      setPhase("confirm");
      setProblem({ text: PRICE_ENTRY_WORDS.keyReused, fields: [] });
      return;
    }
    const text = refusedText(result.message, result.fields);
    if (result.code === "REASON_REQUIRED") {
      setReasonRequired(true);
      setPhase("confirm");
      setFocusOn({ what: "confirm" });
    } else {
      setPhase("editing");
      setFocusOn({ what: "problem" });
    }
    setProblem({ text, fields: result.fields });
  }

  const editing = phase === "editing" || phase === "checking";
  const invalid = (field: string) => (problem?.fields.includes(field) ? true : undefined);
  const unit = entry.unit_text[row.key] ?? "";
  const titleId = `${id}-title`;

  return (
    <form
      className="price-entry__form"
      aria-labelledby={titleId}
      ref={formRef}
      data-price-entry-form={phase}
      onSubmit={editing ? onContinue : onSave}
      noValidate
    >
      <h3 id={titleId} className="price-entry__title">
        {PRICE_ENTRY_WORDS.title} · {row.label}
      </h3>
      <fieldset className="price-entry__fields" disabled={!editing || phase === "checking"}>
        <div className="price-entry__field">
          <label htmlFor={`${id}-value`}>{PRICE_ENTRY_WORDS.amount}</label>
          <span className="price-entry__amount">
            <input
              id={`${id}-value`}
              name="value"
              inputMode="decimal"
              autoComplete="off"
              value={value}
              aria-invalid={invalid("value")}
              onChange={(e) => setValue(e.target.value)}
            />
            <span className="price-entry__unit" data-price-entry-unit>
              {currency} {unit}
            </span>
          </span>
        </div>
        <div className="price-entry__field">
          {fixedCurrency !== null ? (
            <>
              <span className="price-entry__label">{PRICE_ENTRY_WORDS.currency}</span>
              <span data-price-entry-currency="fixed">{fixedCurrency}</span>
            </>
          ) : (
            <>
              <label htmlFor={`${id}-currency`}>{PRICE_ENTRY_WORDS.currency}</label>
              <select
                id={`${id}-currency`}
                name="currency"
                value={currency}
                aria-invalid={invalid("currency")}
                onChange={(e) => setCurrency(e.target.value)}
              >
                {entry.currencies.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </>
          )}
        </div>
        <fieldset className="price-entry__field price-entry__basis" aria-invalid={invalid("basis")}>
          <legend>{PRICE_ENTRY_WORDS.basis}</legend>
          {BASES.map(([b, words]) => (
            <label key={b}>
              <input type="radio" name={`${id}-basis`} value={b} checked={basis === b} onChange={() => setBasis(b)} />{" "}
              {words}
            </label>
          ))}
        </fieldset>
        <div className="price-entry__field">
          <label htmlFor={`${id}-source`}>{PRICE_ENTRY_WORDS.source}</label>
          <input
            id={`${id}-source`}
            name="source"
            maxLength={120}
            value={source}
            aria-invalid={invalid("source")}
            onChange={(e) => setSource(e.target.value)}
          />
        </div>
        <div className="price-entry__field">
          <label htmlFor={`${id}-applies`}>{PRICE_ENTRY_WORDS.appliesFrom}</label>
          <input
            id={`${id}-applies`}
            name="applies_from"
            type="date"
            value={appliesFrom}
            aria-invalid={invalid("applies_from")}
            onChange={(e) => setAppliesFrom(e.target.value)}
          />
        </div>
      </fieldset>
      {editing ? null : (
        <div className="price-entry__confirm" data-price-entry-confirm>
          <h4>{PRICE_ENTRY_WORDS.confirmTitle}</h4>
          <p data-price-entry-summary tabIndex={-1}>{dry?.summary}</p>
          {reasonRequired ? (
            <div className="price-entry__field price-entry__reason">
              <label htmlFor={`${id}-reason`}>{PRICE_ENTRY_WORDS.reason}</label>
              <small>{PRICE_ENTRY_WORDS.reasonHint}</small>
              <textarea
                id={`${id}-reason`}
                name="reason"
                maxLength={200}
                rows={2}
                value={reason}
                aria-invalid={invalid("reason")}
                disabled={phase === "saving"}
                onChange={(e) => setReason(e.target.value)}
              />
            </div>
          ) : null}
        </div>
      )}
      {problem === null ? null : (
        <p className="price-entry__problem" role="alert" data-price-entry-problem>
          {problem.text}
        </p>
      )}
      <div className="price-entry__actions">
        {editing ? (
          <button type="submit" className="button primary" disabled={phase === "checking"} data-price-entry-continue>
            {phase === "checking" ? PRICE_ENTRY_WORDS.checking : PRICE_ENTRY_WORDS.continue}
          </button>
        ) : (
          <>
            <button
              type="submit"
              className="button primary"
              disabled={phase === "saving" || (reasonRequired && reason.trim() === "")}
              data-price-entry-save
            >
              {phase === "saving" ? PRICE_ENTRY_WORDS.saving : PRICE_ENTRY_WORDS.save}
            </button>
            <button
              type="button"
              className="button"
              disabled={phase === "saving"}
              onClick={() => {
                keyRef.current = freshPriceEntryKey();
                setPhase("editing");
                setProblem(null);
                setFocusOn({ what: "amount" });
              }}
            >
              {PRICE_ENTRY_WORDS.change}
            </button>
          </>
        )}
        <button type="button" className="button" disabled={phase === "saving"} onClick={onClose} data-price-entry-cancel>
          {PRICE_ENTRY_WORDS.cancel}
        </button>
      </div>
    </form>
  );
}
