# Algorithm design (Phase 6, to be completed)

## Starting heuristics (not VPA's algorithm, not guaranteed safe)

- CPU request = P95 CPU x (1 + 0.20)
- Memory request = P95 memory x (1 + 0.25)

Example from the design notes (illustrative only): P95 CPU 600m gives 720m;
P95 memory 800Mi gives 1000Mi.

## Open design questions

- Peak usage and sudden traffic spikes
- CPU throttling signals
- Memory safety, OOM events, peak vs P95
- Recommending limits separately from requests
- What to do when a recommendation fails SLO validation (revise or reject)
- Required observation window and minimum request count
