import streamlit as st  # type: ignore
from database.db import init_db  # type: ignore
from ui.landing_page import render_landing_page  # type: ignore
from ui.auth_page import render_login_page, render_signup_page  # type: ignore
from ui.sidebar import render_sidebar  # type: ignore
from ui.upload_ui import render_upload_ui  # type: ignore
from ui.dashboard_ui import render_dashboard  # type: ignore
from ui.validation_ui import validation_ui  # type: ignore
from ui.analytics_ui import render_analytics  # type: ignore
from ui.header import render_header  # type: ignore
from ui.styles import apply_global_styles  # type: ignore
from config.translations import get_text  # type: ignore

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Receipt Vault Analyzer",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={"About": "Receipt Vault Analyzer v2.0 — AI-powered expense intelligence."}
)

# ── One-time init ──────────────────────────────────────────────────────────────
if "init_done" not in st.session_state:
    init_db()
    st.session_state["init_done"] = True

if "page"          not in st.session_state: st.session_state["page"]          = "landing"
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if "language"      not in st.session_state: st.session_state["language"]      = "en"


# ── Router ─────────────────────────────────────────────────────────────────────
def main():
    if not st.session_state.get("authenticated", False):
        page = st.session_state.get("page", "landing")
        if page == "landing":
            render_landing_page()
        elif page == "login":
            render_login_page()
        elif page == "signup":
            render_signup_page()
    else:
        apply_global_styles()
        render_main_app()


def render_main_app():
    render_header()
    lang     = st.session_state.get("language", "en")
    app_page = render_sidebar()   # returns the plain translated label

    # Helper — match regardless of language
    def _is(key: str) -> bool:
        return app_page == get_text(lang, key)

    if _is("upload_receipt"):
        render_upload_ui()
    elif _is("dashboard"):
        render_dashboard()
    elif _is("analytics"):
        render_analytics()
    elif _is("validation"):
        validation_ui()
    elif _is("chat"):
        from ui.chat_ui import render_chat  # type: ignore
        render_chat()
    elif _is("erp_integration"):
        from ui.api_ui import render_api_ui  # type: ignore
        render_api_ui()
    else:
        # Fallback — show upload page
        render_upload_ui()


if __name__ == "__main__":
    main()