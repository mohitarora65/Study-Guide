from dataclasses import replace

import pytest

from study_guide.auth import IdentityError, authenticate_claims
from study_guide.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        allowed_domain="iiti.ac.in",
        admin_emails=frozenset({"admin@iiti.ac.in"}),
        user_key_secret="u" * 32,
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="s" * 24,
    )


def claims(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "email": "student@iiti.ac.in",
        "email_verified": True,
        "iss": "https://accounts.google.com",
        "sub": "google-subject-1",
    }
    values.update(overrides)
    return values


def test_allows_verified_college_email(settings: Settings) -> None:
    identity = authenticate_claims(claims(), settings)

    assert not identity.is_admin
    assert len(identity.user_key) == 64
    assert "student" not in identity.user_key


def test_domain_and_admin_comparison_are_case_insensitive(settings: Settings) -> None:
    identity = authenticate_claims(claims(email="ADMIN@IITI.AC.IN"), settings)

    assert identity.is_admin


@pytest.mark.parametrize(
    "email",
    [
        "student@notiiti.ac.in",
        "student@iiti.ac.in.example",
        "student+iiti.ac.in@example.com",
        "student@iiti.ac.in ",
        "stu dent@iiti.ac.in",
        "@iiti.ac.in",
        "student@@iiti.ac.in",
    ],
)
def test_rejects_non_exact_or_malformed_email(
    settings: Settings, email: str
) -> None:
    with pytest.raises(IdentityError):
        authenticate_claims(claims(email=email), settings)


@pytest.mark.parametrize("verified", [False, None, "true", 1])
def test_requires_boolean_verified_claim(settings: Settings, verified: object) -> None:
    with pytest.raises(IdentityError):
        authenticate_claims(claims(email_verified=verified), settings)


@pytest.mark.parametrize("name", ["email", "iss", "sub"])
def test_requires_identity_claims(settings: Settings, name: str) -> None:
    values = claims()
    values.pop(name)

    with pytest.raises(IdentityError):
        authenticate_claims(values, settings)


def test_user_key_is_stable_and_subject_specific(settings: Settings) -> None:
    first = authenticate_claims(claims(), settings).user_key
    repeated = authenticate_claims(claims(), settings).user_key
    different_subject = authenticate_claims(
        claims(sub="google-subject-2"), settings
    ).user_key
    different_secret = authenticate_claims(
        claims(), replace(settings, user_key_secret="v" * 32)
    ).user_key

    assert first == repeated
    assert first != different_subject
    assert first != different_secret
