from copy import deepcopy
from pathlib import Path
import tomllib

import pytest

from study_guide.config import ConfigurationError, load_settings


def valid_secrets() -> dict[str, object]:
    return {
        "auth": {
            "redirect_uri": "http://localhost:8501/oauth2callback",
            "cookie_secret": "c" * 32,
            "client_id": "google-client-id",
            "client_secret": "google-client-secret-value",
            "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
        },
        "app": {
            "allowed_domain": "iiti.ac.in",
            "admin_emails": ["admin@iiti.ac.in"],
            "user_key_secret": "u" * 32,
        },
        "supabase": {
            "url": "https://project.supabase.co",
            "service_role_key": "s" * 24,
        },
    }


def test_loads_valid_settings() -> None:
    settings = load_settings(valid_secrets())

    assert settings.allowed_domain == "iiti.ac.in"
    assert settings.admin_emails == frozenset({"admin@iiti.ac.in"})
    assert settings.gemini_api_key is None
    assert settings.ai_star_api_key is None
    assert "admin@iiti.ac.in" not in repr(settings)
    assert "ssss" not in repr(settings)


def test_loads_optional_gemini_key_without_exposing_it() -> None:
    secrets = valid_secrets()
    secrets["gemini"] = {"api_key": "g" * 32}

    settings = load_settings(secrets)

    assert settings.gemini_api_key == "g" * 32
    assert "gggg" not in repr(settings)


def test_short_gemini_key_is_rejected() -> None:
    secrets = valid_secrets()
    secrets["gemini"] = {"api_key": "short"}

    with pytest.raises(ConfigurationError, match="gemini.api_key is too short"):
        load_settings(secrets)


def test_loads_optional_ai_star_key_without_exposing_it() -> None:
    secrets = valid_secrets()
    secrets["ai_star"] = {"api_key": "a" * 32}

    settings = load_settings(secrets)

    assert settings.ai_star_api_key == "a" * 32
    assert "aaaa" not in repr(settings)


def test_short_ai_star_key_is_rejected() -> None:
    secrets = valid_secrets()
    secrets["ai_star"] = {"api_key": "short"}

    with pytest.raises(ConfigurationError, match="ai_star.api_key is too short"):
        load_settings(secrets)


def test_missing_section_fails_safely() -> None:
    secrets = valid_secrets()
    secrets.pop("supabase")

    with pytest.raises(ConfigurationError, match="Missing configuration section"):
        load_settings(secrets)


def test_domain_cannot_be_reconfigured() -> None:
    secrets = deepcopy(valid_secrets())
    secrets["app"]["allowed_domain"] = "example.com"  # type: ignore[index]

    with pytest.raises(ConfigurationError, match="must be iiti.ac.in"):
        load_settings(secrets)


def test_admin_must_use_allowed_domain() -> None:
    secrets = deepcopy(valid_secrets())
    secrets["app"]["admin_emails"] = ["admin@example.com"]  # type: ignore[index]

    with pytest.raises(ConfigurationError, match="admin email"):
        load_settings(secrets)


@pytest.mark.parametrize(
    ("section", "key"),
    [
        ("auth", "cookie_secret"),
        ("app", "user_key_secret"),
        ("supabase", "service_role_key"),
    ],
)
def test_short_secrets_are_rejected(section: str, key: str) -> None:
    secrets = deepcopy(valid_secrets())
    secrets[section][key] = "short"  # type: ignore[index]

    with pytest.raises(ConfigurationError):
        load_settings(secrets)


def test_supabase_requires_https() -> None:
    secrets = deepcopy(valid_secrets())
    secrets["supabase"]["url"] = "http://project.supabase.co"  # type: ignore[index]

    with pytest.raises(ConfigurationError, match="HTTPS"):
        load_settings(secrets)


def test_streamlit_upload_limit_matches_pdf_validation() -> None:
    config = tomllib.loads(
        (Path(__file__).parents[1] / ".streamlit" / "config.toml").read_text()
    )

    assert config["server"]["maxUploadSize"] == 25
