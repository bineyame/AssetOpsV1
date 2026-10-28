# Architect reply: efficient long-run design (2026-10-28)

I checked the code and briefly timed the cold-room model. The real problem is not memory. The cold model does exact fraction arithmetic, and its numbers get longer at every simulated minute. One day of history takes under a second, four days take 25 seconds, and 91 days would take somewhere between 3.5 and 23 hours. The previous streaming plan would have failed on this.

The fix is what good simulation software does:

- Hold temperature to a millionth of a degree. A small ledger keeps the energy books exactly balanced.
- Run the 91 days as one history, worked through a week at a time. Each week's results are written to disk as they are produced.
- Give each week its own fingerprint, so any difference can be traced to the week where it started.
- Publish week by week.

Example: with the precision fix, the cold room's 91 days of physics take about 22 seconds instead of hours, and memory should stay flat, under a quarter of a gigabyte.

I rejected three alternatives:

- Thirteen separate weekly runs. A before-and-after comparison would span two runs and lose its money figures.
- A coarser time step. That changes the cold-room physics.
- Replaying a prepared file. It carries no money and no "Simulated with real public inputs" label.

The work grows slightly, from 17.5 to 18.25 builder-days. EV at 91 days fits next sprint if the telemetry builder takes the EV tasks alongside the data builder.
