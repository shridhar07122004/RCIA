from __future__ import annotations


RISK_RULES = [
    (("otp", "authentication", "password", "login", "authorize", "session"), "Security and access control", "Authentication flow changes can create bypasses or lockout issues.", "Verify verification ordering, session issuance, retry limits, and audit events."),
    (("payment", "checkout", "gateway", "transaction", "invoice"), "Transaction and integration", "Payment flow changes can affect provider contracts and transaction state.", "Test provider failures, retries, idempotency, and reconciliation paths."),
    (("database", "schema", "migration", "record", "storage"), "Data compatibility", "Data structure changes may affect existing records and migrations.", "Review migration safety, rollback behavior, and backward compatibility."),
    (("api", "client", "contract", "endpoint"), "API compatibility", "Contract changes may affect dependent clients.", "Version the contract or test every known consumer before release."),
]


def assess(change: str, modules: list[str], affected_count: int) -> list[dict]:
    text = f"{change} {' '.join(modules)}".lower()
    risks = []
    for keywords, name, reason, mitigation in RISK_RULES:
        matched = [word for word in keywords if word in text]
        if matched:
            risks.append({"name": name, "reason": reason, "mitigation": mitigation, "signals": matched[:4]})
    if affected_count >= 4:
        risks.append({"name": "Change surface", "reason": "Several requirements or modules may need coordinated updates.", "mitigation": "Break the work into traceable tasks and run regression tests across the affected modules.", "signals": [f"{affected_count} candidates"]})
    return risks
