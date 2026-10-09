from __future__ import annotations

import hashlib
import hmac
from collections.abc import Mapping
from dataclasses import dataclass

from study_guide.config import Settings


class IdentityError(ValueError):
    """Raised when identity claims do not satisfy the access policy."""


@dataclass(frozen=True)
class Identity:
    user_key: str
    email: str
    is_admin: bool


def _required_claim(claims: Mapping[str, object], name: str) -> str:
    value = claims.get(name)
    if not isinstance(value, str) or not value or value != value.strip():
        raise IdentityError(f"Missing or invalid identity claim: {name}")
    return value


def authenticate_claims(
    claims: Mapping[str, object], settings: Settings
) -> Identity:
    if claims.get("email_verified") is not True:
        raise IdentityError("The identity provider did not verify the email")

    email = _required_claim(claims, "email").casefold()
    if email.count("@") != 1:
        raise IdentityError("The email claim is invalid")
    local_part, domain = email.rsplit("@", 1)
    if (
        not local_part
        or any(character.isspace() for character in local_part)
        or domain != settings.allowed_domain
    ):
        raise IdentityError("The email domain is not allowed")

    issuer = _required_claim(claims, "iss")
    subject = _required_claim(claims, "sub")
    message = f"{issuer}\0{subject}".encode()
    user_key = hmac.new(
        settings.user_key_secret.encode(), message, hashlib.sha256
    ).hexdigest()

    return Identity(
        user_key=user_key,
        email=email,
        is_admin=email in settings.admin_emails,
    )
