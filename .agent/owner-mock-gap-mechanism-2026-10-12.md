# Owner request: mock gap closure mechanism — verbatim, 2026-10-12

Owner asked: "when is a complete visual fedility with the mockup expected for site?"
Coordinator answered: no wave currently schedules complete fidelity; W1 makes core panels truthful and mock-like; non-core panels and data the product doesn't collect remain honest visible gaps with no owner in the queue.

Owner asked: "from a mechanism point of view, if the desired goal is the mock screens, what is the approach to get there currently (systematic addressing of gaps incremntally with honesty and clear gap identificaiton)"
Coordinator explained the current mechanism (manifest → panels → claim portions → registry nodes; waves with core panels; next-work scoring over core paths; slices; honesty on screen/registry/packet; visual gates) and its holes:
- non-core panel portions are recorded but never ranked;
- data with no source (signal strength, firmware, commissioning records, policy documents, productive-use designation) is labelled "Not available yet" on screen but has no registry node, so nothing ever picks it up;
- no later wave revisits an earlier Site's screens.
Coordinator proposed:
1. Every on-screen missing element and every non-core panel portion gets a registry node (what is missing — decision, data source, contract, build, visual — and target wave), making the gap list complete.
2. Non-core portions become rankable at lower weight than core, so they are picked up once a wave's core work runs out.
3. A per-screen "complete to mock" item after a screen's core is accepted (finish, or an explicit won't-do / do-in-wave-X decision).
4. A guard: every on-screen "Not available yet" must reference a registry node, so no gap is orphaned.
Recommendation: do 1 and 4 now; decide 2 and 3 at W1 exit.

Owner: "yes, send it to the architect"
