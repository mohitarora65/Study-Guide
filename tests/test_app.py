from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from streamlit.testing.v1 import AppTest
import app as study_app


def test_unconfigured_app_fails_safely() -> None:
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py")
    app.secrets["auth"] = {}
    app.secrets["app"] = {}
    app.secrets["supabase"] = {}
    app.run()

    assert not app.exception
    assert app.error[0].value == "The application is not configured yet."
    assert "secrets.toml" in app.info[0].value


def test_configured_signed_out_app_offers_google_login() -> None:
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py")
    app.secrets["auth"] = {
        "redirect_uri": "http://localhost:8501/oauth2callback",
        "cookie_secret": "c" * 32,
        "client_id": "google-client-id",
        "client_secret": "google-client-secret-value",
        "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
    }
    app.secrets["app"] = {
        "allowed_domain": "iiti.ac.in",
        "admin_emails": ["admin@iiti.ac.in"],
        "user_key_secret": "u" * 32,
    }
    app.secrets["supabase"] = {
        "url": "https://project.supabase.co",
        "service_role_key": "s" * 24,
    }

    app.run()

    assert not app.exception
    assert app.button[0].label == "Sign in with Google"


def test_authenticated_navigation_assigns_unique_page_paths(monkeypatch) -> None:
    pages = []
    monkeypatch.setattr(study_app, "render_account_controls", Mock())
    monkeypatch.setattr(
        study_app.st,
        "Page",
        lambda page, **kwargs: pages.append(kwargs) or page,
    )
    monkeypatch.setattr(
        study_app.st,
        "navigation",
        lambda *_args, **_kwargs: SimpleNamespace(run=Mock()),
    )

    study_app.render_authenticated_app(
        SimpleNamespace(), SimpleNamespace(is_admin=True)
    )

    assert [page["url_path"] for page in pages] == [
        "study",
        "quiz",
        "progress",
        "documents",
        "question-review",
        "quiz-topics",
        "student-progress",
    ]


def test_student_navigation_does_not_include_admin_pages(monkeypatch) -> None:
    pages = []
    monkeypatch.setattr(study_app, "render_account_controls", Mock())
    monkeypatch.setattr(
        study_app.st,
        "Page",
        lambda page, **kwargs: pages.append(kwargs) or page,
    )
    monkeypatch.setattr(
        study_app.st,
        "navigation",
        lambda *_args, **_kwargs: SimpleNamespace(run=Mock()),
    )

    study_app.render_authenticated_app(
        SimpleNamespace(), SimpleNamespace(is_admin=False)
    )

    assert [page["url_path"] for page in pages] == ["study", "quiz", "progress"]


def test_account_controls_default_to_overall_study_mode() -> None:
    script = '''
from types import SimpleNamespace
import app
app.render_account_controls(SimpleNamespace(is_admin=False))
'''
    app = AppTest.from_string(script).run()

    assert not app.exception
    assert app.selectbox[0].value == "overall"
    assert app.selectbox[0].options == ["Mid Sem", "End Sem", "Class Quiz", "Overall"]


def test_study_history_remains_available_when_answer_provider_is_unconfigured() -> None:
    script = '''
import streamlit as st
from types import SimpleNamespace
from unittest.mock import patch
import app

settings = SimpleNamespace(gemini_api_key="g" * 32, ai_star_api_key=None)
identity = SimpleNamespace(user_key="synthetic-owner")
thread = {"id": "thread-1", "title": "Basis question"}
messages = [
    {"role": "user", "content": "What is a basis?", "citations": []},
    {"role": "assistant", "content": "See page 25.", "citations": [
        {"display_name": "notes.pdf", "page_number": 25}
    ]},
]
def load_messages(client, owner, thread_id):
    st.session_state["history_read"] = (owner, thread_id)
    return messages
with patch.object(app, "build_client", return_value=object()), \\
     patch.object(app, "list_threads", return_value=[thread]), \\
     patch.object(app, "list_thread_messages", side_effect=load_messages):
    app.render_study_page(settings, identity)
'''
    app = AppTest.from_string(script).run()

    assert not app.exception
    assert app.chat_input[0].disabled
    assert app.selectbox[0].value == "thread-1"
    assert app.session_state["history_read"] == ("synthetic-owner", "thread-1")


def test_study_submits_question_and_saves_answer_without_live_providers() -> None:
    script = '''
import streamlit as st
from types import SimpleNamespace
from unittest.mock import patch
import app

settings = SimpleNamespace(gemini_api_key="g" * 32, ai_star_api_key="a" * 32)
identity = SimpleNamespace(user_key="synthetic-owner")
def save_turn(client, owner, thread_id, **values):
    st.session_state["saved_turn"] = (owner, thread_id, values)
with patch.object(app, "build_client", return_value=object()), \\
     patch.object(app, "list_threads", return_value=[]), \\
     patch.object(app, "answer_question", return_value=SimpleNamespace(
         text="A basis spans the space with independent vectors.",
         citations=({"chunk_id": "c1", "page_number": 25},),
     )), \\
     patch.object(app, "create_thread", return_value={"id": "thread-new"}), \\
     patch.object(app, "append_turn", side_effect=save_turn):
    app.render_study_page(settings, identity)
'''
    app = AppTest.from_string(script).run()
    assert not app.exception
    app.chat_input[0].set_value("What is a basis?").run()

    assert not app.exception
    owner, thread_id, turn = app.session_state["saved_turn"]
    assert (owner, thread_id) == ("synthetic-owner", "thread-new")
    assert turn["question"] == "What is a basis?"
    assert turn["citations"] == [{"chunk_id": "c1", "page_number": 25}]


def test_quiz_generates_seven_answers_and_saves_only_summary() -> None:
    script = '''
import streamlit as st
from types import SimpleNamespace
from unittest.mock import patch
import app
from study_guide.quizzing import GeneratedQuiz, QuizQuestion

settings = SimpleNamespace(gemini_api_key=None, ai_star_api_key=None)
identity = SimpleNamespace(
    user_key="synthetic-owner", email="student@iiti.ac.in", is_admin=False
)
question = QuizQuestion(
    prompt="Which set is a basis?",
    options=("A", "B", "C", "D"),
    correct_index=0,
    difficulty="easy",
    explanation="A is independent and spanning.",
    citations=({"display_name": "notes.pdf", "page_number": 12},),
)
quiz = GeneratedQuiz(
    topic="Rank and fundamental subspaces",
    mastery_before=None,
    difficulty_mix={"easy": 4, "medium": 3, "hard": 0},
    questions=(question,) * 7,
)
def save_summary(_client, **values):
    st.session_state["saved_quiz_summary"] = values
    return {"score": 100, "mastery_before": None, "mastery_after": 100,
            "attempt_count": 1, "duplicate": False}
with patch.object(app, "build_client", return_value=object()), \\
     patch.object(app, "list_quiz_topics", return_value=[
         {"id": "topic-1", "name": "Rank and fundamental subspaces", "active": True}
     ]), \\
     patch.object(app, "get_topic_mastery", return_value=None), \\
     patch.object(app, "generate_bank_quiz", return_value=quiz), \\
     patch.object(app, "complete_quiz_attempt", side_effect=save_summary):
    app.render_quiz_page(settings, identity)
'''
    app = AppTest.from_string(script).run()
    assert not app.exception

    next(button for button in app.button if button.label == "Start 7-question quiz").click().run()
    assert not app.exception
    assert len(app.radio) == 7
    for radio in app.radio:
        radio.set_value(0)
    next(button for button in app.button if button.label == "Submit all answers").click().run()

    assert not app.exception
    saved = app.session_state["saved_quiz_summary"]
    assert saved["user_key"] == "synthetic-owner"
    assert saved["email"] == "student@iiti.ac.in"
    assert saved["correct_count"] == 7
    assert "questions" not in saved
    assert any("Score: 7/7" in success.value for success in app.success)


def test_failed_quiz_generation_shows_safe_error_without_saving_attempt() -> None:
    script = '''
from types import SimpleNamespace
from unittest.mock import patch
import app
from study_guide.quizzing import QuizError

settings = SimpleNamespace(gemini_api_key="g" * 32, ai_star_api_key="a" * 32)
identity = SimpleNamespace(user_key="synthetic-owner", email="student@iiti.ac.in", is_admin=False)
message = "The quiz could not be prepared. Please try again."
with patch.object(app, "build_client", return_value=object()), \\
     patch.object(app, "list_quiz_topics", return_value=[
         {"id": "topic-1", "name": "Rank and fundamental subspaces", "active": True}
     ]), \\
     patch.object(app, "get_topic_mastery", return_value=None), \\
     patch.object(app, "generate_bank_quiz", side_effect=QuizError(message)), \\
     patch.object(app, "complete_quiz_attempt", side_effect=AssertionError("failed quiz must not be saved")):
    app.render_quiz_page(settings, identity)
'''
    app = AppTest.from_string(script).run()
    next(button for button in app.button if button.label == "Start 7-question quiz").click().run()

    assert not app.exception
    assert any(error.value == "The quiz could not be prepared. Please try again." for error in app.error)
    assert "active_quiz" not in app.session_state
    assert "saved_quiz_summary" not in app.session_state


def test_quiz_page_hides_topics_without_reviewed_bank_content() -> None:
    script = '''
from types import SimpleNamespace
from unittest.mock import patch
import app

with patch.object(app, "build_client", return_value=object()), \\
     patch.object(app, "list_quiz_topics", return_value=[
         {"id": "topic-1", "name": "Unreviewed topic", "active": True}
     ]):
    app.render_quiz_page(SimpleNamespace(), SimpleNamespace(user_key="owner"))
'''
    app = AppTest.from_string(script).run()

    assert not app.exception
    assert app.info[0].value == "No reviewed quiz topics are available yet."
    assert not any(button.label == "Start 7-question quiz" for button in app.button)


def test_quiz_page_shows_topic_with_approved_extracted_questions() -> None:
    script = '''
from types import SimpleNamespace
from unittest.mock import patch
import app

with patch.object(app, "build_client", return_value=object()), \\
     patch.object(app, "list_approved_question_topic_ids", return_value={"topic-1"}), \\
     patch.object(app, "list_quiz_topics", return_value=[
         {"id": "topic-1", "name": "Uploaded topic", "active": True}
     ]):
    app.render_quiz_page(SimpleNamespace(), SimpleNamespace(user_key="owner"))
'''
    app = AppTest.from_string(script).run()

    assert not app.exception
    assert app.selectbox[0].value == "topic-1"
    assert any(button.label == "Start 7-question quiz" for button in app.button)


def test_student_progress_shows_mastery_and_attempt_summaries() -> None:
    script = '''
from types import SimpleNamespace
from unittest.mock import patch
import app

settings = SimpleNamespace()
identity = SimpleNamespace(user_key="synthetic-owner")
with patch.object(app, "build_client", return_value=object()), \\
     patch.object(app, "list_student_quiz_progress", return_value=[{
         "topic": "Vector spaces", "mastery_score": 71,
         "latest_score": 71.43, "attempt_count": 1,
     }]), \\
     patch.object(app, "list_student_quiz_attempts", return_value=[{
         "topic": "Vector spaces", "correct_count": 5, "score": 71.43,
         "mastery_after": 71, "completed_at": "2026-10-10T00:00:00Z",
     }]):
    app.render_quiz_progress_page(settings, identity)
'''
    app = AppTest.from_string(script).run(timeout=10)

    assert not app.exception
    assert [item.value for item in app.subheader] == ["Topic mastery", "Quiz summaries"]
    assert len(app.dataframe) == 2


def test_admin_progress_filter_matches_email_case_insensitively() -> None:
    script = '''
from types import SimpleNamespace
from unittest.mock import patch
import app

rows = [
    {"user_key": "owner-1", "email": "student@iiti.ac.in", "topic": "Vectors",
     "mastery_score": 71, "latest_score": 71.43, "attempt_count": 1,
     "updated_at": "2026-10-10T00:00:00Z"},
    {"user_key": "owner-2", "email": "other@iiti.ac.in", "topic": "Matrices",
     "mastery_score": 50, "latest_score": 50, "attempt_count": 2,
     "updated_at": "2026-10-10T00:00:00Z"},
]
with patch.object(app, "build_client", return_value=object()), \\
     patch.object(app, "list_admin_quiz_progress", return_value=rows):
    app.render_admin_quiz_progress_page(SimpleNamespace())
'''
    app = AppTest.from_string(script).run()
    assert not app.exception

    app.text_input[0].set_value("STUDENT@IITI.AC.IN").run()

    assert not app.exception
    assert len(app.dataframe) == 1
    assert app.dataframe[0].value.iloc[0]["Email"] == "student@iiti.ac.in"


def test_admin_can_add_a_quiz_topic() -> None:
    script = '''
import streamlit as st
from types import SimpleNamespace
from unittest.mock import patch
import app

def create_topic(_client, name):
    st.session_state["created_topic"] = name
with patch.object(app, "build_client", return_value=object()), \\
     patch.object(app, "create_quiz_topic", side_effect=create_topic), \\
     patch.object(app, "list_quiz_topics", return_value=[]):
    app.render_quiz_topics_page(SimpleNamespace())
'''
    app = AppTest.from_string(script).run()
    assert not app.exception

    app.text_input[0].set_value("Vector spaces")
    app.button[0].click().run()

    assert not app.exception
    assert app.session_state["created_topic"] == "Vector spaces"
