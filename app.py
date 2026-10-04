import smtplib

import streamlit as st
from email.mime.text import MIMEText
from google import genai
from google.genai import types

from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
    SUMMARY_REQUEST_PROMPT,
)


# =========================================================
# CONFIG
# =========================================================

MODEL_NAME = "gemini-3.5-flash"

st.set_page_config(
    page_title="Snap & Study",
    page_icon="📚",
    layout="centered",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #203238;
        --muted-ink: #657579;
        --paper: #f5f7f5;
        --surface: #ffffff;
        --line: #dce5e1;
        --accent: #247b78;
        --accent-dark: #195c5a;
    }

    [data-testid="stAppViewContainer"] {
        background: var(--paper);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    .block-container {
        max-width: 860px;
        padding-top: 3.25rem;
        padding-bottom: 4rem;
    }

    h1 {
        color: var(--ink);
        font-size: 2.15rem;
        letter-spacing: -0.02em;
        margin-bottom: 0.35rem;
    }

    [data-testid="stCaptionContainer"] {
        color: var(--muted-ink);
    }

    [data-testid="stAlert"] {
        border: 1px solid #cfe2df;
        border-radius: 12px;
        background: #edf6f3;
        color: var(--ink);
    }

    div[data-testid="stForm"] {
        border: 1px solid var(--line);
        border-radius: 14px;
        background: var(--surface);
        padding: 1.25rem 1.35rem 1.35rem;
        box-shadow: 0 10px 30px rgba(32, 50, 56, 0.06);
    }

    div[data-testid="stTextInput"] label {
        color: var(--ink);
        font-weight: 600;
    }

    div.stButton > button,
    div[data-testid="stFormSubmitButton"] button {
        border: 1px solid var(--accent);
        border-radius: 10px;
        background: var(--accent);
        color: white;
        font-weight: 700;
        min-height: 2.75rem;
        transition: background 160ms ease, border-color 160ms ease;
    }

    div.stButton > button:hover,
    div[data-testid="stFormSubmitButton"] button:hover {
        border-color: var(--accent-dark);
        background: var(--accent-dark);
        color: white;
    }

    div.stButton > button:disabled {
        border-color: #cbd5d2;
        background: #dfe6e3;
        color: #7d8987;
    }

    [data-testid="stChatMessage"] {
        border: 1px solid var(--line);
        border-radius: 14px;
        background: var(--surface);
        padding: 0.8rem 1rem;
        margin: 0.65rem 0;
        box-shadow: 0 5px 16px rgba(32, 50, 56, 0.04);
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        color: var(--ink);
    }

    [data-testid="stChatInput"] {
        border-color: var(--line);
    }

    [data-testid="stChatInput"] textarea {
        border-radius: 12px;
        background: var(--surface);
    }

    @media (max-width: 640px) {
        .block-container {
            padding-top: 2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        h1 {
            font-size: 1.85rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SECRETS
# =========================================================

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
GMAIL_ADDRESS = st.secrets["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = st.secrets["GMAIL_APP_PASSWORD"]


# =========================================================
# GEMINI CLIENT
# =========================================================

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


# =========================================================
# EMAIL
# =========================================================

def send_email(to_address, subject, body):
    """Send the generated study summary through Gmail."""

    try:
        message = MIMEText(body, "plain", "utf-8")
        message["Subject"] = subject
        message["From"] = GMAIL_ADDRESS
        message["To"] = to_address

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(
                GMAIL_ADDRESS,
                GMAIL_APP_PASSWORD,
            )
            server.send_message(message)

        return True, "Email sent successfully."

    except Exception as error:
        return False, str(error)


# =========================================================
# GEMINI
# =========================================================

def ask_gemini(parts):
    """Send content to the current Gemini conversation."""

    try:
        response = st.session_state.chat.send_message(parts)
        return response.text or "Gemini did not return a response. Please try again."

    except Exception as error:
        return f"Gemini error: {error}"


# =========================================================
# CHAT HELPERS
# =========================================================

def add_message(role, kind, content):
    """Save a message in session history."""

    st.session_state.messages.append(
        {
            "role": role,
            "kind": kind,
            "content": content,
        }
    )


def render_message(message):
    """Display a saved message."""

    with st.chat_message(message["role"]):

        if message["kind"] == "text":
            st.write(message["content"])

        elif message["kind"] == "image":
            st.image(message["content"])


# =========================================================
# ONBOARDING
# =========================================================

if "onboarded" not in st.session_state:

    st.title("📚 Snap & Study")

    st.caption(
        "Snap it. Understand it. Study smarter."
    )

    st.info(
        "Upload a question, notes, diagram, "
        "or textbook page and Gemini will explain it."
    )

    with st.form("onboarding_form"):

        name = st.text_input(
            "Your name",
            placeholder="Enter your name",
        )

        email = st.text_input(
            "Email address",
            placeholder="yourname@gmail.com",
        )

        submitted = st.form_submit_button(
            "Start Learning 🚀",
            use_container_width=True,
        )

    if submitted:

        name = name.strip()
        email = email.strip()

        if not name:
            st.error("Please enter your name.")

        elif not email:
            st.error("Please enter your email address.")

        elif "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            st.error("Please enter a valid email address.")

        else:

            st.session_state.name = name
            st.session_state.email = email

            # Create one persistent Gemini conversation.
            try:
                st.session_state.chat = gemini_client.chats.create(
                    model=MODEL_NAME,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT
                    ),
                )

            except Exception:
                st.error("Could not start Snap & Study. Please try again.")
                st.stop()

            st.session_state.messages = []
            st.session_state.onboarded = True

            st.rerun()

    st.stop()


# =========================================================
# HEADER + EMAIL BUTTON
# =========================================================

header_col, button_col = st.columns(
    [5, 2],
    vertical_alignment="center",
)

with header_col:
    st.title("📚 Snap & Study")

with button_col:

    # Welcome message counts as one message,
    # so require an actual user interaction.
    send_disabled = len(st.session_state.messages) < 2

    if st.button(
        "📧 Send Notes",
        disabled=send_disabled,
        use_container_width=True,
    ):

        with st.spinner(
            "Preparing your study notes..."
        ):

            summary = ask_gemini(
                [SUMMARY_REQUEST_PROMPT]
            )

        success, info = send_email(
            st.session_state.email,
            "📚 Your Snap & Study Notes",
            summary,
        )

        if success:

            st.success(
                "Study notes sent to your email! 📧"
            )

        else:

            st.error(
                f"Email failed: {info}"
            )


st.caption(
    f"Student: {st.session_state.name}"
)


# =========================================================
# DISPLAY CHAT HISTORY
# =========================================================

if not st.session_state.messages:

    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE_TEMPLATE.format(
            name=st.session_state.name
        ),
    )


for message in st.session_state.messages:
    render_message(message)


# =========================================================
# USER INPUT
# =========================================================

user_input = st.chat_input(
    "Ask a question or attach a study image...",
    accept_file=True,
    file_type=[
        "jpg",
        "jpeg",
        "png",
    ],
)


# =========================================================
# PROCESS INPUT
# =========================================================

if user_input:

    parts = []

    photo = (
        user_input.files[0]
        if user_input.files
        else None
    )

    question_text = user_input.text.strip()


    # -----------------------------------------------------
    # IMAGE
    # -----------------------------------------------------

    if photo:

        photo_bytes = photo.getvalue()

        # Save image for chat display.
        add_message(
            "user",
            "image",
            photo_bytes,
        )

        # Send image to Gemini Vision.
        parts.append(
            types.Part.from_bytes(
                data=photo_bytes,
                mime_type=photo.type,
            )
        )


    # -----------------------------------------------------
    # TEXT
    # -----------------------------------------------------

    if question_text:

        add_message(
            "user",
            "text",
            question_text,
        )

        parts.append(question_text)


    # -----------------------------------------------------
    # IMAGE WITHOUT TEXT
    # -----------------------------------------------------

    if photo and not question_text:

        parts.append(
            """
            Analyze this study material carefully.

            If it contains a question:
            - identify the question
            - solve it step by step
            - explain the concept simply

            If it contains notes or a diagram:
            - explain the main concept
            - identify important points

            End with the key points the student should remember.
            """
        )


    # -----------------------------------------------------
    # SEND TO GEMINI
    # -----------------------------------------------------

    if parts:

        with st.spinner(
            "Understanding your study material... 🤔"
        ):

            answer = ask_gemini(parts)

        add_message(
            "assistant",
            "text",
            answer,
        )

        # Refresh UI with the new conversation state.
        st.rerun()