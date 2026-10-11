"""Turn a fetched profile into section-tagged documents, and map questions to likely sections.

Pure functions (no Chroma, no network) so they are unit-testable. Ported from rag_store.py; documents now carry
the CodeQuest `user_id` in metadata so retrieval and delete-all are per learner.
"""
from __future__ import annotations

import hashlib
import json


def _json_text(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _stable_id(user_id: str, section: str, text: str) -> str:
    return hashlib.sha256(f"{user_id}|{section}|{text}".encode("utf-8")).hexdigest()


def profile_to_documents(profile: dict, user_id: str) -> list[dict]:
    username = profile["username"]
    docs: list[dict] = []

    def add(section: str, title: str, payload):
        body = payload if isinstance(payload, str) else _json_text(payload)
        text = (f"LeetCode username: {username}\nSection: {section}\nTitle: {title}\nData:\n{body}")
        docs.append({"id": _stable_id(user_id, section, text), "text": text,
                     "metadata": {"user_id": user_id, "username": username.lower(),
                                  "section": section, "title": title}})

    add("overview", "Public profile overview", profile.get("profile") or {})
    add("social_links", "Public social links", profile.get("social_links") or {})
    add("solved_stats", "Accepted problems solved by difficulty", profile.get("solved_stats") or [])
    add("submission_stats", "Total submissions by difficulty", profile.get("total_submission_stats") or [])
    add("available_questions", "Available LeetCode questions by difficulty", profile.get("available_questions") or [])

    badges = profile.get("badges") or []
    if badges:
        for badge in badges:
            add("badges", f"Earned badge: {badge.get('displayName', 'Unknown')}", badge)
    else:
        add("badges", "Badge information", "No badges were returned.")

    languages = profile.get("languages") or []
    if languages:
        for item in languages:
            add("languages", f"Problems solved using {item.get('languageName', 'Unknown')}", item)
    else:
        add("languages", "Programming language statistics", "No language statistics were returned by the API.")

    topics = profile.get("topics") or {}
    topic_count = 0
    if isinstance(topics, dict):
        for level, items in topics.items():
            if not isinstance(items, list):
                continue
            for topic in items:
                topic_count += 1
                add("topics", f"Topic: {topic.get('tagName', 'Unknown topic')} ({level})", {"level": level, **topic})
    if topic_count == 0:
        add("topics", "Topic-wise problem statistics", "No topic statistics were returned by the API.")

    activity = profile.get("activity") or {}
    if activity:
        add("activity", "Activity, streak and active days",
            {k: v for k, v in activity.items() if k != "submissionCalendar"})
        calendar = activity.get("submissionCalendar")
        if calendar:
            try:
                data = json.loads(calendar) if isinstance(calendar, str) else calendar
                if isinstance(data, dict):
                    active = [int(ts) for ts, count in data.items() if int(count or 0) > 0]
                    summary = {"total_calendar_submissions": sum(int(v or 0) for v in data.values()),
                               "active_calendar_days": len(active),
                               "note": "These are counts derived from the returned submission calendar, "
                                       "not total accepted problems."}
                    if active:
                        summary["latest_active_date_timestamp"] = max(active)
                    add("activity_calendar", "Submission calendar summary", summary)
                else:
                    add("activity_calendar", "Submission calendar", "The API returned an unexpected calendar format.")
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                add("activity_calendar", "Submission calendar", f"Could not parse calendar data: {exc}")
    else:
        add("activity", "Activity statistics", "No activity information was returned by the API.")

    recent = profile.get("recent_accepted") or []
    if recent:
        for item in recent:
            add("recent_accepted", f"Recent accepted problem: {item.get('title', 'Unknown')}", item)
    else:
        add("recent_accepted", "Recent accepted problems", "No recent accepted submissions were returned.")

    contest = profile.get("contest")
    if contest:
        add("contest", "Contest rating and ranking", contest)
    else:  # None means no ranking object was returned; it is not "rating 0"
        add("contest", "Contest rating and ranking",
            "Contest ranking data was not returned. This does not prove the user has never participated.")

    if profile.get("section_status"):
        add("section_status", "Fetch status for each section", profile["section_status"])
    if profile.get("fetch_warnings"):
        add("fetch_warnings", "Fetch warnings and API errors", profile["fetch_warnings"])
    return docs


def question_sections(question: str) -> list[str]:
    """Map question keywords to likely relevant sections (targeted retrieval on top of semantic search)."""
    q = question.lower()
    sections: list[str] = []

    def has_any(*words):
        return any(w in q for w in words)

    if has_any("language", "languages", "python", "java", "c++", "javascript"):
        sections += ["languages"]
    if has_any("topic", "topics", "pattern", "patterns", "weakness", "weaknesses"):
        sections += ["topics", "solved_stats"]
    if has_any("contest", "rating", "global ranking", "attended contests"):
        sections += ["contest"]
    if has_any("streak", "active day", "activity", "calendar", "consistency"):
        sections += ["activity", "activity_calendar"]
    if has_any("recent", "latest", "last solved", "accepted problem"):
        sections += ["recent_accepted"]
    if has_any("badge", "badges", "achievement"):
        sections += ["badges"]
    if has_any("submission", "acceptance rate", "accepted vs", "attempts"):
        sections += ["submission_stats", "solved_stats"]
    if has_any("solved", "problems", "difficulty", "easy", "medium", "hard"):
        sections += ["solved_stats", "available_questions"]
    if has_any("profile", "username", "location", "school", "company", "overview"):
        sections += ["overview", "social_links"]
    return list(dict.fromkeys(sections))


def summarize(profile: dict) -> dict:
    """Small, structured summary for the dashboard (no free text from the profile)."""
    solved = {s.get("difficulty"): s.get("count") for s in profile.get("solved_stats") or []}
    langs = sorted(profile.get("languages") or [], key=lambda x: -(x.get("problemsSolved") or 0))[:3]
    contest = profile.get("contest") or {}
    activity = profile.get("activity") or {}
    return {
        "username": profile.get("username"),
        "fetched_at": profile.get("fetched_at"),
        "solved": solved,
        "top_languages": [{"language": x.get("languageName"), "solved": x.get("problemsSolved")} for x in langs],
        "contest_rating": round(contest["rating"]) if contest.get("rating") is not None else None,
        "streak": activity.get("streak"),
        "total_active_days": activity.get("totalActiveDays"),
        "sections": profile.get("section_status", {}),
    }
