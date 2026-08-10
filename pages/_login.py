# pages/_login.py

import streamlit as st
from sqlalchemy import func

from database import SessionLocal
from models import User


def login_page():
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    st.set_page_config(page_title="Automation Studio", layout="wide")

    st.markdown("""
    <style>

    #MainMenu {visibility:hidden;}
    header {visibility:hidden;}
    footer {visibility:hidden;}

    .stApp{
        background:#ffffff;
    }

    .block-container{
        padding-top:2rem;
        padding-bottom:2rem;
        max-width:900px;
    }

    input{
        border-radius:10px !important;
    }

    .login-card{
        background:#fff;
        border:1px solid #efefef;
        border-radius:22px;
        overflow:hidden;
        box-shadow:0 12px 35px rgba(0,0,0,.05);
    }

    .left-panel{
        background:#fafafa;
        padding:55px 40px;
        text-align:center;
        height:100%;
    }

    .right-panel{
        padding:50px 40px;
    }

    .welcome{
        font-size:11px;
        color:#888;
        letter-spacing:2px;
        font-weight:600;
        text-transform:uppercase;
    }

    .title{
        font-size:28px;
        font-weight:700;
        margin-top:5px;
        margin-bottom:25px;
        color:#111;
    }

    .logo{
        font-size:72px;
    }

    .heading{
        font-size:24px;
        font-weight:700;
        margin-top:10px;
        color:#222;
    }

    .subtitle{
        color:#777;
        font-size:13px;
        line-height:22px;
    }

    div[data-testid="stForm"]{
        border:none;
        padding:0;
    }

    .stButton>button,
    button[kind="primary"]{
        width:100%;
        border-radius:10px;
        background:#111;
        color:white;
        font-weight:600;
        height:45px;
        border:none;
    }

    </style>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container():

        left, right = st.columns([1, 1], gap="large")

        with left:
            st.markdown(
                """
                <div class="left-panel">
                    <div class="logo">📊</div>
                        <div class="heading">
                        Automation Studio
                        </div>
                        <div class="subtitle">
                            Smart Reporting<br>
                            Automated Emails<br>
                        </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with right:

            st.markdown(
                """
                <div class="welcome">
                    WELCOME BACK
                </div>

                <div class="title">
                    Sign in to your account
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("login_form"):

                email = st.text_input(
                    "Email",
                    placeholder="admin@company.com",
                    label_visibility="collapsed",
                )

                password = st.text_input(
                    "Password",
                    placeholder="Password",
                    type="password",
                    label_visibility="collapsed",
                )

                submitted = st.form_submit_button(
                    "Sign In",
                    use_container_width=True,
                    type="primary",
                )

                if submitted:

                    if not email or not password:
                        st.error("Please enter email and password.")
                        st.stop()

                    db = SessionLocal()

                    try:
                        user = (
                            db.query(User)
                            .filter(
                                func.lower(User.email) == email.lower(),
                                User.is_active == "Y",
                            )
                            .first()
                        )

                    finally:
                        db.close()

                    if user and User.verify_password(password, user.password_hash):

                        st.session_state.authenticated = True
                        st.session_state.user_id = user.id
                        st.session_state.user_name = (
                            user.full_name if user.full_name else user.email
                        )
                        st.session_state.user_role = (
                            user.role.value if user.role else "viewer"
                        )

                        st.success("Login successful!")

                        st.rerun()

                    else:
                        st.error("Invalid email or password.")