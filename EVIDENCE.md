# Local acceptance evidence

Recorded 2026-10-01 on Windows, Python 3.12.10, CPU only.

`python -m pytest -q`: 28 passed. Initial test suite elapsed time: 0.45 seconds.

Installed `lco.exe` end-to-end demo (`fixtures --out demo`, `run --input demo`, `report --format md`): 0.831 seconds measured by Python perf_counter across three actual subprocesses, including fixture generation, state write and full report rendering. Acceptance limit: under 5 seconds. Timing is machine-specific measured evidence, not a time-saved claim.

Computed synthetic results: 200 records, 150 selections, 50 infeasible; selected illustrative cost 250; 150 explicit baseline comparisons and illustrative baseline delta 200. All match independent hand arithmetic in README.md and expectations.json. Exactly the 50 planted infeasible IDs are reported, with zero false positives. These are synthetic validation results, not measured production savings or quality guarantees.

Evidence-based improvement during the build: the negative-baseline adversarial test established that enforcing quality can increase cost against a cheaper failing baseline. Reports therefore expose signed baseline deltas and comparison counts, and keep infeasible tasks out of these totals. This avoids treating an uncompleted task as a cost saving. The separate two-week real-use improvement hook remains pending.

The five-record example and fixture contain only synthetic input. No real trial results are shipped. No external model calls or GPU workloads were used. Publication is left to the separate verification step.
