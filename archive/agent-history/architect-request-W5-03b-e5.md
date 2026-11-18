# Architect request: rule on the W5-03b E5 backend review items A1-A6

You are the AssetOps Architect. Read .ai/ROLE_CONFIG.md, the E5 sections of .agent/W5-03-build-spec.md ("Unit E5", "E5 consolidated correction" and the pre-flight rulings that touch E5), .agent/W5-04-build-spec.md (which consumes the E5 read methods), .agent/W5-03b-e5-handoff.md (judgment calls 1-10), and .agent/W5-03b-e5-review.md (verdict REVISE, items A1-A6). The code is on branch task/W5-03b-e5-backend; read it with `git show task/W5-03b-e5-backend:<path>`.

Rule on each item with exact codes, statuses, messages and test cases:
- A1: money from the current head or from the as-of path.
- A2: the list-limit refusal code.
- A3: the correction error codes.
- A4: index id direction.
- A5: the currency-mismatch refusal. If it is required, give the trigger, the code, the message and the test.
- A6: the definition of "foreign" meter evidence (accepted set or cited set). If it changes, give the test.

Also confirm or amend the reviewer's M1 and L1-L3 test additions as stated. Record every ruling in the E5 refusal table so that the spec has no gaps.

Write .agent/W5-03b-e5-rulings.md (numbered) and apply it to .agent/W5-03-build-spec.md. Do not touch product code. Do not commit.
