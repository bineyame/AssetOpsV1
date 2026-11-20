"""One-off sweep (rev 16.6, OD-6 and G-F5): in loop-*.js display strings, "plan" used for a declared target becomes
"target"; "plan" stays only for the new portfolio plan. Exact substrings, each must exist; data keys (.plan) untouched.
Run once: python3 tools/plain_target_sweep.py   (idempotent: an already-swept file reports 0 and is left alone)."""
import pathlib, sys
here = pathlib.Path(__file__).resolve().parent.parent
R = [
 ('against plan', 'against target'), ('Off plan', 'Off target'), ('On plan', 'On target'), ('on plan in October', 'on target in October'),
 ('From plan to October', 'From target to October'), ("['Factor','Plan','October'", "['Factor','Target','October'"),
 ("o.kind==='cost'?'Plan cost':'Plan'", "o.kind==='cost'?'Target cost':'Target'"), ("['Ratio','October','Plan']", "['Ratio','October','Target']"),
 ("['Operations measure','Plan'", "['Operations measure','Target'"), ("['Site','Money factor','Plan'", "['Site','Money factor','Target'"),
 ('<th>Plan</th>', '<th>Target</th>'), ("{label:'Plan',total:true", "{label:'Target',total:true"),
 ('(plan $3 L)', '(target $3 L)'), ('carried at plan', 'carried at target'), ('estimated at plan', 'estimated at target'),
 ('the plan amount is carried', 'the target amount is carried'), ('plan amount carried', 'target amount carried'),
 ('`plan ${num(C.', '`target ${num(C.'), ('`plan ${usd(C.plan', '`target ${usd(C.plan'), ('`plan ${usd(T.plan)}', '`target ${usd(T.plan)}'),
 ('(plan ${usd2(', '(target ${usd2('), ('cellnote">plan ${', 'cellnote">target ${'), ('(plan ${m.plan})', '(target ${m.plan})'),
 ('(plan ${P.plan.max_kw}', '(target ${P.plan.max_kw}'), ('Share at peak: plan ${', 'Share at peak: target ${'), ('→ plan ${num(P.kwh)}', '→ target ${num(P.kwh)}'),
 ('occupancy (plan ${', 'occupancy (target ${'), ('against a plan of', 'against a target of'), ('how:`Plan ${usd(P.energy_cost)}', 'how:`Target ${usd(P.energy_cost)}'),
 ('formula:`Plan ${pl} · October', 'formula:`Target ${pl} · October'), ("'plan not declared at this factor'", "'no target declared at this factor'"),
 ("'difference from plan'", "'difference from target'"), ('the plan is declared only as a bill total', 'the target is declared only as a bill total'),
 ('the plan has no split by time of day', 'the target has no split by time of day'), ('Plan split of litres by reason', 'Target split of litres by reason'),
 ('Plan at sub-factor level', 'Targets below the site total'), ('Plan comparison below total litres', 'Target comparison below total litres'),
 ('Plan split by time of day', 'Target split by time of day'), ("'Monthly plan and budget spreadsheet'", "'Monthly targets and budget spreadsheet'"),
 ("'Monthly plan or budget'", "'Monthly targets or budget'"), ('% plan, so the', '% target, so the'), ('Plan against October', 'Target against October'),
 ('to plan against actual', 'to target against actual'), ('leaves; plan against October', 'leaves; target against October'),
 ('A verification plan with three separate verdicts', 'A way to prove each change, with three separate verdicts'),
]
total = 0
for f in sorted(here.glob('loop-*.js')):
    t = f.read_text(encoding='utf-8'); n0 = 0
    for a, b in R:
        k = t.count(a)
        if k: t = t.replace(a, b); n0 += k
    if n0: f.write_text(t, encoding='utf-8')
    total += n0; print(f.name, n0)
print('total', total)
