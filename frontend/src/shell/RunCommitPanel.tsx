import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Fact, FactList, Panel } from "../ui";
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

  if (commit === "NOT_COMMITTED") {
    const eligible = stage !== null && stage.status === "loaded" && stage.stage.release_eligible;
    const blockers =
      stage !== null && stage.status === "loaded" ? stage.stage.release_blockers : [];
    return (
      <>
        <p data-commit-state="NOT_COMMITTED">
          {eligible
            ? "Not committed. Commit seals this draft's stage as an immutable artifact and releases it through ingestion; what ingestion accepts is reported here separately."
            : "Not committed. Commit is available only when the stage is eligible for release, and this stage is not."}
        </p>
        {eligible || blockers.length === 0 ? null : (
          <ul className="cell-list" data-commit-blockers>
            {blockers.map((blocker) => (
              <li key={blocker.kind} data-commit-blocker={blocker.kind}>
                <strong>{blocker.kind}.</strong> {blocker.statement}
              </li>
            ))}
          </ul>
        )}
        <p>
          <button type="button" disabled={!eligible || pending} onClick={onCommit}>
            Commit and release
          </button>
        </p>
      </>
    );
  }

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
      {release === null || release.status === "IN_PROGRESS" ? (
        <p>
          <button type="button" disabled={pending} onClick={onCommit}>
            Resume release
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
