import os
from pathlib import Path

try:  # optional: read the untracked repo-root .env (real environment variables always win)
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:
    pass


def _flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, "1" if default else "0") == "1"


MOCK = _flag("MOCK")
API_TOKEN = os.getenv("API_TOKEN", "change-me")
CORS_ORIGINS = [o for o in os.getenv("CORS_ORIGINS", "").split(",") if o]
# The extension calls through its service worker, but allow any extension origin for direct fetches.
CORS_ORIGIN_REGEX = os.getenv("CORS_ORIGIN_REGEX", r"^chrome-extension://[a-p]{32}$")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/codequest.db")
SANDBOX_MODE = os.getenv("SANDBOX_MODE", "auto")  # docker | native | remote | auto
SANDBOX_URL = os.getenv("SANDBOX_URL", "http://sandbox:9000")
SANDBOX_TOKEN = os.getenv("SANDBOX_TOKEN", "sandbox-dev-token")  # shared with the sandbox service
DAILY_ANALYZE_CAP = int(os.getenv("DAILY_ANALYZE_CAP", "300"))  # per user per UTC day
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "60"))

# Feature flags: unfinished work merges behind a flag defaulting to off.
FEATURE_CHAT = _flag("FEATURE_CHAT")
FEATURE_PROFILE_RAG = _flag("FEATURE_PROFILE_RAG")  # LeetCode profile RAG (needs requirements/profile_rag.txt)
FEATURE_CREW = _flag("FEATURE_CREW")  # AI crew: explain / generated tests / debug / trace / LLM hints (needs GEMINI_API_KEY for the LLM parts)
CREW_ALLOW_FIX_CODE = _flag("CREW_ALLOW_FIX_CODE")  # the Debugger may return a corrected full solution (off: product rule = no full solutions)
FEATURE_MEMORY = _flag("FEATURE_MEMORY")
FEATURE_PROFILE = _flag("FEATURE_PROFILE")
FEATURE_VOICE_AGENT = _flag("FEATURE_VOICE_AGENT")
FEATURE_ORACLE_FOREIGN = _flag("FEATURE_ORACLE_FOREIGN")
USE_REAL_AI = _flag("USE_REAL_AI")
USE_REAL_VOICE = _flag("USE_REAL_VOICE")
USE_REAL_ENGINE = _flag("USE_REAL_ENGINE")

# LeetCode profile RAG (ported from codequest_leetcode_rag). Keys live in the untracked .env only.
CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/chroma")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
PROFILE_SYNC_MIN_INTERVAL_S = int(os.getenv("PROFILE_SYNC_MIN_INTERVAL_S", "600"))  # be gentle with LeetCode

# Per-learner authentication for chat / profile endpoints (X-User-Token issued by POST /users).
# Off by default so existing clients keep working; turn on for any shared deployment.
REQUIRE_USER_TOKEN = _flag("REQUIRE_USER_TOKEN")
PROFILE_SNAPSHOT_DIR = os.getenv("PROFILE_SNAPSHOT_DIR", "./data/profiles")  # profile_<username>.json (git-ignored)
FEATURE_DEV_UI = _flag("FEATURE_DEV_UI")  # serves backend/app/static/dev_chat.html at /dev/ (manual testing only)
