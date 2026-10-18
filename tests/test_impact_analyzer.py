from types import SimpleNamespace

from app.services.impact_analyzer import analyze


def requirements():
    return [
        SimpleNamespace(id=1, code="FR-01", requirement_code="FR-01", description="Users can log in using email and password.", category="Functional", module="Authentication", references=[]),
        SimpleNamespace(id=2, code="FR-02", requirement_code="FR-02", description="The system validates the user's password before starting a session.", category="Functional", module="Authentication", references=[]),
        SimpleNamespace(id=3, code="FR-03", requirement_code="FR-03", description="Users can reset their password through email.", category="Functional", module="Account recovery", references=[]),
        SimpleNamespace(id=4, code="FR-04", requirement_code="FR-04", description="The system manages authenticated user sessions after successful login.", category="Functional", module="Authentication", references=[]),
        SimpleNamespace(id=5, code="NFR-01", requirement_code="NFR-01", description="The system must protect sensitive user information during authentication.", category="Non-functional", module="Authentication", references=[]),
    ]


def test_otp_change_identifies_explainable_candidates_without_model():
    result = analyze(requirements(), "Add OTP verification after password validation during login.", "add")
    assert result["impacts"]
    assert any(item["requirement_code"] in {"FR-01", "FR-02", "FR-04"} for item in result["impacts"])
    assert all(item["explanation"] and item["evidence"] for item in result["impacts"])
    assert result["test_cases"]


def test_unrelated_change_has_no_forced_results():
    result = analyze(requirements(), "Add a campus cafeteria menu search feature.", "add")
    assert result["summary"].startswith("No strong impact") or result["impacts"] == []
