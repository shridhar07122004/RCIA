from __future__ import annotations

import re
from dataclasses import dataclass


ID_PATTERN = re.compile(r"\b((?:FR|NFR|BR|SR|REQ)[-_ ]?\d{1,4})\b", re.IGNORECASE)
REQUIREMENT_WORDS = re.compile(r"\b(shall|must|required to|should|can|allow|enable|support|provide|system|users?)\b", re.IGNORECASE)
REF_PATTERN = re.compile(r"\b((?:FR|NFR|BR|SR|REQ)[-_ ]?\d{1,4})\b", re.IGNORECASE)


@dataclass
class ExtractedRequirement:
    code: str
    description: str
    category: str
    module: str
    source_reference: str
    references: list[str]


def _category(code: str, text: str) -> str:
    lowered = text.lower()
    if code.upper().startswith("NFR") or any(word in lowered for word in ("secure", "performance", "availability", "privacy", "scalab")):
        return "Non-functional"
    if code.upper().startswith("BR"):
        return "Business"
    return "Functional"


def _module(text: str) -> str:
    lowered = text.lower()
    mapping = {
        "Authentication": ("login", "password", "otp", "authentication", "authorize", "session"),
        "Account recovery": ("reset", "recover", "verification email", "mobile number"),
        "Payments": ("payment", "checkout", "transaction", "gateway", "invoice"),
        "Reporting": ("report", "export", "dashboard", "analytics"),
        "Data management": ("database", "record", "profile", "data", "storage"),
        "Notifications": ("email", "sms", "notification", "alert"),
    }
    for module, keywords in mapping.items():
        if any(keyword in lowered for keyword in keywords):
            return module
    return "General"


def extract_requirements(text: str) -> list[ExtractedRequirement]:
    lines = [line.strip(" \t•*-\r") for line in text.splitlines()]
    candidates: list[tuple[str | None, str, str]] = []
    for index, line in enumerate(lines):
        if not line or len(line) < 12:
            continue
        match = ID_PATTERN.search(line)
        description = line[match.end():].strip(" :-–—") if match else line
        numbered = bool(re.match(r"^\d+[.)]\s+", line))
        likely = bool(match or numbered or REQUIREMENT_WORDS.search(description))
        if not likely or len(description) < 10:
            continue
        if match:
            code = re.sub(r"[ _]+", "-", match.group(1).upper())
        else:
            code = None
        source = f"Line {index + 1}"
        candidates.append((code, description.rstrip(".;"), source))

    if not candidates:
        # A paragraph-level fallback keeps extraction useful for SRS files with prose sections.
        for index, paragraph in enumerate(re.split(r"\n\s*\n", text)):
            paragraph = " ".join(paragraph.split())
            if len(paragraph) >= 30 and REQUIREMENT_WORDS.search(paragraph):
                candidates.append((None, paragraph[:2000], f"Paragraph {index + 1}"))

    results: list[ExtractedRequirement] = []
    used_codes: set[str] = set()
    auto_number = 1
    for code, description, source in candidates:
        if code is None:
            while f"AUTO-{auto_number:03d}" in used_codes:
                auto_number += 1
            code = f"AUTO-{auto_number:03d}"
            auto_number += 1
        if code in used_codes:
            continue
        used_codes.add(code)
        refs = [re.sub(r"[ _]+", "-", ref.upper()) for ref in REF_PATTERN.findall(description) if ref.upper() != code]
        results.append(ExtractedRequirement(code, description, _category(code, description), _module(description), source, refs))
    return results
