/**
 * W1-UX-06: the ONE shared width check and as-of pattern for every browser evidence script in tools/.
 *
 * Why: a CDP `Emulation.setDeviceMetricsOverride` can silently not take (UX-05 review L1 recorded
 * `clientWidth` 1425 in a nominal 390 pass), and a page wider than its viewport can widen a mobile layout
 * viewport. A "no sideways scroll" claim measured then is a claim about the wrong width. So after every
 * resize, navigation and capture resize, a script calls `requireWidth(width, height, where)`, which
 *
 *   1. waits (bounded) for `window.innerWidth === width`;
 *   2. fails unless `document.documentElement.clientWidth` is in `[width - WIDTH_SLACK, width]`;
 *   3. if that fails, retries once with a width-specific Chrome window (`Browser.setWindowBounds`) and the
 *      override re-sent, then checks again;
 *   4. records both widths in a claim (or only on failure with `{ record: false }`), and throws on failure,
 *      so nothing is measured or captured at a width that was not reached.
 *
 * `node tools/evidence-checks.mjs --self-test` proves it in a real Chrome: a real 390 passes, a page
 * wider than requested fails, and a deliberately wrong width fails. Unit and inventory tests:
 * tools/checks/test_evidence_checks.mjs (run by tools/check-all.ps1).
 */
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

/** A classic scrollbar is about 15 px; 20 leaves room for it and nothing else. */
export const WIDTH_SLACK = 20;

/**
 * The only two forms an "as of" bound may take (frontend `asOfText`): a formatted UTC instant or the honest
 * "time not recorded". Mirrors `AS_OF_PATTERN` in frontend/src/test/productPresentation.ts; the inventory
 * test asserts the two sources are identical.
 */
export const AS_OF_PATTERN = /^As of(?: \d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4}, \d{2}:\d{2} UTC|: time not recorded)$/;

export const WIDTH_PROBE = "({ innerWidth: window.innerWidth, clientWidth: document.documentElement.clientWidth, innerHeight: window.innerHeight })";

/** Pure verdict: the page was laid out at `requested` only if both widths agree with it. */
export function widthVerdict(requested, innerWidth, clientWidth) {
  const ok =
    Number.isFinite(innerWidth) &&
    Number.isFinite(clientWidth) &&
    innerWidth === requested &&
    clientWidth >= requested - WIDTH_SLACK &&
    clientWidth <= requested;
  return { requested, innerWidth, clientWidth, ok };
}

const pause = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * Build the guard for one CDP page session. `send(method, params)` is the script's CDP call;
 * `claim(name, ok, detail)` its claim recorder (optional: without it the guard only throws).
 */
export function widthGuard({ send, claim = null, waitMs = 5000, sleep = pause }) {
  const probe = async () => {
    const r = await send("Runtime.evaluate", { expression: WIDTH_PROBE, returnByValue: true });
    return r?.result?.value ?? {};
  };
  const settle = async (requested) => {
    const end = Date.now() + waitMs;
    let m = await probe();
    while (m.innerWidth !== requested && Date.now() < end) {
      await sleep(100);
      m = await probe();
    }
    return { ...widthVerdict(requested, m.innerWidth, m.clientWidth), innerHeight: m.innerHeight };
  };
  /** `height` is re-sent only by the window fallback; null keeps the page's current height. */
  return async function requireWidth(requested, height, where, { record = true } = {}) {
    let v = await settle(requested);
    if (!v.ok) {
      height = height ?? v.innerHeight;
      // The override did not hold: use a width-specific Chrome window and re-send the override, then recheck.
      const first = { innerWidth: v.innerWidth, clientWidth: v.clientWidth };
      try {
        const { windowId } = await send("Browser.getWindowForTarget");
        await send("Browser.setWindowBounds", { windowId, bounds: { windowState: "normal" } });
        await send("Browser.setWindowBounds", { windowId, bounds: { width: requested, height } });
        await send("Emulation.setDeviceMetricsOverride", { width: requested, height, deviceScaleFactor: 1, mobile: requested < 600 });
      } catch (error) {
        v = { ...v, fallbackError: String(error) };
      }
      v = { ...(await settle(requested)), firstAttempt: first, fallbackError: v.fallbackError, windowFallback: true };
    }
    delete v.innerHeight;
    const name = `${where}: laid out at the requested ${requested}px (innerWidth ${v.innerWidth}, clientWidth ${v.clientWidth})`;
    if (claim !== null && (record || !v.ok)) claim(name, v.ok, v);
    if (!v.ok) {
      throw new Error(
        `width check failed at ${where}: requested ${requested}, innerWidth ${v.innerWidth}, clientWidth ${v.clientWidth}` +
          ` (allowed [${requested - WIDTH_SLACK}, ${requested}]); nothing was measured at this width`,
      );
    }
    return v;
  };
}

// --- Real-Chrome self-test --------------------------------------------------------------------------------

async function selfTest() {
  const PORT = Number(process.env.ASSETOPS_CDP_PORT ?? 9479);
  const CHROME = process.env.ASSETOPS_CHROME ?? "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
  const profile = mkdtempSync(join(tmpdir(), "assetops-width-selftest-"));
  const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-first-run", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
  const results = [];
  const claim = (name, ok, detail) => {
    results.push({ name, ok });
    console.log(`${ok ? "PASS" : "FAIL"}  ${name}${detail === undefined ? "" : `  ${JSON.stringify(detail)}`}`);
  };
  let ws;
  try {
    for (let i = 0; i < 80 && !ws; i += 1) {
      try {
        const page = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page");
        if (page?.webSocketDebuggerUrl) {
          const sock = new WebSocket(page.webSocketDebuggerUrl);
          await new Promise((res, rej) => {
            sock.addEventListener("open", res);
            sock.addEventListener("error", rej);
          });
          ws = sock;
        }
      } catch {
        /* not up yet */
      }
      if (!ws) await pause(250);
    }
    if (!ws) throw new Error("Chrome did not expose a page target");
    let seq = 0;
    const pending = new Map();
    ws.addEventListener("message", (e) => {
      const msg = JSON.parse(e.data);
      if (msg.id && pending.has(msg.id)) {
        pending.get(msg.id)(msg);
        pending.delete(msg.id);
      }
    });
    const send = (method, params = {}) =>
      new Promise((res, rej) => {
        seq += 1;
        const id = seq;
        const timer = setTimeout(() => rej(new Error(`timeout ${method}`)), 30000);
        pending.set(id, (msg) => {
          clearTimeout(timer);
          msg.error ? rej(new Error(JSON.stringify(msg.error))) : res(msg.result);
        });
        ws.send(JSON.stringify({ id, method, params }));
      });
    await send("Page.enable");
    const responsive = "data:text/html," + encodeURIComponent('<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><body style="margin:0"><p>Responsive page</p></body>');
    const wide = "data:text/html," + encodeURIComponent('<!doctype html><body style="margin:0"><div style="width:1400px;height:20px;background:#ccc">wider than requested</div></body>');
    const load = async (url) => {
      await send("Page.navigate", { url });
      await pause(400);
    };
    const quietGuard = widthGuard({ send, waitMs: 1500 });
    const loudGuard = widthGuard({ send, claim, waitMs: 1500 });
    const expectFailure = async (label, fn) => {
      try {
        const v = await fn();
        claim(`${label}: the width check FAILS`, false, v);
      } catch (error) {
        claim(`${label}: the width check FAILS`, /width check failed/.test(String(error)), String(error));
      }
    };

    // 1. A real 390: override, responsive page, check passes with both widths recorded.
    await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 900, deviceScaleFactor: 1, mobile: true });
    await load(responsive);
    await loudGuard(390, 900, "self-test real 390 (responsive page)");
    await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
    await load(responsive);
    await loudGuard(1440, 1000, "self-test real 1440 (responsive page)");

    // 2. A page wider than requested: a 1400px-wide page with no viewport meta at a mobile 390.
    await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 900, deviceScaleFactor: 1, mobile: true });
    await load(wide);
    await expectFailure("self-test page wider than requested (1400px content, mobile 390)", async () => {
      // No window fallback here: the page itself widens the layout viewport, so the fallback cannot help either.
      return quietGuard(390, 900, "wide page at 390");
    });

    // 3. A deliberately wrong width: the override is 1440 but the claim asks for 390.
    await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
    await load(responsive);
    const wrong = widthGuard({
      // Swallow the fallback so the deliberately wrong override stays in place.
      send: (method, params) => (method.startsWith("Browser.") || method === "Emulation.setDeviceMetricsOverride" ? Promise.resolve({ windowId: 0 }) : send(method, params)),
      waitMs: 1500,
    });
    await expectFailure("self-test deliberately wrong width (override 1440, claimed 390)", () => wrong(390, 900, "wrong width"));
  } catch (error) {
    claim("self-test completed", false, String(error));
  } finally {
    try {
      ws?.close();
    } catch {
      /* closing */
    }
    chrome.kill();
    await pause(500);
    try {
      rmSync(profile, { recursive: true, force: true });
    } catch {
      /* Chrome may still hold the profile briefly */
    }
  }
  const failed = results.filter((r) => !r.ok);
  console.log(`${results.length - failed.length}/${results.length} self-test claims passed`);
  process.exit(failed.length === 0 && results.length >= 4 ? 0 : 1);
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1] && process.argv.includes("--self-test")) {
  await selfTest();
}
