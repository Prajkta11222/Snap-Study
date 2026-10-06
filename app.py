import smtplib
import time

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ── Design tokens ────────────────────────────────── */
    :root {
        --ink:         #1a2e35;
        --ink-soft:    #3d5a63;
        --muted-ink:   #6b8a91;
        --paper:       #f4f7f6;
        --surface:     #ffffff;
        --surface-alt: #f9fbfa;
        --line:        #dde6e3;
        --line-light:  #eaf0ee;
        --accent:      #1a8a7d;
        --accent-hover:#137a6e;
        --accent-light:#e6f5f2;
        --accent-glow: rgba(26, 138, 125, 0.12);
        --shadow-sm:   0 1px 3px rgba(26, 46, 53, 0.04),
                       0 4px 12px rgba(26, 46, 53, 0.03);
        --shadow-md:   0 2px 8px rgba(26, 46, 53, 0.05),
                       0 8px 28px rgba(26, 46, 53, 0.06);
        --shadow-lg:   0 4px 12px rgba(26, 46, 53, 0.06),
                       0 16px 40px rgba(26, 46, 53, 0.08);
        --radius-sm:   8px;
        --radius-md:   12px;
        --radius-lg:   16px;
        --font:        'Inter', -apple-system, BlinkMacSystemFont,
                       'Segoe UI', Roboto, sans-serif;
    }

    /* ── Global base ──────────────────────────────────── */
    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stApp"] {
        font-family: var(--font) !important;
    }

    [data-testid="stAppViewContainer"] {
        background: var(--paper);
    }

    [data-testid="stHeader"] {
        background: transparent !important;
    }

    .block-container {
        max-width: 840px;
        padding-top: 2.5rem;
        padding-bottom: 3.5rem;
    }

    /* ── Fade-in animation ────────────────────────────── */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ── Typography ───────────────────────────────────── */
    h1 {
        font-family: var(--font) !important;
        color: var(--ink);
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin-bottom: 0.15rem;
        line-height: 1.2;
    }

    h2, h3, h4 {
        font-family: var(--font) !important;
        color: var(--ink);
        letter-spacing: -0.015em;
    }

    p, li, span, div {
        font-family: var(--font) !important;
    }

    [data-testid="stCaptionContainer"] {
        color: var(--muted-ink);
        font-size: 0.88rem;
        font-weight: 500;
        letter-spacing: 0.01em;
    }

    /* ── Alert / info box ─────────────────────────────── */
    [data-testid="stAlert"] {
        border: 1px solid var(--line);
        border-radius: var(--radius-md);
        background: var(--accent-light);
        color: var(--ink-soft);
        font-size: 0.92rem;
        animation: fadeInUp 0.4s ease-out;
    }

    /* ── Onboarding form ──────────────────────────────── */
    div[data-testid="stForm"] {
        border: 1px solid var(--line);
        border-radius: var(--radius-lg);
        background: var(--surface);
        padding: 1.6rem 1.5rem 1.65rem;
        box-shadow: var(--shadow-md);
        animation: fadeInUp 0.45s ease-out 0.1s both;
    }

    /* ── Input fields ─────────────────────────────────── */
    div[data-testid="stTextInput"] label {
        color: var(--ink);
        font-weight: 600;
        font-size: 0.88rem;
        letter-spacing: 0.01em;
        margin-bottom: 0.25rem;
    }

    div[data-testid="stTextInput"] input {
        border: 1.5px solid var(--line) !important;
        border-radius: var(--radius-sm) !important;
        background: var(--surface-alt) !important;
        font-family: var(--font) !important;
        font-size: 0.92rem !important;
        padding: 0.6rem 0.75rem !important;
        transition: border-color 200ms ease, box-shadow 200ms ease;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-glow) !important;
    }

    /* ── Buttons ──────────────────────────────────────── */
    div.stButton > button,
    div[data-testid="stFormSubmitButton"] button {
        border: none;
        border-radius: var(--radius-sm);
        background: var(--accent);
        color: white;
        font-family: var(--font) !important;
        font-weight: 700;
        font-size: 0.92rem;
        letter-spacing: 0.01em;
        min-height: 2.75rem;
        box-shadow: 0 2px 8px rgba(26, 138, 125, 0.18);
        transition: all 200ms ease;
    }

    div.stButton > button:hover,
    div[data-testid="stFormSubmitButton"] button:hover {
        background: var(--accent-hover);
        color: white;
        box-shadow: 0 4px 14px rgba(26, 138, 125, 0.25);
        transform: translateY(-1px);
    }

    div.stButton > button:active,
    div[data-testid="stFormSubmitButton"] button:active {
        transform: translateY(0);
        box-shadow: 0 2px 6px rgba(26, 138, 125, 0.15);
    }

    div.stButton > button:disabled {
        border: none;
        background: var(--line);
        color: var(--muted-ink);
        box-shadow: none;
        transform: none;
        cursor: not-allowed;
    }

    /* ── Chat messages ────────────────────────────────── */
    [data-testid="stChatMessage"] {
        border: 1px solid var(--line-light);
        border-radius: var(--radius-lg);
        background: var(--surface);
        padding: 0.85rem 1.1rem;
        margin: 0.5rem 0;
        box-shadow: var(--shadow-sm);
        animation: fadeInUp 0.35s ease-out;
        transition: box-shadow 200ms ease;
    }

    [data-testid="stChatMessage"]:hover {
        box-shadow: var(--shadow-md);
    }

    /* Assistant bubble — subtle teal tint */
    [data-testid="stChatMessage"][data-testid-type="assistant"],
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background: linear-gradient(135deg, var(--surface) 0%, #f2faf8 100%);
        border-color: #d3ece7;
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        color: var(--ink);
        line-height: 1.65;
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
        margin-bottom: 0.5em;
    }

    /* ── Chat input ───────────────────────────────────── */
    [data-testid="stChatInput"] {
        border-color: var(--line);
    }

    [data-testid="stChatInput"] textarea {
        border-radius: var(--radius-md) !important;
        background: var(--surface) !important;
        font-family: var(--font) !important;
        font-size: 0.92rem !important;
        border: 1.5px solid var(--line) !important;
        transition: border-color 200ms ease, box-shadow 200ms ease;
    }

    [data-testid="stChatInput"] textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-glow) !important;
    }

    /* ── Spinner ──────────────────────────────────────── */
    [data-testid="stSpinner"] {
        color: var(--accent) !important;
    }

    /* ── Success / Error messages ──────────────────────── */
    div[data-testid="stAlert"][data-baseweb] {
        border-radius: var(--radius-md);
        font-size: 0.92rem;
    }

    /* ── Scrollbar polish ─────────────────────────────── */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: var(--line);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--muted-ink);
    }

    /* ── Images in chat ───────────────────────────────── */
    [data-testid="stChatMessage"] [data-testid="stImage"] img {
        border-radius: var(--radius-md);
        border: 1px solid var(--line-light);
    }

    /* ── Responsive ───────────────────────────────────── */
    @media (max-width: 640px) {
        .block-container {
            padding-top: 1.5rem;
            padding-left: 0.85rem;
            padding-right: 0.85rem;
        }

        h1 {
            font-size: 1.65rem;
        }

        div[data-testid="stForm"] {
            padding: 1.25rem 1.1rem 1.3rem;
        }

        [data-testid="stChatMessage"] {
            padding: 0.7rem 0.85rem;
            border-radius: var(--radius-md);
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

    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = st.session_state.chat.send_message(parts)
            return response.text or "Gemini did not return a response. Please try again."

        except Exception as error:
            if "503" in str(error) and attempt < max_retries - 1:
                time.sleep(2)
                continue
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