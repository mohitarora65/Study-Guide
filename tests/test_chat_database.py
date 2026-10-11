from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from study_guide.database import (
    DatabaseError,
    append_turn,
    create_thread,
    delete_thread,
    list_thread_messages,
    list_threads,
    rename_thread,
)


class FakeQuery:
    def __init__(self, tables: dict[str, list[dict[str, Any]]], table: str) -> None:
        self.tables = tables
        self.table = table
        self.operation = "select"
        self.filters: list[tuple[str, Any]] = []
        self.limit_count: int | None = None
        self.order_by: str | None = None
        self.desc = False
        self.values: Any = None

    def select(self, _columns: str) -> "FakeQuery":
        return self

    def insert(self, values: Any) -> "FakeQuery":
        self.operation, self.values = "insert", values
        return self

    def update(self, values: dict[str, Any]) -> "FakeQuery":
        self.operation, self.values = "update", values
        return self

    def delete(self) -> "FakeQuery":
        self.operation = "delete"
        return self

    def eq(self, column: str, value: Any) -> "FakeQuery":
        self.filters.append((column, value))
        return self

    def order(self, column: str, desc: bool = False) -> "FakeQuery":
        self.order_by, self.desc = column, desc
        return self

    def limit(self, count: int) -> "FakeQuery":
        self.limit_count = count
        return self

    def execute(self) -> Any:
        rows = self.tables.setdefault(self.table, [])
        if self.operation == "insert":
            items = self.values if isinstance(self.values, list) else [self.values]
            created = []
            for item in items:
                row = dict(item)
                row.setdefault("id", f"{self.table}-{len(rows) + 1}")
                row.setdefault("created_at", datetime.now(timezone.utc).isoformat())
                row.setdefault("updated_at", row["created_at"])
                rows.append(row)
                created.append(row)
            return type("Result", (), {"data": created})()

        matched = [
            row
            for row in rows
            if all(row.get(column) == value for column, value in self.filters)
        ]
        if self.operation == "update":
            for row in matched:
                row.update(self.values)
            return type("Result", (), {"data": matched})()
        if self.operation == "delete":
            for row in matched:
                rows.remove(row)
            if self.table == "threads":
                ids = {row["id"] for row in matched}
                self.tables["messages"] = [
                    row for row in self.tables.get("messages", []) if row["thread_id"] not in ids
                ]
            return type("Result", (), {"data": matched})()
        if self.order_by:
            matched.sort(key=lambda row: row.get(self.order_by, ""), reverse=self.desc)
        if self.limit_count is not None:
            matched = matched[: self.limit_count]
        return type("Result", (), {"data": matched})()


class FakeClient:
    def __init__(self) -> None:
        self.tables: dict[str, list[dict[str, Any]]] = {"threads": [], "messages": []}

    def table(self, name: str) -> FakeQuery:
        return FakeQuery(self.tables, name)


def test_chat_history_is_filtered_by_opaque_owner_key() -> None:
    client = FakeClient()
    alice = create_thread(client, "alice-key", "Basis question")
    bob = create_thread(client, "bob-key", "Other question")
    append_turn(
        client,
        "alice-key",
        alice["id"],
        question="What is a basis?",
        answer="A set of linearly independent spanning vectors.",
        is_refusal=False,
        citations=[{"chunk_id": "chunk-1", "page_number": 25}],
    )

    assert [row["id"] for row in list_threads(client, "alice-key")] == [alice["id"]]
    assert list_thread_messages(client, "bob-key", alice["id"]) == []
    assert list_thread_messages(client, "alice-key", alice["id"])[1]["citations"] == [
        {"chunk_id": "chunk-1", "page_number": 25}
    ]

    delete_thread(client, "bob-key", alice["id"])
    assert len(client.tables["threads"]) == 2
    with pytest.raises(DatabaseError):
        append_turn(
            client,
            "bob-key",
            alice["id"],
            question="No",
            answer="No",
            is_refusal=True,
            citations=[],
        )
    delete_thread(client, "alice-key", alice["id"])
    assert [row["id"] for row in client.tables["threads"]] == [bob["id"]]
    assert client.tables["messages"] == []


def test_thread_creation_and_turn_limits() -> None:
    client = FakeClient()
    thread = create_thread(client, "alice-key", "x" * 100)
    assert len(thread["title"]) == 80
    with pytest.raises(DatabaseError):
        append_turn(
            client,
            "alice-key",
            thread["id"],
            question="q" * 1_001,
            answer="answer",
            is_refusal=False,
            citations=[],
        )


def test_thread_rename_is_bounded_and_owner_scoped() -> None:
    client = FakeClient()
    thread = create_thread(client, "alice-key", "Original")

    rename_thread(client, "bob-key", thread["id"], "Not allowed")
    assert thread["title"] == "Original"

    rename_thread(client, "alice-key", thread["id"], "  " + "x" * 100)
    assert thread["title"] == "x" * 80
    with pytest.raises(DatabaseError):
        rename_thread(client, "alice-key", thread["id"], "   ")
