import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LinkedMemoryRouter as MemoryRouter } from "../../test/refLinks";
import { settledScreen } from "../../test/settled";
import { ReadingUploadEntry, ReadingUploadPage } from "../ReadingUpload";
import {
  createReadingUploadClient,
  type ReadingUploadClient,
  type UploadChecked,
  type UploadEntry,
  type UploadResult,
  type UploadStatus,
} from "../readingUploadClient";

const ZONE = "Africa/Nairobi"; // UTC+3
const FILE = new File(["timestamp_utc,pv_ac_power [kW]\r\n"], "kobo-2026-11-17-early.csv", { type: "text/csv" });

const CHECKED: UploadChecked = {
  state: "CHECKED",
  latest_saved: "2026-11-16T20:45:00Z",
  text: "Checked the whole file: 160 readings. Nothing is saved until you confirm.",
  preview: {
    period_start: "2026-11-17T00:00:00Z", period_end: "2026-11-17T10:00:00Z", rows: 40, cells: 160, readings: 156, blanks: 4,
    columns: [
      { column: "pv_ac_power [kW]", unit: "kW", unit_matches: true, readings: 39, blanks: 1, blank_times: ["2026-11-17T00:15:00Z"],
        meter_text: "Solar inverter output", role_name_text: "Solar power" },
      { column: "clinic_feeder_power [kW]", unit: "kW", unit_matches: true, readings: 39, blanks: 1, blank_times: [],
        meter_text: "Clinic feeder meter", role_name_text: "Feeder demand" },
    ],
  },
};

function status(state: UploadStatus["state"], over: Partial<UploadStatus> = {}): UploadStatus {
  const accepted = state === "SENT" ? 0 : 160;
  return {
    upload_id: "u-1", file_name: FILE.name, state, held: false,
    counts: { rows: 40, readings: 156, blanks: 4, admitted: 160, held: 0, accepted, accepted_of: 160 },
    period_start: "2026-11-17T00:00:00Z", period_end: "2026-11-17T10:00:00Z",
    uploaded_by_text: "Uploaded by site admin", entered_at: "2026-11-17T10:05:00Z",
    text: `server words for ${state}`, ...over,
  };
}

function fakeClient(over: Partial<ReadingUploadClient> & { states?: UploadStatus[] } = {}) {
  const states = [...(over.states ?? [])];
  const calls = { check: 0, save: 0, status: 0 };
  const client: ReadingUploadClient = {
    entry: over.entry ?? (async (): Promise<UploadEntry> => ({ status: "on", templateNote: "One row per 15 minutes, times in UTC." })),
    check: over.check ?? (async (): Promise<UploadResult<UploadChecked>> => { calls.check += 1; return { status: "ok", value: CHECKED }; }),
    save: over.save ?? (async (): Promise<UploadResult<UploadStatus>> => { calls.save += 1; return { status: "ok", value: status("SENT") }; }),
    status: async () => {
      calls.status += 1;
      const next = states.length > 1 ? states.shift()! : states[0];
      return { status: "ok", value: next };
    },
  };
  return { client, calls };
}

function renderPage(client: ReadingUploadClient) {
  return render(
    <MemoryRouter initialEntries={["/sites/KOBO-001/uploads"]}>
      <ReadingUploadPage siteId="KOBO-001" siteName="Kobo" timeZone={ZONE} client={client} pollMs={5}
        boardHref={(day) => `/sites/KOBO-001?date=${day}`} />
    </MemoryRouter>,
  );
}

function choose(file: File = FILE) {
  fireEvent.change(screen.getByLabelText("Choose a CSV file of Kobo's readings"), { target: { files: [file] } });
}

afterEach(() => vi.restoreAllMocks());

describe("UP-1 Health entry panel (D-UP.4)", () => {
  it("shows the panel and its link only when the server's switch names the Site", async () => {
    const { client } = fakeClient();
    render(<MemoryRouter><ReadingUploadEntry siteId="KOBO-001" uploadsHref="/sites/KOBO-001/uploads" client={client} /></MemoryRouter>);
    const link = await screen.findByRole("link", { name: "Upload readings" });
    expect(link.getAttribute("href")).toBe("/sites/KOBO-001/uploads");
    expect(screen.getByRole("heading", { name: "Readings from a file" })).toBeTruthy();
  });

  it("renders nothing when the switch is off", async () => {
    const entry = vi.fn(async (): Promise<UploadEntry> => ({ status: "off" }));
    const { client } = fakeClient({ entry });
    const { container } = render(<MemoryRouter><ReadingUploadEntry siteId="KOBO-001" uploadsHref="/x" client={client} /></MemoryRouter>);
    await waitFor(() => expect(entry).toHaveBeenCalled());
    expect(container.querySelector("[data-upload-entry]")).toBeNull();
    expect(screen.queryByRole("link", { name: "Upload readings" })).toBeNull();
  });
});

describe("UP-1 upload page", () => {
  it("says plainly that uploading is not available when the switch is off", async () => {
    const { client } = fakeClient({ entry: async () => ({ status: "off" }) });
    renderPage(client);
    await settledScreen();
    expect(screen.getByText("Uploading readings is not available for this site.")).toBeTruthy();
    expect(screen.queryByLabelText("Choose a CSV file of Kobo's readings")).toBeNull();
  });

  it("checks before saving, saves, follows the readings to Analysed and links the board day", async () => {
    const { client, calls } = fakeClient({ states: [status("PROCESSING"), status("ANALYSED", { board_day: "2026-11-17" })] });
    renderPage(client);
    await settledScreen();
    expect(screen.getByRole("link", { name: "Download the template (CSV)" }).getAttribute("href"))
      .toBe("/api/sites/KOBO-001/reading-uploads/template");
    expect(screen.getByText("One row per 15 minutes, times in UTC.")).toBeTruthy();
    expect(screen.getByText(/recorded as/).textContent).toContain('"Uploaded by site admin"');
    choose();

    const check = await screen.findByRole("region", { name: `${FILE.name} · ready to save` });
    expect(within(check).getByText("17 Nov, 03:00 – 13:00")).toBeTruthy(); // Kobo time (UTC+3)
    expect(within(check).getByText("Solar inverter output")).toBeTruthy();
    expect(within(check).getByText("Feeder demand")).toBeTruthy();
    expect(within(check).getByText("Kobo's latest saved reading is 16 Nov, 23:45. This file starts after it.")).toBeTruthy();
    expect(calls.save).toBe(0); // the dry run saves nothing

    fireEvent.click(within(check).getByRole("button", { name: "Save 160 readings" }));
    await waitFor(() => expect(document.querySelector('[data-upload-state="ANALYSED"]')).not.toBeNull());
    expect(calls.save).toBe(1);
    expect(screen.getByText("Analysed", { selector: ".badge" })).toBeTruthy();
    expect(screen.getByText("Uploaded by site admin · 17 Nov 2026, 13:05")).toBeTruthy();
    const board = screen.getByRole("link", { name: "Open Kobo's board for 17 Nov" });
    expect(board.getAttribute("href")).toBe("/sites/KOBO-001?date=2026-11-17");
    const settled = calls.status;
    await new Promise((r) => setTimeout(r, 30));
    expect(calls.status).toBe(settled); // polling stops once Analysed
  });

  it("shows Still processing as the step under way while the readings are being worked out", async () => {
    const { client } = fakeClient({ states: [status("PROCESSING")] });
    renderPage(client);
    await settledScreen();
    choose();
    fireEvent.click(await screen.findByRole("button", { name: "Save 160 readings" }));
    await waitFor(() => expect(document.querySelector('[data-upload-state="PROCESSING"]')).not.toBeNull());
    const now = document.querySelector('[aria-current="step"]');
    expect(now?.textContent).toContain("Still processing");
    expect(now?.textContent).toContain("server words for PROCESSING");
    expect(screen.getByText("Kobo's board for 17 Nov will show these readings.")).toBeTruthy();
  });

  it("shows held readings with the accepted/held bar", async () => {
    const held = status("PROCESSING", { held: true, counts: { rows: 40, readings: 156, blanks: 4, admitted: 120, held: 40, accepted: 120, accepted_of: 120 } });
    const { client } = fakeClient({ states: [held] });
    renderPage(client);
    await settledScreen();
    choose();
    fireEvent.click(await screen.findByRole("button", { name: "Save 160 readings" }));
    await waitFor(() => expect(screen.queryByRole("img", { name: "120 accepted, 40 held" })).not.toBeNull());
    expect(screen.getByText("Held", { selector: ".badge" })).toBeTruthy();
  });

  it("shows Not analysed when the analysis failed, with no board link", async () => {
    const { client } = fakeClient({ states: [status("NOT_ANALYSED")] });
    renderPage(client);
    await settledScreen();
    choose();
    fireEvent.click(await screen.findByRole("button", { name: "Save 160 readings" }));
    await waitFor(() => expect(document.querySelector('[data-upload-state="NOT_ANALYSED"]')).not.toBeNull());
    expect(screen.getByText("Not analysed", { selector: ".badge" })).toBeTruthy();
    expect(screen.getByText("server words for NOT_ANALYSED")).toBeTruthy();
    expect(screen.queryByRole("link", { name: /board for/ })).toBeNull();
  });

  it("shows a refused file in the server's words with the row and column, and saves nothing", async () => {
    const { client, calls } = fakeClient({
      check: async () => ({ status: "refused", refusal: { code: "SPAN_MISMATCH", field: "row 7 timestamp_utc", upload_id: null,
        message: "The file was not saved: a time is not on a 15-minute step (:00, :15, :30, :45). Row 7." } }),
    });
    renderPage(client);
    await settledScreen();
    choose();
    const alert = await screen.findByRole("alert");
    expect(within(alert).getByRole("heading", { name: /a time is not on a 15-minute step/ })).toBeTruthy();
    expect(within(alert).getByText("row 7 timestamp_utc")).toBeTruthy();
    expect(within(alert).getByText("Refused")).toBeTruthy();
    expect(calls.save).toBe(0);
    fireEvent.click(within(alert).getByRole("button", { name: "Choose the corrected file" }));
    expect(screen.getByLabelText("Choose a CSV file of Kobo's readings")).toBeTruthy();
  });
});

describe("UP-1 client (D-UP.5)", () => {
  it("sends the file as a raw text/csv body with dry_run and file_name, and reads a refusal", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({
      code: "SPAN_MISMATCH", message: "The file was not saved.", state: "REFUSED", refusal: { code: "SPAN_MISMATCH", field: "row 7", detail: "" },
    }), { status: 422 }));
    vi.stubGlobal("fetch", fetchMock);
    const result = await createReadingUploadClient().check("KOBO-001", FILE);
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/api/sites/KOBO-001/reading-uploads?dry_run=true&file_name=kobo-2026-11-17-early.csv");
    expect(init.method).toBe("POST");
    expect(init.body).toBe(FILE);
    expect((init.headers as Record<string, string>)["Content-Type"]).toBe("text/csv");
    expect(result).toEqual({ status: "refused", refusal: { code: "SPAN_MISMATCH", message: "The file was not saved.", field: "row 7", upload_id: null } });
    vi.unstubAllGlobals();
  });

  it("treats any refusal of the entry read as off", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ code: "READING_UPLOAD_OFF" }), { status: 403 })));
    expect(await createReadingUploadClient().entry("KOBO-001")).toEqual({ status: "off" });
    vi.unstubAllGlobals();
  });
});
