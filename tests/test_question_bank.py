from collections import Counter
import random

import pytest

from study_guide.question_bank import QUESTION_BANK, generate_bank_quiz, has_bank_topic
from study_guide.quizzing import QuizError, difficulty_mix


@pytest.mark.parametrize("topic", QUESTION_BANK)
@pytest.mark.parametrize("mastery", [None, 60, 85])
def test_bank_builds_every_adaptive_mix(topic: str, mastery: int | None) -> None:
    quiz = generate_bank_quiz(topic, mastery, rng=random.Random(7))

    assert len(quiz.questions) == 7
    assert Counter(question.difficulty for question in quiz.questions) == Counter(
        {level: count for level, count in difficulty_mix(mastery).items() if count}
    )
    assert len({question.prompt for question in quiz.questions}) == 7
    assert all(len(set(question.options)) == 4 for question in quiz.questions)
    assert all(question.options[question.correct_index] for question in quiz.questions)
    assert all(question.citations[0]["display_name"] == "lA notes.pdf" for question in quiz.questions)
    assert all(question.citations[0]["page_number"] > 0 for question in quiz.questions)


def test_bank_rejects_unreviewed_topic() -> None:
    with pytest.raises(QuizError, match="No reviewed questions"):
        generate_bank_quiz("Unreviewed topic", None, rng=random.Random(1))
    assert not has_bank_topic("Unreviewed topic")
    assert not has_bank_topic(None)  # type: ignore[arg-type]
    assert has_bank_topic("  Singular Value Decomposition  ")


def test_bank_content_meets_quiz_contract() -> None:
    for questions in QUESTION_BANK.values():
        assert Counter(question.difficulty for question in questions) == {
            "easy": 4, "medium": 4, "hard": 3,
        }
        assert len({question.prompt.casefold() for question in questions}) == 11
        for question in questions:
            assert 0 < len(question.prompt) <= 160
            assert len(set(option.casefold() for option in question.options)) == 4
            assert all(0 < len(option) <= 60 for option in question.options)
            assert 0 <= question.correct_index < 4
            assert 0 < len(question.explanation) <= 120
            assert question.page > 0


def test_option_shuffle_keeps_the_correct_answer() -> None:
    expected = {
        row.prompt: row.options[row.correct_index]
        for row in QUESTION_BANK["singular value decomposition"]
    }
    quiz = generate_bank_quiz("Singular value decomposition", 85, rng=random.Random(3))

    assert all(question.options[question.correct_index] == expected[question.prompt] for question in quiz.questions)


def test_approved_source_question_is_preferred_and_cited() -> None:
    row = {
        "prompt": "Uploaded easy question",
        "options": ["A", "B", "C", "D"],
        "correct_index": 0,
        "difficulty": "easy",
        "explanation": "Uploaded explanation",
        "page_number": 9,
        "display_name": "questions.pdf",
    }

    quiz = generate_bank_quiz(
        "Rank and fundamental subspaces", None,
        source_questions=[row], rng=random.Random(7),
    )

    uploaded = next(question for question in quiz.questions if question.prompt == row["prompt"])
    assert uploaded.citations == ({"display_name": "questions.pdf", "page_number": 9},)
