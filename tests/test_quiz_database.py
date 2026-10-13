from typing import Any
from uuid import uuid4

import pytest

from study_guide.database import (
    DatabaseError,
    complete_custom_quiz_attempt,
    complete_quiz_attempt,
    list_student_custom_quiz_attempts,
    list_student_quiz_progress,
)


class Result:
    def __init__(self, data: Any) -> None:
        self.data = data


class Rpc:
    def __init__(self, data: Any) -> None:
        self.data = data

    def execute(self) -> Result:
        return Result(self.data)


class Client:
    def __init__(self) -> None:
        self.call: tuple[str, dict[str, Any]] | None = None

    def rpc(self, name: str, parameters: dict[str, Any]) -> Rpc:
        self.call = (name, parameters)
        return Rpc(
            [
                {
                    "score": 71.43,
                    "mastery_before": 50,
                    "mastery_after": 63,
                    "attempt_count": 2,
                    "duplicate": False,
                }
            ]
        )


def test_quiz_result_is_saved_atomically_with_normalized_email() -> None:
    client = Client()
    attempt_id, topic_id = str(uuid4()), str(uuid4())

    result = complete_quiz_attempt(
        client,
        attempt_id=attempt_id,
        user_key="opaque-user-key",
        email="student@iiti.ac.in",
        topic_id=topic_id,
        correct_count=5,
        difficulty_mix={"easy": 2, "medium": 4, "hard": 1},
    )

    assert result["mastery_after"] == 63
    assert client.call == (
        "complete_quiz_attempt",
        {
            "p_attempt_id": attempt_id,
            "p_user_key": "opaque-user-key",
            "p_email": "student@iiti.ac.in",
            "p_topic_id": topic_id,
            "p_correct_count": 5,
            "p_difficulty_mix": {"easy": 2, "medium": 4, "hard": 1},
        },
    )


def test_quiz_result_rejects_bad_identifiers_or_email_before_database_call() -> None:
    client = Client()
    with pytest.raises(DatabaseError):
        complete_quiz_attempt(
            client,
            attempt_id="not-a-uuid",
            user_key="opaque-user-key",
            email="Student@iiti.ac.in",
            topic_id=str(uuid4()),
            correct_count=7,
            difficulty_mix={"easy": 4, "medium": 3, "hard": 0},
        )
    assert client.call is None


def test_custom_quiz_result_is_saved_without_mastery_update() -> None:
    client = Client()
    attempt_id = str(uuid4())

    result = complete_custom_quiz_attempt(
        client,
        attempt_id=attempt_id,
        user_key="opaque-user-key",
        email="student@iiti.ac.in",
        topics=("Vectors", "Matrices"),
        question_count=5,
        correct_count=4,
        difficulty_mix={"easy": 2, "medium": 2, "hard": 1},
    )

    assert result["score"] == 71.43
    assert client.call == (
        "complete_custom_quiz_attempt",
        {
            "p_attempt_id": attempt_id,
            "p_user_key": "opaque-user-key",
            "p_email": "student@iiti.ac.in",
            "p_topics": ["Vectors", "Matrices"],
            "p_question_count": 5,
            "p_correct_count": 4,
            "p_difficulty_mix": {"easy": 2, "medium": 2, "hard": 1},
        },
    )


def test_custom_quiz_result_rejects_a_mix_with_the_wrong_count() -> None:
    client = Client()
    with pytest.raises(DatabaseError):
        complete_custom_quiz_attempt(
            client,
            attempt_id=str(uuid4()),
            user_key="opaque-user-key",
            email="student@iiti.ac.in",
            topics=("Vectors",),
            question_count=5,
            correct_count=4,
            difficulty_mix={"easy": 2, "medium": 2, "hard": 2},
        )
    assert client.call is None


def test_custom_quiz_history_query_is_scoped_to_owner() -> None:
    observed: dict[str, Any] = {}

    class Query:
        def select(self, columns: str) -> "Query":
            observed["columns"] = columns
            return self

        def eq(self, column: str, value: str) -> "Query":
            observed["owner"] = (column, value)
            return self

        def order(self, _column: str, desc: bool = False) -> "Query":
            return self

        def limit(self, _count: int) -> "Query":
            return self

        def execute(self) -> Result:
            return Result([{"topics": ["Vectors"], "question_count": 5}])

    class RowsClient:
        def table(self, name: str) -> Query:
            observed["table"] = name
            return Query()

    rows = list_student_custom_quiz_attempts(RowsClient(), "opaque-owner")

    assert rows[0]["topics"] == ["Vectors"]
    assert observed["table"] == "custom_quiz_attempts"
    assert observed["owner"] == ("user_key", "opaque-owner")


def test_student_progress_query_is_scoped_to_opaque_owner_key() -> None:
    topic_id = str(uuid4())

    class Query:
        def __init__(self, rows: list[dict[str, Any]]) -> None:
            self.rows = rows

        def select(self, _columns: str) -> "Query":
            return self

        def order(self, _column: str, desc: bool = False) -> "Query":
            return self

        def eq(self, column: str, value: Any) -> "Query":
            self.rows = [row for row in self.rows if row.get(column) == value]
            return self

        def in_(self, column: str, values: list[Any]) -> "Query":
            self.rows = [row for row in self.rows if row.get(column) in values]
            return self

        def limit(self, count: int) -> "Query":
            self.rows = self.rows[:count]
            return self

        def execute(self) -> Result:
            return Result(self.rows)

    class RowsClient:
        def table(self, name: str) -> Query:
            rows = {
                "topic_mastery": [
                    {"user_key": "alice", "topic_id": topic_id, "mastery_score": 71},
                    {"user_key": "bob", "topic_id": topic_id, "mastery_score": 100},
                ],
                "quiz_topics": [{"id": topic_id, "name": "Vector spaces"}],
            }
            return Query(rows[name])

    assert list_student_quiz_progress(RowsClient(), "alice") == [
        {
            "user_key": "alice",
            "topic_id": topic_id,
            "mastery_score": 71,
            "topic": "Vector spaces",
        }
    ]
