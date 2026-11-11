/**
 * DIESEL-K6b (DIESEL-1-R3m §9m.4): the fuel verdict page body at `/sites/{code}/domain-actions/{id}/fuel-verification`,
 * the "after" check of a FUEL_BALANCE domain Action raised from an unexplained-fuel Finding. Layout follows v69
 * `verification` (`frontend/mockups/v69/index.html:498-503`) with the existing components only: the status line,
 * the header, four cards, the night-by-night table, then the Activity / Outcome evidence pair. Every string is the
 * server's (`fuel_verification.py`); the browser formats no number. No value line and no money card (H2); the fixed
 * H1 line is shown in every state.
 *
 * MOCK DEVIATION MD-FUEL-K6-1: v69 `:501` evaluates one target with guardrails. The fuel check has one target and no
 * guardrails (`guardrails = {}`, the BL-09/SCOPE-1 mill precedent), and its table lists nights, not metrics.
 * MOCK DEVIATION MD-FUEL-K6-2: v69's four cards (`:500`: target change, reserve breaches, critical service, final
 * outcome) become nights checked, fuel accounted for, tank sensor and final outcome. There is no money card and no
 * "Realized savings" (H2).
 * MOCK DEVIATION MD-FUEL-K6-3: v69's "Provisional target pass" badge is not shown. A night is either checked or "Not
 * checked yet", and an undecided check reads the server's not-judged text.
 * MOCK DEVIATION MD-FUEL-K6-4: v69's "Outcome evidence" prose and its "Review a complete evidence example" button
 * are replaced by the server's sentence and the fixed H1 line.
 */
import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { Badge, ChartNote, DataTable, KeyValues, MetricCard, MetricCards, MetricHeader, Panel, StatusBar, displayCode } from "../ui";
import { useLinkFor, type Ref } from "./chainRef";
import type { FuelVerification, FuelVerificationClient, FuelVerificationResult } from "./fuelVerificationClient";
import { MILL_NOT_FOUND } from "./SiteMillVerification";

export const FUEL_LOADING = "Loading the fuel check.";
export const FUEL_NOT_FOUND = MILL_NOT_FOUND;
export const FUEL_TABLE_HEADING_ID = "fuel-verification-nights-heading";
export const FUEL_MOCK_DEVIATIONS = "MOCK DEVIATION MD-FUEL-K6-1, MD-FUEL-K6-2, MD-FUEL-K6-3, MD-FUEL-K6-4";

export function useFuelVerification(client: FuelVerificationClient, siteCode: string, actionId: string) {
  const [state, setState] = useState<FuelVerificationResult | null>(null);
  useEffect(() => {
    let live = true;
    setState(null);
    void client.read(siteCode, actionId).then((r) => {
      if (live) setState(r);
    });
    return () => {
      live = false;
    };
  }, [client, siteCode, actionId]);
  return state;
}

export function FuelVerificationBody({ state }: { state: FuelVerificationResult | null }) {
  if (state === null) return <p role="status">{FUEL_LOADING}</p>;
  if (state.status === "not_found") return <p role="alert">{FUEL_NOT_FOUND}</p>;
  if (state.status === "error") return <p role="alert">{state.message}</p>;
  return <FuelVerificationView body={state.body} />;
}

function RefLink({ to, children }: { to: Ref; children: string }) {
  const href = useLinkFor()(to);
  return href === null ? <>{children}</> : <Link to={href}>{children}</Link>;
}

/** v69 `:502` "Activity evidence": the linked request, its completion and the site visit citing it (absent: no row). */
function ActivityPanel({ activity }: { activity: NonNullable<FuelVerification["activity"]> }) {
  const rows: [ReactNode, ReactNode, string?, boolean?][] = [];
  if (activity.case_code !== null) {
    rows.push(["Maintenance request", <RefLink to={activity.case_ref}>{activity.case_code}</RefLink>, "case"]);
  }
  rows.push(["Completed", activity.completed_text, "completed"]);
  if (activity.site_visit_text !== null) {
    // The site-visit note is the operator's own words (the frontend exemption).
    rows.push(["Site visit", <span data-vocabulary-exempt="user-owned">{activity.site_visit_text}</span>, "visit", true]);
  }
  return (
    <Panel heading="Activity evidence">
      <KeyValues rows={rows} />
      <ChartNote>{activity.note}</ChartNote>
    </Panel>
  );
}

const CARD_KEYS =["nights", "accounted", "sensor", "outcome"] as const;

function tone(state: FuelVerification["state"]): "green" | "red" | "amber" | "muted" {
  return state === "VERIFIED" ? "green" : state === "INEFFECTIVE" ? "red" : state === "INCONCLUSIVE" ? "amber" : "muted";
}

export function FuelVerificationView({ body }: { body: FuelVerification }) {
  const code = body.action_code ? displayCode(body.action_code) : null;
  const subtitle = [code, `source: ${[body.origin.title, body.origin.night_text].filter(Boolean).join(", ")}`, body.owner_label ? `owner: ${body.owner_label}` : null]
    .filter(Boolean)
    .join(" · ");
  const outcomeLines = [body.sentence ?? body.not_judged_text].filter((l): l is string => l !== null && l !== "");
  return (
    <div className="fuel-verification" data-fuel-state={body.state}>
      <StatusBar label="Verification status" items other={subtitle}>
        <Badge tone="neutral">{code === null ? body.headline : `${code} · ${body.headline}`}</Badge>
      </StatusBar>
      <MetricHeader
        label="Action"
        cells={[
          ...(body.owner_label === null ? [] : [["Owner", body.owner_label, "owner"] as [ReactNode, ReactNode, string]]),
          ["State", body.headline, "state"],
          ["Source", <RefLink to={body.origin.ref}>{body.origin.title}</RefLink>, "source"],
          ["Success criterion", body.criterion_text, "criterion"],
        ]}
      />
      <MetricCards label="Fuel check measures" data={{ "data-fuel-cards": body.state }}>
        {body.cards.map((c, i) => (
          <MetricCard
            key={c.label}
            label={c.label}
            value={c.value}
            note={c.note}
            word={i === 3 || c.value === "Not judged yet"}
            assessment={i === 3}
            tone={i === 3 ? tone(body.state) : undefined}
            data={{ "data-fuel-card": CARD_KEYS[i] }}
          />
        ))}
      </MetricCards>
      <Panel heading="Target evaluated night by night" headingId={FUEL_TABLE_HEADING_ID}>
        <DataTable labelledBy={FUEL_TABLE_HEADING_ID}>
          <thead>
            <tr>
              <th scope="col">Night</th>
              <th scope="col">Role</th>
              <th scope="col">Unexplained fuel range</th>
              <th scope="col">Tank sensor</th>
              <th scope="col">Result</th>
            </tr>
          </thead>
          <tbody>
            {body.nights.map((n) => (
              <tr key={`${n.window_id}-${n.revision}`} data-fuel-night={n.role} data-fuel-pass={n.passes === null ? "baseline" : String(n.passes)}>
                <th scope="row">{n.label}</th>
                <td>{n.role === "BASELINE" ? "Before the change" : "Target"}</td>
                <td>{n.range_text}</td>
                <td>{n.sensor_text}</td>
                <td>{n.result_text}</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
        <ChartNote data={{ "data-fuel-rule": "" }}>{body.rule_text}</ChartNote>
      </Panel>
      <div className="panel-pair panel-pair--equal">
        {body.activity === null ? null : <ActivityPanel activity={body.activity} />}
        <Panel heading="Outcome evidence">
          {outcomeLines.map((l) => (
            <p key={l} className="prose" data-fuel-line>
              {l}
            </p>
          ))}
          <p className="prose" data-fuel-fixed-line>
            {body.fixed_line}
          </p>
        </Panel>
      </div>
      <p className="mock-deviation-line" data-mock-deviation="R709">
        {FUEL_MOCK_DEVIATIONS}
      </p>
    </div>
  );
}
