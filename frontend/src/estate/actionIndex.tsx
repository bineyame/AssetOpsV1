/**
 * W3-01 commit 3: the estate Actions root (v6.9 `actions`) read from `GET /api/estate/actions`
 * (`estate-action-index-1`). Copy follows `.agent/W3-01-build-spec.md` "Per-screen panel/copy/layout dry-read",
 * Review closure B4/B9/W9 and Run 6 readings 8-9: owner and due are `Not set`, the title is `Action {code}`, the
 * success criterion is `No success criterion recorded`, and `Verified` appears only for a surviving VERIFIED
 * resolution. No mock ACT number, Incident or Maintenance link is rendered.
 */
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { siteDetailHref } from "../shell/operatorSiteRoutes";
import { DataTable, MetricCard, MetricCards, Notice, PageHeader, Panel } from "../ui";
import {
  createEstateClient,
  type EstateActionRow,
  type EstateActionsBody,
  type EstateClient,
  type EstateResult,
} from "./estateClient";
import {
  EstateDateBar,
  EstateRefusal,
  LimitationNotice,
  PARTIAL_COVERAGE,
  PARTIAL_TOTALS,
  Pager,
  estateHref,
  limitationSentences,
  queryFromParams,
} from "./estateShared";

export const ESTATE_ACTIONS_PATH = "/actions";

export const ACTIONS_NOTICE =
  "Verification needs a frozen plan and later accepted evidence. An Action event alone does not prove an outcome.";
export const NO_VERIFIED_OUTCOME = "No verified outcome in the last 30 days";
export const ACTIONS_LIFECYCLE = "Pending → Applied → Verification window → Verified or withdrawn";

const APPLICATION_WORDS: Readonly<Record<EstateActionRow["application_state"], { text: string; tone: string }>> = {
  PENDING: { text: "Pending", tone: "amber" },
  APPLIED: { text: "Applied", tone: "blue" },
  NONE_AT_CUTOFF: { text: "No action yet", tone: "neutral" },
};

function verified(row: EstateActionRow): boolean {
  return row.resolution_state === "RESOLVED" && row.verification_outcome === "VERIFIED";
}

function count(value: number | null): string {
  return value === null ? "Coverage incomplete" : String(value);
}

function Cards({ body }: { body: EstateActionsBody }) {
  const s = body.summary;
  const complete = body.total_count !== null;
  return (
    <MetricCards label="Actions summary" data={{ "data-estate-cards": "" }}>
      <MetricCard
        label="Open actions"
        value={count(s.open_actions)}
        word={s.open_actions === null}
        tone={s.open_actions === null ? "amber" : undefined}
        note={s.basis_count !== null && s.basis_count > 0 ? "Accepted work" : undefined}
        data={{ "data-estate-card": "open_actions" }}
      />
      <MetricCard
        label="Due / overdue"
        value={s.due_overdue !== null ? String(s.due_overdue) : complete ? "Not set" : "Coverage incomplete"}
        word={s.due_overdue === null}
        tone={complete ? undefined : "amber"}
        note={s.due_overdue === null && complete ? "No due dates recorded" : undefined}
        data={{ "data-estate-card": "due_overdue" }}
      />
      <MetricCard
        label="Verification window"
        value={count(s.verification_window)}
        word={s.verification_window === null}
        tone={s.verification_window === null ? "amber" : undefined}
        data={{ "data-estate-card": "verification_window" }}
      />
      <MetricCard
        label="Verified in 30 days"
        value={count(s.verified_in_30_days)}
        word={s.verified_in_30_days === null}
        tone={s.verified_in_30_days === null ? "amber" : s.verified_in_30_days > 0 ? "green" : undefined}
        note={s.verified_in_30_days === 0 && complete ? NO_VERIFIED_OUTCOME : undefined}
        data={{ "data-estate-card": "verified_in_30_days" }}
      />
    </MetricCards>
  );
}

/**
 * Post-W6 W3-estate Q5 (R293): the row title is the selected stored `action_title` when present, otherwise the
 * `action_code` alone. No Action-kind wording is supplied by the page.
 */
export function actionRowTitle(row: Pick<EstateActionRow, "action_title" | "action_code">): string {
  const title: unknown = row.action_title;
  return typeof title === "string" && title.trim() !== "" ? title : row.action_code;
}

function Row({ row }: { row: EstateActionRow }) {
  const state = APPLICATION_WORDS[row.application_state];
  return (
    <tr data-estate-action={row.action_id}>
      <td>
        <Link className="estate-cell__primary" to={row.links.action} data-estate-action-link>
          {actionRowTitle(row)}
        </Link>
      </td>
      <td>
        <Link className="estate-cell__primary" to={siteDetailHref(row.site_code)} data-estate-site-link>
          {row.site_name}
        </Link>
        <span className="estate-cell__secondary">{row.site_code}</span>
      </td>
      <td>
        {row.links.source ? (
          <Link to={row.links.source} data-estate-source-link>
            Finding {row.source_finding_id.slice(0, 8)}
          </Link>
        ) : (
          "Source unavailable"
        )}
      </td>
      <td>{row.owner ?? "Not set"}</td>
      <td>
        <span className={`estate-chip estate-chip--${state.tone}`} data-estate-application={row.application_state}>
          {state.text}
        </span>
        {verified(row) ? (
          <span className="estate-chip estate-chip--green" data-estate-verified>
            Verified
          </span>
        ) : null}
      </td>
      <td>{row.success_criterion ?? "No success criterion recorded"}</td>
    </tr>
  );
}

function ActionRowsTable({ body }: { body: EstateActionsBody }) {
  return (
    <DataTable labelledBy="estate-actions-heading">
      <colgroup>
        {[24, 13, 17, 11, 13, 22].map((width, index) => (
          <col key={index} style={{ width: `${width}%` }} />
        ))}
      </colgroup>
      <thead>
        <tr>
          {["Action", "Site", "Source", "Owner", "State", "Success criterion"].map((h) => (
            <th key={h} scope="col">
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {body.rows.map((row) => (
          <Row key={row.action_id} row={row} />
        ))}
      </tbody>
    </DataTable>
  );
}

export function EstateActionsPage({ client }: { client?: EstateClient }) {
  const reads = useMemo(() => client ?? createEstateClient(), [client]);
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const query = queryFromParams(params);
  const key = params.toString();
  const [result, setResult] = useState<{ key: string; read: EstateResult<EstateActionsBody> } | null>(null);

  useEffect(() => {
    let live = true;
    void reads.actions(query).then((read) => {
      if (live) setResult({ key, read });
    });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reads, key]);

  const firstPage = estateHref(ESTATE_ACTIONS_PATH, query);
  const read = result?.key === key ? result.read : null;
  const body = read?.status === "loaded" ? read.value : null;
  const next =
    body === null || body.next_cursor === null ? null : estateHref(ESTATE_ACTIONS_PATH, query, { cursor: body.next_cursor });

  return (
    <div className="estate-page" data-estate-root="actions">
      <PageHeader title="Actions" subtitle="Interventions, owners and declared outcome criteria" />
      <EstateDateBar
        key={`${query.from}|${query.to}|${query.known_at ?? ""}`}
        query={query}
        body={body}
        windowRefused={read?.status === "refused" && read.code === "INVALID_WINDOW"}
        onApply={(nextQuery) => navigate(estateHref(ESTATE_ACTIONS_PATH, nextQuery))}
      />
      {read === null ? (
        <p className="estate-loading">Loading the Actions across the estate.</p>
      ) : read.status === "refused" ? (
        <EstateRefusal code={read.code} copy={read.copy} window={query} firstPage={firstPage} />
      ) : (
        <>
          <Cards body={read.value} />
          <Panel heading="Managed actions" headingId="estate-actions-heading" description={ACTIONS_LIFECYCLE}>
            {read.value.rows.length > 0 ? <ActionRowsTable body={read.value} /> : null}
            {read.value.total_count === 0 ? (
              <div className="estate-empty" data-estate-empty>
                <p>No actions match.</p>
              </div>
            ) : null}
            {read.value.total_count === null ? (
              <p className="estate-partial" data-estate-partial>
                {PARTIAL_TOTALS}
              </p>
            ) : null}
            <Pager next={next} first={firstPage} paged={query.cursor !== null} />
          </Panel>
          <LimitationNotice sentences={limitationSentences(read.value, PARTIAL_COVERAGE)} />
          <Notice tone="blue" data={{ "data-estate-notice": "" }}>
            {ACTIONS_NOTICE}
          </Notice>
        </>
      )}
    </div>
  );
}
