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

# TODO [BE]: Outcome, MistakeClass, FailureClass (freeze at T+0:45)
