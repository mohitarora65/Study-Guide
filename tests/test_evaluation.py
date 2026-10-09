from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from evaluation.run_evaluation import (
    merge_retry_results,
    run_questions,
    summarize_results,
    validate_dataset,
)


DATASET_PATH = Path(__file__).parents[1] / "evaluation" / "questions.json"


def test_ta_approved_question_set_has_prd_split() -> None:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    items, reviewed = validate_dataset(dataset)

    assert len(items) == 40
    assert sum(item["expected"] == "supported" for item in items) == 25
    assert sum(item["expected"] == "unsupported" for item in items) == 15
    assert reviewed


def test_live_review_gate_requires_ta_approval_for_every_question() -> None:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    dataset["review"] = {
        "status": "approved",
        "reviewed_by_role": "teaching_assistant",
        "reviewed_on": "2026-10-09",
    }
    for item in dataset["items"]:
        item["review_status"] = "approved"
    dataset["items"][0]["review_status"] = "pending"

    _, reviewed = validate_dataset(dataset)

    assert not reviewed


def test_dataset_rejects_invalid_split_and_duplicate_ids() -> None:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    changed = copy.deepcopy(dataset)
    changed["items"][0]["id"] = changed["items"][1]["id"]
    with pytest.raises(ValueError, match="invalid or duplicate"):
        validate_dataset(changed)

    changed = copy.deepcopy(dataset)
    changed["items"][0]["expected"] = "unsupported"
    with pytest.raises(ValueError, match="25 supported"):
        validate_dataset(changed)


def test_runner_records_citation_provenance_without_persisting_chat() -> None:
    items = [{"id": "A01", "expected": "supported", "formula_risk": False, "question": "What is a basis?"}]
    citation = {
        "document_id": "doc-1",
        "version_id": "version-1",
        "page_number": 25,
        "display_name": "notes.pdf",
    }
    asked: list[str] = []
    waits: list[float] = []

    def answer(question: str) -> SimpleNamespace:
        asked.append(question)
        return SimpleNamespace(text="A basis spans the space.", citations=(citation,))

    results = run_questions(
        items,
        answer,
        {"doc-1": ("version-1", 80)},
        pause=waits.append,
    )

    assert asked == ["What is a basis?"]
    assert waits == []
    assert results[0]["valid_citation_count"] == 1
    assert results[0]["ta_citation_supported"] is None
    assert results[0]["ta_formula_correct"] is None


def test_runner_marks_wrong_version_or_page_as_invalid_citation() -> None:
    items = [{"id": "A01", "expected": "supported", "formula_risk": False, "question": "Q?"}]
    invalid = {"document_id": "doc-1", "version_id": "old", "page_number": 81}
    results = run_questions(
        items,
        lambda _question: SimpleNamespace(text="answer", citations=(invalid,)),
        {"doc-1": ("version-1", 80)},
    )
    assert results[0]["citation_count"] == 1
    assert results[0]["valid_citation_count"] == 0


def test_summary_keeps_manual_judgments_pending_until_completed() -> None:
    rows = [
        {
            "expected": "unsupported",
            "refused": True,
            "formula_risk": False,
            "citations": [],
            "valid_citation_count": 0,
            "ta_citation_supported": None,
            "ta_formula_correct": None,
            "error": None,
        },
        {
            "expected": "supported",
            "refused": False,
            "formula_risk": True,
            "citations": [{"page_number": 2}],
            "valid_citation_count": 1,
            "ta_citation_supported": True,
            "ta_formula_correct": True,
            "error": None,
        },
    ]
    summary = summarize_results(rows)
    assert summary["citation_validity"] == 1.0
    assert summary["refusal_recall"] == 1.0
    assert summary["unsupported_answer_rate"] == 0.0
    assert summary["citation_support"] == 1.0
    assert summary["formula_review_complete"]
    assert all(value == "incomplete" for value in summary["thresholds"].values())


def test_retry_merge_replaces_only_retried_rows() -> None:
    original = [
        {"id": "A01", "answer": "keep", "error": None},
        {"id": "A02", "answer": None, "error": "AnsweringError"},
    ]
    retried = [{"id": "A02", "answer": "recovered", "error": None}]

    assert merge_retry_results(original, retried) == [original[0], retried[0]]
