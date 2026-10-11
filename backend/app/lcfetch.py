"""Fetch a PUBLIC LeetCode problem by URL (server side, no cookies) and turn it into an LCProblem.

Only https://leetcode.com/problems/<slug>/ URLs are accepted (host allowlist: no SSRF). The page itself is never
scraped; the same public GraphQL `question` query the extension uses is called, rate-limited to 1 request/second.
[VERIFY] LeetCode's unofficial GraphQL schema can change without notice.
"""
from __future__ import annotations

import hashlib
import html
import re
import threading
import time
from urllib.parse import urlparse

import requests

from .contracts.models import Example, LCProblem

GRAPHQL_URL = "https://leetcode.com/graphql"
TIMEOUT_S = 20
MIN_INTERVAL_S = 1.0
MAX_STATEMENT = 8000
_SLUG = re.compile(r"^/problems/([a-z0-9][a-z0-9-]{0,100})(?:/|$)")
_lock = threading.Lock()
_last = 0.0

QUERY = """query q($s: String!) { question(titleSlug: $s) {
  titleSlug title difficulty content topicTags { name } codeSnippets { langSlug code } } }"""
HEADERS = {"Content-Type": "application/json", "Referer": "https://leetcode.com/", "Origin": "https://leetcode.com",
           "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36"}


class FetchError(Exception):
    pass


def slug_from_url(url: str) -> str:
    try:
        u = urlparse((url or "").strip())
    except ValueError as e:
        raise FetchError("invalid URL") from e
    if u.scheme != "https" or (u.hostname or "").lower() not in ("leetcode.com", "www.leetcode.com"):
        raise FetchError("only https://leetcode.com/problems/<name>/ links are supported")
    m = _SLUG.match(u.path)
    if not m:
        raise FetchError("not a LeetCode problem link (expected https://leetcode.com/problems/<name>/)")
    return m.group(1)


def _text(content_html: str) -> str:
    t = re.sub(r"(?i)<sup>(.*?)</sup>", lambda m: "^" + m.group(1), content_html or "")
    t = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</pre>|</ul>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t).replace("\xa0", " ")
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", t)).strip()


_EX = re.compile(r"Input:\s*(.+?)\s*Output:\s*(.+?)(?=\n\s*(?:Explanation:|Example\s*\d|Constraints:)|\n\n|\Z)", re.S)


def parse_content(content_html: str) -> tuple[str, list[Example], str]:
    """-> (statement, examples, constraints)."""
    text = _text(content_html)
    constraints = ""
    m = re.search(r"Constraints:\s*(.*?)(?=\n\s*Follow[- ]up|\Z)", text, re.S | re.I)
    if m:
        constraints = m.group(1).strip()
    examples = [Example(input_text=a.strip().replace("\n", " "), output_text=b.strip().split("\n")[0].strip())
                for a, b in _EX.findall(text)][:6]
    first_example = re.search(r"\n\s*Example\s*1", text)
    statement = (text[:first_example.start()] if first_example else text).strip()
    return statement[:MAX_STATEMENT], examples, constraints[:1500]


def fetch_problem(url: str) -> LCProblem:
    global _last
    slug = slug_from_url(url)
    with _lock:
        wait = MIN_INTERVAL_S - (time.monotonic() - _last)
        if wait > 0:
            time.sleep(wait)
        _last = time.monotonic()
    try:
        r = requests.post(GRAPHQL_URL, json={"query": QUERY, "variables": {"s": slug}}, headers=HEADERS, timeout=TIMEOUT_S)
        r.raise_for_status()
        q = (r.json().get("data") or {}).get("question")
    except (requests.RequestException, ValueError) as e:
        raise FetchError("could not reach LeetCode") from e
    if not q:
        raise FetchError("LeetCode returned no problem for this link")
    statement, examples, constraints = parse_content(q.get("content") or "")
    if not statement:
        raise FetchError("this problem has no readable statement (premium or interactive?)")
    starter = next((s["code"] for s in q.get("codeSnippets") or [] if s.get("langSlug") == "python3"), None)
    return LCProblem(slug=q["titleSlug"], title=q["title"], difficulty=q.get("difficulty") or "Unknown",
                     tags=[t["name"] for t in q.get("topicTags") or []], statement_text=statement, examples=examples,
                     constraints_text=constraints, starter_python=starter, lang_selected="python3",
                     content_hash=hashlib.sha256((statement + "python3").encode()).hexdigest()[:32])
