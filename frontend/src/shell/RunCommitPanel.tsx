import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Fact, FactList, Panel } from "../ui";
import { RegisteredDeliveryView } from "./RegisteredDeliveryView";
import type {
  ReleaseBatch,
  RunCommitResult,
  RunSetupClient,
  RunStageResult,
} from "./runSetupClient";

/** The heading id the Commit panel is labelled by, for layout evidence. */
export const RUN_COMMIT_HEADING_ID = "run-commit-heading";

export interface RunCommitPanelProps {
  runId: string;
  runSetup: RunSetupClient;
  stage: RunStageResult | null;
}

/**
 * Commit and release for one Draft (T027 AC18), on the Lab run screen.
 *
 * Commit and release are two facts, never one: Commit seals the eligible stage
 * as an immutable artifact; release is what ingestion did with it, read from
 * ingestion. The release fact never says every record was accepted unless
 * ingestion's own accepted count equals the total, and an interrupted release
 * says how far it got and offers to resume rather than implying completion.
 *
 * Reload reads the persisted Commit, so a refreshed screen shows the same
 * outcome rather than a fresh Commit button.
 */
export function RunCommitPanel({ runId, runSetup, stage }: RunCommitPanelProps) {
  const [read, setRead] = useState<RunCommitResult | null>(null);
  const [refusal, setRefusal] = useState<RunCommitResult | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    let active = true;
    setRead(null);
    void runSetup.getCommit(runId).then((loaded) => {
      if (active) {
        setRead(loaded);
      }
    });
    return () => {
      active = false;
    };
  }, [runSetup, runId]);

  const commit = useCallback(async () => {
    setPending(true);
    const answer = await runSetup.commit(runId);
    if (answer.status === "loaded") {
      setRead(answer);
      setRefusal(null);
    } else {
      setRefusal(answer);
    }
    setPending(false);
  }, [runSetup, runId]);

  return (
    <Panel heading="Commit and release" headingId={RUN_COMMIT_HEADING_ID}>
      <div data-run-commit>
        <CommitBody
          read={read}
          stage={stage}
          pending={pending}
          onCommit={() => void commit()}
        />
        {refusal === null ? null : <Refusal answer={refusal} />}
      </div>
    </Panel>
  );
}

function CommitBody({
  read,
  stage,
  pending,
  onCommit,
}: {
  read: RunCommitResult | null;
  stage: RunStageResult | null;
  pending: boolean;
  onCommit: () => void;
}) {
  if (read === null) {
    return <p>Loading the commit status.</p>;
  }
  if (read.status === "not_found") {
    return <p>No Commit surface answered for this run identity.</p>;
  }
  if (read.status === "unavailable" || read.status === "refused") {
    return (
      <p data-commit-unavailable>
        {read.message ??
          "The Commit status could not be read, so nothing is known about whether this draft was committed."}
      </p>
    );
  }

  const { commit, release, open_in_assetops, release_error } = read.commit;

  if (read.commit.registered_release !== undefined) {
    // S2-02 phase 3b: a registered run's Commit asks its gateway to release
    // the existing sealed batches; the status is the gateway ledger's delivery
    // plus the Lab publication schedule, never Stage STAGED alone.
    return (
      <RegisteredDeliveryView
        view={read.commit.registered_release}
        statement={read.commit.statement}
        pending={pending}
        onRelease={onCommit}
      />
    );
  }
  if (commit === "RELEASED_TO_GATEWAY") {
    return (
      <p data-commit-unavailable>
        The gateway release answer carried no delivery status, so nothing is known about its progress.
      </p>
    );
  }

  if (commit === "NOT_COMMITTED") {
    // S2-01a: the configuration this Draft froze can forbid release whatever
    // the stage says - every run on a registered Site, and a legacy Draft
    // whose Site has since been registered. The server refuses either way.
    const basisBlock = commitBasisBlock(stage);
    const eligible =
      basisBlock === null &&
      stage !== null &&
      stage.status === "loaded" &&
      stage.stage.release_eligible;
    const blockers =
      stage !== null && stage.status === "loaded" ? stage.stage.release_blockers : [];
    return (
      <>
        <p
          id="run-commit-reason"
          data-commit-state="NOT_COMMITTED"
          data-commit-basis-block={basisBlock === null ? undefined : ""}
        >
          {basisBlock !== null
            ? basisBlock
            : eligible
            ? "Not committed. Commit seals this draft's stage as an immutable artifact and releases it through ingestion; what ingestion accepts is reported here separately."
            : "Not committed. Commit is available only when the stage is eligible for release, and this stage is not."}
        </p>
        {eligible || basisBlock !== null || blockers.length === 0 ? null : (
          <ul className="cell-list" data-commit-blockers>
            {blockers.map((blocker) => (
              <li key={blocker.kind} data-commit-blocker={blocker.kind}>
                <strong>{blocker.kind}.</strong> {blocker.statement}
              </li>
            ))}
          </ul>
        )}
        <p>
          <button
            type="button"
            disabled={!eligible || pending}
            aria-describedby={eligible ? undefined : "run-commit-reason"}
            onClick={onCommit}
          >
            Commit and release
          </button>
        </p>
      </>
    );
  }

  // S2-01a carry F1: a legacy artifact committed before its Site was
  // registered is read-only history now, and the server refuses to resume or
  // retry its release; the same frozen basis that blocks Commit blocks that.
  const releaseBlock = releaseBasisBlock(stage);
  return (
    <>
      <FactList>
        <Fact term="Commit">
          <span data-commit-state="COMMITTED">
            {`Sealed ${commit.artifact_id}: ${commit.envelope_count} envelopes, sealed at ${commit.sealed_at}, integrity digest ${shortDigest(commit.integrity_digest)}.`}
          </span>
        </Fact>
        <Fact term="Release">
          <ReleaseFact release={release} />
        </Fact>
      </FactList>
      {release_error === null ? null : (
        <p data-commit-release-error>
          <strong>Release error.</strong> {release_error}
        </p>
      )}
      {releaseBlock !== null &&
      (release === null || release.status === "IN_PROGRESS" || release.status === "REFUSED") ? (
        <p data-commit-basis-block data-release-basis-block>
          {releaseBlock}
        </p>
      ) : release === null || release.status === "IN_PROGRESS" || release.status === "REFUSED" ? (
        <p>
          {/* The backend accepts a retry after a refusal (a refused batch wrote
              no records), so the same POST is offered; the refusal stays shown
              above it. T027 fix round N3. */}
          <button type="button" disabled={pending} onClick={onCommit}>
            {release !== null && release.status === "REFUSED" ? "Retry release" : "Resume release"}
          </button>
        </p>
      ) : null}
      {open_in_assetops === null ? null : (
        <p>
          <Link to={open_in_assetops.href} data-commit-open-in-assetops>
            Open in AssetOps
          </Link>
        </p>
      )}
    </>
  );
}

function ReleaseFact({ release }: { release: ReleaseBatch | null }) {
  if (release === null) {
    return (
      <span data-release-status="NONE">
        No release is recorded for this Commit. Nothing has reached ingestion
        from it yet.
      </span>
    );
  }
  const counts = `${release.accepted} accepted, ${release.duplicates} duplicates, ${release.rejected} rejected, ${release.conflicts} conflicts`;
  let summary: string;
  if (release.status === "IN_PROGRESS") {
    summary = `Release interrupted after ${release.processed} of ${release.total}. So far: ${counts}.`;
  } else if (release.status === "REFUSED") {
    summary =
      release.refusal === null
        ? "Ingestion refused this release; no record was accepted from it."
        : `Ingestion refused this release (${release.refusal.kind}): ${release.refusal.detail}`;
  } else if (release.accepted === release.total) {
    summary = `Ingestion accepted all ${release.total} records: ${counts}.`;
  } else {
    summary = `Ingestion accepted ${release.accepted} of ${release.total} records: ${counts}.`;
  }
  return (
    <span
      data-release-status={release.status}
      data-release-processed={release.processed}
      data-release-total={release.total}
    >
      {`${release.status}, ${release.processed} of ${release.total} processed. `}
      {summary}
    </span>
  );
}

function Refusal({ answer }: { answer: RunCommitResult }) {
  if (answer.status === "loaded") {
    return null;
  }
  const message =
    answer.status === "not_found"
      ? "No run with this identity answered the Commit."
      : (answer.message ??
        "The Commit did not complete, so nothing is known about whether it was sealed.");
  return (
    <div data-commit-refusal={answer.status === "refused" ? (answer.code ?? "") : answer.status}>
      <p>
        <strong>Commit not completed.</strong> {message}
      </p>
      {answer.status === "refused" && answer.releaseBlockers.length > 0 ? (
        <ul className="cell-list">
          {answer.releaseBlockers.map((blocker) => (
            <li key={blocker.kind}>
              <strong>{blocker.kind}.</strong> {blocker.statement}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function shortDigest(digest: string): string {
  const bare = digest.includes(":") ? digest.slice(digest.indexOf(":") + 1) : digest;
  return bare.length <= 12 ? digest : `${digest.slice(0, digest.length - bare.length)}${bare.slice(0, 12)}…`;
}

/**
 * Why the frozen configuration forbids Commit, or null when it does not.
 *
 * Read from the Stage read's `frozen_basis`; a backend that does not report
 * one leaves the stage's own eligibility to decide, as before.
 */
export function commitBasisBlock(stage: RunStageResult | null): string | null {
  if (stage === null || (stage.status !== "loaded" && stage.status !== "gateway")) {
    return null;
  }
  if (stage.status === "gateway") {
    // S2-01b: only a registered run's Stage is the gateway ledger, and the
    // server refuses Commit for every one of them whatever the basis says.
    return (
      "Not committed. This run was set up from a registered Site configuration, " +
      "and committing such runs is not available yet: its reports wait in the " +
      "gateway's local outbox, and accepted Site evidence for registered Sites " +
      "is not delivered in this build."
    );
  }
  const basis = stage.frozenBasis;
  if (basis === undefined || basis?.can_release) {
    return null;
  }
  if (basis === null) {
    return (
      "Not committed. The configuration this draft froze could not be read, " +
      "so nothing is offered for release."
    );
  }
  if (basis.configuration_store === "REGISTERED") {
    return (
      "Not committed. This run was set up from a registered Site configuration, " +
      "and committing such runs is not available yet: accepted Site evidence " +
      "for registered Sites is not delivered in this build."
    );
  }
  if (basis.site_imported === null) {
    return (
      "Not committed. Whether this Site has since been registered could not be " +
      "checked, so nothing is offered for release."
    );
  }
  return (
    "Not committed. This draft was set up from the legacy Site file and the " +
    "Site has since been registered, so the draft is read-only history and " +
    "cannot be committed."
  );
}

/**
 * Why the frozen configuration forbids resuming or retrying the release of an
 * already committed artifact, or null when it does not (S2-01a carry F1).
 *
 * The same `frozen_basis` that blocks Commit decides it: the server refuses
 * release for a registered run and for a legacy artifact whose Site has since
 * been registered, so no Resume or Retry button is offered for either.
 */
export function releaseBasisBlock(stage: RunStageResult | null): string | null {
  // S2-01b carry F2: while the Stage read is pending or failed, or it does not
  // report the frozen basis, whether release is allowed is unknown, and an
  // unknown basis offers no Resume or Retry. The server refusal remains.
  if (stage === null) {
    return (
      "Release is not offered yet. The configuration this draft froze is still " +
      "being read, so the release is not resumed or retried until it is known."
    );
  }
  if (stage.status === "unavailable" || stage.status === "not_found") {
    return (
      "Release is not offered. The configuration this draft froze could not be " +
      "read, so the release is not resumed or retried."
    );
  }
  if (stage.status === "loaded" && stage.frozenBasis === undefined) {
    return (
      "Release is not offered. This build did not report the configuration this " +
      "draft froze, so the release is not resumed or retried."
    );
  }
  if (commitBasisBlock(stage) === null) {
    return null;
  }
  if (stage.status === "gateway") {
    return (
      "Release is not offered. This run was set up from a registered Site " +
      "configuration, and releasing such runs is not available in this build."
    );
  }
  if (stage.status !== "loaded") {
    return null;
  }
  const basis = stage.frozenBasis;
  if (basis === null || basis === undefined) {
    return (
      "Release is not offered. The configuration this draft froze could not be " +
      "read, so the release is not resumed or retried."
    );
  }
  if (basis.configuration_store === "REGISTERED") {
    return (
      "Release is not offered. This run was set up from a registered Site " +
      "configuration, and releasing such runs is not available in this build."
    );
  }
  if (basis.site_imported === null) {
    return (
      "Release is not offered. Whether this Site has since been registered could " +
      "not be checked, so the release is not resumed or retried."
    );
  }
  return (
    "Release is not offered. This artifact was committed from the legacy Site " +
    "file before the Site was registered. The Site is now registered, so this " +
    "artifact is read-only history and its release cannot be resumed or retried."
  );
}
