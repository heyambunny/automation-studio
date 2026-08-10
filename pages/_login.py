import streamlit as st
from sqlalchemy import func
from database import SessionLocal
from models import User
from textwrap import dedent


def login_page():

    # ---------------------------------------------------------
    # Session state
    # ---------------------------------------------------------

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # ---------------------------------------------------------
    # Page config
    # ---------------------------------------------------------

    st.set_page_config(
        page_title="Automation Studio",
        page_icon="⚡",
        layout="centered"
    )

    # ---------------------------------------------------------
    # CSS
    # ---------------------------------------------------------

    st.markdown(
        """
        <style>

        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {
            --ink: #12141c;
            --ink-soft: #4b4f5d;
            --paper: #f6f5f2;
            --card: #ffffff;
            --line: #e8e6e1;
            --amber: #d98e2b;
            --amber-soft: #fbe9d0;
            --danger: #c0432c;
            --danger-bg: #fbeae6;
        }

        /* -----------------------------------------------------
           Global
        ----------------------------------------------------- */

        * {
            font-family: 'Inter', sans-serif;
        }

        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {
            width: 100% !important;
            height: 100vh !important;
            max-height: 100vh !important;
            overflow: hidden !important;
            background: var(--paper) !important;
        }

        #MainMenu {
            visibility: hidden !important;
        }

        header {
            visibility: hidden !important;
        }

        footer {
            visibility: hidden !important;
        }

        section[data-testid="stSidebar"] {
            display: none !important;
        }

        /* -----------------------------------------------------
           Main page

           40px outer spacing around the login card.
        ----------------------------------------------------- */

        [data-testid="stMainBlockContainer"] {
            width: 100% !important;
            max-width: 100% !important;

            height: 100vh !important;
            max-height: 100vh !important;

            padding: 40px !important;
            margin: 0 !important;

            display: flex !important;
            align-items: center !important;
            justify-content: center !important;

            box-sizing: border-box !important;
            overflow: hidden !important;

            background: var(--paper) !important;

            background-image:
                radial-gradient(
                    circle at 1px 1px,
                    rgba(18, 20, 28, 0.06) 1px,
                    transparent 0
                );

            background-size: 26px 26px;
        }

        /* -----------------------------------------------------
           Streamlit wrapper
        ----------------------------------------------------- */

        [data-testid="stMainBlockContainer"] > div {
            width: 100% !important;
            max-width: 100% !important;

            padding: 0 !important;
            margin: 0 !important;

            display: flex !important;
            align-items: center !important;
            justify-content: center !important;

            box-sizing: border-box !important;
        }

        /* -----------------------------------------------------
           Login card

           This is the ONLY element receiving the white card
           background.
        ----------------------------------------------------- */

        div[data-testid="stVerticalBlock"]:has(> div .card-marker) {
            width: 460px !important;
            max-width: 100% !important;

            margin: 0 auto !important;

            padding: 38px 44px 28px !important;

            background: var(--card) !important;

            border: 1px solid var(--line) !important;
            border-radius: 18px !important;

            box-sizing: border-box !important;

            box-shadow:
                0 1px 2px rgba(18, 20, 28, 0.04),
                0 12px 32px rgba(18, 20, 28, 0.06) !important;

            gap: 0 !important;
        }

        .card-marker {
            display: none !important;
        }

        /* -----------------------------------------------------
           Brand
        ----------------------------------------------------- */

        .brand-row {
            display: flex;
            align-items: center;
            justify-content: center;

            gap: 10px;

            margin-bottom: 22px;
        }

        .logo-icon {
            width: 34px;
            height: 34px;

            background: var(--ink);

            border-radius: 9px;

            display: flex;
            align-items: center;
            justify-content: center;

            font-size: 16px;
            color: var(--amber);

            flex-shrink: 0;
        }

        .brand-name {
            font-family: 'Space Grotesk', sans-serif;

            font-weight: 600;
            font-size: 15px;

            color: var(--ink);

            letter-spacing: -0.01em;
        }

        /* -----------------------------------------------------
           Status
        ----------------------------------------------------- */

        .status-line {
            font-family: 'JetBrains Mono', monospace;

            font-size: 10.5px;

            color: var(--ink-soft);

            display: flex;
            align-items: center;
            justify-content: center;

            gap: 6px;

            margin: -8px 0 26px;

            letter-spacing: 0.01em;

            text-align: center;
        }

        .status-dot {
            width: 6px;
            height: 6px;

            border-radius: 50%;

            background: var(--amber);

            box-shadow:
                0 0 0 3px var(--amber-soft);

            flex-shrink: 0;
        }

        /* -----------------------------------------------------
           Heading
        ----------------------------------------------------- */

        div[data-testid="stVerticalBlock"]:has(> div .card-marker) h2 {
            font-family: 'Space Grotesk', sans-serif;

            font-size: 24px;
            font-weight: 600;

            color: var(--ink);

            margin: 0 0 4px;

            letter-spacing: -0.01em;

            text-align: center;
        }

        .subtitle {
            color: var(--ink-soft);

            font-size: 13px;

            margin: 0 0 26px;

            text-align: center;
        }

        /* -----------------------------------------------------
           Form
        ----------------------------------------------------- */

        [data-testid="stForm"] {
            border: none !important;

            padding: 0 !important;
            margin: 0 !important;

            background: transparent !important;

            box-shadow: none !important;
        }

        /* -----------------------------------------------------
           Labels
        ----------------------------------------------------- */

        .input-label {
            font-size: 10.5px;

            font-weight: 600;

            color: var(--ink-soft);

            margin-bottom: 6px;

            text-transform: uppercase;

            letter-spacing: 0.06em;
        }

        /* -----------------------------------------------------
           Inputs
        ----------------------------------------------------- */

        div[data-testid="stTextInput"] {
            width: 100% !important;

            margin: 0 !important;
        }

        div[data-testid="stTextInput"] input {
            width: 100% !important;

            background: var(--paper) !important;

            border: 1.5px solid var(--line) !important;

            border-radius: 10px !important;

            padding: 12px 14px !important;

            font-size: 13.5px !important;

            color: var(--ink) !important;

            box-sizing: border-box !important;
        }

        div[data-testid="stTextInput"] input:focus {
            border-color: var(--ink) !important;

            background: var(--card) !important;

            box-shadow:
                0 0 0 3px rgba(18, 20, 28, 0.06) !important;
        }

        div[data-testid="stTextInput"] input::placeholder {
            color: #b9b6ae !important;
        }

        /* -----------------------------------------------------
           Forgot password
        ----------------------------------------------------- */

        .forgot-row {
            display: flex;
            justify-content: flex-end;

            margin-top: 6px;
            margin-bottom: 22px;
        }

        .forgot-row a {
            font-size: 11.5px;

            color: var(--ink-soft);

            text-decoration: none;

            font-weight: 500;

            border-bottom: 1px solid transparent;
        }

        .forgot-row a:hover {
            border-bottom: 1px solid var(--ink-soft);
        }

        /* -----------------------------------------------------
           Sign in button
        ----------------------------------------------------- */

        div[data-testid="stFormSubmitButton"] {
            width: 100% !important;
        }

        div[data-testid="stFormSubmitButton"] button {
            width: 100% !important;

            background: var(--ink) !important;

            border: none !important;

            color: var(--paper) !important;

            font-weight: 600 !important;

            font-size: 13.5px !important;

            padding: 12px !important;

            border-radius: 10px !important;

            height: auto !important;

            transition: background 0.15s ease;
        }

        div[data-testid="stFormSubmitButton"] button:hover {
            background: #262a38 !important;
        }

        /* -----------------------------------------------------
           Alerts
        ----------------------------------------------------- */

        .stAlert {
            background: var(--danger-bg) !important;

            border: 1px solid #f0c8bc !important;

            border-radius: 10px !important;

            color: var(--danger) !important;

            font-size: 12px !important;
        }

        div[data-testid="stAlertContentSuccess"] {
            color: #2f7a4f !important;
        }

        /* -----------------------------------------------------
           Footer text
        ----------------------------------------------------- */

        .footnote {
            text-align: center;

            font-size: 11px;

            color: var(--ink-soft);

            margin-top: 22px;

            opacity: 0.8;
        }

        /* -----------------------------------------------------
           Mobile
        ----------------------------------------------------- */

        @media (max-width: 560px) {

            [data-testid="stMainBlockContainer"] {
                padding: 20px !important;
            }

            div[data-testid="stVerticalBlock"]:has(> div .card-marker) {
                width: 100% !important;
                max-width: 100% !important;

                padding: 28px 22px 22px !important;
            }

            div[data-testid="stVerticalBlock"]:has(> div .card-marker) h2 {
                font-size: 22px;
            }
        }

        </style>
        """,
        unsafe_allow_html=True
    )

    # ---------------------------------------------------------
    # Login container
    # ---------------------------------------------------------

    with st.container():

        # CSS marker
        st.markdown(
            '<div class="card-marker"></div>',
            unsafe_allow_html=True
        )

        # -----------------------------------------------------
        # Brand / Header
        # -----------------------------------------------------

        st.markdown(
            dedent(
                """
                <div class="brand-row">
                    <div class="logo-icon">⚡</div>
                    <div class="brand-name">Automation Studio</div>
                </div>

                <div class="status-line">
                    <span class="status-dot"></span>
                    128 automations running · synced 2m ago
                </div>

                <h2>Sign in</h2>

                <p class="subtitle">
                    Welcome back — Enter your details to continue
                </p>
                """
            ),
            unsafe_allow_html=True
        )

        # -----------------------------------------------------
        # Login form
        # -----------------------------------------------------

        with st.form(
            "login_form",
            clear_on_submit=False
        ):

            # Email label
            st.markdown(
                '<div class="input-label">Email</div>',
                unsafe_allow_html=True
            )

            # Email input
            email = st.text_input(
                "Email",
                placeholder="admin@company.com",
                label_visibility="collapsed",
                key="le"
            )

            # Spacing
            st.markdown(
                '<div style="height:14px;"></div>',
                unsafe_allow_html=True
            )

            # Password label
            st.markdown(
                '<div class="input-label">Password</div>',
                unsafe_allow_html=True
            )

            # Password input
            password = st.text_input(
                "Password",
                placeholder="••••••••",
                type="password",
                label_visibility="collapsed",
                key="lp"
            )

            # Forgot password
            st.markdown(
                dedent(
                    """
                    <div class="forgot-row">
                        <a href="#">Forgot password?</a>
                    </div>
                    """
                ),
                unsafe_allow_html=True
            )

            # Submit button
            submitted = st.form_submit_button(
                "Sign In",
                type="primary",
                use_container_width=True
            )

            # -------------------------------------------------
            # Login processing
            # -------------------------------------------------

            if submitted:

                if not email or not password:

                    st.error(
                        "Please enter your email and password."
                    )

                else:

                    db = SessionLocal()
                    user = None

                    try:

                        user = (
                            db.query(User)
                            .filter(
                                func.lower(User.email) == email.lower(),
                                User.is_active == "Y"
                            )
                            .first()
                        )

                    except Exception:

                        pass

                    finally:

                        db.close()

                    # -----------------------------------------
                    # Verify credentials
                    # -----------------------------------------

                    if user and User.verify_password(
                        password,
                        user.password_hash
                    ):

                        st.session_state.authenticated = True

                        st.session_state.user_id = user.id

                        st.session_state.user_name = (
                            user.full_name
                            or user.email
                        )

                        st.session_state.user_role = (
                            user.role.value
                            if user.role
                            else "viewer"
                        )

                        st.success(
                            "Login successful!"
                        )

                        import time

                        time.sleep(0.5)

                        st.rerun()

                    else:

                        st.error(
                            "Invalid email or password."
                        )

        # -----------------------------------------------------
        # Footnote
        # -----------------------------------------------------

        st.markdown(
            dedent(
                """
                <div class="footnote">
                    Protected access · Automation Studio internal
                </div>
                """
            ),
            unsafe_allow_html=True
        )