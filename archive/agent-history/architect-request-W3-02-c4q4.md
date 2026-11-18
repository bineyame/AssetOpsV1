# Architect request: W3-02 c4-q4 (Aggregation panel still over its cap)

Read `.agent/W3-02-build-spec.md` (c4), `.agent/W3-02-pending-rulings.md` c4-q4, and the v69 `globalfinancials` mock, including its CSS for the Aggregation panel prose.

After the c4 fixes, the Aggregation panel measures 148 px against a cap of 123 at 1440, and 194 against 187 at 390. The cause is the 14 px prose, which wraps to 2 lines where the mock's 12 px prose takes 1. Title and prose alone measure 126/172, against the mock's 99/163.

The mock is the layout authority. Rule the exact fix: the prose font size and line height that match the mock, or a copy shortening that keeps the meaning. Give the exact CSS and copy, and the test assertion for both caps.

Append the result as "Commit-4 rulings (c4b)" to `.agent/W3-02-build-spec.md`. Write nothing else. Do not commit.
