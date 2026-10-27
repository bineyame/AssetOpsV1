# Demo-sprint review Lows (open; fold into a Sonnet fix round or the backlog)

- TEL-T1 L1: the emulator does not count a write sent during a pause.
- TEL-T1 L2: the client ignores the MBAP protocol identifier in replies.
- TEL-T1 L3: the new guard patterns share blind spots with the existing rules (bare `import_module("host")`, comma-joined imports).
- TEL-04 L1: an unexpected exception after START exits 1 with no EXIT line; an identity refusal exits 1, not 3 (`modbus_poller.py:558`, `:517`).
- TEL-04 L2: a KeyError gives exit 1, not 2 (`modbus_poller.py:531`).
- TEL-04 L3: the inner deliver loop in the proof has no deadline (`proof:182`).
- TEL-04 L4: the CONFIG_FAULT, unavailable-limit and SEAL_REFUSED exits are untested.
- CC-R1 Lows: fixed in CC-R2 commit 1407a4b0.
- TEL-05 L1: `NO_GENERATOR_STATE` is only a substring match (acceptance test line 237).
- TEL-05 L2: no check that no Finding exists (line 240).
