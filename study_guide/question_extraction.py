from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from study_guide.ingestion import ExtractedPage
from study_guide.study_modes import validate_material_type, validate_study_scopes


_QUESTION = re.compile(r"^\s*(?:q(?:uestion)?\s*)?(\d{1,3})[.)\-:]\s+(.+)$", re.I)
_OPTION = re.compile(r"^\s*[(\[]?([A-Da-d])[).\]:\-]\s+(.+)$")
_ANSWER = re.compile(r"^\s*(?:answer|ans(?:wer)?\.?|correct)\s*[:\-]\s*([A-Da-d])\b", re.I)
_THEORY_HEADING = re.compile(r"^\s*(?:review\s+)?(?:questions?|exercises?|problems?)\s*$", re.I)


@dataclass(frozen=True)
class ExtractedQuestion:
    page_number: int
    prompt: str
    options: tuple[str, ...] | None
    correct_index: int | None
    content_hash: str


def extract_question_candidates(
    pages: tuple[ExtractedPage, ...], material_type: str
) -> tuple[ExtractedQuestion, ...]:
    material_type = validate_material_type(material_type)
    candidates: list[ExtractedQuestion] = []
    seen: set[str] = set()
    theory_section = material_type == "questions"

    for page in pages:
        lines = [line.strip() for line in page.text.splitlines() if line.strip()]
        if material_type == "theory":
            # shortcut: question mode lasts to EOF; add end-heading detection if it drafts later numbered text.
            theory_section = theory_section or any(
                _THEORY_HEADING.fullmatch(line.rstrip(":")) for line in lines
            )
        if not theory_section:
            continue

        starts = [index for index, line in enumerate(lines) if _QUESTION.match(line)]
        for position, start in enumerate(starts):
            end = starts[position + 1] if position + 1 < len(starts) else len(lines)
            block = lines[start:end]
            first = _QUESTION.match(block[0])
            if not first:
                continue
            prompt_parts = [first.group(2)]
            options: dict[str, str] = {}
            correct_index = None
            for line in block[1:]:
                option = _OPTION.match(line)
                answer = _ANSWER.match(line)
                if option:
                    options[option.group(1).upper()] = option.group(2).strip()
                elif answer:
                    correct_index = ord(answer.group(1).upper()) - ord("A")
                elif not options:
                    prompt_parts.append(line)
            prompt = " ".join(prompt_parts).strip()[:1000]
            normalized = " ".join(prompt.casefold().split())
            content_hash = hashlib.sha256(normalized.encode()).hexdigest()
            if len(prompt) < 3 or content_hash in seen:
                continue
            seen.add(content_hash)
            ordered = tuple(options.get(letter, "") for letter in "ABCD")
            complete_options = ordered if all(ordered) else None
            candidates.append(
                ExtractedQuestion(
                    page_number=page.page_number,
                    prompt=prompt,
                    options=complete_options,
                    correct_index=correct_index if complete_options else None,
                    content_hash=content_hash,
                )
            )
    return tuple(candidates)


def candidate_rows(
    questions: tuple[ExtractedQuestion, ...],
    *,
    document_id: str,
    version_id: str,
    material_type: str,
    study_scopes: tuple[str, ...],
) -> list[dict[str, object]]:
    material_type = validate_material_type(material_type)
    scopes = validate_study_scopes(study_scopes)
    return [
        {
            "document_id": document_id,
            "version_id": version_id,
            "page_number": question.page_number,
            "source_kind": material_type,
            "prompt": question.prompt,
            "options": list(question.options) if question.options else None,
            "correct_index": question.correct_index,
            "study_scopes": list(scopes),
            "content_hash": question.content_hash,
        }
        for question in questions
    ]
