"""MOCK=1 canned responses so Frontend/AI/Agents can build before real routers exist.

Shapes follow contracts/models.py and the examples in openapi.yaml. Never contains fuzz data.
"""
from fastapi import APIRouter, Response

from ..engine.lang import normalize_lang
from ..contracts.models import (AnalyzeResponse, CaptureResponse, Diagnosis,
                                Divergence, GuardResult, HintResult, LCProblem,
                                TestResult)

router = APIRouter(tags=["mock"])

EXAMPLE_ANALYZE = AnalyzeResponse(
    attempt_id=1,
    verified="oracle-verified",
    results=[
        TestResult(kind="example", outcome="passed", input="nums = [2,7,11,15], target = 9",
                   expected="[0,1]", actual="[0,1]"),
        TestResult(kind="fuzz", outcome="wrong_output", failure_class="single_element"),
    ],
    diagnosis=Diagnosis(
        mistake_class="missing_edge_single", confidence=0.86, failure_class="single_element",
        divergence=Divergence(iteration=2, variable="seen", expected={"2": 0}, actual={}, line=7)),
    explanation="Your loop skips the case where the list has a single element.",
    flags=[],
)


@router.post("/users")
def users():
    return {"user_id": "mock-user-1"}


@router.post("/problems/capture", response_model=CaptureResponse)
def capture(problem: LCProblem):
    # Mirrors the plan: only python3 is executed; other languages = explanation-only.
    if normalize_lang(problem.lang_selected) != "python3":
        return CaptureResponse(problem_id=problem.slug, slug=problem.slug, supported=False, reason="UNSUPPORTED_LANGUAGE")
    return CaptureResponse(problem_id=problem.slug, slug=problem.slug, supported=True)


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze():
    return EXAMPLE_ANALYZE


@router.post("/hint", response_model=HintResult)
def hint():
    return HintResult(level=1, text="Think about what you need to remember while scanning the list.",
                      guard=GuardResult(passed=True, retries=0, source="template"))


@router.get("/dashboard/{user_id}")
def dashboard(user_id: str):
    return {"user_id": user_id, "mastery": {"arrays": 1210, "hashing": 1185},
            "mistakes": {"missing_edge_single": 2}, "recent": [], "verified": {"oracle-verified": 1, "unverified": 0}}


@router.get("/recommend/{user_id}")
def recommend(user_id: str):
    return {"slug": "binary-search", "title": "Binary Search", "reason": "weakest concept: boundaries"}


@router.post("/tts")
def tts(response: Response):
    response.headers["X-Cache"] = "miss"
    return {"fallback": "browser_tts"}
