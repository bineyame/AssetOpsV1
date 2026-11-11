# Owner: move to a VPS, 2026-11-11 ~17:50 local (verbatim)

"here is another context. I'll use caludecode on a vps that has 24GB RAM and 8 virtual cores, so this laptop won't be the machine i'll be using starting tomorrow or sooner. I want how to seamlessly continue on the server as well"

Answers to the coordinator's three questions:
- Cutover: "After Thursday demo (Recommended)"
- Code transfer (git bundle vs push to GitHub): "as long as the main is pushed to github with all branches merged, why would i need to branches?"
- VPS / access (Linux + Claude there / Linux + SSH from here / Windows): "1 and 2"

Coordinator reading:
- Cut over after Thursday's demo. Tonight's rebuild and the demo stay on the laptop.
- Pushing `main` to the private GitHub remote is authorized by the owner for the move (only main, after branches are merged). Unmerged in-flight branches at cutover are either merged first (if ACCEPTed) or carried as a git bundle so no work is lost.
- The VPS is Linux; the owner runs a Claude Code session there, and the laptop may also reach it over SSH for copying and setup.
