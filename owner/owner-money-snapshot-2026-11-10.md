# Owner, 2026-11-10 (verbatim)

Context: the coordinator reported that the day snapshot stores the headroom facts but not the money. Potential income is computed at read time by `priced_energy@1`, using the declared price. The opportunity thread lifecycle is stored, but the money is not.

Owner: "currency calcuations may be relevant in the future along with tarrif changes and it is important to save outcome of calcuations in the snapshot for that reason; another option is to save the data bases of calcuation(one that is is likely to change) along with versioned mechanism(formula), but that may not be data efficent. Let the architect weigh in, and push back if my proposal doesn't make sense(ofcourse with reason)"
