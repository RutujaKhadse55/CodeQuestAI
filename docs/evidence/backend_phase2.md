# Backend Phase 2 — verification pipeline (fuzz, shrink, trace, hints, mastery)

Pipeline per `/analyze`: AST policy -> run examples (+ Run capture) -> differential fuzz vs oracle (200 inputs,
fresh seed per attempt, stored, never returned) -> shrink -> classify -> trace vs reference -> Diagnoser (AI) ->
persist. One extra sandbox call (verify mode) runs fuzz + shrink + trace inside the container; **raw fuzz inputs
never leave it** (only counts, a 0/1 fingerprint vector, a failure class and a divergence).

| Item | Detail |
|---|---|
| Fuzz | learner vs oracle, comparator exact/unordered/float_tol, per-call limit 1 s, stops after 3 timeouts, 15 s budget |
| Fingerprint vector | fixed seed, 64 inputs, bit=1 when the learner fails; handed to AI's Diagnoser (mutation matching) |
| Shrinker | greedy delta-debugging on list/int/str args (300 steps); classes: empty, single_element, duplicates, negatives, large, boundary, general |
| Tracer | `sys.settrace` on learner + reference, same input; iteration = backward line jump; first shared variable that differs; learner line only; 2,000-step cap, falls back to final-output compare |
| Hint unlock | L1 always; L2 >=2 attempts or 3 min; L3 >=3 or 6 min; L4 >=4 or 10 min; copy-flagged attempts do not count |
| Copy detector | paste >=120 chars and >=60% of the code, pass, run within 90 s of start; flagged attempts defer mastery until `release_pending` |
| Mastery | Elo per LeetCode topic tag, K=32, base 1000, Easy/Medium/Hard opponent 900/1100/1300; a re-pass is not rewarded twice |
| Dashboard v1 | mastery per concept, mistake counts, recent diagnoses (with divergence), verified breakdown, attempts/solved |

## Measured (Backend laptop, Docker Desktop, warm)
| Case | Result |
|---|---|
| `/analyze` v1 on Binary Search (examples + fuzz + shrink + trace), 6 calls | 1.09 – 1.26 s each (target p95 < 6 s) |
| Example-passing single-element bug (`while lo < hi`) | examples pass; fuzz fails; class `single_element`; fallback mistake `missing_edge_single`; divergence `<return>` expected 0 / actual -1 at learner line 9 |
| Wrong init (`best = 0`) on Maximum Subarray | caught by fuzz (all-negative input), class `single_element` or `negatives` |
| Infinite-loop learner | fuzz outcome `timeout`, response in well under 60 s |
| Stand-in bundles (two-sum, binary-search, maximum-subarray) | each reference agrees with its oracle on >=150 valid generated inputs |

## Stand-ins until AI/Agents merge (flag `USE_REAL_AI`)
`contracts/fakes/backend_fakes.py`: `FakeReferenceBuilder` (3 hand-written, hand-verified bundles) and
`FakeDiagnoser`. `providers.py` is the single switch point. Mistake class currently comes from Backend's
rule fallback (confidence 0.3) — AI's fingerprint matcher replaces it. Divergence quality on loop-heavy bugs
beyond these 3 problems is untested.

Bundle convention for AI: oracle/reference define the same method + parameter names as the starter;
`gen_inputs(rng)` returns the list of call arguments and uses only the passed `rng`.
