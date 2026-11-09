/**
 * OWN-G3b: the live "Record a manual reading" form on Operational records (build sheet OWN-GAPS §3.3, §3.5 G3b vitest
 * list, Rev 1 and R2-G3b). Typed client answers only; the §3.2 route is G3a's.
 */
import { act, cleanup, fireEvent, render, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import globalWorkCss from "../globalWork.css?raw";
import { OPERATIONAL_RECORDS_PATH } from "../../shell/operatorSiteRoutes";
import { panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import {
  ENTRY_ERRORS,
  ENTRY_OUTCOMES,
  OperationalRecordsFrame,
  entryOutcome,
} from "../OperationalRecords";
import {
  createGlobalWorkClient,
  operationalEntryKey,
  type GlobalOperationalBody,
  type GlobalOperationalRow,
  type GlobalWorkClient,
  type OperationalEntryBody,
  type OperationalEntryResult,
} from "../globalWorkClient";

const PAGE = `/operational-records?from=${encodeURIComponent("2026-10-14T00:00:00Z")}&to=${encodeURIComponent("2026-10-21T00:00:00Z")}`;
const KEY = /^oprec-entry-[0-9a-f]{32}$/;
const TIME = "2026-10-20T06:00";

function row(over: Partial<GlobalOperationalRow> = {}): GlobalOperationalRow {
  const id = "00000000-0000-4000-8000-000000000101";
  return {
    site_code: "KIS-001",
    site_name: "Kisiwa",
    site_id: "00000000-0000-4000-8000-000000000002",
    site_code_key: "kis-001",
    site_domain: "MINIGRID",
    canonical_record_id: id,
    root_id: id,
    head_id: id,
    code: "REC-000001",
    kind: "TANK_DIP",
    body: "Tank dip at the 06:00 round: 198 L.",
    root_occurred_at: "2026-10-18T03:00:00Z",
    occurred_at: "2026-10-18T03:00:00Z",
    recorded_at: "2026-10-18T03:01:00Z",
    period_end: null,
    actor_kind: "SERVICE",
    actor_id: "service:operator-entry",
    quantity: "198",
    unit: "L",
    source_document_sha256: null,
    case_id: null,
    case_kind: null,
    case_code: null,
    state: "SUBMITTED",
    supersedes_record_id: null,
    correction_reason: null,
    source_provenance: { classification: "UNKNOWN", state: "UNKNOWN", source_ids: [], evidence_ids: [], basis_sha256: `sha256:${"0".repeat(64)}`, reasons: [] },
    links: { site: { label: "Kisiwa", href: "/sites/KIS-001" }, case: null },
    ...over,
  };
}

const BODY: GlobalOperationalBody = {
  schema_version: "global-work-index-1",
  scope: { tenant_id: "00000000-0000-4000-8000-000000000001", authorized_site_count: 2, covered_site_count: 2, access_basis: "sha256:x" },
  window: { from: "2026-10-14T00:00:00Z", to: "2026-10-21T00:00:00Z", bounds: "[from, to)" },
  known_at: "2026-10-21T08:00:00Z",
  status: "CURRENT",
  coverage: {
    state: "COMPLETE",
    reason: null,
    sites: [
      { site_code: "KIS-001", site_id: "00000000-0000-4000-8000-000000000002", state: "COVERED" },
      { site_code: "COLD-LAB-001", site_id: "00000000-0000-4000-8000-000000000003", state: "COVERED" },
    ],
  },
  total_count: 1,
  state_counts: null,
  rows: [row()],
  next_cursor: null,
  selection_token: "sha256:token",
};

type Submit = (siteCode: string, body: OperationalEntryBody) => Promise<OperationalEntryResult>;

function client(submit?: Submit, gate?: () => Promise<void>) {
  const reads: number[] = [];
  const sent: [string, OperationalEntryBody][] = [];
  const reader: GlobalWorkClient = {
    async incidents() {
      throw new Error("never read");
    },
    async operationalRecords() {
      reads.push(reads.length);
      if (gate) await gate();
      return { status: "loaded", value: BODY };
    },
    ...(submit
      ? {
          submitOperationalEntry: (siteCode: string, body: OperationalEntryBody) => {
            sent.push([siteCode, body]);
            return submit(siteCode, body);
          },
        }
      : {}),
  };
  return { reader, reads, sent };
}

async function mount(reader: GlobalWorkClient) {
  render(
    <MemoryRouter initialEntries={[PAGE]}>
      <Routes>
        <Route path={OPERATIONAL_RECORDS_PATH} element={<OperationalRecordsFrame client={reader} />} />
      </Routes>
    </MemoryRouter>,
  );
  await waitFor(() => expect(document.querySelector("[data-global-work-loading]")).toBeNull());
  await settledScreen();
  await waitFor(() => expect(form().querySelector("[data-global-work-form-site]")).toHaveValue("KIS-001"));
}

const form = () => panelTitled("Record a manual reading");
const q = <T extends Element>(selector: string) => form().querySelector(selector) as T;
const text = (el: Element | null) => (el?.textContent ?? "").replace(/\s+/g, " ").trim();
const errors = () => Array.from(form().querySelectorAll("[data-global-work-field-error]")).map(text);
const result = () => Array.from(q("[data-global-work-form-result]").querySelectorAll("p")).map(text);
const set = (selector: string, value: string) => fireEvent.change(q(selector), { target: { value } });
const submitButton = () => q<HTMLButtonElement>("[data-rec-submit]");
const saved: OperationalEntryResult = { status: "saved", publicCode: "REC-000042" };

function fillDip(value = "198") {
  set("[data-global-work-form-value]", value);
  set("[data-global-work-form-time]", TIME);
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("OWN-G3b: the Record a manual reading form", () => {
  it("keeps the mock field order and labels, offers the four readings and shows the ticket row only for a delivery", async () => {
    await mount(client(async () => saved).reader);
    const rows = Array.from(form().querySelectorAll(".input-row"));
    expect(rows.map((r) => Array.from(r.querySelectorAll(".field > label")).map(text))).toEqual([
      ["Site", "Reading"],
      ["Value", "Taken at (Site local time)"],
    ]);
    expect(Array.from(q("[data-global-work-form-site]").querySelectorAll("option")).map(text)).toEqual([
      "Kisiwa · KIS-001",
      "COLD-LAB-001",
    ]);
    expect(Array.from(q("[data-global-work-form-reading]").querySelectorAll("option")).map((o) => [text(o), (o as HTMLOptionElement).value])).toEqual([
      ["Fuel tank dip", "TANK_DIP"],
      ["Fuel delivery", "FUEL_DELIVERY"],
      ["Stock in chamber", "STOCK_IN_CHAMBER"],
      ["Meter reading", "METER_READING"],
    ]);
    expect(q("[data-global-work-form-reading]")).toHaveValue("TANK_DIP");
    const time = q<HTMLInputElement>("[data-global-work-form-time]");
    expect([time.type, time.step, time.value]).toEqual(["datetime-local", "60", ""]);
    expect(q<HTMLInputElement>("[data-global-work-form-value]").inputMode).toBe("decimal");
    expect(form().querySelector("[data-global-work-ticket-row]")).toBeNull();

    const shapes: [string, string, string][] = [];
    for (const entry of ["TANK_DIP", "FUEL_DELIVERY", "STOCK_IN_CHAMBER", "METER_READING"]) {
      set("[data-global-work-form-reading]", entry);
      shapes.push([entry, q<HTMLInputElement>("[data-global-work-form-value]").placeholder, text(q("[data-global-work-form-unit]"))]);
      expect(form().querySelector("[data-global-work-ticket-row]") !== null).toBe(entry === "FUEL_DELIVERY");
    }
    expect(shapes).toEqual([
      ["TANK_DIP", "e.g. 192 L", "L"],
      ["FUEL_DELIVERY", "e.g. 300 L", "L"],
      ["STOCK_IN_CHAMBER", "e.g. 40 kg", "kg"],
      ["METER_READING", "e.g. 1520 kWh", "kWh"],
    ]);
    set("[data-global-work-form-reading]", "FUEL_DELIVERY");
    const ticket = within(q("[data-global-work-ticket-row]")).getByLabelText("Ticket reference") as HTMLInputElement;
    expect(ticket.placeholder).toBe("e.g. KIS-DT-0002");
    // §3.3: no UnavailableInline on the form; the button keeps the mock label.
    expect(form().querySelector("[data-link-unavailable]")).toBeNull();
    expect(text(submitButton())).toBe("Submit for review");
    // §1 / §3.5: no forbidden fuel words anywhere on the form.
    expect(form().textContent).not.toMatch(/theft|stolen|steal|siphon|pilfer/i);
  });

  it("shows each validation message under its field after a Submit and sends nothing", async () => {
    const c = client(async () => saved);
    await mount(c.reader);
    expect(errors()).toEqual([]);
    fireEvent.click(submitButton());
    expect(errors()).toEqual([ENTRY_ERRORS.value, ENTRY_ERRORS.time]);
    expect(q("[data-global-work-form-value]").getAttribute("aria-invalid")).toBe("true");
    set("[data-global-work-form-value]", "1.2345");
    expect(errors()).toEqual([ENTRY_ERRORS.value, ENTRY_ERRORS.time]);
    set("[data-global-work-form-value]", "1234567");
    expect(errors()[0]).toBe(ENTRY_ERRORS.value);
    set("[data-global-work-form-reading]", "FUEL_DELIVERY");
    set("[data-global-work-form-value]", "0");
    set("[data-global-work-form-time]", TIME);
    fireEvent.click(submitButton());
    expect(errors()).toEqual([ENTRY_ERRORS.delivery, ENTRY_ERRORS.ticket]);
    set("[data-global-work-form-value]", "300");
    set("[data-global-work-form-ticket]", "#KIS");
    expect(errors()).toEqual([ENTRY_ERRORS.ticketPattern]);
    expect(c.sent).toEqual([]);
    expect([ENTRY_ERRORS.site, ENTRY_ERRORS.value, ENTRY_ERRORS.delivery, ENTRY_ERRORS.time, ENTRY_ERRORS.ticket, ENTRY_ERRORS.ticketPattern]).toEqual([
      "Choose a Site.",
      "Enter a number of 0 or more, with at most 3 decimals.",
      "Enter the delivered litres (more than 0).",
      "Enter the time the reading was taken.",
      "Enter the delivery ticket reference.",
      "Use letters, digits, spaces and / . _ - only, up to 40 characters, starting with a letter or digit.",
    ]);
  });

  it("moves focus to the first invalid field in form order on a refused Submit (polish L2)", async () => {
    const c = client(async () => saved);
    await mount(c.reader);
    fireEvent.click(submitButton());
    expect(q("[data-global-work-form-value]")).toHaveFocus();
    set("[data-global-work-form-value]", "198");
    fireEvent.click(submitButton());
    expect(q("[data-global-work-form-time]")).toHaveFocus();
    set("[data-global-work-form-reading]", "FUEL_DELIVERY");
    set("[data-global-work-form-time]", TIME);
    fireEvent.click(submitButton());
    expect(q("[data-global-work-form-ticket]")).toHaveFocus();
    expect(c.sent).toEqual([]);
  });

  it("keeps the live region rendered and clears it when a send starts, so a repeat is announced (polish L1)", async () => {
    const pending: ((v: OperationalEntryResult) => void)[] = [];
    const c = client(() => new Promise((resolve) => pending.push(resolve)));
    await mount(c.reader);
    const region = q<HTMLElement>("[data-global-work-form-result]");
    expect(region.isConnected).toBe(true);
    expect(region.getAttribute("role")).toBe("status");
    fillDip();
    fireEvent.click(submitButton());
    await act(async () => pending[0]({ status: "unconfirmed" }));
    expect(result()).toEqual([ENTRY_OUTCOMES.unconfirmed]);
    fireEvent.click(submitButton());
    await waitFor(() => expect(pending).toHaveLength(2));
    expect(result()).toEqual([]);
    await act(async () => pending[1]({ status: "unconfirmed" }));
    expect(result()).toEqual([ENTRY_OUTCOMES.unconfirmed]);
    // The empty region must not be taken out of the accessibility tree by the stylesheet.
    expect(globalWorkCss).not.toMatch(/\.global-work-form-result:empty\s*\{[^}]*display:\s*none/);
  });

  it("states Choose a Site when no Site is offered, with Submit disabled", async () => {
    const empty = { ...BODY, coverage: { ...BODY.coverage, sites: [] } };
    const reader: GlobalWorkClient = { async incidents() { throw new Error("never"); }, async operationalRecords() { return { status: "loaded", value: empty }; } };
    render(
      <MemoryRouter initialEntries={[PAGE]}>
        <Routes>
          <Route path={OPERATIONAL_RECORDS_PATH} element={<OperationalRecordsFrame client={reader} />} />
        </Routes>
      </MemoryRouter>,
    );
    await settledScreen();
    await waitFor(() => expect(form().querySelector("[data-global-work-form-site] option")).not.toBeNull());
    expect(submitButton()).toBeDisabled();
    fireEvent.submit(q("[data-global-work-manual-form]"));
    expect(errors()[0]).toBe(ENTRY_ERRORS.site);
  });

  it("sends the exact closed body, disables Submit in flight, then states the save, re-reads and clears the values", async () => {
    let release: (value: OperationalEntryResult) => void = () => undefined;
    const c = client(() => new Promise((resolve) => (release = resolve)));
    await mount(c.reader);
    set("[data-global-work-form-site]", "COLD-LAB-001");
    set("[data-global-work-form-reading]", "FUEL_DELIVERY");
    set("[data-global-work-form-value]", " 300.5 ");
    set("[data-global-work-form-time]", TIME);
    set("[data-global-work-form-ticket]", " KIS-DT-0002 ");
    fireEvent.click(submitButton());
    expect(c.sent).toHaveLength(1);
    const [siteCode, sentBody] = c.sent[0];
    expect(siteCode).toBe("COLD-LAB-001");
    expect(Object.keys(sentBody)).toEqual(["entry", "value", "taken_at_local", "ticket_reference", "idempotency_key"]);
    expect(sentBody).toEqual({
      entry: "FUEL_DELIVERY",
      value: "300.5",
      taken_at_local: TIME,
      ticket_reference: "KIS-DT-0002",
      idempotency_key: expect.stringMatching(KEY),
    });
    expect(submitButton()).toBeDisabled();
    expect(text(submitButton())).toBe("Submit for review");
    fireEvent.click(submitButton());
    expect(c.sent).toHaveLength(1);
    expect(c.reads).toHaveLength(1);
    await act(async () => release({ status: "saved", publicCode: "REC-000042" }));
    expect(result()).toEqual(["Saved as REC-042, status Submitted.", ENTRY_OUTCOMES.fuelRecheck]);
    expect(q("[data-global-work-form-result]").getAttribute("role")).toBe("status");
    expect(q("[data-global-work-form-result]").getAttribute("aria-live")).toBe("polite");
    await waitFor(() => expect(c.reads).toHaveLength(2));
    await waitFor(() => expect(q("[data-global-work-form-site]")).toHaveValue("COLD-LAB-001"));
    expect(q("[data-global-work-form-reading]")).toHaveValue("FUEL_DELIVERY");
    expect(q("[data-global-work-form-value]")).toHaveValue("");
    expect(q("[data-global-work-form-ticket]")).toHaveValue("");
    expect(q("[data-global-work-form-time]")).toHaveValue("");
    expect(errors()).toEqual([]);
    expect(result()[0]).toBe("Saved as REC-042, status Submitted.");
    expect(submitButton()).toBeEnabled();
  });

  it("sends a null ticket for a tank dip and shows one line for a stock reading", async () => {
    const c = client(async () => saved);
    await mount(c.reader);
    fillDip();
    fireEvent.click(submitButton());
    await waitFor(() => expect(result()).toEqual(["Saved as REC-042, status Submitted.", ENTRY_OUTCOMES.fuelRecheck]));
    expect(c.sent[0][1]).toMatchObject({ entry: "TANK_DIP", value: "198", ticket_reference: null });
    set("[data-global-work-form-reading]", "STOCK_IN_CHAMBER");
    fillDip("40");
    fireEvent.click(submitButton());
    await waitFor(() => expect(result()).toEqual(["Saved as REC-042, status Submitted."]));
  });

  it("keeps the key after a failed confirmation, a 5xx or a 4xx, and replaces it after an edit or a success", async () => {
    const answers: OperationalEntryResult[] = [
      { status: "unconfirmed" },
      { status: "refused", httpStatus: 503, code: "WORK_STORE_UNAVAILABLE" },
      { status: "refused", httpStatus: 422, code: "WORK_OCCURRED_AT_FUTURE" },
      { status: "unconfirmed" },
      saved,
      saved,
    ];
    const c = client(async () => answers.shift()!);
    await mount(c.reader);
    fillDip();
    const send = async () => {
      fireEvent.click(submitButton());
      await waitFor(() => expect(submitButton()).toBeEnabled());
    };
    await send();
    expect(result()).toEqual([ENTRY_OUTCOMES.unconfirmed]);
    await send();
    expect(result()).toEqual([ENTRY_OUTCOMES.unconfirmed]);
    await send();
    expect(result()).toEqual([ENTRY_OUTCOMES.future]);
    const keys = () => c.sent.map(([, b]) => b.idempotency_key);
    expect(new Set(keys()).size).toBe(1);
    expect(q("[data-global-work-form-value]")).toHaveValue("198");
    set("[data-global-work-form-value]", "199");
    await send();
    expect(keys()[3]).not.toBe(keys()[2]);
    await send();
    expect(keys()[4]).toBe(keys()[3]);
    fillDip();
    await send();
    expect(keys()[5]).not.toBe(keys()[4]);
    expect(keys().every((k) => KEY.test(k))).toBe(true);
  });

  it("an edit made while a save is in flight replaces the key for the next submit", async () => {
    let release: (value: OperationalEntryResult) => void = () => undefined;
    const c = client(() => new Promise((resolve) => (release = resolve)));
    await mount(c.reader);
    fillDip();
    fireEvent.click(submitButton());
    set("[data-global-work-form-value]", "200");
    await act(async () => release({ status: "unconfirmed" }));
    fireEvent.click(submitButton());
    expect(c.sent[1][1].idempotency_key).not.toBe(c.sent[0][1].idempotency_key);
    expect(c.sent[1][1].value).toBe("200");
  });

  it("states every outcome row's text", async () => {
    const refused = (httpStatus: number, code: string | null): OperationalEntryResult => ({ status: "refused", httpStatus, code });
    expect(entryOutcome(saved, "METER_READING")).toEqual(["Saved as REC-042, status Submitted."]);
    expect(entryOutcome(saved, "TANK_DIP")).toEqual([
      "Saved as REC-042, status Submitted.",
      "If this Site's tank level is measured, the night it falls in is checked again at the next background refresh.",
    ]);
    const cases: [OperationalEntryResult, string][] = [
      [refused(403, "WORK_WRITE_FORBIDDEN"), "Saving records is not switched on for this installation."],
      [refused(422, "OPREC_ENTRY_NO_TANK"), "This Site has no single fuel tank to record against."],
      [refused(422, "WORK_OCCURRED_AT_FUTURE"), "The time taken is in the future."],
      [refused(422, "WORK_OCCURRED_AT_TOO_OLD"), "The time taken is more than 30 days ago."],
      [refused(409, "WORK_EVENT_DUPLICATE_KEY"), "This entry was already saved with different values. Reload the page and enter it again."],
      [refused(422, "OPREC_ENTRY_INVALID"), "Check the values and try again."],
      [refused(422, "OPREC_ENTRY_TICKET_REQUIRED"), "Check the values and try again."],
      [refused(422, "WORK_RECORD_QUANTITY_INVALID"), "Check the values and try again."],
      [refused(403, "SITE_SCOPE_FORBIDDEN"), "Check the values and try again."],
      [refused(401, "UNAUTHENTICATED"), "Check the values and try again."],
      [refused(404, "SITE_NOT_FOUND"), "Check the values and try again."],
      [refused(503, "WORK_STORE_UNAVAILABLE"), "The record could not be confirmed. Try again; it will not be saved twice."],
      [refused(500, null), "The record could not be confirmed. Try again; it will not be saved twice."],
      [{ status: "unconfirmed" }, "The record could not be confirmed. Try again; it will not be saved twice."],
    ];
    for (const [answer, line] of cases) expect(entryOutcome(answer, "TANK_DIP")).toEqual([line]);

    // Rendered: a refusal keeps the form values.
    const c = client(async () => refused(422, "OPREC_ENTRY_NO_TANK"));
    await mount(c.reader);
    fillDip();
    fireEvent.click(submitButton());
    await waitFor(() => expect(result()).toEqual([ENTRY_OUTCOMES.noTank]));
    expect(q("[data-global-work-form-value]")).toHaveValue("198");
    expect(c.reads).toHaveLength(1);
  });

  it("a client without the submit method shows the not-switched-on row", async () => {
    const c = client();
    await mount(c.reader);
    fillDip();
    fireEvent.click(submitButton());
    await waitFor(() => expect(result()).toEqual([ENTRY_OUTCOMES.forbidden]));
  });

  it("labels the entry service's records Entered by site admin and leaves other ids as stored", async () => {
    const two = { ...BODY, total_count: 2, rows: [row(), row({ root_id: "r2", head_id: "r2", code: "REC-000002", actor_id: "service:w401-fixture" })] };
    const reader: GlobalWorkClient = { async incidents() { throw new Error("never"); }, async operationalRecords() { return { status: "loaded", value: two }; } };
    await mount(reader);
    expect(Array.from(document.querySelectorAll("[data-global-work-actor]")).map(text)).toEqual([
      "Entered by site admin",
      "service:w401-fixture",
    ]);
  });
});

describe("OWN-G3b: the entry client and key", () => {
  it("posts JSON to the Site entry route and reads saved, refused and unconfirmed answers", async () => {
    const calls: [string, RequestInit | undefined][] = [];
    const answers = [
      new Response(JSON.stringify({ schema_version: "operational-record-1", id: "x", canonical_record_id: "x", public_code: "REC-000007", state: "SUBMITTED", recorded_at: "t" }), { status: 201 }),
      new Response(JSON.stringify({ schema_version: "operational-record-1", public_code: "REC-000007" }), { status: 200 }),
      new Response(JSON.stringify({ detail: { code: "OPREC_ENTRY_NO_TANK", message: "m" } }), { status: 422 }),
      new Response("not json", { status: 201 }),
      new Response(JSON.stringify({ schema_version: "other", public_code: "REC-1" }), { status: 201 }),
      new Response("gateway", { status: 502 }),
    ];
    vi.stubGlobal("fetch", async (path: string, init?: RequestInit) => {
      calls.push([path, init]);
      const next = answers.shift();
      if (next === undefined) throw new TypeError("network");
      return next;
    });
    const body: OperationalEntryBody = { entry: "TANK_DIP", value: "198", taken_at_local: TIME, ticket_reference: null, idempotency_key: `oprec-entry-${"a".repeat(32)}` };
    const api = createGlobalWorkClient();
    const results = [];
    for (let i = 0; i < 7; i += 1) results.push(await api.submitOperationalEntry!("KIS 001", body));
    expect(calls[0][0]).toBe("/api/sites/KIS%20001/work/operational-entries");
    expect(calls[0][1]?.method).toBe("POST");
    expect((calls[0][1]?.headers as Record<string, string>)["Content-Type"]).toBe("application/json");
    expect(JSON.parse(String(calls[0][1]?.body))).toEqual(body);
    expect(results).toEqual([
      { status: "saved", publicCode: "REC-000007" },
      { status: "saved", publicCode: "REC-000007" },
      { status: "refused", httpStatus: 422, code: "OPREC_ENTRY_NO_TANK" },
      { status: "unconfirmed" },
      { status: "unconfirmed" },
      { status: "refused", httpStatus: 502, code: null },
      { status: "unconfirmed" },
    ]);
  });

  it("makes oprec-entry-<32 hex> keys with randomUUID, and from getRandomValues when randomUUID is absent", () => {
    expect(operationalEntryKey()).toMatch(KEY);
    const real = globalThis.crypto;
    vi.stubGlobal("crypto", { getRandomValues: (bytes: Uint8Array) => real.getRandomValues(bytes) });
    expect((globalThis.crypto as Crypto).randomUUID).toBeUndefined();
    const keys = [operationalEntryKey(), operationalEntryKey()];
    expect(keys[0]).toMatch(KEY);
    expect(keys[1]).toMatch(KEY);
    expect(keys[0]).not.toBe(keys[1]);
  });
});
