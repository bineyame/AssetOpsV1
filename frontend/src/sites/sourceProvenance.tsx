import { Disclosure } from "../ui";

/**
 * S4-05b phase 1: the stored exact-revision source provenance every Finding and money read carries
 * (`backend/assetops_backend/evidence/provenance_read.py`, S4-05 shared contract item 3).
 *
 * The source label comes only from the server's stored binding of the exact accepted evidence IDs, never from a
 * date, a Site or a spec file. Labels and statements follow D-2026-10-16-s405b-label (interim; the owner's W1
 * copy checkpoint sets final wording). Label and statement are always visible; identifiers, publications and
 * reasons sit in the closed source disclosure in plain words; reason codes stay in `data-source-reason`.
 */

export type SourceState = "AUTHORED_DEMONSTRATION" | "REGISTERED_SIMULATION" | "MIXED" | "UNKNOWN";

export interface SourceReason {
  code: string;
  accepted_evidence_ids: string[];
  [detail: string]: unknown;
}

export interface SourceEvidenceLink {
  accepted_evidence_id: string;
  status: string;
  batch_id: string | null;
  publication_id: string | null;
  source_class: string | null;
  fixture_id: string | null;
  fixture_version: string | null;
  run_id: string | null;
  run_identity_sha256: string | null;
  broken_detail: string | null;
}

/** The detail block of a public DTO (`evidence/public_provenance.py` `DETAIL_KEYS`). */
export interface SourceProvenanceDetail {
  state?: string;
  reasons?: SourceReason[];
  accepted_evidence_ids?: string[];
  problematic_accepted_evidence_ids?: string[];
  publication_ids?: string[];
  source_classes?: string[];
  fixtures?: { fixture_id: string; fixture_version: string }[];
  runs?: { run_id: string; run_identity_sha256: string }[];
  evidence?: SourceEvidenceLink[];
}

/**
 * W3-01 (Run 3 q3): one source block. A W1 resolver result keeps its top-level fields and gains the public keys;
 * a cold/EV set-only DTO has only `classification,state,source_ids,evidence_ids,basis_sha256,reasons` and an
 * optional `detail`; the fail-closed `unresolved` W1 shape has `state` and `reasons` without the public keys.
 * Every field is therefore optional and read defensively.
 */
export interface SourceProvenance {
  classification?: string | null;
  state?: SourceState | string;
  source_ids?: string[];
  evidence_ids?: string[];
  basis_sha256?: string | null;
  detail?: SourceProvenanceDetail;
  tenant_id?: string;
  site_id?: string;
  finding_revision_id?: string | null;
  consequence_revision_id?: string | null;
  cited_accepted_evidence_ids?: string[];
  power_accepted_evidence_ids?: string[] | null;
  finding_revision_state?: SourceState;
  reasons?: SourceReason[];
  accepted_evidence_ids?: string[];
  problematic_accepted_evidence_ids?: string[];
  publication_ids?: string[];
  source_classes?: string[];
  fixtures?: { fixture_id: string; fixture_version: string }[];
  runs?: { run_id: string; run_identity_sha256: string }[];
  evidence?: SourceEvidenceLink[];
}

/** The three window siblings a cold/EV envelope carries (Run 1 ruling 5, Run 3 q3). */
export interface SourceProvenanceBlocks {
  source_provenance: SourceProvenance;
  selected_source_provenance?: SourceProvenance | null;
  pending_source_provenance?: SourceProvenance | null;
}

/** The pair a money read names: the selected Finding version's set and the consequence version's union. */
export interface SourceProvenancePair {
  finding_revision: SourceProvenance | null;
  consequence_revision: SourceProvenance | null;
}

export const SOURCE_WORDS: Record<SourceState, { label: string; statement: string }> = {
  AUTHORED_DEMONSTRATION: {
    label: "Prepared example data",
    statement: "These records were prepared for an example. They are not readings from physical equipment.",
  },
  REGISTERED_SIMULATION: {
    label: "Generated test data",
    statement: "These records were generated for a test. They are not readings from physical equipment.",
  },
  MIXED: {
    label: "Sources do not agree",
    statement: "The records behind this result have different or unverified sources. No current cost is shown.",
  },
  UNKNOWN: {
    label: "Source unverified",
    statement: "We cannot establish the source of all records behind this result. No current cost is shown.",
  },
};

/** Plain words for each typed reason; the code itself stays in `data-source-reason`. */
const REASON_WORDS: Record<string, string> = {
  EMPTY_CITATION_SET: "This version cites no records.",
  EVIDENCE_NOT_FOUND: "Some cited records could not be found.",
  FOREIGN_SITE_EVIDENCE: "Some cited records belong to another site.",
  BROKEN_PUBLICATION_LINK: "The source record of some readings is damaged or does not match them.",
  NO_POSITIVE_BINDING: "No reading has a confirmed source.",
  BOUND_AND_UNBOUND: "Some readings have a confirmed source and some do not.",
  CROSSED_SOURCE_CLASSES: "Prepared example records and generated test records are combined.",
  AUTHORED_FIXTURE_VERSION_CONFLICT: "Records from different prepared examples are combined.",
  MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS: "Readings from more than one generated data set are combined.",
  RUN_IDENTITY_CONFLICT: "One generated data set is recorded with conflicting identities.",
  CONSEQUENCE_POWER_INPUT_CONFLICT: "The generator readings used for the cost do not share the finding's source.",
  PROVENANCE_NOT_WIRED: "The source record could not be read.",
  PROVENANCE_UNREADABLE: "The source record could not be read.",
  PROVENANCE_REVISION_NOT_FOUND: "The source record could not be read.",
  SOURCE_CLASS_MISMATCH: "The stored source label does not match the records it cites.",
};

export function reasonWords(code: string): string {
  return REASON_WORDS[code] ?? "Another source problem was recorded.";
}

/** The state a reader is shown; a missing block is unknown, never positive. */
export function sourceState(p: SourceProvenance | null | undefined): SourceState {
  // Review L2: a state this client does not know (e.g. a later attested class) reads as unverified, never throws.
  // W3-01: the public `classification` first, then the W1 resolver `state`; absent or unrecognized is unknown.
  const state = p?.classification ?? p?.state;
  return typeof state === "string" && Object.prototype.hasOwnProperty.call(SOURCE_WORDS, state) ? (state as SourceState) : "UNKNOWN";
}

function IdList({ title, ids }: { title: string; ids: string[] }) {
  if (ids.length === 0) return null;
  return (
    <p>
      {title}: <code data-vocabulary-exempt="source-reference">{ids.join(", ")}</code>
    </p>
  );
}

/** The source line for one exact Finding or consequence version, with its identifiers in a closed disclosure. */
export function SourceProvenanceNotice({
  provenance,
  subject,
  name,
  compact = false,
  record = "inline",
}: {
  provenance: SourceProvenance | null | undefined;
  subject: string;
  name: string;
  /**
   * W1-F2 compaction: the same statement as a note-size line and the same disclosure in the mock's small
   * link-styled form, for a panel the mock keeps short (the Overview money panel). Words are unchanged.
   */
  compact?: boolean;
  /**
   * W1-F5b (carry 8): "inline" keeps the record in this notice's own disclosure; "elsewhere" renders only the
   * statement, for a panel that folds the record into its one closed detail row via `SourceProvenanceRecord`.
   */
  record?: "inline" | "elsewhere";
}) {
  const state = sourceState(provenance);
  const words = SOURCE_WORDS[state];
  const tone = state === "AUTHORED_DEMONSTRATION" || state === "REGISTERED_SIMULATION" ? "notice--info" : "";
  return (
    <div
      className={compact ? "source-provenance source-provenance--compact" : "source-provenance"}
      data-source-provenance={state}
      data-source-provenance-subject={name}
    >
      <p className={compact ? "v69-chart-note source-provenance__line" : `notice ${tone}`.trim()}>
        <strong>{words.label}.</strong> {words.statement}
      </p>{" "}
      {provenance && record === "inline" ? (
        <Disclosure
          summary={`Source record for this ${subject}`}
          name={`source-provenance-${name}`}
          variant={compact ? "tech" : undefined}
        >
          <SourceProvenanceRecord provenance={provenance} />
        </Disclosure>
      ) : null}
    </div>
  );
}

/** The source record behind a result: the method, reasons and the exact registrations, fixtures and runs. */
export function SourceProvenanceRecord({ provenance }: { provenance: SourceProvenance }) {
  // W3-01: read the public `detail` when present, else the W1 top-level fields; missing lists are empty.
  const d = provenance.detail ?? {};
  const reasons = d.reasons ?? provenance.reasons ?? [];
  const accepted = d.accepted_evidence_ids ?? provenance.accepted_evidence_ids ?? provenance.evidence_ids ?? [];
  const problematic = d.problematic_accepted_evidence_ids ?? provenance.problematic_accepted_evidence_ids ?? [];
  const publications = d.publication_ids ?? provenance.publication_ids ?? [];
  const fixtures = d.fixtures ?? provenance.fixtures ?? [];
  const runs = d.runs ?? provenance.runs ?? [];
  const cited = provenance.cited_accepted_evidence_ids ?? [];
  return (
    <>
      <p data-source-method>
        Each record behind this result is checked against the source registration made before the record was
        accepted. A result is labelled as prepared or generated only when every one of its records has that same
        registered source.
      </p>
      {reasons.length > 0 ? (
        <ul>
          {reasons.map((r) => (
            <li key={r.code} data-source-reason={r.code}>
              {reasonWords(r.code)}
              {(r.accepted_evidence_ids ?? []).length > 0 ? ` (${(r.accepted_evidence_ids ?? []).length} records)` : null}
            </li>
          ))}
        </ul>
      ) : null}
      {provenance.finding_revision_id ? (
        <IdList title="Finding version" ids={[provenance.finding_revision_id]} />
      ) : null}
      {provenance.consequence_revision_id ? (
        <IdList title="Fuel cost version" ids={[provenance.consequence_revision_id]} />
      ) : null}
      <IdList title="Source registrations" ids={publications} />
      <IdList title="Prepared examples" ids={fixtures.map((f) => `${f.fixture_id} v${f.fixture_version}`)} />
      <IdList title="Generated test sets" ids={runs.map((r) => r.run_id)} />
      <IdList title="Records whose source is not established" ids={problematic} />
      <p>
        {accepted.length} accepted records checked
        {provenance.power_accepted_evidence_ids
          ? ` (${cited.length} cited by the finding, ${provenance.power_accepted_evidence_ids.length} generator readings used for the cost)`
          : ""}
        .
      </p>
    </>
  );
}

/** W3-01 r1 M2: the selected-result source block of an envelope. A selection-less read has null; a read that carries no
 * sibling (a detail read) falls back to its own row block. The pending alias `source_provenance` never stands in. */
export function selectedSourceBlock<B>(env: { source_provenance: B; selected_source_provenance?: B | null }): B | null {
  return env.selected_source_provenance !== undefined ? env.selected_source_provenance : env.source_provenance;
}

/** The selected-result classification, or null for no selection or an UNKNOWN block. */
export function selectedClassification(env: { source_provenance: { classification: string | null }; selected_source_provenance?: { classification: string | null } | null }): string | null {
  const c = selectedSourceBlock(env)?.classification ?? null;
  return c === "UNKNOWN" ? null : c;
}
