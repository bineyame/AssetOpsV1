# Owner authorization: local preview servers for the final recapture (2026-10-26)

Context: the auto-mode safety check refused, without explanation, one call by the batch 05-08 recapture agent that started the unmodified producer `serve` in the background and Vite via `.agent/post-W6-final-recapture/tools/start-vite.ps1` (the same script batches 01-04 used successfully).

Question asked: "The retake needs to start local preview servers in the background (the demo-data server and the web preview, on this machine only) for each batch. The safety check just refused that once, without saying why. How should I proceed?"

Owner answer (verbatim selection): "Allow, and retry (Recommended)" — "Starting local preview servers for the retake is fine. I'll relaunch the batch with that authorization recorded. If it's refused again, I'll come back to you."

Scope: starting local (127.0.0.1) producer `serve` processes and Vite dev servers in the background for the final recapture batches, stopped by PID afterwards. If refused again, stop and report to the coordinator, who returns to the owner. No workaround.

## Addendum (2026-10-26, later): no execution-policy bypass

The safety check refused `powershell -ExecutionPolicy Bypass -File tools\start-vite.ps1 ...` as "[Security Weaken]" during batch 13. Owner asked; answer (verbatim selection): "Start it plainly (Recommended)" — "Start the web preview directly with the normal command, with no safety setting switched off. It does the same job, and I'll record your approval. If that is refused too, I'll come back to you."

From now on: start Vite directly (e.g. a background `npm run dev -- --port <port> --strictPort` from `frontend/`, or `Start-Process npm.cmd ... -PassThru` in the PowerShell tool), never with `-ExecutionPolicy Bypass` or any other policy/safety override. If that is refused, stop and report.
