/**
 * The body of Site > Evidence at T027: what accepted records exist for this
 * Site, their delivery and quality, their coverage for the selected window and
 * the mapping and configuration they were accepted under (part A of the
 * Evidence recommendation; AC20).
 *
 * From T028 (part B, AC20) the capability table sits above source health:
 * readiness, claim ceiling and missing evidence per declared analytic, all
 * scored by the backend (`CapabilityReadiness.tsx`). Everything shown is
 * accepted evidence or a backend read model over it, never a stage, a run or
 * a simulator artifact.
 *
 * The record inspector is a drill-down, not the tab body: a source or signal
 * row opens it in place, its state lives in the search params (`signal=` or
 * `source=`, then `record=`), and the Site root and tab never change.
 */

import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { DataTable, Fact, FactList, Panel } from "../ui";
import { CapabilityReadinessAnalysis, CapabilityReadinessTable } from "./CapabilityReadiness";
import { INPUT_WORDS } from "./assessmentAnalysis";
import { CoverageByInput } from "./assessmentGraphics";
import { LocalViews, OUTCOME_WORDS, localView, readablePeriod, readableTime } from "./findingPresentation";
import type { DomainPresentationProfile } from "./presentationProfile";
import type { DispatchAssessments, SiteAnalytics, SiteAnalyticsClient } from "./siteAnalyticsClient";
import type {
  EvidenceCoverage,
  EvidenceOverview,
  EvidenceRead,
  EvidenceRecordDetail,
  EvidenceRecordList,
  EvidenceRejections,
  EvidenceSourceHealth,
  SiteEvidenceClient,
} from "./siteEvidenceClient";
import { sourceReferences } from "./vocabularyReference";

/** How many records the inspector lists for one row, newest first. */
export const INSPECTOR_RECORD_LIMIT = 50;

/** The id of the in-page record inspector, for layout evidence and focus. */
export const EVIDENCE_INSPECTOR_ID = "site-evidence-inspector";

type Loaded = {
  overview: EvidenceRead<EvidenceOverview>;
  rejections: EvidenceRead<EvidenceRejections>;
  declaration: EvidenceRead<SiteAnalytics> | null;
};

export interface SiteEvidenceProps {
  siteId: string;
  client: SiteEvidenceClient;
  /** The analytics read model; absent, no capability table is rendered. */
  analytics?: SiteAnalyticsClient;
  profile?: DomainPresentationProfile | null;
}

/** Shown for a rejection when the backend serves no plain reason; never its code. */
const REJECTION_UNAVAILABLE =
  "This record was not accepted. A plain description of the reason is not available.";

function provenance(mode: string): string {
  if (mode === "SIMULATED") {
    return "Demonstration data";
  }
  if (mode === "LIVE") {
    return "Live data";
  }
  return mode;
}

function instant(value: string | null): string {
  return value ?? "none";
}

function windowBasis(basis: string): string {
  return basis === "REQUESTED"
    ? "the window requested in this address"
    : "the accepted window of the latest completed release";
}

export function SiteEvidence({
  siteId,
  client,
  analytics,
  profile = null,
}: SiteEvidenceProps) {
  const [params, setParams] = useSearchParams();
  const from = params.get("from");
  const to = params.get("to");
  const batch = params.get("batch");
  const [loaded, setLoaded] = useState<Loaded | null>(null);

  useEffect(() => {
    let active = true;
    setLoaded(null);
    void Promise.all([
      client.getEvidence(siteId, { from, to }),
      client.listRejections(siteId),
      analytics === undefined ? Promise.resolve(null) : analytics.getDeclaration(siteId),
    ]).then(([overview, rejections, declaration]) => {
      if (active) {
        setLoaded({ overview, rejections, declaration });
      }
    });
    return () => {
      active = false;
    };
  }, [client, analytics, siteId, from, to]);

  const inspect = (key: "signal" | "source", value: string) => {
    const next = new URLSearchParams(params);
    next.delete("signal");
    next.delete("source");
    next.delete("record");
    next.set(key, value);
    setParams(next);
  };

  if (loaded === null) {
    return <p>Loading the site&apos;s evidence.</p>;
  }

  const { overview } = loaded;
  const view = localView(params);
  if (overview.status === "not_found") {
    return (
      <Panel heading="Evidence not found" headingId="site-evidence-missing-heading">
        <p data-evidence-state="not_found">
          The evidence store does not know this site, so no accepted record can
          be shown for it.
        </p>
      </Panel>
    );
  }
  if (overview.status === "unavailable") {
    return (
      <Panel
        heading="Evidence unavailable"
        headingId="site-evidence-unavailable-store-heading"
      >
        <p data-evidence-state="unavailable">
          {overview.message ??
            "The evidence store could not be read, so nothing is known about what this site has accepted."}
        </p>
      </Panel>
    );
  }

  const evidence = overview.value;
  const empty = evidence.sources.length === 0;
  const rejections =
    loaded.rejections.status === "loaded" ? loaded.rejections.value : null;
  const hasBasis =
    evidence.basis.mappings.length > 0 ||
    evidence.basis.configurations.length > 0;

  return (
    <div
      className="site-evidence"
      data-evidence-state={empty ? "empty" : "populated"}
      data-evidence-view={view}
    >
      <LocalViews label={EVIDENCE_VIEWS_LABEL} current={view} params={params} />
      {view === "overview" ? (
        <CapabilityReadinessTable declaration={loaded.declaration} profile={profile} />
      ) : (
        <>
          <CapabilityReadinessAnalysis declaration={loaded.declaration} profile={profile} />
          {analytics === undefined || params.get("assessment") === null ? null : (
            <SelectedAssessmentCoverage
              siteId={siteId}
              analytics={analytics}
              assessmentId={params.get("assessment") as string}
            />
          )}
        </>
      )}
      <p data-evidence-window={evidence.window.basis}>
        {evidence.window.start === null || evidence.window.end === null ? (
          <>
            <strong>Selected window:</strong> all accepted records; no window
            bounds are recorded yet.
          </>
        ) : (
          <>
            <strong>Selected window:</strong>{" "}
            {readablePeriod(evidence.window.start, evidence.window.end)}, from{" "}
            {windowBasis(evidence.window.basis)}. The records below are for
            this window only.
          </>
        )}
      </p>

      {empty ? (
        <Panel heading="No accepted records" headingId="site-evidence-empty-heading">
          <p data-evidence-empty>
            No records have been received and accepted for this site, so there
            is no source status or recorded input to show. Records appear here
            once a delivery from a source has been accepted.
          </p>
        </Panel>
      ) : view === "overview" ? (
        <SourceSummary
          evidence={evidence}
          onInspect={(source) => inspect("source", source)}
        />
      ) : (
        <SourceHealth
          evidence={evidence}
          highlighted={batch}
          onInspect={(source) => inspect("source", source)}
        />
      )}

      {evidence.coverage.length === 0 ? null : view === "overview" ? (
        <CoverageSummary evidence={evidence} />
      ) : (
        <SignalCoverage
          evidence={evidence}
          onInspect={(row) => inspect("signal", `${row.device_id}/${row.signal_id}`)}
        />
      )}

      <RecordInspector
        siteId={siteId}
        client={client}
        window={evidence.window}
      />

      {view === "analysis" && hasBasis ? <Basis evidence={evidence} /> : null}

      {evidence.rejection_count === 0 && empty ? null : view === "analysis" ? (
        <Rejections count={evidence.rejection_count} rejections={rejections} />
      ) : (
        <p data-evidence-rejection-count={evidence.rejection_count}>
          {evidence.rejection_count === 0
            ? "No record has been rejected for this site."
            : `${evidence.rejection_count} ${evidence.rejection_count === 1 ? "record was" : "records were"} rejected; the reasons are on the Analysis view.`}
        </p>
      )}
    </div>
  );
}

export const EVIDENCE_VIEWS_LABEL = "Evidence views";

/** Overview: each source in ordinary words, with its records one click away. */
function SourceSummary({
  evidence,
  onInspect,
}: {
  evidence: EvidenceOverview;
  onInspect: (source: string) => void;
}) {
  return (
    <Panel heading="Where the records come from" headingId="site-evidence-sources-heading">
      <ul className="cell-list" data-evidence-source-summary>
        {evidence.sources.map((source) => (
          <li key={source.source_id} data-evidence-source={source.source_id} {...sourceReferences(source.source_id)}>
            <span data-evidence-provenance={source.source_mode}>
              {`${provenance(source.source_mode)}: `}
            </span>
            {`${source.accepted_in_window} records accepted in this window (${source.accepted_total} in all), ${source.rejected} rejected; latest received ${source.last_received_at === null ? "never" : readableTime(source.last_received_at)}. Source reference ${source.source_id}. `}
            <button
              type="button"
              className="link-button"
              onClick={() => onInspect(source.source_id)}
              aria-label={`Inspect records from ${source.source_id}`}
            >
              Inspect records
            </button>
          </li>
        ))}
      </ul>
    </Panel>
  );
}

/** Overview: how many inputs have records in the selected window. */
function CoverageSummary({ evidence }: { evidence: EvidenceOverview }) {
  const missing = evidence.coverage.filter((row) => row.status === "NOT_REPORTED");
  return (
    <p data-evidence-coverage-summary={missing.length}>
      {`${evidence.coverage.length - missing.length} of ${evidence.coverage.length} recorded inputs have records in this window.`}
      {missing.length === 0
        ? ""
        : ` No records in this window for: ${missing.map((row) => `${row.device_id} / ${row.signal_id}`).join(", ")}.`}
      {" Each input's coverage is on the Analysis view."}
    </p>
  );
}

function SourceHealth({
  evidence,
  highlighted,
  onInspect,
}: {
  evidence: EvidenceOverview;
  highlighted: string | null;
  onInspect: (source: string) => void;
}) {
  return (
    <Panel heading="Source status" headingId="site-evidence-sources-heading" flush>
      <p className="note" data-evidence-source-statement>
        {evidence.source_health_statement}
      </p>
      <DataTable labelledBy="site-evidence-sources-heading">
        <thead>
          <tr>
            <th scope="col">Source and gateway</th>
            <th scope="col">Provenance</th>
            <th scope="col">Accepted in window</th>
            <th scope="col">Accepted in all</th>
            <th scope="col">Rejected</th>
            <th scope="col">Conflicts</th>
            <th scope="col">Duplicates</th>
            <th scope="col">Last source time</th>
            <th scope="col">Last sent</th>
            <th scope="col">Last received</th>
            <th scope="col">Deliveries</th>
            <th scope="col">Inspect</th>
          </tr>
        </thead>
        <tbody>
          {evidence.sources.map((source) => (
            <SourceRow
              key={source.source_id}
              source={source}
              highlighted={highlighted}
              onInspect={onInspect}
            />
          ))}
        </tbody>
      </DataTable>
    </Panel>
  );
}

function SourceRow({
  source,
  highlighted,
  onInspect,
}: {
  source: EvidenceSourceHealth;
  highlighted: string | null;
  onInspect: (source: string) => void;
}) {
  return (
    <tr data-evidence-source={source.source_id} {...sourceReferences(`${source.source_id} / ${source.gateway_id}`, source.source_id)}>
      <th scope="row">{`${source.source_id} / ${source.gateway_id}`}</th>
      <td data-evidence-provenance={source.source_mode}>
        {provenance(source.source_mode)}
      </td>
      <td>{String(source.accepted_in_window)}</td>
      <td>{String(source.accepted_total)}</td>
      <td>{String(source.rejected)}</td>
      <td>{String(source.conflicts)}</td>
      <td>{String(source.duplicates)}</td>
      <td>{instant(source.last_source_time)}</td>
      <td>{instant(source.last_published_at)}</td>
      <td>{instant(source.last_received_at)}</td>
      <td>
        <ul className="cell-list">
          {source.batches.map((item) => (
            <li
              key={item.batch_id}
              data-evidence-batch={item.batch_id}
              {...sourceReferences(item.batch_id)}
              data-evidence-batch-highlighted={
                item.batch_id === highlighted ? "yes" : undefined
              }
            >
              {item.batch_id === highlighted ? (
                <strong>{`${item.batch_id} (the release you opened)`}</strong>
              ) : (
                item.batch_id
              )}
              {`: ${item.status}, ${item.processed} of ${item.total} processed`}
            </li>
          ))}
        </ul>
      </td>
      <td>
        <button
          type="button"
          onClick={() => onInspect(source.source_id)}
          aria-label={`Inspect records from ${source.source_id}`}
        >
          Inspect records
        </button>
      </td>
    </tr>
  );
}

function SignalCoverage({
  evidence,
  onInspect,
}: {
  evidence: EvidenceOverview;
  onInspect: (row: EvidenceCoverage) => void;
}) {
  return (
    <Panel heading="Input coverage in this window" headingId="site-evidence-coverage-heading" flush>
      <p className="note">
        {evidence.coverage_statement} {evidence.overlap_statement}
      </p>
      <DataTable labelledBy="site-evidence-coverage-heading">
        <thead>
          <tr>
            <th scope="col">Device and signal</th>
            <th scope="col">Unit</th>
            <th scope="col">Records</th>
            <th scope="col">Good</th>
            <th scope="col">Unavailable</th>
            <th scope="col">Overlapping</th>
            <th scope="col">First source time</th>
            <th scope="col">Last source time</th>
            <th scope="col">Longest silence</th>
            <th scope="col">Needed by</th>
            <th scope="col">Inspect</th>
          </tr>
        </thead>
        <tbody>
          {evidence.coverage.map((row) => {
            const name = `${row.device_id} / ${row.signal_id}`;
            const neededBy =
              row.needed_by.length === 0 ? "Not used yet" : row.needed_by.join(", ");
            return (
              <tr
                key={`${row.device_id}/${row.signal_id}`}
                data-evidence-coverage={`${row.device_id}/${row.signal_id}`}
                data-coverage-status={row.status}
                {...sourceReferences(name)}
              >
                <th scope="row">{name}</th>
                <td>{row.unit ?? "none declared"}</td>
                {row.status === "NOT_REPORTED" ? (
                  <td colSpan={7} data-coverage-gap>
                    <strong>Coverage gap:</strong> no accepted record for this
                    signal in the window, so it has no value here.
                  </td>
                ) : (
                  <>
                    <td>{String(row.records)}</td>
                    <td>{String(row.good)}</td>
                    <td>{String(row.unavailable)}</td>
                    <td>{String(row.overlapping)}</td>
                    <td>{instant(row.first_source_time)}</td>
                    <td>{instant(row.last_source_time)}</td>
                    <td>
                      {row.longest_silence_seconds === null
                        ? "none"
                        : `${row.longest_silence_seconds} seconds`}
                    </td>
                  </>
                )}
                <td>{neededBy}</td>
                <td>
                  {row.status === "NOT_REPORTED" ? (
                    "None to inspect"
                  ) : (
                    <button
                      type="button"
                      onClick={() => onInspect(row)}
                      aria-label={`Inspect records for ${name}`}
                    >
                      Inspect records
                    </button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </DataTable>
    </Panel>
  );
}

function Basis({ evidence }: { evidence: EvidenceOverview }) {
  const current = evidence.basis.current_foundation;
  return (
    <Panel
      heading="Record interpretation and equipment details"
      headingId="site-evidence-basis-heading"
    >
      <p className="note">
        Accepted records keep the equipment details and record interpretation
        they were accepted under. A later Foundation edit does not reinterpret
        them.
      </p>
      <FactList>
        <Fact term="Record interpretation used">
          <ul className="cell-list" data-evidence-mappings>
            {evidence.basis.mappings.map((mapping) => (
              <li key={`${mapping.mapping_set_id}-${mapping.mapping_version}`} {...sourceReferences(`${mapping.mapping_set_id} v${mapping.mapping_version}`)}>
                {`${mapping.mapping_set_id} v${mapping.mapping_version}`}
              </li>
            ))}
          </ul>
        </Fact>
        <Fact term="Equipment details used">
          <ul className="cell-list" data-evidence-configurations>
            {evidence.basis.configurations.map((configuration) => (
              <li
                key={`${configuration.foundation_version}-${configuration.foundation_valid_from}`}
              >
                {`Foundation v${configuration.foundation_version}, valid from ${configuration.foundation_valid_from}, ${configuration.signal_count} signals`}
              </li>
            ))}
          </ul>
        </Fact>
        <Fact term="Current Foundation">
          <span data-evidence-current-foundation>
            {current === null
              ? "none recorded"
              : `v${current.foundation_version}, valid from ${current.foundation_valid_from}`}
          </span>
        </Fact>
      </FactList>
    </Panel>
  );
}

function Rejections({
  count,
  rejections,
}: {
  count: number;
  rejections: EvidenceRejections | null;
}) {
  return (
    <Panel heading="Rejected records" headingId="site-evidence-rejections-heading">
      <p data-evidence-rejection-count={count}>
        {count === 0
          ? "No record has been rejected for this site."
          : `${count} ${count === 1 ? "record was" : "records were"} rejected and never accepted.`}
      </p>
      {count === 0 ? null : rejections === null ? (
        <p>The rejection list could not be read.</p>
      ) : (
        <ul className="cell-list" data-evidence-rejections>
          {rejections.rejections.map((item, index) => (
            <li
              key={`${item.batch_id}-${item.index ?? index}-${item.kind}`}
              data-evidence-rejection={item.kind}
            >
              {item.reason ?? REJECTION_UNAVAILABLE}{" "}
              Delivery reference{" "}
              <span data-vocabulary-exempt="source-reference">{item.batch_id}</span>.
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

function RecordInspector({
  siteId,
  client,
  window,
}: {
  siteId: string;
  client: SiteEvidenceClient;
  window: EvidenceOverview["window"];
}) {
  const [params, setParams] = useSearchParams();
  const signal = params.get("signal");
  const source = params.get("source");
  const record = params.get("record");
  const [list, setList] = useState<EvidenceRead<EvidenceRecordList> | null>(null);
  const [detail, setDetail] = useState<EvidenceRead<EvidenceRecordDetail> | null>(
    null,
  );
  const slash = signal === null ? -1 : signal.indexOf("/");
  const device = signal === null || slash < 0 ? null : signal.slice(0, slash);
  const signalId = signal === null || slash < 0 ? null : signal.slice(slash + 1);
  const open = (device !== null && signalId !== null) || source !== null;

  useEffect(() => {
    if (!open) {
      setList(null);
      return undefined;
    }
    let active = true;
    setList(null);
    void client
      .listRecords(siteId, {
        device: source === null ? device : null,
        signal: source === null ? signalId : null,
        source,
        from: window.start,
        to: window.end,
        limit: INSPECTOR_RECORD_LIMIT,
      })
      .then((loaded) => {
        if (active) {
          setList(loaded);
        }
      });
    return () => {
      active = false;
    };
  }, [client, siteId, open, device, signalId, source, window.start, window.end]);

  useEffect(() => {
    if (record === null) {
      setDetail(null);
      return undefined;
    }
    let active = true;
    setDetail(null);
    void client.getRecord(siteId, record).then((loaded) => {
      if (active) {
        setDetail(loaded);
      }
    });
    return () => {
      active = false;
    };
  }, [client, siteId, record]);

  if (!open) {
    return null;
  }

  const close = () => {
    const next = new URLSearchParams(params);
    next.delete("signal");
    next.delete("source");
    next.delete("record");
    setParams(next);
  };
  const select = (messageId: string) => {
    const next = new URLSearchParams(params);
    next.set("record", messageId);
    setParams(next);
  };
  const subject =
    source !== null ? `source ${source}` : `${device ?? ""} / ${signalId ?? ""}`;

  return (
    <div id={EVIDENCE_INSPECTOR_ID} data-evidence-inspector={subject}>
      <Panel heading={`Records: ${subject}`} headingId="site-evidence-inspector-heading">
        <p>
          <button type="button" onClick={close}>
            Close records
          </button>
        </p>
        {list === null ? (
          <p>Loading the inspected records.</p>
        ) : list.status !== "loaded" ? (
          <p data-inspector-unavailable>
            {list.status === "unavailable" && list.message !== null
              ? list.message
              : "The records could not be read."}
          </p>
        ) : (
          <>
            <p>
              {`${list.value.records.length} of ${list.value.total} accepted records, newest source time first.`}
            </p>
            <DataTable labelledBy="site-evidence-inspector-heading">
              <thead>
                <tr>
                  <th scope="col">Source time</th>
                  <th scope="col">Device and signal</th>
                  <th scope="col">Value</th>
                  <th scope="col">Quality</th>
                  <th scope="col">Source</th>
                  <th scope="col">Detail</th>
                </tr>
              </thead>
              <tbody>
                {list.value.records.map((item) => (
                  <tr
                    key={item.message_id}
                    data-evidence-record={item.message_id}
                    aria-selected={item.message_id === record}
                  >
                    <th scope="row">{item.source_time}</th>
                    <td>{`${item.device_id} / ${item.signal_id}`}</td>
                    <td>
                      {item.value === null
                        ? "no value"
                        : `${item.value}${item.unit === null ? "" : ` ${item.unit}`}`}
                    </td>
                    <td>
                      {item.quality}
                      {item.overlapping ? " (overlapping)" : ""}
                    </td>
                    <td {...sourceReferences(item.source_id)}>{item.source_id}</td>
                    <td>
                      <button
                        type="button"
                        onClick={() => select(item.message_id)}
                        aria-label={`Show record ${item.message_id}`}
                        {...sourceReferences(item.message_id)}
                      >
                        Show record
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          </>
        )}
        {record === null ? null : <RecordDetail detail={detail} />}
      </Panel>
    </div>
  );
}

export function RecordDetail({
  detail,
}: {
  detail: EvidenceRead<EvidenceRecordDetail> | null;
}) {
  if (detail === null) {
    return <p>Loading the inspected record.</p>;
  }
  if (detail.status !== "loaded") {
    return (
      <p data-record-unavailable>
        {detail.status === "not_found"
          ? "No accepted record has that message ID."
          : (detail.message ?? "The record could not be read.")}
      </p>
    );
  }
  const item = detail.value;
  const valueText = (value: { value: string | null; unit: string | null }) =>
    value.value === null
      ? "no value"
      : `${value.value}${value.unit === null ? "" : ` ${value.unit}`}`;
  return (
    <section
      aria-labelledby="site-evidence-record-heading"
      data-evidence-record-detail={item.message_id}
    >
      <h3 id="site-evidence-record-heading" className="identity-heading">
        Record <span data-vocabulary-exempt="source-reference">{item.message_id}</span>
      </h3>
      <FactList>
        <Fact term="Source, device and signal">
          <span data-vocabulary-exempt="source-reference">
            {`${item.source_id} / ${item.device_id} / ${item.signal_id}`}
          </span>
        </Fact>
        <Fact term="Record interpretation">
          <span data-vocabulary-exempt="source-reference">
            {`${item.mapping.mapping_set_id} v${item.mapping.mapping_version}`}
          </span>
        </Fact>
        <Fact term="Equipment details used">
          {`Site ${item.site_id}, Foundation v${item.configuration.foundation_version}, valid from ${item.configuration.foundation_valid_from}`}
        </Fact>
        <Fact term="Provenance">{provenance(item.source_mode)}</Fact>
        <Fact term="Quality">
          {item.unavailable_reason === null
            ? item.quality
            : `${item.quality}: ${item.unavailable_reason}`}
        </Fact>
        <Fact term="Original value">{valueText(item.original)}</Fact>
        <Fact term="Value as interpreted">
          {valueText(item.normalized)}. {item.normalization_statement}
        </Fact>
        <Fact term="Source time">
          <span data-record-time="source">{item.source_time}</span>
        </Fact>
        <Fact term="Sent">
          <span data-record-time="published">{item.published_at}</span>
        </Fact>
        <Fact term="Received">
          <span data-record-time="received">{item.received_at}</span>
        </Fact>
        <Fact term="Delivery">
          <span data-vocabulary-exempt="source-reference">{item.batch_id}</span>
        </Fact>
        {item.overlapping_with.length === 0 ? null : (
          <Fact term="Overlapping records">
            {item.overlapping_with.join(", ")}
          </Fact>
        )}
        {item.conflicts.length === 0 ? null : (
          <Fact term="Conflicts">
            <ul className="cell-list">
              {item.conflicts.map((conflict) => (
                <li key={`${conflict.batch_id}-${conflict.conflicting_digest}`}>
                  {`Delivery ${conflict.batch_id} sent different content for this record (${conflict.conflicting_digest}) at ${conflict.received_at}.`}
                </li>
              ))}
            </ul>
          </Fact>
        )}
      </FactList>
    </section>
  );
}

/**
 * One clearly selected assessed period's record coverage (T028 presentation
 * checkpoint 2a), read from the existing dispatch assessment and labelled with
 * its scope. It is kept apart from the site-wide record check above: readiness
 * never becomes a time-coverage gauge.
 */
function SelectedAssessmentCoverage({
  siteId,
  analytics,
  assessmentId,
}: {
  siteId: string;
  analytics: SiteAnalyticsClient;
  assessmentId: string;
}) {
  const [result, setResult] = useState<EvidenceRead<DispatchAssessments> | null>(null);
  useEffect(() => {
    let active = true;
    setResult(null);
    void analytics.getDispatch(siteId).then((value) => {
      if (active) {
        setResult(value);
      }
    });
    return () => {
      active = false;
    };
  }, [analytics, siteId]);
  const row =
    result?.status === "loaded"
      ? (result.value.assessments.find((r) => r.assessment_id === assessmentId) ?? null)
      : null;
  return (
    <Panel heading="Record coverage for one assessed period" headingId="site-evidence-assessment-coverage-heading">
      <div data-evidence-assessment-coverage={assessmentId}>
        {result === null ? (
          <p>Loading the selected assessed period.</p>
        ) : row === null ? (
          <p data-evidence-assessment-missing>
            The selected assessed period is not among the current results: it may
            have been withdrawn or replaced. No other period is shown in its place.
          </p>
        ) : (
          <>
            <p data-evidence-assessment-scope>
              {`Only the assessed period ${readablePeriod(row.interval.first_running_observed, row.interval.last_running_observed)} (${row.reading?.outcome ?? OUTCOME_WORDS[row.claim_level] ?? "Assessed"}), not the whole site. The site-wide record check above is separate.`}
            </p>
            <CoverageByInput
              inputs={row.assessment.coverage.inputs}
              unobserved={row.assessment.coverage.unobserved_generator_state}
              words={INPUT_WORDS}
            />
          </>
        )}
      </div>
    </Panel>
  );
}
