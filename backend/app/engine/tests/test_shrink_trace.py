from app.engine.shrinker import classify_failure, shrink
from app.engine.tracer.tracer import trace_compare


# ---- shrinker ----
def test_shrink_list_to_minimal_failing_input():
    fails = lambda a: 7 in a[0]  # noqa: E731
    assert shrink([[1, 5, 7, 9, 3, 7], 4], fails) == [[7], 0]


def test_shrink_respects_predicate_and_budget():
    assert shrink([[1, 2, 3]], lambda a: len(a[0]) == 3) == [[0, 0, 0]]
    assert shrink([[1, 2, 3]], lambda a: False) == [[1, 2, 3]]


def test_classify_failure_buckets():
    assert classify_failure([[], 3]) == "empty"
    assert classify_failure([[5], 5]) == "single_element"
    assert classify_failure([[3, 3], 6]) == "duplicates"
    assert classify_failure([[1, -2, 4], 3]) == "negatives"
    assert classify_failure([[1, 2000, 5], 3]) == "large"
    assert classify_failure([[2, 4, 8], 1]) == "boundary"
    assert classify_failure([[2, 4, 8], 6]) == "general"
    assert classify_failure([5]) == "boundary" or classify_failure([5]) == "general"


# ---- tracer (host-side, pure Python) ----
def ref_sum(nums):
    total = 0
    for n in nums:
        total += n
    return total


def buggy_skip_last(nums):
    total = 0
    for i in range(len(nums) - 1):
        total += nums[i]
    return total


def buggy_init(nums):
    total = 1
    for n in nums:
        total += n
    return total


def buggy_crash(nums):
    total = 0
    for i in range(len(nums) + 1):
        total += nums[i]
    return total


def test_trace_reports_first_divergent_iteration_and_learner_line():
    d = trace_compare(buggy_init, ref_sum, [[2, 3, 4]])
    assert d["variable"] == "total" and d["actual"] != d["expected"]
    assert d["line"] is not None


def test_trace_off_by_one_loop_bound():
    d = trace_compare(buggy_skip_last, ref_sum, [[2, 3, 4]])
    assert d["variable"] == "total" and d["iteration"] == 3
    assert (d["expected"], d["actual"]) == ("9", "5")


def test_trace_exception_in_learner():
    d = trace_compare(buggy_crash, ref_sum, [[1, 2]])
    assert d is not None and (d["variable"] in ("<exception>", "total", "i"))


def test_trace_no_divergence_and_step_cap_fallback():
    assert trace_compare(ref_sum, ref_sum, [[1, 2, 3]]) is None

    def slow(nums):
        t = 0
        for _ in range(5000):
            t += 1
        return t

    def other(nums):
        return 1

    d = trace_compare(slow, other, [[1]], max_steps=100)
    assert d["variable"] == "<return>" and d["line"] is None


def test_trace_uses_bound_methods():
    class S:
        def f(self, nums):
            total = 0
            for n in nums:
                total += n
            return total

    class Bad:
        def f(self, nums):
            total = 0
            for n in nums:
                total -= n
            return total

    d = trace_compare(Bad().f, S().f, [[2, 3]])
    assert d["variable"] == "total" and d["iteration"] == 1
