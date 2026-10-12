from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from urllib.parse import urlparse


APPROVED_DOMAIN = "iiti.ac.in"
GOOGLE_METADATA_URL = "https://accounts.google.com/.well-known/openid-configuration"


class ConfigurationError(ValueError):
    """Raised when required operator configuration is missing or unsafe."""


@dataclass(frozen=True)
class Settings:
    allowed_domain: str
    admin_emails: frozenset[str] = field(repr=False)
    user_key_secret: str = field(repr=False)
    supabase_url: str
    supabase_service_role_key: str = field(repr=False)
    voyage_api_key: str | None = field(default=None, repr=False)
    ai_star_api_key: str | None = field(default=None, repr=False)


def _section(values: Mapping[str, object], name: str) -> Mapping[str, object]:
    section = values.get(name)
    if not isinstance(section, Mapping):
        raise ConfigurationError(f"Missing configuration section: {name}")
    return section


def _required_string(values: Mapping[str, object], path: str) -> str:
    value = values.get(path.rsplit(".", 1)[-1])
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"Missing configuration: {path}")
    if value != value.strip():
        raise ConfigurationError(f"Configuration contains outer whitespace: {path}")
    return value


def _validate_url(value: str, path: str, *, allow_local_http: bool = False) -> None:
    parsed = urlparse(value)
    local_http = allow_local_http and parsed.scheme == "http" and parsed.hostname in {
        "localhost",
        "127.0.0.1",
    }
    if not parsed.netloc or (parsed.scheme != "https" and not local_http):
        raise ConfigurationError(f"Configuration must use a valid HTTPS URL: {path}")


def load_settings(secrets: Mapping[str, object]) -> Settings:
    auth = _section(secrets, "auth")
    app = _section(secrets, "app")
    supabase = _section(secrets, "supabase")

    redirect_uri = _required_string(auth, "auth.redirect_uri")
    cookie_secret = _required_string(auth, "auth.cookie_secret")
    _required_string(auth, "auth.client_id")
    client_secret = _required_string(auth, "auth.client_secret")
    metadata_url = _required_string(auth, "auth.server_metadata_url")

    _validate_url(redirect_uri, "auth.redirect_uri", allow_local_http=True)
    if len(cookie_secret) < 32:
        raise ConfigurationError("auth.cookie_secret must contain at least 32 characters")
    if len(client_secret) < 16:
        raise ConfigurationError("auth.client_secret is too short")
    if metadata_url != GOOGLE_METADATA_URL:
        raise ConfigurationError("auth.server_metadata_url must be the Google OIDC endpoint")

    allowed_domain = _required_string(app, "app.allowed_domain").casefold()
    if allowed_domain != APPROVED_DOMAIN:
        raise ConfigurationError(f"app.allowed_domain must be {APPROVED_DOMAIN}")

    raw_admins = app.get("admin_emails")
    if (
        not isinstance(raw_admins, Sequence)
        or isinstance(raw_admins, (str, bytes))
        or not raw_admins
        or not all(isinstance(email, str) for email in raw_admins)
    ):
        raise ConfigurationError("app.admin_emails must be a non-empty list")

    admin_emails = frozenset(email.casefold() for email in raw_admins)
    if any(
        email != email.strip()
        or email.count("@") != 1
        or email.rsplit("@", 1)[1] != allowed_domain
        for email in admin_emails
    ):
        raise ConfigurationError("Every admin email must be an exact allowed-domain address")

    user_key_secret = _required_string(app, "app.user_key_secret")
    if len(user_key_secret) < 32:
        raise ConfigurationError("app.user_key_secret must contain at least 32 characters")

    supabase_url = _required_string(supabase, "supabase.url")
    _validate_url(supabase_url, "supabase.url")
    service_role_key = _required_string(
        supabase, "supabase.service_role_key"
    )
    if len(service_role_key) < 20:
        raise ConfigurationError("supabase.service_role_key is too short")

    voyage = secrets.get("voyage", {})
    if not isinstance(voyage, Mapping):
        raise ConfigurationError("Configuration section must be a mapping: voyage")
    voyage_api_key = voyage.get("api_key")
    if voyage_api_key in (None, ""):
        voyage_api_key = None
    elif not isinstance(voyage_api_key, str) or voyage_api_key != voyage_api_key.strip():
        raise ConfigurationError("Invalid configuration: voyage.api_key")
    elif len(voyage_api_key) < 20:
        raise ConfigurationError("voyage.api_key is too short")

    ai_star = secrets.get("ai_star", {})
    if not isinstance(ai_star, Mapping):
        raise ConfigurationError("Configuration section must be a mapping: ai_star")
    ai_star_api_key = ai_star.get("api_key")
    if ai_star_api_key in (None, ""):
        ai_star_api_key = None
    elif not isinstance(ai_star_api_key, str) or ai_star_api_key != ai_star_api_key.strip():
        raise ConfigurationError("Invalid configuration: ai_star.api_key")
    elif len(ai_star_api_key) < 20:
        raise ConfigurationError("ai_star.api_key is too short")

    return Settings(
        allowed_domain=allowed_domain,
        admin_emails=admin_emails,
        user_key_secret=user_key_secret,
        supabase_url=supabase_url,
        supabase_service_role_key=service_role_key,
        voyage_api_key=voyage_api_key,
        ai_star_api_key=ai_star_api_key,
    )
