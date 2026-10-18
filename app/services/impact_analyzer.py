from __future__ import annotations

from dataclasses import asdict

from app.config import HIGH_IMPACT_THRESHOLD, LOW_IMPACT_THRESHOLD, MODEL_NAME, SCORING_WEIGHTS
from app.services.dependency_analyzer import build_dependency_graph, related_strength
from app.services.effort_estimator import estimate
from app.services.explanation_service import explain
from app.services.risk_analyzer import assess
from app.services.semantic_analyzer import compare, fallback_notice
from app.services.test_case_generator import generate
from app.services.text_preprocessor import keyword_score, keywords


DOMAIN_RULES = {
    "Authentication": {"otp", "2fa", "two-factor", "verification", "login", "password", "session", "authorize"},
    "Payments": {"payment", "checkout", "gateway", "transaction", "invoice"},
    "Reporting": {"report", "export", "dashboard", "analytics"},
    "Account recovery": {"reset", "recover", "password", "email", "mobile"},
}


def _domain_rule(change: str, requirement) -> float:
    terms = DOMAIN_RULES.get(requirement.module, set())
    if not terms:
        return 0.0
    change_terms = keywords(change)
    matched = change_terms & terms
    if not matched:
        return 0.0
    # Module context is a defensible rule signal, not a claim that the behavior must change.
    return min(0.75, 0.3 + 0.12 * len(matched))


def _severity(score: float) -> str:
    if score >= HIGH_IMPACT_THRESHOLD:
        return "High"
    if score >= LOW_IMPACT_THRESHOLD:
        return "Medium"
    return "Low"


def analyze(requirements, change: str, change_type: str, target_code: str | None = None) -> dict:
    descriptions = [item.description for item in requirements]
    semantic_scores, model_mode = compare(change, descriptions, MODEL_NAME)
    graph, edges = build_dependency_graph(requirements)
    change_keywords = keywords(change)
    impacts = []
    target_index = next((i for i, item in enumerate(requirements) if item.code == target_code), None)
    for index, requirement in enumerate(requirements):
        semantic = semantic_scores[index]
        lexical_kw_score = keyword_score(change, requirement.description)
        domain_rule_score = _domain_rule(change, requirement)
        kw_score = max(lexical_kw_score, domain_rule_score)
        shared = sorted(change_keywords & keywords(requirement.description))
        explicit = 1.0 if target_code and requirement.code == target_code else 0.0
        dependency_score, dependency_evidence = (0.0, None)
        if target_code:
            dependency_score, dependency_evidence = related_strength(graph, target_code, requirement.code)
        if target_code and target_index is not None and index == target_index:
            dependency_score = max(dependency_score, 1.0)
        score = sum((semantic * SCORING_WEIGHTS["semantic"], kw_score * SCORING_WEIGHTS["keywords"], dependency_score * SCORING_WEIGHTS["dependency"], explicit * SCORING_WEIGHTS["explicit"]))
        # A selected target is always reviewed, while unrelated low-signal requirements are omitted.
        if score < LOW_IMPACT_THRESHOLD and not (target_code and requirement.code == target_code):
            continue
        if target_code and requirement.code == target_code:
            impact_type = "direct"
        elif dependency_score > 0:
            impact_type = "indirect"
        elif semantic >= HIGH_IMPACT_THRESHOLD or kw_score >= 0.2:
            impact_type = "direct"
        else:
            impact_type = "possible"
        confidence = min(1.0, 0.45 * semantic + 0.25 * kw_score + 0.2 * dependency_score + 0.1 * explicit)
        signals = {"semantic_similarity": round(semantic, 3), "keyword_relevance": round(kw_score, 3), "domain_rule": round(domain_rule_score, 3), "dependency_strength": round(dependency_score, 3), "explicit_reference": round(explicit, 3), "shared_keywords": shared}
        explanation, evidence, action = explain(change, requirement, impact_type, signals, dependency_evidence)
        impacts.append({"requirement_id": requirement.id, "requirement_code": requirement.code, "description": requirement.description, "module": requirement.module, "category": requirement.category, "impact_type": impact_type, "impact_score": round(score, 3), "severity": _severity(score), "confidence": round(confidence, 3), "similarity": round(semantic, 3), "explanation": explanation, "evidence": evidence, "recommended_action": action, "signals": signals})
    impacts.sort(key=lambda item: item["impact_score"], reverse=True)
    direct = sum(item["impact_type"] == "direct" for item in impacts)
    indirect = sum(item["impact_type"] == "indirect" for item in impacts)
    possible = sum(item["impact_type"] == "possible" for item in impacts)
    modules = sorted({item["module"] for item in impacts})
    risks = assess(change, modules, len(impacts))
    effort = estimate(direct, indirect, possible, len(modules), change_type)
    summary = (f"{direct} direct, {indirect} indirect, and {possible} possible impact candidates identified across {len(modules)} module(s)." if impacts else "No strong impact detected. The available evidence did not cross the configured impact threshold; review the proposed change with a domain owner.")
    recommendations = [item["recommended_action"] for item in impacts[:5]]
    if not recommendations:
        recommendations = ["Validate the proposed change with a product owner and add explicit requirement references if a relationship is confirmed."]
    return {"summary": summary, "overall_risk": "High" if len(risks) >= 3 or direct >= 4 else "Medium" if risks or impacts else "Low", "total_requirements": len(requirements), "requirements_considered": [{"requirement_code": item.code, "description": item.description, "module": item.module, "category": item.category} for item in requirements], "counts": {"direct": direct, "indirect": indirect, "possible": possible}, "modules": modules, "impacts": impacts, "dependencies": [asdict(edge) for edge in edges if any(item["requirement_code"] in {edge.source, edge.target} for item in impacts)], "risks": risks, "effort": effort, "recommendations": recommendations, "test_cases": generate(change, impacts, change_type), "analysis_mode": model_mode, "fallback_notice": fallback_notice(model_mode), "scoring": {"weights": SCORING_WEIGHTS, "thresholds": {"low": LOW_IMPACT_THRESHOLD, "high": HIGH_IMPACT_THRESHOLD}}}
