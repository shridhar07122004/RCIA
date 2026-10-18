from app.services.requirement_extractor import extract_requirements


def test_preserves_ids_and_generates_stable_auto_ids():
    text = """
    FR-01: Users can log in using email and password.
    2. The system must validate a password before creating a session.
    NFR-01: The system must protect sensitive user information.
    """
    requirements = extract_requirements(text)
    assert [item.code for item in requirements] == ["FR-01", "AUTO-001", "NFR-01"]
    assert requirements[1].category == "Functional"


def test_extracts_explicit_references_and_modules():
    requirements = extract_requirements("FR-01: Login leads to FR-04 sessions.\nFR-04: The system manages authenticated sessions.")
    assert requirements[0].references == ["FR-04"]
    assert requirements[0].module == "Authentication"
