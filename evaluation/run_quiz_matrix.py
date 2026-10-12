"""Run the approved, bounded V2.2 quiz matrix once per topic."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time
import tomllib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from study_guide.config import load_settings
from study_guide.database import build_client, list_quiz_topics
from study_guide.quizzing import QuizError, _call_ai_star_langchain, generate_quiz


CALL_CAP = 3
RESULT_PATH = Path("evaluation/quiz_results/v22_20261010.json")
MATRIX = (
    ("Rank and fundamental subspaces", 0, "a"),
    ("Eigenvalues and eigenvectors", 60, "b"),
    ("Singular value decomposition", 85, "c"),
)


def main() -> None:
    record = json.loads(RESULT_PATH.read_text())
    record["matrix"] = [
        {"topic": topic, "mastery_before": mastery}
        for topic, mastery, _label in MATRIX
    ]
    record["call_cap"] = CALL_CAP
    completed = {result["topic"] for result in record["results"]}
    calls_used = sum(result["provider_calls"] for result in record["results"])
    settings = load_settings(tomllib.loads(Path(".streamlit/secrets.toml").read_text()))
    client = build_client(settings)
    topics = {row["name"]: row for row in list_quiz_topics(client)}

    for topic, mastery, label in MATRIX:
        if topic in completed or calls_used >= CALL_CAP:
            continue
        if topic not in topics:
            raise RuntimeError(f"Approved evaluation topic is missing: {topic}")

        topic_calls = 0
        repair_requested = False
        repair_reason = None
        provider_error = None
        started = time.monotonic()

        def one_call(messages: list[dict[str, str]]) -> str:
            nonlocal topic_calls, repair_requested, repair_reason, provider_error
            if topic_calls:
                repair_requested = True
                repair_reason = messages[-1]["content"][:300]
                raise QuizError("No provider retry in the V2.2 evaluation")
            if calls_used + topic_calls >= CALL_CAP:
                raise QuizError("The V2.2 provider-call cap has been reached")
            topic_calls += 1
            try:
                return _call_ai_star_langchain(settings.ai_star_api_key or "", messages)
            except QuizError as exc:
                cause = exc.__cause__
                provider_error = {
                    "exception_class": type(cause).__name__ if cause else type(exc).__name__
                }
                status = getattr(getattr(cause, "response", None), "status_code", None)
                if isinstance(status, int):
                    provider_error["http_status"] = status
                raise

        try:
            quiz = generate_quiz(
                topic,
                mastery_before=mastery,
                voyage_api_key=settings.voyage_api_key,
                ai_star_api_key=settings.ai_star_api_key,
                database_client=client,
                user_key=f"synthetic-v22-eval-{label}-20261010",
                generator=one_call,
            )
            result = {
                "status": "generated",
                "question_count": len(quiz.questions),
                "difficulty_mix": quiz.difficulty_mix,
                "questions": [
                    {
                        "question": question.prompt,
                        "options": list(question.options),
                        "correct_index": question.correct_index,
                        "difficulty": question.difficulty,
                        "explanation": question.explanation,
                        "citations": list(question.citations),
                    }
                    for question in quiz.questions
                ],
            }
        except QuizError as exc:
            result = {"status": "safe_failure", "safe_error": str(exc)}

        result.update(
            {
                "provider_calls": topic_calls,
                "repair_requested": repair_requested,
                "repair_reason": repair_reason,
                "provider_error": provider_error,
                "elapsed_seconds": round(time.monotonic() - started, 2),
            }
        )
        record["results"].append(
            {"topic": topic, "mastery_before": mastery, **result}
        )
        calls_used += topic_calls
        assert calls_used <= CALL_CAP
        RESULT_PATH.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        print(
            json.dumps(
                {key: value for key, value in result.items() if key != "questions"},
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
