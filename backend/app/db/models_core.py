"""[BE] Core tables (plan §6 Phase 1). No migrations: create_all() at startup.

Fuzz/hidden inputs are never stored here — test_results rows of kind="fuzz" keep only outcome + failure_class.
"""
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"
    user_id: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=_now)


class UserSettings(SQLModel, table=True):
    __tablename__ = "user_settings"
    user_id: str = Field(primary_key=True)
    settings_json: str = "{}"  # ui/mentor language, verbosity, voice/memory toggles


class LCProblemRow(SQLModel, table=True):
    __tablename__ = "lc_problems"
    slug: str = Field(primary_key=True)
    source: str = "leetcode"
    title: str
    difficulty: str
    content_hash: str = Field(index=True)
    lang_selected: str
    supported: bool = True
    reason: str | None = None
    payload_json: str  # full LCProblem (statement capped at 8,000 chars)
    captured_at: datetime = Field(default_factory=_now)


class Attempt(SQLModel, table=True):
    __tablename__ = "attempts"
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    problem_slug: str = Field(index=True)
    code: str
    language: str = "python3"
    verified: str = "unverified"
    passed_all: bool = False
    paste_chars: int = 0
    elapsed_ms: int = 0
    created_at: datetime = Field(default_factory=_now)


class TestResultRow(SQLModel, table=True):
    __tablename__ = "test_results"
    id: int | None = Field(default=None, primary_key=True)
    attempt_id: int = Field(index=True)
    kind: str
    outcome: str
    input: str | None = None
    expected: str | None = None
    actual: str | None = None
    error: str | None = None
    failure_class: str | None = None


class DiagnosisRow(SQLModel, table=True):
    __tablename__ = "diagnoses"
    id: int | None = Field(default=None, primary_key=True)
    attempt_id: int = Field(index=True)
    mistake_class: str | None = None
    confidence: float = 0.0
    failure_class: str | None = None
    divergence_json: str | None = None


class HintState(SQLModel, table=True):
    __tablename__ = "hint_state"
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    problem_slug: str = Field(index=True)
    max_level_given: int = 0
    updated_at: datetime = Field(default_factory=_now)


class HabitEvent(SQLModel, table=True):
    __tablename__ = "habit_events"
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    kind: str  # paste | run | first_run_delay ...
    value: float = 0.0
    problem_slug: str | None = None
    created_at: datetime = Field(default_factory=_now)


class ConceptMastery(SQLModel, table=True):
    __tablename__ = "concept_mastery"
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    concept: str
    rating: float = 1200.0


class UserMistakeCount(SQLModel, table=True):
    __tablename__ = "user_mistake_counts"
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    mistake_class: str
    count: int = 0


class ApiToken(SQLModel, table=True):
    __tablename__ = "api_tokens"
    token_hash: str = Field(primary_key=True)
    user_id: str | None = None
    created_at: datetime = Field(default_factory=_now)
