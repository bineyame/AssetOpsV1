# Owner decision — Kobo night data (2026-11-06, verbatim)

Question: "Kobo's demo days need to be full 24-hour days, but we have no example night data for 8pm–6am. The build would repeat the early-evening 'no sun' values through the night, labelled as such (and it stops if that starts the generator, uses fuel, raises a problem or changes any money). OK?"

Owner answer: "let the architect provide one based on domain knowledge and utility to the application grounded on how actual sites operate and what makes nights interesting"

Supersedes DD1a1-R Q2 (repeat-evening night) and its stop gate.

Follow-up (2026-11-06, verbatim selection) to: "On a normal sunny day Kobo's battery runs down to the generator start level about an hour before dawn, so the generator switches on around 5am and delivers almost nothing before sunrise. The simulator doesn't model idle fuel, so those minutes show 0 litres — the screen will say so in plain words. No story figure changes (ACT-001, mill, spare solar). OK to show?"
Owner answer: "Yes, show it (Recommended)". Idle fuel model stays backlog BL-16.
