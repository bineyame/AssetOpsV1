/**
 * S6-01b: shared words and small pieces for the Action and Recommendation
 * screens. Plain product wording only: the trial is a policy-sensitivity
 * experiment, the actor of every command is a SYSTEM demonstration, and no
 * screen claims a changed operation, a measured effect or a saving before
 * verification exists (S6-02).
 */
import type { ReactNode } from "react";

import { Panel, UNRECOGNISED_SENTENCE, type ProductWords } from "../ui";
import type { Limitation, Refusal, SystemDemoCapability } from "./actionClient";
import { stamp } from "./dispatchWords";

/** The label every command control and resulting actor carries (Architect Q4). */
import { stateLabel } from "./verificationWords";

export const SYSTEM_DEMONSTRATION = "SYSTEM demonstration";

/**
 * Plain words for the trial limitation by its stable code. The server's own
 * text is the fallback for a code this build does not know.
 */
const LIMITATION_WORDS: Record<string, string> = {
  POLICY_SENSITIVITY_TRIAL_ONLY:
    "A five-percentage-point battery reserve trial chosen by a fixed rule. It tests whether the reserve setting " +
    "matters. It does not say the reserve caused this finding, and it does not predict less generator time, any " +
    "saving or any safety effect.",
};

export function limitationText(limitation: Limitation): string {
  return LIMITATION_WORDS[limitation.code] ?? limitation.text;
}

export function TrialLimitation({ limitation }: { limitation: Limitation }) {
  return (
    <p className="action-limitation" data-action-limitation={limitation.code}>
      <strong>Trial only. </strong>
      {limitationText(limitation)}
    </p>
  );
}

/**
 * An exact stored identifier (ID, code, digest, service name), shown as one
 * source-owned reference value rather than prose.
 */
export function Ref({ value, attr }: { value: string; attr?: string }) {
  return (
    <code className="action-ref" data-vocabulary-exempt="source-reference" {...(attr ? { [attr]: value } : {})}>
      {value}
    </code>
  );
}

export const EVENT_WORDS: Record<string, string> = {
  ACCEPTED: "Accepted",
  APPLIED: "Applied to the Site Foundation",
  FAILED: "Attempt failed",
  OBSERVED: "Review note recorded",
};

export function eventWords(kind: string): string {
  return EVENT_WORDS[kind] ?? kind;
}

export const APPLICATION_WORDS: Record<string, string> = {
  PENDING: "Not applied yet",
  APPLIED: "Applied to the Site Foundation",
};

/**
 * W1-UX-04: the application state as shared state-line words. Domain-local
 * (the shared map does not own application states). Applied is never
 * positive: applying changes a recorded setting, not a measured result.
 */
export function applicationWords(code: string | null | undefined, failedAttempts = 0): ProductWords {
  if (code === "PENDING") {
    return {
      label: failedAttempts > 0 ? "Not applied yet; an attempt failed" : "Not applied yet",
      sentence:
        failedAttempts > 0
          ? "A failed attempt changed nothing on the site. The accepted change can be attempted again."
          : "The change was accepted but has not been applied to the site's recorded settings.",
      next: "Apply the accepted change, or open History to see what was attempted.",
      tone: failedAttempts > 0 ? "problem" : "waiting",
      code,
      unrecognised: false,
    };
  }
  if (code === "APPLIED") {
    return {
      label: "Applied; effect not yet measured",
      sentence:
        "The new setting is recorded for the site. This does not show that generator use, cost or safety changed.",
      next: "Whether it worked is judged on Verification, from a trial plan fixed before the later readings.",
      tone: "limited",
      code,
      unrecognised: false,
    };
  }
  return { label: "Application state not recognised", sentence: UNRECOGNISED_SENTENCE, tone: "limited", code: code ?? null, unrecognised: true };
}

/** An event kind in plain words; an unknown kind never shows its raw code. */
export function plainEventWords(kind: string): string {
  return EVENT_WORDS[kind] ?? "Recorded event of a kind this screen does not recognise";
}

/** The pending outcome, in this build's own words (no effect, saving or verification is claimed). */
export function outcomeWords(state: string): string {
  return state === "PENDING"
    ? "Pending. Nothing has been verified yet, and no effect or saving is claimed."
    : `${stateLabel(state)}.`;
}

export function when(instant: string | null | undefined): string {
  return `${stamp(instant)} UTC`;
}

/**
 * Whether the server granted the exact SYSTEM demonstration command. A client
 * flag can never enable one: only `allowed` from the read, for the named command.
 */
export function granted(capability: SystemDemoCapability | null | undefined, command: string): boolean {
  return capability !== null && capability !== undefined && capability.allowed === true && capability.command === command;
}

/** The read-only state shown instead of a command control. */
export function CommandUnavailable({ capability, what }: { capability: SystemDemoCapability | null | undefined; what: string }) {
  return (
    <p className="action-command-unavailable" data-action-command-unavailable={capability?.command ?? "UNKNOWN"}>
      {what} is read-only here: no {SYSTEM_DEMONSTRATION} capability is granted for this command.
      {capability?.unavailable_reason ? ` Reason given: ${capability.unavailable_reason}` : ""}
    </p>
  );
}

const REFUSAL_HEADINGS: Record<number, string> = {
  401: "Sign-in required",
  403: "No access",
  404: "Not found",
  409: "Refused",
  422: "Refused",
};

/** A typed refusal from a read: HTTP status, server code and message, never an empty result. */
export function RefusalPanel({
  refusal,
  subject,
  headingId,
  children,
}: {
  refusal: Refusal;
  subject: string;
  headingId: string;
  children?: ReactNode;
}) {
  const heading =
    refusal.http === null
      ? `${subject} unavailable`
      : refusal.http === 404
        ? `${subject} not found`
        : (REFUSAL_HEADINGS[refusal.http] ?? `${subject} unavailable`);
  const text =
    refusal.http === null
      ? "The server could not be reached."
      : refusal.http === 401
        ? "Sign in to read this site's Actions."
        : refusal.http === 403
          ? "Your account has no access to this."
          : refusal.http === 404
            ? `This site has no such ${subject.toLowerCase()}.`
            : `The ${subject.toLowerCase()} could not be read (HTTP ${refusal.http}).`;
  return (
    <Panel heading={heading} headingId={headingId}>
      <p data-action-read="refused" data-action-http={refusal.http ?? "none"} data-action-code={refusal.code ?? ""}>
        {text}
      </p>
      {refusal.code ? (
        <p className="action-note">
          Code: <Ref value={refusal.code} />
        </p>
      ) : null}
      {refusal.message ? <p className="action-note">Reason given: {refusal.message}</p> : null}
      {children}
    </Panel>
  );
}

/** A refused command, beside (never instead of) what was already read. */
export function CommandRefusal({ refusal, children }: { refusal: Refusal; children?: ReactNode }) {
  return (
    <div className="action-command-refusal" role="alert" data-action-command-refused={refusal.code ?? refusal.http ?? "none"}>
      <p>
        The command was refused
        {refusal.http !== null ? ` (HTTP ${refusal.http})` : " (the server could not be reached)"}.
        {refusal.code ? (
          <>
            {" "}
            Code: <Ref value={refusal.code} />.
          </>
        ) : null}
      </p>
      {refusal.message ? <p className="action-note">Reason given: {refusal.message}</p> : null}
      {children}
    </div>
  );
}
