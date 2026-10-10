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


def test_quiz_graph_stops_on_invalid_batch_without_repair() -> None:
    mix = difficulty_mix(60)
    calls: list[list[dict[str, str]]] = []

    def generate(messages: list[dict[str, str]]) -> str:
        calls.append(messages)
        return "not json"

    result = build_quiz_graph(retrieve=lambda _topic: EVIDENCE, generate=generate).invoke(
        {"topic": "Vector spaces", "difficulty_mix": mix, "repair_count": 0}
    )

    assert "not valid JSON" in result["safe_error"]
    assert len(calls) == 1


@pytest.mark.parametrize("mastery", [None, 60, 85])
def test_batches_preserve_mix_and_bound_calls(mastery: int | None) -> None:
    mix = difficulty_mix(mastery)
    calls = []

    def generate(messages):
        batch_mix = json.loads(messages[1]["content"])["required_difficulty_mix"]
        payload = json.loads(quiz_json(batch_mix))
        for row in payload["questions"]:
            row["question"] = f"Batch {len(calls)}: {row['question']}"
        calls.append(batch_mix)
        return json.dumps(payload)

    result = build_quiz_graph(retrieve=lambda _: EVIDENCE, generate=generate).invoke(
        {"topic": "Vector spaces", "difficulty_mix": mix}
    )
    assert len(result["questions"]) == 7
    assert len(calls) <= 3
    assert all(sum(batch.values()) <= 3 for batch in calls)
    assert {level: sum(batch[level] for batch in calls) for level in mix} == mix
    if mastery == 85:
        assert [sum(batch.values()) for batch in calls] == [1, 3, 3]


def test_duplicate_across_batches_stops_before_next_call() -> None:
    calls = []

    def generate(messages):
        batch_mix = json.loads(messages[1]["content"])["required_difficulty_mix"]
        calls.append(batch_mix)
        return quiz_json(batch_mix)

    result = build_quiz_graph(retrieve=lambda _: EVIDENCE, generate=generate).invoke(
        {"topic": "Vector spaces", "difficulty_mix": difficulty_mix(85)}
    )
    assert "duplicate questions" in result["safe_error"]
    assert len(calls) == 2


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
        batch_mix = json.loads(messages[1]["content"])["required_difficulty_mix"]
        payload = json.loads(quiz_json(batch_mix))
        for row in payload["questions"]:
            row["question"] = f"Batch {len(captured)}: {row['question']}"
        captured.extend(messages)
        return json.dumps(payload)

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
    assert "limit each explanation to eight words" in captured[0]["content"]
    assert "never write that product as Ay" in captured[0]["content"]


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
    assert captured["model"] == quizzing.AI_STAR_MODEL
    assert captured["extra_body"] == {"max_tokens": quizzing.MAX_QUIZ_OUTPUT_TOKENS}
    assert captured["timeout"] == 30


def test_adapter_sends_provider_token_cap_on_wire(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx
    from langchain_openai import ChatOpenAI
    import study_guide.quizzing as quizzing

    captured = {}

    def respond(request):
        captured.update(json.loads(request.content))
        return httpx.Response(200, json={
            "id": "synthetic-response", "object": "chat.completion", "created": 0,
            "model": "synthetic-model", "choices": [{"index": 0,
            "message": {"role": "assistant", "content": "{}"}, "finish_reason": "stop"}],
        })

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        monkeypatch.setattr(quizzing, "ChatOpenAI", lambda **kwargs: ChatOpenAI(
            **kwargs, http_client=client
        ))
        assert quizzing._call_ai_star_langchain("synthetic-key", [
            {"role": "user", "content": "Return JSON."}
        ]) == "{}"

    assert captured["max_tokens"] == 2000
    assert captured["model"] == quizzing.AI_STAR_MODEL
    assert "max_completion_tokens" not in captured
    assert captured["response_format"] == {"type": "json_object"}
