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

    assert [page["url_path"] for page in pages] == ["study", "documents"]


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
