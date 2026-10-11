import os


def _flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, "1" if default else "0") == "1"


MOCK = _flag("MOCK")
API_TOKEN = os.getenv("API_TOKEN", "change-me")
CORS_ORIGINS = [o for o in os.getenv("CORS_ORIGINS", "").split(",") if o]
# The extension calls through its service worker, but allow any extension origin for direct fetches.
CORS_ORIGIN_REGEX = os.getenv("CORS_ORIGIN_REGEX", r"^chrome-extension://[a-p]{32}$")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/codequest.db")
SANDBOX_MODE = os.getenv("SANDBOX_MODE", "auto")  # docker | native | auto
DAILY_ANALYZE_CAP = int(os.getenv("DAILY_ANALYZE_CAP", "300"))  # per user per UTC day
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "60"))

# Feature flags: unfinished work merges behind a flag defaulting to off.
FEATURE_CHAT = _flag("FEATURE_CHAT")
FEATURE_MEMORY = _flag("FEATURE_MEMORY")
FEATURE_PROFILE = _flag("FEATURE_PROFILE")
FEATURE_VOICE_AGENT = _flag("FEATURE_VOICE_AGENT")
FEATURE_ORACLE_FOREIGN = _flag("FEATURE_ORACLE_FOREIGN")
USE_REAL_AI = _flag("USE_REAL_AI")
USE_REAL_VOICE = _flag("USE_REAL_VOICE")
USE_REAL_ENGINE = _flag("USE_REAL_ENGINE")
