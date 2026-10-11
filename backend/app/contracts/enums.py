from enum import Enum, IntEnum


class Lang(str, Enum):
    en = "en"
    hi = "hi"
    mr = "mr"


class HintLevel(IntEnum):
    L1 = 1
    L2 = 2
    L3 = 3
    L4 = 4


class Verified(str, Enum):
    verified = "oracle-verified"
    unverified = "unverified"


class ErrorCode(str, Enum):
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    CODE_REJECTED = "CODE_REJECTED"
    HINT_LOCKED = "HINT_LOCKED"
    UNSUPPORTED_PROBLEM = "UNSUPPORTED_PROBLEM"
    UNSUPPORTED_LANGUAGE = "UNSUPPORTED_LANGUAGE"
    CREDIT_CAP_REACHED = "CREDIT_CAP_REACHED"
    UPSTREAM_FAILED = "UPSTREAM_FAILED"



class Outcome(str, Enum):
    passed = "passed"
    wrong_output = "wrong_output"
    runtime_error = "runtime_error"
    timeout = "timeout"


class MistakeClass(str, Enum):
    off_by_one_bound = "off_by_one_bound"
    missing_empty_case = "missing_empty_case"
    wrong_init = "wrong_init"
    wrong_comparison = "wrong_comparison"
    accumulator_reset = "accumulator_reset"
    wrong_operator = "wrong_operator"
    missing_edge_single = "missing_edge_single"
    hardcoded_output = "hardcoded_output"


class FailureClass(str, Enum):
    empty = "empty"
    single_element = "single_element"
    duplicates = "duplicates"
    negatives = "negatives"
    large = "large"
    boundary = "boundary"
    general = "general"
