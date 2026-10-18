from __future__ import annotations


def generate(change: str, impacts: list[dict], change_type: str) -> list[dict]:
    lower = change.lower()
    cases = []
    if any(word in lower for word in ("otp", "two-factor", "2fa", "verification")):
        cases.extend([
            ("Valid verification", "A user is eligible and has a valid verification code.", "Complete the primary flow and submit a valid code.", "The user proceeds only after successful verification.", "Functional"),
            ("Invalid verification", "A user has reached the verification step.", "Submit an incorrect code, then observe the response.", "Access is denied, an actionable message is shown, and no session is issued.", "Negative"),
            ("Expired or reused code", "An expired or previously used code exists.", "Submit the expired or reused code.", "The code is rejected and the user can request a safe replacement.", "Security"),
            ("Excessive attempts", "A verification challenge is active.", "Submit invalid codes until the configured limit is reached.", "Further attempts are throttled or blocked and the event is recorded.", "Security"),
        ])
    elif any(word in lower for word in ("payment", "checkout", "gateway")):
        cases.extend([
            ("Successful transaction", "A valid cart and payment method exist.", "Complete checkout with a successful provider response.", "The order is recorded once and the user sees confirmation.", "Integration"),
            ("Provider failure", "The provider returns a failure or timeout.", "Submit checkout and simulate a provider failure.", "The user receives a clear failure state and no duplicate charge is recorded.", "Negative"),
        ])
    else:
        cases.extend([
            ("Updated behavior succeeds", "Required data and permissions are available.", "Execute the changed workflow using valid input.", "The updated behavior matches the proposed requirement and preserves expected output.", "Functional"),
            ("Invalid input remains safe", "The workflow is available.", "Exercise missing, malformed, or unauthorized input.", "The system rejects invalid input without data loss or unintended access.", "Negative"),
        ])
    primary_id = impacts[0].get("requirement_id") if impacts else None
    return [{"test_case_id": f"TC-{index:03d}", "objective": objective, "preconditions": preconditions, "steps": steps, "expected_result": expected, "related_requirement_id": primary_id, "category": category} for index, (objective, preconditions, steps, expected, category) in enumerate(cases, 1)]
