from __future__ import annotations

from collections.abc import Iterable


STUDY_SCOPES = ("mid_sem", "end_sem", "quiz")
STUDY_MODE_LABELS = {
    "mid_sem": "Mid Sem",
    "end_sem": "End Sem",
    "quiz": "Class Quiz",
    "overall": "Overall",
}
MATERIAL_TYPES = ("theory", "questions")


def validate_study_scopes(values: Iterable[str]) -> tuple[str, ...]:
    scopes = tuple(dict.fromkeys(values))
    if not scopes or any(scope not in STUDY_SCOPES for scope in scopes):
        raise ValueError("Choose at least one valid study coverage option.")
    return scopes


def validate_material_type(value: str) -> str:
    if value not in MATERIAL_TYPES:
        raise ValueError("Choose Theory or Questions as the material type.")
    return value


def active_study_scope(mode: str | None) -> str | None:
    return None if mode in (None, "overall") else mode
