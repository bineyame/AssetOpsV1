/**
 * POLISH §3 ids (Addendum 5): the one region allowed to hold identifiers. Every UUID, record reference, enum code
 * and raw timestamp a page keeps for audit sits inside a closed "Technical details" disclosure that carries
 * `data-technical-details`; the capture gate removes only that region's text before its id checks.
 */
import type { ReactNode } from "react";

import { Disclosure } from "./Disclosure";
import type { ExactReference } from "./ProductStatus";

export const TECHNICAL_DETAILS = "Technical details";

/** The closed "Technical details" disclosure. */
export function TechnicalDetails({
  name,
  summary = TECHNICAL_DETAILS,
  children,
}: {
  name: string;
  summary?: ReactNode;
  children: ReactNode;
}) {
  return (
    <Disclosure summary={summary} name={name} variant="tech" technical>
      {children}
    </Disclosure>
  );
}

/** Labelled exact values, as `ExactReferences` lists them, for use inside `TechnicalDetails`. */
export function TechnicalReferenceList({ references }: { references: readonly ExactReference[] }) {
  if (references.length === 0) return null;
  return (
    <dl className="exact-references__list">
      {references.map((reference) => (
        <div className="exact-references__row" key={reference.label}>
          <dt>{reference.label}</dt>
          <dd>
            {reference.value === null ? "not recorded" : <code data-vocabulary-exempt="source-reference">{reference.value}</code>}
          </dd>
        </div>
      ))}
    </dl>
  );
}

/**
 * The closed "How this was worked out" disclosure (the `ExactReferences` shape and data attributes) whose plain
 * lines stay readable, with the exact values nested one level down in "Technical details".
 */
export function WorkedOut({
  name,
  lines,
  references,
  extra,
  variant,
}: {
  name: string;
  /** Plain-language lines shown when the disclosure opens. */
  lines?: ReactNode;
  references: readonly ExactReference[];
  /** Other closed detail folded into the same disclosure. */
  extra?: ReactNode;
  variant?: "tech";
}) {
  const hasLines = lines !== undefined && lines !== null && lines !== false;
  if (references.length === 0 && !hasLines && (extra === undefined || extra === null)) return null;
  const className = variant === "tech" ? "disclosure exact-references exact-references--tech" : "disclosure exact-references";
  if (!hasLines && (extra === undefined || extra === null)) {
    // PB-2 review M1: with no plain lines the middle level would only reveal another disclosure, so the values sit
    // one fold deep in "Technical details" itself (keeping the `data-exact-references` hook and name).
    return (
      <details className={`${className} disclosure--tech`} data-disclosure={name} data-exact-references data-technical-details="">
        <summary className="disclosure__summary">{TECHNICAL_DETAILS}</summary>
        <div className="disclosure__body">
          <TechnicalReferenceList references={references} />
        </div>
      </details>
    );
  }
  return (
    <details className={className} data-disclosure={name} data-exact-references>
      <summary className="disclosure__summary">How this was worked out</summary>
      <div className="disclosure__body">
        {hasLines ? <div className="exact-references__lines">{lines}</div> : null}
        {references.length === 0 ? null : (
          <TechnicalDetails name={`${name}-technical`}>
            <TechnicalReferenceList references={references} />
          </TechnicalDetails>
        )}
      </div>
      {extra === undefined || extra === null ? null : <div className="disclosure__body exact-references__extra">{extra}</div>}
    </details>
  );
}
