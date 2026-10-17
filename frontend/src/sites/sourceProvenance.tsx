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

export interface SourceProvenance {
  tenant_id: string;
  site_id: string;
  finding_revision_id: string | null;
  consequence_revision_id: string | null;
  cited_accepted_evidence_ids: string[];
  power_accepted_evidence_ids: string[] | null;
  finding_revision_state?: SourceState;
  state: SourceState;
  reasons: SourceReason[];
  accepted_evidence_ids: string[];
  problematic_accepted_evidence_ids: string[];
  publication_ids: string[];
  source_classes: string[];
  fixtures: { fixture_id: string; fixture_version: string }[];
  runs: { run_id: string; run_identity_sha256: string }[];
  evidence: SourceEvidenceLink[];
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
};

export function reasonWords(code: string): string {
  return REASON_WORDS[code] ?? "Another source problem was recorded.";
}

/** The state a reader is shown; a missing block is unknown, never positive. */
export function sourceState(p: SourceProvenance | null | undefined): SourceState {
  // Review L2: a state this client does not know (e.g. a later attested class) reads as unverified, never throws.
  const state = p?.state;
  return state !== undefined && Object.prototype.hasOwnProperty.call(SOURCE_WORDS, state) ? state : "UNKNOWN";
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
}: {
  provenance: SourceProvenance | null | undefined;
  subject: string;
  name: string;
}) {
  const state = sourceState(provenance);
  const words = SOURCE_WORDS[state];
  const tone = state === "AUTHORED_DEMONSTRATION" || state === "REGISTERED_SIMULATION" ? "notice--info" : "";
  return (
    <div className="source-provenance" data-source-provenance={state} data-source-provenance-subject={name}>
      <p className={`notice ${tone}`.trim()}>
        <strong>{words.label}.</strong> {words.statement}
      </p>{" "}
      {provenance ? (
        <Disclosure summary={`Source record for this ${subject}`} name={`source-provenance-${name}`}>
          <p data-source-method>
            Each record behind this result is checked against the source registration made before the record was
            accepted. A result is labelled as prepared or generated only when every one of its records has that same
            registered source.
          </p>
          {provenance.reasons.length > 0 ? (
            <ul>
              {provenance.reasons.map((r) => (
                <li key={r.code} data-source-reason={r.code}>
                  {reasonWords(r.code)}
                  {r.accepted_evidence_ids.length > 0 ? ` (${r.accepted_evidence_ids.length} records)` : null}
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
          <IdList title="Source registrations" ids={provenance.publication_ids} />
          <IdList title="Prepared examples" ids={provenance.fixtures.map((f) => `${f.fixture_id} v${f.fixture_version}`)} />
          <IdList title="Generated test sets" ids={provenance.runs.map((r) => r.run_id)} />
          <IdList title="Records whose source is not established" ids={provenance.problematic_accepted_evidence_ids} />
          <p>
            {provenance.accepted_evidence_ids.length} accepted records checked
            {provenance.power_accepted_evidence_ids
              ? ` (${provenance.cited_accepted_evidence_ids.length} cited by the finding, ${provenance.power_accepted_evidence_ids.length} generator readings used for the cost)`
              : ""}
            .
          </p>
        </Disclosure>
      ) : null}
    </div>
  );
}
