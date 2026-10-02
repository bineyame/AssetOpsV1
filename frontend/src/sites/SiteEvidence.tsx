/**
 * The body of Site > Evidence at T027: what accepted records exist for this
 * Site, their delivery and quality, their coverage for the selected window and
 * the mapping and configuration they were accepted under (part A of the
 * Evidence recommendation; AC20).
 *
 * It says nothing about capability readiness or claim ceilings: no analytic
 * exists yet, so there is no claim for evidence to qualify. Everything shown
 * is accepted evidence read from ingestion's store, never a stage, a run or a
 * simulator artifact.
 *
 * The record inspector is a drill-down, not the tab body: a source or signal
 * row opens it in place, its state lives in the search params (`signal=` or
 * `source=`, then `record=`), and the Site root and tab never change.
 */

import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { DataTable, Fact, FactList, Panel } from "../ui";
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

/** How many records the inspector lists for one row, newest first. */
export const INSPECTOR_RECORD_LIMIT = 50;

/** The id of the in-page record inspector, for layout evidence and focus. */
export const EVIDENCE_INSPECTOR_ID = "site-evidence-inspector";

type Loaded = {
  overview: EvidenceRead<EvidenceOverview>;
  rejections: EvidenceRead<EvidenceRejections>;
};

export interface SiteEvidenceProps {
  siteId: string;
  client: SiteEvidenceClient;
}

function provenance(mode: string): string {
  if (mode === "SIMULATED") {
    return "Simulated source";
  }
  if (mode === "LIVE") {
    return "Live source";
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

export function SiteEvidence({ siteId, client }: SiteEvidenceProps) {
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
    ]).then(([overview, rejections]) => {
      if (active) {
        setLoaded({ overview, rejections });
      }
    });
    return () => {
      active = false;
    };
  }, [client, siteId, from, to]);

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
    <div className="site-evidence" data-evidence-state={empty ? "empty" : "populated"}>
      <p data-evidence-window={evidence.window.basis}>
        {evidence.window.start === null || evidence.window.end === null ? (
          <>
            <strong>Window:</strong> all accepted records; no window bounds
            are recorded yet.
          </>
        ) : (
          <>
            <strong>Window:</strong>{" "}
            {`${evidence.window.start} to ${evidence.window.end}`}, from{" "}
            {windowBasis(evidence.window.basis)}.
          </>
        )}
      </p>

      {empty ? (
        <Panel heading="No accepted evidence" headingId="site-evidence-empty-heading">
          <p data-evidence-empty>
            No source batch has been accepted for this site, so there is no
            source health or recorded signal to show. Evidence appears here
            once a source batch has been ingested.
          </p>
        </Panel>
      ) : (
        <SourceHealth
          evidence={evidence}
          highlighted={batch}
          onInspect={(source) => inspect("source", source)}
        />
      )}

      {evidence.coverage.length === 0 ? null : (
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

      {hasBasis ? <Basis evidence={evidence} /> : null}

      {evidence.rejection_count === 0 && empty ? null : (
        <Rejections count={evidence.rejection_count} rejections={rejections} />
      )}
    </div>
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
    <Panel heading="Source health" headingId="site-evidence-sources-heading" flush>
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
            <th scope="col">Last published</th>
            <th scope="col">Last received</th>
            <th scope="col">Batches</th>
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
    <tr data-evidence-source={source.source_id}>
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
    <Panel heading="Signal coverage" headingId="site-evidence-coverage-heading" flush>
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
              row.needed_by.length === 0 ? "No metric yet" : row.needed_by.join(", ");
            return (
              <tr
                key={`${row.device_id}/${row.signal_id}`}
                data-evidence-coverage={`${row.device_id}/${row.signal_id}`}
                data-coverage-status={row.status}
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
      heading="Configuration and mapping basis"
      headingId="site-evidence-basis-heading"
    >
      <p className="note">
        Accepted records keep the configuration and mapping they were accepted
        under. A later Foundation edit does not reinterpret them.
      </p>
      <FactList>
        <Fact term="Mappings accepted under">
          <ul className="cell-list" data-evidence-mappings>
            {evidence.basis.mappings.map((mapping) => (
              <li key={`${mapping.mapping_set_id}-${mapping.mapping_version}`}>
                {`${mapping.mapping_set_id} v${mapping.mapping_version}`}
              </li>
            ))}
          </ul>
        </Fact>
        <Fact term="Configurations accepted under">
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
    <Panel heading="Rejections" headingId="site-evidence-rejections-heading">
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
              <strong>{item.kind}</strong>
              {item.field === null ? "" : ` (${item.field})`}: {item.detail}{" "}
              {`Batch ${item.batch_id}.`}
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
                    <td>{item.source_id}</td>
                    <td>
                      <button
                        type="button"
                        onClick={() => select(item.message_id)}
                        aria-label={`Show record ${item.message_id}`}
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

function RecordDetail({
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
      <h3 id="site-evidence-record-heading">{`Record ${item.message_id}`}</h3>
      <FactList>
        <Fact term="Source, device and signal">
          {`${item.source_id} / ${item.device_id} / ${item.signal_id}`}
        </Fact>
        <Fact term="Mapping">
          {`${item.mapping.mapping_set_id} v${item.mapping.mapping_version}`}
        </Fact>
        <Fact term="Configuration basis">
          {`Site ${item.site_id}, Foundation v${item.configuration.foundation_version}, valid from ${item.configuration.foundation_valid_from}`}
        </Fact>
        <Fact term="Provenance">{provenance(item.source_mode)}</Fact>
        <Fact term="Quality">
          {item.unavailable_reason === null
            ? item.quality
            : `${item.quality}: ${item.unavailable_reason}`}
        </Fact>
        <Fact term="Original value">{valueText(item.original)}</Fact>
        <Fact term="Normalized value">
          {valueText(item.normalized)}. {item.normalization_statement}
        </Fact>
        <Fact term="Source time">
          <span data-record-time="source">{item.source_time}</span>
        </Fact>
        <Fact term="Published">
          <span data-record-time="published">{item.published_at}</span>
        </Fact>
        <Fact term="Received">
          <span data-record-time="received">{item.received_at}</span>
        </Fact>
        <Fact term="Batch">{item.batch_id}</Fact>
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
                  {`Batch ${conflict.batch_id} sent different content for this message ID (${conflict.conflicting_digest}) at ${conflict.received_at}.`}
                </li>
              ))}
            </ul>
          </Fact>
        )}
      </FactList>
    </section>
  );
}
