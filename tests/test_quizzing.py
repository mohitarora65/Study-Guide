import json
from decimal import Decimal

import pytest

from study_guide.quizzing import (
    QuizError,
    build_quiz_graph,
    difficulty_mix,
    score_percent,
    updated_mastery,
    validate_quiz_response,
    generate_quiz,
)


EVIDENCE = [
    {
        "document_id": "document-1",
        "version_id": "version-1",
        "chunk_id": "chunk-1",
        "display_name": "Linear Algebra.pdf",
        "page_number": 12,
        "content": "A basis is a linearly independent spanning set.",
    }
]


def quiz_json(mix: dict[str, int], *, chunk_id: str = "chunk-1") -> str:
    difficulties = [level for level, count in mix.items() for _ in range(count)]
    return json.dumps(
        {
            "questions": [
                {
                    "question": f"Question {number}?",
                    "options": [f"A{number}", f"B{number}", f"C{number}", f"D{number}"],
                    "correct_index": number % 4,
                    "difficulty": difficulty,
                    "explanation": "Supported by the supplied passage.",
                    "cited_chunk_ids": [chunk_id],
                }
                for number, difficulty in enumerate(difficulties, start=1)
            ]
        }
    )


def test_mastery_drives_exact_seven_question_mix_and_rolling_score() -> None:
    assert difficulty_mix(None) == {"easy": 4, "medium": 3, "hard": 0}
    assert difficulty_mix(49) == {"easy": 4, "medium": 3, "hard": 0}
    assert difficulty_mix(50) == {"easy": 2, "medium": 4, "hard": 1}
    assert difficulty_mix(79) == {"easy": 2, "medium": 4, "hard": 1}
    assert difficulty_mix(80) == {"easy": 1, "medium": 3, "hard": 3}
    assert score_percent(5) == Decimal("71.43")
    assert updated_mastery(None, 5) == 71
    assert updated_mastery(50, 5) == 63


def test_quiz_validation_maps_only_retrieved_citations() -> None:
    mix = difficulty_mix(None)
    questions = validate_quiz_response(quiz_json(mix), EVIDENCE, mix)

    assert len(questions) == 7
    assert questions[0].citations[0]["page_number"] == 12
    with pytest.raises(QuizError, match="citations"):
        validate_quiz_response(quiz_json(mix, chunk_id="fabricated"), EVIDENCE, mix)


def test_quiz_validation_bounds_output_for_provider_token_cap() -> None:
    mix = difficulty_mix(None)
    payload = json.loads(quiz_json(mix))
    payload["questions"][0]["options"][0] = "x" * 61

    with pytest.raises(QuizError, match="answer option"):
        validate_quiz_response(json.dumps(payload), EVIDENCE, mix)


def test_quiz_graph_repairs_invalid_provider_json_once() -> None:
    mix = difficulty_mix(60)
    outputs = iter(["not json", quiz_json(mix)])
    calls: list[list[dict[str, str]]] = []

    def generate(messages: list[dict[str, str]]) -> str:
        calls.append(messages)
        return next(outputs)

    result = build_quiz_graph(retrieve=lambda _topic: EVIDENCE, generate=generate).invoke(
        {"topic": "Vector spaces", "difficulty_mix": mix, "repair_count": 0}
    )

    assert len(result["questions"]) == 7
    assert len(calls) == 2
    assert "failed validation" in calls[1][-1]["content"]


def test_quiz_graph_stops_before_generation_without_evidence() -> None:
    called = False

    def generate(_messages: list[dict[str, str]]) -> str:
        nonlocal called
        called = True
        return "{}"

    result = build_quiz_graph(retrieve=lambda _topic: [], generate=generate).invoke(
        {"topic": "Missing", "difficulty_mix": difficulty_mix(None), "repair_count": 0}
    )

    assert "does not sufficiently cover" in result["safe_error"]
    assert not called


def test_quiz_provider_payload_excludes_student_identity() -> None:
    captured: list[dict[str, str]] = []
    mix = difficulty_mix(None)

    def generate(messages: list[dict[str, str]]) -> str:
        captured.extend(messages)
        return quiz_json(mix)

    quiz = generate_quiz(
        "Vector spaces",
        mastery_before=None,
        gemini_api_key="g" * 32,
        ai_star_api_key="a" * 32,
        database_client=object(),
        user_key="opaque-private-owner-key",
        retrieve=lambda _topic: EVIDENCE,
        generator=generate,
    )

    payload = json.dumps(captured)
    assert len(quiz.questions) == 7
    assert "opaque-private-owner-key" not in payload
    assert "@iiti.ac.in" not in payload


def test_ai_star_adapter_disables_hidden_transport_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    import study_guide.quizzing as quizzing

    captured: dict[str, object] = {}

    class BoundModel:
        def invoke(self, _messages: list[dict[str, str]]) -> object:
            return type("Response", (), {"content": "{}"})()

    class Model:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

        def bind(self, **_kwargs: object) -> BoundModel:
            return BoundModel()

    monkeypatch.setattr(quizzing, "ChatOpenAI", Model)

    assert quizzing._call_ai_star_langchain("a" * 32, []) == "{}"
    assert captured["max_retries"] == 0
    assert captured["max_tokens"] == quizzing.MAX_QUIZ_OUTPUT_TOKENS
