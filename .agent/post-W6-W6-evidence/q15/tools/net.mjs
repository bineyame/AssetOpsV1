// cap-q15 diagnostics: log network requests + console during a load.
import { session } from "./cdp.mjs";
const s = await session(); const log = []; const T0 = Date.now(); const P = (x) => log.push((Date.now() - T0) + " " + x);
s.on((m) => { if (m.method === "Network.requestWillBeSent") P("REQ " + m.params.request.url.slice(0, 120)); if (m.method === "Network.responseReceived") P("RES " + m.params.response.status + " " + m.params.response.url.slice(0, 100)); if (m.method === "Network.loadingFailed") P("FAIL " + m.params.errorText); if (m.method === "Runtime.consoleAPICalled") P("CON " + JSON.stringify(m.params.args.map((a) => a.value)).slice(0, 200)); if (m.method === "Runtime.exceptionThrown") P("EXC " + JSON.stringify(m.params.exceptionDetails).slice(0, 300)); });
await s.send("Network.enable"); await s.send("Runtime.enable");
await s.open(process.argv[2], 1440, 1000);
console.log(await s.js("document.querySelector(\".global-work-loading\")?.textContent ?? \"loaded\""));console.log(log.filter((l) => !l.includes("/src/") && !l.includes("node_modules") && !l.includes("@")).join("\n"));
await s.close(); process.exit(0);
