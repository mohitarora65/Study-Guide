from __future__ import annotations

from dataclasses import dataclass
from random import SystemRandom
from typing import Any

from study_guide.quizzing import (
    Difficulty,
    GeneratedQuiz,
    QuizError,
    QuizQuestion,
    difficulty_mix,
    validate_topic_name,
)


@dataclass(frozen=True)
class _BankQuestion:
    prompt: str
    options: tuple[str, str, str, str]
    correct_index: int
    difficulty: Difficulty
    explanation: str
    page: int


def _q(
    prompt: str,
    options: tuple[str, str, str, str],
    correct_index: int,
    difficulty: Difficulty,
    explanation: str,
    page: int,
) -> _BankQuestion:
    return _BankQuestion(prompt, options, correct_index, difficulty, explanation, page)


QUESTION_BANK: dict[str, tuple[_BankQuestion, ...]] = {
    "rank and fundamental subspaces": (
        _q("Which set is the column space C(A)?", ("All vectors Ax", "All vectors A^T y", "All x with Ax = 0", "All y with A^T y = 0"), 0, "easy", "Column space contains every vector Ax.", 24),
        _q("Which condition defines the nullspace N(A)?", ("Ax = 0", "A^T y = 0", "Ax = b", "A^T y = x"), 0, "easy", "Nullspace contains vectors satisfying Ax = 0.", 24),
        _q("What dimension do the row and column spaces share?", ("r", "n - r", "m - r", "m + n"), 0, "easy", "Both dimensions equal the rank r.", 28),
        _q("For rank r, how many independent solutions has Ax = 0?", ("n - r", "m - r", "r", "m + n"), 0, "easy", "The counting theorem gives n - r.", 28),
        _q("For an m by n rank-r matrix, what is dim N(A^T)?", ("m - r", "n - r", "r", "m + n"), 0, "medium", "Left nullspace dimension is m - r.", 28),
        _q("If rref identifies pivot columns 1 and 3, which columns form a basis for C(A)?", ("Columns 1 and 3 of the original A", "Columns 1 and 3 of rref(A)", "Every column of the original A", "The zero rows of rref(A)"), 0, "medium", "Use the matching pivot columns of the original A.", 26),
        _q("For diag(1,1,0), what is dim N(A)?", ("1", "2", "3", "0"), 0, "medium", "Its nullspace is the z-axis.", 25),
        _q("A connected graph has n nodes; what is its incidence-matrix rank?", ("n - 1", "n", "m - 1", "m - n + 1"), 0, "medium", "A connected incidence matrix has rank n - 1.", 29),
        _q("If A is 5 by 7 with rank 3, what are dim N(A) and dim N(A^T)?", ("4 and 2", "2 and 4", "3 and 3", "7 and 5"), 0, "hard", "They are n-r=4 and m-r=2.", 28),
        _q("A 4 by 6 matrix has rank 4; which dimensions are correct?", ("dim N(A)=2, dim N(A^T)=0", "dim N(A)=0, dim N(A^T)=2", "Both nullspaces have dimension 2", "Both nullspaces have dimension 4"), 0, "hard", "Apply n-r and m-r to both nullspaces.", 28),
        _q("Why must Ax = 0 have a nonzero solution when n > m?", ("Because r ≤ m, so n-r > 0", "Because r = n", "Because m-r > n", "Because every column is zero"), 0, "hard", "Rank cannot exceed the number of rows.", 28),
    ),
    "eigenvalues and eigenvectors": (
        _q("Which equation defines an eigenpair of A?", ("Ax = λx", "Ax = 0", "A + x = λx", "x = λAx"), 0, "easy", "An eigenvector satisfies Ax = λx.", 43),
        _q("If Ax = λx, what is A^n x?", ("λ^n x", "nλx", "λx^n", "A^n λx"), 0, "easy", "Repeated multiplication gives λ^n x.", 43),
        _q("Which equation determines the eigenvalues of A?", ("det(A - λI) = 0", "det(A) = λ", "A + λI = 0", "Ax = 0 for every x"), 0, "easy", "Eigenvalues solve the characteristic equation.", 43),
        _q("What equals the sum of a matrix's eigenvalues?", ("trace(A)", "det(A)", "rank(A)", "trace(A^T A)"), 0, "easy", "The eigenvalue sum equals the trace.", 43),
        _q("For A=[[.8,.3],[.2,.7]], what are its eigenvalues?", ("1 and 1/2", ".8 and .7", "1 and 0", "2 and 1/2"), 0, "medium", "Its characteristic polynomial factors accordingly.", 43),
        _q("For the example matrix, which vector belongs to λ=1?", ("[.6,.4]", "[1,-1]", "[1,0]", "[.4,-.4]"), 0, "medium", "The notes give [.6,.4] for λ=1.", 43),
        _q("For the example matrix, which vector belongs to λ=1/2?", ("[1,-1]", "[.6,.4]", "[1,0]", "[.3,.2]"), 0, "medium", "The notes give [1,-1] for λ=1/2.", 43),
        _q("If A has independent eigenvectors in X, which identity holds?", ("A = XΛX^-1", "A = X^-1ΛX", "A = XΛX", "A = ΛX^-1"), 0, "medium", "Diagonalization gives A = XΛX^-1.", 44),
        _q("When does A^k approach the zero matrix?", ("Every |λ_i| < 1", "Every λ_i > 1", "Every λ_i = 1", "At least one |λ_i| > 1"), 0, "hard", "All eigenvalue magnitudes must be below one.", 44),
        _q("Why is [[3,6],[0,3]] not diagonalizable?", ("It lacks two independent eigenvectors", "Its determinant is nonzero", "Its trace is six", "Its eigenvalue is positive"), 0, "hard", "The repeated eigenvalue has one eigenvector.", 44),
        _q("If A = XΛX^-1, which formula computes A^4?", ("XΛ^4X^-1", "X^4ΛX^-1", "XΛX^-4", "Λ^4"), 0, "hard", "Middle inverse factors cancel in powers.", 44),
    ),
    "singular value decomposition": (
        _q("Which factorization is the SVD of A?", ("A = UΣV^T", "A = VΣU^T", "A = U^TΣV", "A = ΣUV^T"), 0, "easy", "SVD factors A as UΣV^T.", 49),
        _q("Which matrices are orthogonal in an SVD?", ("U and V", "U and Σ", "Σ and V", "A and Σ"), 0, "easy", "The singular-vector matrices are orthogonal.", 49),
        _q("Which equation relates right and left singular vectors?", ("Av_k = σ_k u_k", "Au_k = σ_k v_k", "Av_k = σ_k v_k", "Au_k = σ_k u_k"), 0, "easy", "A maps v_k to σ_k u_k.", 50),
        _q("How are positive singular values ordered?", ("σ_1 ≥ ... ≥ σ_r > 0", "σ_1 ≤ ... ≤ σ_r", "All σ_k = 1", "σ_1 < 0"), 0, "easy", "Positive singular values use descending order.", 50),
        _q("What are σ_k^2 for A?", ("Eigenvalues of A^T A", "Eigenvalues of A", "Entries of U", "Diagonal entries of A"), 0, "medium", "A^T A has eigenvalues σ_k squared.", 50),
        _q("What does the reduced SVD retain?", ("U_rΣ_rV_r^T", "UΣV", "U_rΣV", "UΣ_rV"), 0, "medium", "Reduced SVD stops at rank r.", 50),
        _q("For A=[[3,0],[4,5]], which singular values are given?", ("3√5 and √5", "5 and 3", "8 and 1", "3 and 0"), 0, "medium", "The worked example gives these singular values.", 49),
        _q("Which vectors form the row-space input basis in the SVD?", ("v_1,...,v_r", "u_1,...,u_r", "σ_1,...,σ_r", "The columns of Σ"), 0, "medium", "Right singular vectors span the row space.", 49),
        _q("A 3 by 4 rank-2 matrix has which reduced-SVD shapes?", ("U_r:3x2, Σ_r:2x2, V_r^T:2x4", "U_r:3x3, Σ_r:3x4, V_r^T:4x4", "U_r:2x3, Σ_r:2x2, V_r^T:4x2", "U_r:3x2, Σ_r:3x2, V_r^T:2x4"), 0, "hard", "Reduced factors follow m×r, r×r, r×n.", 50),
        _q("If A^T A v = 25v for unit v, what is the associated σ?", ("5", "25", "1/5", "625"), 0, "hard", "Singular values are square roots of eigenvalues.", 50),
        _q("If A has singular values 8, 1, 0, what is rank(A)?", ("2", "3", "1", "0"), 0, "hard", "Rank counts the positive singular values.", 50),
    ),
}


def generate_bank_quiz(
    topic: str,
    mastery_before: int | None,
    *,
    source_questions: list[dict[str, Any]] | None = None,
    rng: Any | None = None,
) -> GeneratedQuiz:
    topic = validate_topic_name(topic)
    mix = difficulty_mix(mastery_before)
    bank_questions = QUESTION_BANK.get(topic.casefold())
    reviewed: list[_BankQuestion] = []
    citations: dict[str, dict[str, Any]] = {}
    for row in source_questions or []:
        options = row.get("options")
        if (
            isinstance(row.get("prompt"), str)
            and isinstance(options, list)
            and len(options) == 4
            and all(isinstance(option, str) and option.strip() for option in options)
            and isinstance(row.get("correct_index"), int)
            and 0 <= row["correct_index"] < 4
            and row.get("difficulty") in {"easy", "medium", "hard"}
            and isinstance(row.get("explanation"), str)
            and row["explanation"].strip()
            and isinstance(row.get("page_number"), int)
        ):
            question = _q(
                row["prompt"].strip(),
                tuple(option.strip() for option in options),  # type: ignore[arg-type]
                row["correct_index"],
                row["difficulty"],
                row["explanation"].strip(),
                row["page_number"],
            )
            reviewed.append(question)
            citations[question.prompt] = {
                "display_name": row.get("display_name") or "Course material",
                "page_number": question.page,
            }
    if bank_questions is None and not reviewed:
        raise QuizError("No reviewed questions are available for this topic yet.")
    fallback = tuple(
        question for question in (bank_questions or ())
        if question.prompt.casefold() not in {item.prompt.casefold() for item in reviewed}
    )
    rng = rng or SystemRandom()
    selected: list[_BankQuestion] = []
    for level, count in mix.items():
        source_candidates = [question for question in reviewed if question.difficulty == level]
        fallback_candidates = [question for question in fallback if question.difficulty == level]
        if len(source_candidates) + len(fallback_candidates) < count:
            raise QuizError("No reviewed questions are available for this mastery level yet.")
        source_count = min(count, len(source_candidates))
        selected.extend(rng.sample(source_candidates, source_count))
        selected.extend(rng.sample(fallback_candidates, count - source_count))
    rng.shuffle(selected)

    rendered: list[QuizQuestion] = []
    for question in selected:
        order = list(range(4))
        rng.shuffle(order)
        rendered.append(QuizQuestion(
            prompt=question.prompt,
            options=tuple(question.options[index] for index in order),  # type: ignore[arg-type]
            correct_index=order.index(question.correct_index),
            difficulty=question.difficulty,
            explanation=question.explanation,
            citations=(citations.get(question.prompt, {"display_name": "lA notes.pdf", "page_number": question.page}),),
        ))
    return GeneratedQuiz(
        topic=topic,
        mastery_before=mastery_before,
        difficulty_mix=mix,
        questions=tuple(rendered),
    )


def has_bank_topic(topic: str) -> bool:
    try:
        return validate_topic_name(topic).casefold() in QUESTION_BANK
    except QuizError:
        return False
