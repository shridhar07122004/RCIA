from __future__ import annotations


def explain(change: str, requirement, impact_type: str, signals: dict, dependency_evidence: str | None) -> tuple[str, str, str]:
    evidence_parts = [f"{requirement.requirement_code}: {requirement.description}"]
    if dependency_evidence:
        evidence_parts.append(dependency_evidence)
    shared = signals.get("shared_keywords", [])
    if shared:
        evidence_parts.append(f"Shared terms: {', '.join(shared[:6])}")
    evidence = " | ".join(evidence_parts)
    if impact_type == "direct":
        explanation = f"The proposed change directly overlaps with {requirement.requirement_code} in the {requirement.module.lower()} module. The behavior described by this requirement may need to change to accommodate the new flow. Verify the requirement wording, acceptance criteria, and any implementation path that owns this behavior."
        action = "Review and update this requirement's acceptance criteria, implementation tasks, and focused tests before coding."
    elif impact_type == "indirect":
        explanation = f"{requirement.requirement_code} is connected through a documented or inferred dependency. A change to the proposed behavior could propagate to this related {requirement.module.lower()} behavior even though its text is not the primary match. Verify the dependency path with the module owner."
        action = "Trace the dependency path, confirm whether the contract changes, and add regression coverage if it does."
    else:
        explanation = f"{requirement.requirement_code} has related language or module context, but the available evidence is not strong enough to claim a definite impact. Treat it as a review candidate and confirm with the product and engineering owners."
        action = "Ask a domain owner to verify this relationship; update only if the change alters this requirement's behavior."
    return explanation, evidence, action
