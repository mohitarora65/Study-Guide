from study_guide.ingestion import ExtractedPage
from study_guide.question_extraction import candidate_rows, extract_question_candidates


def _page(number: int, text: str) -> ExtractedPage:
    return ExtractedPage(number, text, len(text), False)


def test_question_upload_extracts_mcq_answer_and_descriptive_draft() -> None:
    questions = extract_question_candidates(
        (_page(3, "1. What is rank?\nA. Number of pivots\nB. Rows\nC. Columns\nD. Zero\nAnswer: A\n2. Prove rank-nullity theorem."),),
        "questions",
    )

    assert len(questions) == 2
    assert questions[0].options == ("Number of pivots", "Rows", "Columns", "Zero")
    assert questions[0].correct_index == 0
    assert questions[1].options is None
    assert questions[1].correct_index is None


def test_theory_only_extracts_from_explicit_question_section() -> None:
    questions = extract_question_candidates(
        (
            _page(1, "1. This numbered theory point is ignored."),
            _page(2, "Review Questions\n1) What is a basis?"),
        ),
        "theory",
    )

    assert [question.prompt for question in questions] == ["What is a basis?"]
    assert questions[0].page_number == 2


def test_candidate_rows_keep_source_and_coverage() -> None:
    extracted = extract_question_candidates((_page(7, "Q1: Define SVD."),), "questions")
    rows = candidate_rows(
        extracted,
        document_id="document",
        version_id="version",
        material_type="questions",
        study_scopes=("end_sem",),
    )

    assert rows[0]["page_number"] == 7
    assert rows[0]["source_kind"] == "questions"
    assert rows[0]["study_scopes"] == ["end_sem"]
