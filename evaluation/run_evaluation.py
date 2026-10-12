from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
import tomllib
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from study_guide.answering import INSUFFICIENT_MATERIAL, answer_question
from study_guide.config import load_settings
from study_guide.database import build_client, list_documents


DATASET = ROOT / "evaluation" / "questions.json"


def validate_dataset(data: object) -> tuple[list[dict[str, Any]], bool]:
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise ValueError("Evaluation dataset must contain an items list")
    items = data["items"]
    if len(items) != 40:
        raise ValueError("Evaluation dataset must contain exactly 40 items")
    ids: set[str] = set()
    for item in items:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("id"), str)
            or item["id"] in ids
            or not isinstance(item.get("question"), str)
            or not item["question"].strip()
            or item.get("expected") not in {"supported", "unsupported"}
            or not isinstance(item.get("formula_risk"), bool)
            or item.get("review_status") not in {"pending", "approved"}
        ):
            raise ValueError("Evaluation dataset contains an invalid or duplicate item")
        ids.add(item["id"])
    counts = {label: sum(item["expected"] == label for item in items) for label in ("supported", "unsupported")}
    if counts != {"supported": 25, "unsupported": 15}:
        raise ValueError("Evaluation dataset must contain 25 supported and 15 unsupported items")
    review = data.get("review")
    reviewed = (
        isinstance(review, dict)
        and review.get("status") == "approved"
        and review.get("reviewed_by_role") == "teaching_assistant"
        and isinstance(review.get("reviewed_on"), str)
        and all(item["review_status"] == "approved" for item in items)
    )
    return items, reviewed


def citation_is_valid(citation: dict[str, Any], active_documents: dict[str, tuple[str, int]]) -> bool:
    document = active_documents.get(str(citation.get("document_id", "")))
    page = citation.get("page_number")
    return bool(
        document
        and citation.get("version_id") == document[0]
        and isinstance(page, int)
        and 1 <= page <= document[1]
    )


def run_questions(
    items: list[dict[str, Any]],
    answer: Callable[[str], Any],
    active_documents: dict[str, tuple[str, int]],
    *,
    limit: int | None = None,
    pause: Callable[[float], None] = time.sleep,
) -> list[dict[str, Any]]:
    rows = items[:limit] if limit is not None else items
    results = []
    for index, item in enumerate(rows):
        started = time.monotonic()
        try:
            generated = answer(item["question"])
            citations = list(generated.citations)
            text = generated.text
            results.append(
                {
                    "id": item["id"],
                    "expected": item["expected"],
                    "formula_risk": item["formula_risk"],
                    "answer": text,
                    "refused": text == INSUFFICIENT_MATERIAL,
                    "citations": citations,
                    "valid_citation_count": sum(citation_is_valid(citation, active_documents) for citation in citations),
                    "citation_count": len(citations),
                    "duration_seconds": round(time.monotonic() - started, 3),
                    "ta_citation_supported": None,
                    "ta_formula_correct": None,
                    "error": None,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "id": item["id"],
                    "expected": item["expected"],
                    "formula_risk": item["formula_risk"],
                    "answer": None,
                    "refused": None,
                    "citations": [],
                    "valid_citation_count": 0,
                    "citation_count": 0,
                    "duration_seconds": round(time.monotonic() - started, 3),
                    "ta_citation_supported": None,
                    "ta_formula_correct": None,
                    "error": type(exc).__name__,
                    "error_cause": type(exc.__cause__).__name__ if exc.__cause__ else None,
                }
            )
        if index < len(rows) - 1:
            pause(12.2)  # Stay below the app's per-user five-requests-per-minute guard.
    return results


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    citations = [citation for row in results for citation in row["citations"]]
    support_rows = [row for row in results if row["expected"] == "supported" and not row["refused"] and row["error"] is None]
    unsupported = [row for row in results if row["expected"] == "unsupported"]
    formula_rows = [row for row in results if row["formula_risk"] and row["expected"] == "supported" and not row["refused"]]
    summary = {
        "question_count": len(results),
        "citation_validity": (sum(row["valid_citation_count"] for row in results) / len(citations)) if citations else None,
        "citation_support": (sum(row["ta_citation_supported"] is True for row in support_rows) / len(support_rows)) if support_rows and all(row["ta_citation_supported"] is not None for row in support_rows) else None,
        "refusal_recall": (sum(row["refused"] is True for row in unsupported) / len(unsupported)) if unsupported else None,
        "unsupported_answer_rate": (sum(row["refused"] is False for row in unsupported) / len(unsupported)) if unsupported else None,
        "formula_review_complete": bool(formula_rows) and all(row["ta_formula_correct"] is not None for row in formula_rows),
        "formula_errors": sum(row["ta_formula_correct"] is False for row in formula_rows),
        "provider_errors": sum(row["error"] is not None for row in results),
    }
    incomplete = len(results) != 40 or summary["provider_errors"] > 0

    def threshold(value: float | None, passes: Callable[[float], bool]) -> str:
        if incomplete:
            return "incomplete"
        if value is None:
            return "pending-human-review"
        return "pass" if passes(value) else "fail"

    summary["thresholds"] = {
        "citation_validity_100_percent": threshold(summary["citation_validity"], lambda value: value >= 1.0),
        "citation_support_at_least_90_percent": threshold(summary["citation_support"], lambda value: value >= 0.9),
        "refusal_recall_at_least_90_percent": threshold(summary["refusal_recall"], lambda value: value >= 0.9),
        "unsupported_answer_rate_at_most_10_percent": threshold(summary["unsupported_answer_rate"], lambda value: value <= 0.1),
        "high_risk_formula_review": (
            "incomplete" if incomplete else
            "pending-human-review" if not summary["formula_review_complete"] else
            "pass" if summary["formula_errors"] == 0 else "fail"
        ),
    }
    return summary


def merge_retry_results(
    original: list[dict[str, Any]], retries: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_id = {row["id"]: row for row in original}
    updates = {row["id"]: row for row in retries}
    if len(by_id) != len(original) or len(updates) != len(retries):
        raise ValueError("Evaluation results contain duplicate IDs")
    if not set(updates).issubset(by_id):
        raise ValueError("Retry results contain unknown IDs")
    return [updates.get(row["id"], row) for row in original]


def _load_settings():
    secrets_path = ROOT / ".streamlit" / "secrets.toml"
    with secrets_path.open("rb") as secrets_file:
        return load_settings(tomllib.load(secrets_file))


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare or run the V1.4 grounding evaluation.")
    parser.add_argument("--live", action="store_true", help="Call configured providers; requires TA-approved questions.")
    parser.add_argument("--limit", type=int, help="Run only the first N approved questions (for a smoke test).")
    parser.add_argument("--retry-errors", type=Path, help="Retry only errors from a prior full result file and merge them.")
    parser.add_argument("--output", type=Path, help="Write live results to this JSON file.")
    parser.add_argument("--summarize", type=Path, help="Summarize a prior result JSON without provider calls.")
    args = parser.parse_args()
    if args.summarize:
        results = json.loads(args.summarize.read_text(encoding="utf-8"))
        print(json.dumps(summarize_results(results), indent=2))
        return 0

    data = json.loads(DATASET.read_text(encoding="utf-8"))
    items, reviewed = validate_dataset(data)
    if not args.live:
        if args.retry_errors:
            parser.error("--retry-errors requires --live")
        state = "TA-approved" if reviewed else "draft; TA review pending"
        print(f"{len(items)} questions validated (25 supported, 15 unsupported); {state}. No providers called.")
        return 0
    if not reviewed:
        parser.error("Live evaluation is disabled until the teaching assistant approves every question.")
    if args.limit is not None and not 1 <= args.limit <= len(items):
        parser.error("--limit must be between 1 and 40")
    if args.retry_errors and args.limit is not None:
        parser.error("--retry-errors cannot be combined with --limit")

    prior_results = None
    if args.retry_errors:
        prior_results = json.loads(args.retry_errors.read_text(encoding="utf-8"))
        dataset_ids = {item["id"] for item in items}
        if (
            not isinstance(prior_results, list)
            or len(prior_results) != len(items)
            or {row.get("id") for row in prior_results if isinstance(row, dict)} != dataset_ids
        ):
            parser.error("Retry source must contain exactly one result per approved question")
        failed_ids = {row["id"] for row in prior_results if row.get("error")}
        if not failed_ids:
            print("No errored questions to retry.")
            print(json.dumps(summarize_results(prior_results), indent=2))
            return 0
        items = [item for item in items if item["id"] in failed_ids]

    try:
        settings = _load_settings()
        if not settings.voyage_api_key or not settings.ai_star_api_key:
            raise ValueError
        client = build_client(settings)
        documents = list_documents(client)
        active_documents = {
            row["id"]: (row["active_version_id"], row["active_version"]["page_count"])
            for row in documents
            if row.get("active_version_id") and row.get("active_version")
        }
        if not active_documents:
            raise ValueError
    except Exception:
        parser.error("Local provider/database configuration or active course documents are unavailable.")

    results = run_questions(
        items,
        lambda question: answer_question(
            question,
            voyage_api_key=settings.voyage_api_key,
            ai_star_api_key=settings.ai_star_api_key,
            database_client=client,
            user_key="v1.4-evaluation",
        ),
        active_documents,
        limit=args.limit,
    )
    if prior_results is not None:
        results = merge_retry_results(prior_results, results)
    output = args.output or ROOT / "evaluation" / "results" / f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(results)} results to {output.relative_to(ROOT) if output.is_relative_to(ROOT) else output}.")
    if prior_results is not None:
        print(f"Retried {len(failed_ids)} errored questions and merged with earlier results.")
    print(json.dumps(summarize_results(results), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
