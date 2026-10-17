import type { ReactNode } from "react";
import { asOfText, type OutcomeWords, type ProductWords } from "./productWords";

/**
 * The shared W1 presentation components (W1-UX-01, D-2026-10-16-w1-ux).
 *
 * Each renders words and values its caller already read. None of them reads a
 * store or decides a state: currentness, outcome, amount, zero, completeness
 * and source all arrive as props. The state sentence, its scope and the plain
 * "as of" bound render in the default reading, never inside a tab or the
 * closed exact-reference disclosure.
 */

export interface ProductStatusProps {
  /** Words from the shared map (`currentnessWords`, `moneyWords`, ...). */
  words: ProductWords;
  /** What the state is about: the site, period or object, in plain words. */
  scope: ReactNode;
  /** The instant the read is bounded by, exactly as the read returned it. */
  asOf: string | null | undefined;
  /** Extra material beside the state (a failed limit, known failures). */
  children?: ReactNode;
  /**
   * W1-F3 (additive): render as one-line `status-strip__*` parts for use inside
   * a `.status-strip--line`, with the same words, scope and bound. No blocks.
   */
  inline?: boolean;
}

/** The plain state line: state sentence, scope and "as of" bound together. */
export function ProductStatus({ words, scope, asOf, children, inline = false }: ProductStatusProps) {
  if (inline) {
    return (
      <span className={`status-strip__state product-status--${words.tone}`} data-product-status={words.tone}>
        <strong className="product-status__label" data-product-status-label>
          {words.label}
        </strong>{" "}
        <span className="product-status__sentence">{words.sentence}</span>
        {children}{" "}
        {/* W1-F3 review L10: no leading separator, so a wrapped bound never starts its line with "·". */}
        <span className="product-status__bound">
          <span data-product-status-scope>{scope}</span>
          <span aria-hidden="true"> · </span>
          <span data-product-status-as-of>{asOfText(asOf)}</span>
        </span>
        {words.next === undefined ? null : (
          <>
            <span aria-hidden="true"> · </span>
            <span className="product-status__next" data-product-status-next>
              {words.next}
            </span>
          </>
        )}
      </span>
    );
  }
  return (
    <div className={`product-status product-status--${words.tone}`} data-product-status={words.tone}>
      <p className="product-status__label" data-product-status-label>
        {words.label}
      </p>
      <p className="product-status__sentence">{words.sentence}</p>
      {children}
      <p className="product-status__bound">
        <span data-product-status-scope>{scope}</span>
        <span aria-hidden="true"> · </span>
        <span data-product-status-as-of>{asOfText(asOf)}</span>
      </p>
      {words.next === undefined ? null : (
        <p className="product-status__next" data-product-status-next>
          {words.next}
        </p>
      )}
    </div>
  );
}

export interface FailedLimit {
  /** Plain name of the measured limit, e.g. "Battery reserve". */
  name: string;
  /** The measured value as the read returned it. */
  value: string;
  /** The threshold as the read returned it. */
  threshold: string;
  unit: string;
}

export interface ProductOutcomeProps {
  words: OutcomeWords;
  scope: ReactNode;
  asOf: string | null | undefined;
  /** Failed limits the read reported; shown beside a safety or service miss. */
  failedLimits?: readonly FailedLimit[];
  /** Known failures the read reported, in plain words. */
  knownFailures?: readonly string[];
  /** Show the measured limits even where the outcome is not a safety miss (an inconclusive read that measured one). */
  showLimits?: boolean;
}

/**
 * A trial outcome. The source qualification is always visible; a
 * demonstration source carries the policy-trial, no-benefit note; a safety or
 * service miss shows each failed limit with value, threshold and unit; an
 * inconclusive or ineffective outcome keeps every known failure visible.
 */
export function ProductOutcome({ words, scope, asOf, failedLimits = [], knownFailures = [], showLimits = false }: ProductOutcomeProps) {
  return (
    <ProductStatus words={words} scope={scope} asOf={asOf}>
      <p className="product-status__source" data-product-outcome-source>
        Source: {words.source.label}
      </p>
      {words.demonstrationNote === null ? null : (
        <p className="product-status__note" data-product-outcome-demonstration>
          {words.demonstrationNote}
        </p>
      )}
      {words.showsFailedLimit || (showLimits && failedLimits.length > 0) ? (
        failedLimits.length > 0 ? (
          <ul className="product-status__list" data-product-outcome-failed-limits>
            {failedLimits.map((limit) => (
              <li key={limit.name}>
                {limit.name}: measured {limit.value} {limit.unit}, limit {limit.threshold} {limit.unit}
              </li>
            ))}
          </ul>
        ) : (
          <p className="product-status__note" data-product-outcome-failed-limits>
            The failed limit's measured value is not in this record.
          </p>
        )
      ) : null}
      {words.showsKnownFailures && knownFailures.length > 0 ? (
        <ul className="product-status__list" data-product-outcome-known-failures>
          {knownFailures.map((failure) => (
            <li key={failure}>Known failure: {failure}</li>
          ))}
        </ul>
      ) : null}
    </ProductStatus>
  );
}

export interface ProductLimitationProps {
  /** Words from `limitationWords`. */
  words: ProductWords;
}

/** One limitation: its cause sentence and, when known, the next useful step. */
export function ProductLimitation({ words }: ProductLimitationProps) {
  return (
    <li className="product-limitation" data-product-limitation={words.unrecognised ? "unrecognised" : "known"}>
      <span className="product-limitation__label">{words.label}.</span> {words.sentence}
      {words.next === undefined ? null : <> {words.next}</>}
    </li>
  );
}

export interface ExactReference {
  /** A plain label saying what the value identifies. */
  label: string;
  /** The exact value, unchanged. Null renders "not recorded". */
  value: string | null;
}

export interface ExactReferencesProps {
  /** A stable name, on `data-disclosure`. */
  name: string;
  references: readonly ExactReference[];
  /** `tech`: the mock's small link-styled `details.tech`, for a strip or table foot. */
  variant?: "tech";
}

/**
 * The closed "How this was worked out" disclosure: a few individually
 * labelled exact values, nothing else. Each value is one exempt source
 * reference; its label is scanned. The closed summary is fixed text, so a raw
 * code never reaches it or its accessible name. Method, coverage and
 * calculation belong in the owning destination, not here.
 */
export function ExactReferences({ name, references, variant }: ExactReferencesProps) {
  if (references.length === 0) return null;
  const className = variant === "tech" ? "disclosure exact-references exact-references--tech" : "disclosure exact-references";
  return (
    <details className={className} data-disclosure={name} data-exact-references>
      <summary className="disclosure__summary">How this was worked out</summary>
      <dl className="disclosure__body exact-references__list">
        {references.map((reference) => (
          <div className="exact-references__row" key={reference.label}>
            <dt>{reference.label}</dt>
            <dd>
              {reference.value === null ? (
                "not recorded"
              ) : (
                <code data-vocabulary-exempt="source-reference">{reference.value}</code>
              )}
            </dd>
          </div>
        ))}
      </dl>
    </details>
  );
}

export interface HeadlineVisualCardProps {
  /** The screen's question, as a small eyebrow above the answer. */
  question: string;
  /**
   * A panel title (the v69 panel heading). When given it is the card's
   * heading and the answer is its lead paragraph; otherwise the answer is the
   * heading.
   */
  title?: string;
  /** One plain line under the title. Only with `title`. */
  description?: string;
  /** The heading id, for `aria-labelledby`. */
  headingId: string;
  /** The answer, only as strong as the read. */
  headline: ReactNode;
  /** The plain state line (usually a `ProductStatus`), beside the headline. */
  status: ReactNode;
  /** A small visual with readable text. Omitted when there is nothing to draw. */
  visual?: ReactNode;
  /** "What this means" content. */
  meaning: ReactNode;
  /** "What to do" content. Omitted when there is no useful next step. */
  todo?: ReactNode;
  /** The owning destination link (Analysis, Evidence, ...), with its context. */
  destination?: ReactNode;
  /** The closed exact-reference disclosure. */
  references?: ReactNode;
  /** Extra data attributes for the card's tests. */
  dataName: string;
}

/**
 * The v69 answer card: question, headline answer, state line, small visual,
 * then "What this means" and "What to do", the destination link, and the
 * closed exact-reference disclosure last.
 */
export function HeadlineVisualCard({
  question,
  title,
  description,
  headingId,
  headline,
  status,
  visual,
  meaning,
  todo,
  destination,
  references,
  dataName,
}: HeadlineVisualCardProps) {
  return (
    <section className="panel headline-card" aria-labelledby={headingId} data-headline-card={dataName}>
      {title === undefined ? null : (
        <div className="panel__header">
          <h2 className="panel__heading" id={headingId}>
            {title}
          </h2>
          {description === undefined ? null : <p className="panel__description">{description}</p>}
        </div>
      )}
      <div className="panel__body headline-card__body">
        <p className="headline-card__question">{question}</p>
        {title === undefined ? (
          <h2 className="headline-card__headline" id={headingId}>
            {headline}
          </h2>
        ) : (
          <p className="headline-card__headline">{headline}</p>
        )}
        <div className="headline-card__status">{status}</div>
        {visual === undefined ? null : <div className="headline-card__visual">{visual}</div>}
        <div className="headline-card__pair">
          <div className="headline-card__block" data-headline-card-meaning>
            <h3 className="headline-card__block-title">What this means</h3>
            {meaning}
          </div>
          {todo === undefined ? null : (
            <div className="headline-card__block" data-headline-card-todo>
              <h3 className="headline-card__block-title">What to do</h3>
              {todo}
            </div>
          )}
        </div>
        {destination === undefined ? null : <p className="headline-card__destination">{destination}</p>}
        {references}
      </div>
    </section>
  );
}

export interface ValueBarItem {
  label: string;
  /** A stable key, on `data-value-bar-key`. Defaults to the label. */
  key?: string;
  /** The value the read returned; null when it is not known. */
  value: number | null;
  /** Readable value text, e.g. "288 readings". Ignored when value is null. */
  valueText: string;
}

export interface ValueBarsProps {
  /** Accessible name of the whole graphic. */
  title: string;
  items: readonly ValueBarItem[];
}

/**
 * Small horizontal bars with readable text. A null value draws a distinct
 * hatched "not known" mark with the words "not known", never a zero-length
 * bar; a known zero draws an empty track with its "0" text. The scale is the
 * largest known value; with no known positive value every bar is empty.
 */
export function ValueBars({ title, items }: ValueBarsProps) {
  const known = items.map((i) => i.value).filter((v): v is number => v !== null && v > 0);
  const max = known.length === 0 ? 0 : Math.max(...known);
  const description = items.map((i) => `${i.label}: ${i.value === null ? "not known" : i.valueText}`).join("; ");
  return (
    <figure className="value-bars" data-value-bars>
      <figcaption className="value-bars__title">{title}</figcaption>
      <ul className="value-bars__list" aria-label={`${title}. ${description}`}>
        {items.map((item) => (
          <li
            className="value-bars__row"
            key={item.key ?? item.label}
            data-value-bar={item.value === null ? "not-known" : "known"}
            data-value-bar-key={item.key ?? item.label}
          >
            <span className="value-bars__label">{item.label}</span>
            <span className="value-bars__track" aria-hidden="true">
              {item.value === null ? (
                <span className="value-bars__unknown" data-value-bar-mark="not-known" />
              ) : (
                <span
                  className="value-bars__fill"
                  data-value-bar-mark="known"
                  style={{ width: max === 0 ? "0%" : `${Math.round((item.value / max) * 100)}%` }}
                />
              )}
            </span>
            <span className="value-bars__value">{item.value === null ? "not known" : item.valueText}</span>
          </li>
        ))}
      </ul>
    </figure>
  );
}

export type StepState = "done" | "waiting" | "problem" | "not-known";

export interface Step {
  label: string;
  state: StepState;
  /** Readable detail under the step, e.g. a date or "Not applied yet". */
  detail: string;
}

const STEP_WORDS: Record<StepState, string> = {
  done: "Done",
  waiting: "Not yet",
  problem: "Problem",
  "not-known": "Not known",
};

/**
 * A small ordered step strip with readable text: each step says its state in
 * words, so meaning never rests on the mark or its colour. The caller passes
 * each step's state from its read; nothing is inferred here.
 */
export function StepStrip({ title, steps }: { title: string; steps: readonly Step[] }) {
  return (
    <figure className="step-strip" data-step-strip>
      <figcaption className="value-bars__title">{title}</figcaption>
      <ol className="step-strip__list">
        {steps.map((step) => (
          <li className={`step-strip__step step-strip__step--${step.state}`} key={step.label} data-step={step.state}>
            <span className="step-strip__mark" aria-hidden="true" />
            <span className="step-strip__label">{step.label}</span>
            <span className="step-strip__state">{STEP_WORDS[step.state]}</span>
            <span className="step-strip__detail">{step.detail}</span>
          </li>
        ))}
      </ol>
    </figure>
  );
}
