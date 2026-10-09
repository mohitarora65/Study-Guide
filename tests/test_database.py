import pytest

from study_guide.database import DatabaseError, check_connection


class Query:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def select(self, column: str) -> "Query":
        assert column == "id"
        return self

    def limit(self, count: int) -> "Query":
        assert count == 1
        return self

    def execute(self) -> None:
        if self.fail:
            raise RuntimeError("provider detail that must not escape")


class Client:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def table(self, name: str) -> Query:
        assert name == "documents"
        return Query(fail=self.fail)


def test_database_connection_check_uses_documents_table() -> None:
    check_connection(Client())


def test_database_connection_check_hides_provider_error() -> None:
    with pytest.raises(DatabaseError, match="Development database check failed") as error:
        check_connection(Client(fail=True))

    assert "provider detail" not in str(error.value)
