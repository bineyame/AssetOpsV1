# Lab cockpit notes: reading the two Motivation images

This note travels with `SimulatorLab1.png` and `ScreenMockups.png` in this
folder. The images are unchanged, and they still guide how the Simulator Lab
looks. They do not decide what it can do. Where a picture shows something the
product does not do, or would do differently, this note corrects the picture.
It records the annotation from `.ai/PLANNING_HANDOFF_LAB_COCKPIT.md` and
`D-2026-09-30-lab-cockpit-presentation`, which the owner accepted on
2026-09-30. Operator surfaces keep the v6.9 product text as their authority.

Linked from both L1 delivery packets: `.agent/T025c-review-packet.md` (L1a)
and T025d's packet (L1b).

## `SimulatorLab1.png`

- **Step and speed.** Step means the run's frozen, declared boundary. It is
  not an editable one-second simulation step. The proposal's universal
  15-minute example is out of date: the T024 daytime examples use 15 minutes
  and the T025b mini-grid recipes use 5. The screen always shows the selected
  run's actual timestep, and the T025c run header states it. Speed is how
  fast the browser plays the run back, not how fast the simulation runs, so
  "100x" promises no supported timing behaviour.
- **Quick Actions.** This becomes T029A's future workflow: declare an
  intervention, then create a new Draft. The picture does not mean live
  injection, editing the environment, a destructive restart or jumping to an
  arbitrary time. A history cursor, like T025c's shared boundary selection,
  inspects the record. It never executes anything.
- **Devices.** In the Lab, devices show their actual reporting quality and
  source time: GOOD, STALE with the reading's original time, or no reading
  with its outcome. Operator views of Online, last seen or source health need
  accepted evidence of observations, arrivals and cadence. Gateway staging is
  labelled as staged until a real Commit and ingestion provide more.
- **What is drawn.** Draw the configured modelled assets and the three
  addressed mini-grid loads. The pictured cold room and its temperature are
  not default capabilities. T032 may explicitly add a cold-room electrical
  load, without thermal physics.
- **Values with no contract behind them.** Do not copy live breaker positions,
  400 V / 50 Hz, weather values, arbitrary sample rates or topology from the
  image. No content contract provides them. Reuse the existing two shells: the
  mockup's rail does not add operator routes.

## `ScreenMockups.png`

- **Screens 4-5 and 8-9.** Screens 4-5 (New and Edit scenario) and screens
  8-9 (health and log dashboards) remain followers. They have prerequisites:
  versioned, immutable scenario content for authoring, and real release,
  ingestion and cadence evidence for health and logs. The existing setup
  screens and inspectors remain usable. Leaving a control out does not promise
  that the capability is coming.

## What T025c built against this note

T025c's cockpit keeps each of these corrections:

- **Timestep.** The header shows the run's own frozen timestep and its
  boundary counts from the execution port.
- **Charts.** The day curves are recorded history. Their unit axes are kept
  separate (kW, % and L).
- **Reports.** Each reported reading is plotted once, at its own source time.
  A due attempt that produced no reading shows as a glyph with its outcome in
  words. A retained reading is labelled STALE with its original time.
- **Selection.** The shared selection only reads. Nothing in the cockpit
  injects, resets or jumps a run.
