from __future__ import annotations

import re


STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "when", "then", "than", "must", "shall",
    "system", "users", "user", "using", "allow", "able", "their", "can", "will", "should", "after", "before",
}


def normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def keywords(text: str) -> set[str]:
    return {token for token in normalize(text).split() if len(token) > 2 and token not in STOPWORDS}


def keyword_score(left: str, right: str) -> float:
    first, second = keywords(left), keywords(right)
    if not first or not second:
        return 0.0
    return len(first & second) / max(1, len(first | second))
