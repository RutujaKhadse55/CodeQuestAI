# Diagnosis accuracy (generated 2026-10-11 15:54)

Labelled buggy submissions: **10** (Backend set: Two Sum x10; AI/Agents/Frontend sets are added by their owners under `fixtures/lc/<slug>/buggy/`).

- **Detection rate** (pipeline reports a failure): **10/10** (100%)
- **Mistake-class accuracy** (exact label match): **2/10** (20%)

Mistake classes currently come from Backend's failure-class RULE FALLBACK (confidence 0.3), because AI's mutation-fingerprint matcher is not merged yet. Go/no-go (plan P2): if matching < 50 %, keep the tracer and AST rules. This table is the baseline to beat.

| Problem | File | Label | Predicted | Failure class | Detected | Match |
|---|---|---|---|---|---|---|
| two-sum | bug_off_by_one_bound_1.py | off_by_one_bound | None | general | yes | no |
| two-sum | bug_off_by_one_bound_2.py | off_by_one_bound | missing_edge_single | single_element | yes | no |
| two-sum | bug_wrong_operator_1.py | wrong_operator | None | general | yes | no |
| two-sum | bug_wrong_operator_2.py | wrong_operator | wrong_init | negatives | yes | no |
| two-sum | bug_accumulator_reset_1.py | accumulator_reset | None | general | yes | no |
| two-sum | bug_wrong_comparison_1.py | wrong_comparison | wrong_init | negatives | yes | no |
| two-sum | bug_wrong_init_1.py | wrong_init | missing_edge_single | single_element | yes | no |
| two-sum | bug_missing_edge_single_1.py | missing_edge_single | None | general | yes | no |
| two-sum | bug_hardcoded_output_1.py | hardcoded_output | hardcoded_output | empty | yes | yes |
| two-sum | bug_wrong_comparison_2.py | wrong_comparison | wrong_comparison | duplicates | yes | yes |
