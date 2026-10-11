"""Fetch a learner's PUBLIC LeetCode profile sections via LeetCode's unofficial GraphQL API.

Ported from codequest_leetcode_rag/leetcode_client.py with Backend changes:
  - username validation, injectable HTTP session (tests never touch the network)
  - >= 1 s between calls (plan §1.6; the original used 0.35 s)
  - 20 recent accepted submissions (matches the README; the original asked for 50)
  - user-triggered, single-profile only: no crawling, no private data, no other learners' submissions.
[VERIFY] LeetCode's GraphQL schema and terms can change without notice; organisers' OK for live data (plan §1.6).
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timezone

import requests

GRAPHQL_URL = "https://leetcode.com/graphql"
MIN_INTERVAL_S = 1.0
REQUEST_TIMEOUT_S = 25
RECENT_LIMIT = 20
_USERNAME = re.compile(r"^[A-Za-z0-9_-]{1,40}$")

HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com/",
    "Origin": "https://leetcode.com",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0 Safari/537.36"
    ),
}

QUERIES = {
    "profile": """
        query($u: String!) {
          matchedUser(username: $u) {
            username githubUrl twitterUrl linkedinUrl
            profile {
              ranking userAvatar realName aboutMe school countryName
              company jobTitle skillTags reputation location
            }
            badges { id displayName icon creationDate }
            submitStats {
              acSubmissionNum { difficulty count submissions }
              totalSubmissionNum { difficulty count submissions }
            }
          }
        }
    """,
    "languages": """
        query($u: String!) {
          matchedUser(username: $u) { languageProblemCount { languageName problemsSolved } }
        }
    """,
    "topics": """
        query($u: String!) {
          matchedUser(username: $u) {
            tagProblemCounts {
              fundamental { tagName tagSlug problemsSolved }
              intermediate { tagName tagSlug problemsSolved }
              advanced { tagName tagSlug problemsSolved }
            }
          }
        }
    """,
    "activity": """
        query($u: String!) {
          matchedUser(username: $u) { userCalendar { activeYears streak totalActiveDays submissionCalendar } }
        }
    """,
    "recent_accepted": """
        query($u: String!, $limit: Int!) {
          recentAcSubmissionList(username: $u, limit: $limit) { title titleSlug timestamp lang }
        }
    """,
    "contest": """
        query($u: String!) {
          userContestRanking(username: $u) { rating globalRanking attendedContestsCount topPercentage }
        }
    """,
    "available_questions": """
        query { allQuestionsCount { difficulty count } }
    """,
}


class ProfileNotFound(ValueError):
    pass


def valid_username(username: str) -> bool:
    return bool(_USERNAME.match((username or "").strip()))


def _graphql(session, query: str, variables: dict | None = None) -> tuple[dict, list[str]]:
    """Return partial data as well as any GraphQL errors."""
    response = session.post(GRAPHQL_URL, json={"query": query, "variables": variables or {}},
                            timeout=REQUEST_TIMEOUT_S)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Unexpected GraphQL response format.")
    errors = [str(item.get("message", item)) for item in (payload.get("errors") or [])]
    return payload.get("data") or {}, errors  # keep partial data even when errors are reported


def fetch_profile(username: str, session=None, sleep=time.sleep) -> dict:
    username = (username or "").strip()
    if not valid_username(username):
        raise ValueError("LeetCode username must be 1-40 letters, digits, '_' or '-'.")

    result = {
        "username": username, "fetched_at": datetime.now(timezone.utc).isoformat(),
        "profile": {}, "social_links": {}, "solved_stats": [], "total_submission_stats": [],
        "available_questions": [], "badges": [], "languages": [], "topics": {}, "activity": {},
        "recent_accepted": [], "contest": None, "section_status": {}, "fetch_warnings": [],
    }
    own_session = session is None
    if own_session:
        session = requests.Session()
        session.headers.update(HEADERS)

    def fetch_section(name, variables, extractor):
        """Fetch one section without blocking the others."""
        try:
            data, errors = _graphql(session, QUERIES[name], variables)
            for message in errors:
                result["fetch_warnings"].append(f"{name} GraphQL warning: {message}")
            value = extractor(data)
            result[name] = value
            if errors:
                result["section_status"][name] = "partial" if value not in (None, {}, []) else "error"
            elif value is None or value == {} or value == []:
                result["section_status"][name] = "empty_or_unavailable"
            else:
                result["section_status"][name] = "ok"
            return value
        except Exception as exc:  # noqa: BLE001
            result["section_status"][name] = "error"
            result["fetch_warnings"].append(f"{name}: {type(exc).__name__}: {exc}")
            return None

    try:
        user = fetch_section("profile", {"u": username}, lambda d: d.get("matchedUser"))
        if not user:
            raise ProfileNotFound(f"No accessible public profile found for '{username}'. "
                                  "Check the username and try again.")
        result["username"] = user.get("username") or username
        result["profile"] = user.get("profile") or {}
        result["social_links"] = {k: user.get(k) for k in ("githubUrl", "twitterUrl", "linkedinUrl") if user.get(k)}
        stats = user.get("submitStats") or {}
        result["solved_stats"] = stats.get("acSubmissionNum") or []
        result["total_submission_stats"] = stats.get("totalSubmissionNum") or []
        result["badges"] = user.get("badges") or []
        result["section_status"]["profile"] = "ok" if result["profile"] or result["solved_stats"] else "partial"

        u = {"u": result["username"]}
        tasks = [
            ("languages", u, lambda d: (d.get("matchedUser") or {}).get("languageProblemCount") or []),
            ("topics", u, lambda d: (d.get("matchedUser") or {}).get("tagProblemCounts") or {}),
            ("activity", u, lambda d: (d.get("matchedUser") or {}).get("userCalendar") or {}),
            ("recent_accepted", {**u, "limit": RECENT_LIMIT}, lambda d: d.get("recentAcSubmissionList") or []),
            ("contest", u, lambda d: d.get("userContestRanking") or None),
            ("available_questions", {}, lambda d: d.get("allQuestionsCount") or []),
        ]
        for name, variables, extractor in tasks:
            sleep(MIN_INTERVAL_S)
            fetch_section(name, variables, extractor)
    finally:
        if own_session:
            session.close()
    return result
