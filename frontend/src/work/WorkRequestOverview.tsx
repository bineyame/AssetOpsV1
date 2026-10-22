/**
 * W6-01c C2: the work request Overview (v6.9 `wr-overview`, `index.html:968`), read from
 * `GET /api/work/requests/{case_id}?site_id={site_code}` (`global-work-detail-1`). Mock order: breadcrumb, heading
 * with `Open site`, the `Context tabs` row, the date bar, the `wrHeader` mheader, then the `Work done` / `Lifecycle`
 * pair. Copy follows `.agent/W6-01-build-spec.md` section 2 and the "C1-C3 pre-flight rulings" P-C2-1..14, which
 * supersede CL3-5, F5 `wr-overview` and A2Q7 here.
 *
 * MOCK DEVIATION (P-C2-6..8, P-C2-10): mock values are replaced by stored facts or stated gaps: Asset has no diagram
 * link, Warranty is `Warranty not recorded`, a `Latest activity` line carries the real latest record, Lifecycle marks
 * a step only on an exact stored fact (Verified never), and the chart-note states that no outcome evaluator exists.
 */
import { KeyValues, Panel } from "../ui";
import type { GlobalWorkClient, GlobalWorkDetailBody } from "./globalWorkClient";
import { LinkOrText, joined } from "./globalWorkParts";
import { WorkRequestFrame, recordHeads } from "./workRequestShared";

export const NO_MAINTENANCE_ACTIVITY = "No maintenance activity recorded";
export const WARRANTY_NOT_RECORDED = "Warranty not recorded";
export const NO_ASSET_RECORDED = "No asset recorded";
export const NO_LINKED_ACTION = "No linked action recorded";
export const LIFECYCLE_NOTE = "Completed is not Verified. No work-case outcome evaluator is available.";
export const CANCELLED_NOTE = "Cancelled · work stopped";
export const LIFECYCLE_STEPS = ["Finding", "Triage", "Assigned", "Visit", "Completed", "Verified"] as const;

const CASE_KIND_LABEL: Readonly<Record<string, string>> = { MAINTENANCE_REQUEST: "Corrective" };

/** Section 2: a three-line preview and the complete escaped value in a named disclosure. */
function Long({ text, name, hook }: { text: string; name: "narrative" | "activity"; hook: string }) {
  return (
    <>
      <div className="global-work-clamp work-request-prose" data-work-request-clamp={hook}>
        {text}
      </div>
      <details className="global-work-details" data-work-request-full={hook}>
        <summary>{`Full ${name} text`}</summary>
        {text}
      </details>
    </>
  );
}

/** The selected head with the greatest `(recorded_at, id)`, else null (CL3-5). */
function latestActivity(body: GlobalWorkDetailBody): string | null {
  const heads = recordHeads(body.work_detail.records);
  return heads.length > 0 ? heads[heads.length - 1].activity : null;
}

function WorkDone({ body }: { body: GlobalWorkDetailBody }) {
  const activity = latestActivity(body);
  const asset = body.work_asset;
  const actions = body.links.actions;
  return (
    <>
      <Long text={body.work_detail.selected_revision.narrative} name="narrative" hook="narrative" />
      <p className="work-request-latest" data-work-request-latest={activity === null ? "none" : "recorded"}>
        <span className="work-request-latest__label">Latest activity: </span>
        {activity === null ? NO_MAINTENANCE_ACTIVITY : null}
      </p>
      {activity !== null ? <Long text={activity} name="activity" hook="activity" /> : null}
      <KeyValues
        label="Work request facts"
        rows={[
          ["Type", CASE_KIND_LABEL[body.selected.case_kind] ?? body.selected.case_kind, "type"],
          ["Asset", asset === null ? NO_ASSET_RECORDED : `${asset.code} · ${asset.type}`, "asset"],
          ["Warranty", WARRANTY_NOT_RECORDED, "warranty"],
          [
            "Linked action",
            actions.length === 0
              ? NO_LINKED_ACTION
              : joined(
                  actions.map((link, index) => (
                    <LinkOrText key={`${link.label}-${index}`} link={link} data={{ "data-work-request-action": "" }} />
                  )),
                  " · ",
                ),
            "linked_action",
          ],
        ]}
      />
    </>
  );
}

/**
 * P-C2-7: the six mock steps, each `done` only on an exact stored fact. Finding: a pinned Finding; Triage: a COMMENT
 * or ASSIGN event; Assigned: an ASSIGN event; Visit: a selected maintenance record; Completed: the selected state is
 * COMPLETED (so not after REOPEN); Verified: never. CANCELLED adds its note.
 */
export function lifecycleDone(body: GlobalWorkDetailBody): Record<(typeof LIFECYCLE_STEPS)[number], boolean> {
  const kinds = new Set(body.work_detail.events.map((e) => e.kind));
  return {
    Finding: body.work_detail.finding_links.length > 0,
    Triage: kinds.has("COMMENT") || kinds.has("ASSIGN"),
    Assigned: kinds.has("ASSIGN"),
    Visit: recordHeads(body.work_detail.records).length > 0,
    Completed: body.work_detail.case.state === "COMPLETED",
    Verified: false,
  };
}

function Lifecycle({ body }: { body: GlobalWorkDetailBody }) {
  const done = lifecycleDone(body);
  return (
    <>
      <ol className="lifecycle" aria-label="Lifecycle steps" data-work-request-lifecycle>
        {LIFECYCLE_STEPS.map((step) => (
          <li key={step} className={done[step] ? "done" : undefined} data-lifecycle-step={step} data-done={done[step] ? "true" : "false"}>
            {step}
          </li>
        ))}
      </ol>
      {body.work_detail.case.state === "CANCELLED" ? (
        <p className="v69-chart-note" data-work-request-cancelled>
          {CANCELLED_NOTE}
        </p>
      ) : null}
    </>
  );
}

function OverviewPanels({ body }: { body: GlobalWorkDetailBody | null }) {
  // Both panels keep their slots in every state; the chart-note stays inside the Lifecycle body (P-C2-8).
  return (
    <div className="panel-pair" data-work-request-pair>
      <Panel heading="Work done" headingId="work-request-work-done">
        {body !== null ? <WorkDone body={body} /> : null}
      </Panel>
      <Panel heading="Lifecycle" headingId="work-request-lifecycle">
        {body !== null ? <Lifecycle body={body} /> : null}
        <p className="v69-chart-note" data-work-request-chart-note>
          {LIFECYCLE_NOTE}
        </p>
      </Panel>
    </div>
  );
}

export function WorkRequestOverviewFrame({ client }: { client?: GlobalWorkClient }) {
  return (
    <WorkRequestFrame client={client} rootClass="work-request--overview">
      {(body) => <OverviewPanels body={body} />}
    </WorkRequestFrame>
  );
}
