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
    fuzz_seed: int | None = None  # stored for reproducibility; never returned by any endpoint
    copy_flagged: bool = False
    mastery_pending: bool = False  # deferred until explain-back passes (Mastery.release_pending)
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
    fuzz_vector: str | None = None  # 0/1 pass-fail bits on the fixed fingerprint set (no inputs)


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


class LeetCodeProfileSnapshot(SQLModel, table=True):
    """The learner's last synced PUBLIC LeetCode profile (one per CodeQuest user). Wiped by delete-all."""
    __tablename__ = "leetcode_profile_snapshots"
    user_id: str = Field(primary_key=True)
    username: str
    payload_json: str
    docs_indexed: int = 0
    fetched_at: datetime = Field(default_factory=_now)


class ProfileConsent(SQLModel, table=True):
    """The learner's explicit permission to read their PUBLIC LeetCode profile for personalised chat."""
    __tablename__ = "profile_consents"
    user_id: str = Field(primary_key=True)
    granted: bool = False
    scope: str = "leetcode_public_profile"
    consent_version: str = "1"
    leetcode_username: str | None = None
    granted_at: datetime | None = None
    revoked_at: datetime | None = None


class ChatThread(SQLModel, table=True):
    __tablename__ = "chat_threads"
    id: str = Field(primary_key=True)
    user_id: str = Field(index=True)
    problem_slug: str = Field(index=True)
    title: str = ""
    language: str = "en"
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"
    id: int | None = Field(default=None, primary_key=True)
    thread_id: str = Field(index=True)
    role: str  # user | assistant
    content: str
    meta_json: str | None = None  # tools used, guard result, mode, sources (never hidden-test data)
    created_at: datetime = Field(default_factory=_now)


class LearnerContext(SQLModel, table=True):
    """The problem a learner is currently working on (set by the Explain tab, read by every other tab/endpoint)."""
    __tablename__ = "learner_context"
    user_id: str = Field(primary_key=True)
    problem_slug: str
    problem_url: str
    problem_title: str | None = None
    leetcode_username: str | None = None
    updated_at: datetime = Field(default_factory=_now)
