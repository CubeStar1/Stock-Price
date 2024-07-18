import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime, timedelta
import google.generativeai as genai
from supabase import create_client, Client
# from streamlit_cookies_controller import CookieController
import time
import os
from tessa import Symbol



# Initialize Supabase client
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

@st.cache_resource
def init_db():
    conn = sqlite3.connect('all_stock_data.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS stocks (
        company TEXT,
        start_date TEXT,
        end_date TEXT,
        percent_change REAL
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS stock_lists (
        list_name TEXT,
        tickers TEXT
    )
    ''')
    conn.commit()
    conn.close()


supabase = init_supabase()
if 'supabase_client' not in st.session_state:
    st.session_state.supabase_client = supabase

# Initialize cookie controller
# cookie_name = st.secrets['COOKIE_NAME']
# controller = CookieController(key='cookies')



def sign_up(email, password):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        return response
    except Exception as e:
        st.error(f"Sign up failed: {str(e)}")
        return None

def sign_in(email, password):
    return supabase.auth.sign_in_with_password({"email": email, "password": password})


def sign_out():
    return supabase.auth.sign_out()


if 'user' not in st.session_state:
    # Check for existing session
    session = supabase.auth.get_session()
    if session:
        st.session_state.user = session.user
    else:
        st.session_state.user = None

if st.session_state.user is None:
    st.title("Welcome to Stock Tikr")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        with st.form(key="login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                response = sign_in(email, password)
                if response.user:
                    st.session_state.user = response.user
                    st.success("Logged in successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Login failed. Please check your credentials.")

    with tab2:
        with st.form(key="sign_up_form"):
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign Up"):
                response = sign_up(new_email, new_password)
                if response and response.user:
                    st.success("Account created successfully!")
                    st.info("A verification email has been sent to your email address. Please check your inbox and click the verification link to complete the sign-up process.")
                    st.warning("You won't be able to log in until you've verified your email address.")
                else:
                    st.error("Sign up failed. Please try again.")

else:
    st.success(f"Welcome {st.session_state.user.email}!")
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)

    if "selected_tickers" not in st.session_state:
        st.session_state.selected_tickers = ["AAPL", "GOOGL", "AMZN", "MSFT", "TSLA", "FB"]

    init_db()

    if st.sidebar.button("Logout"):
        sign_out()
        st.session_state.user = None
        st.experimental_rerun()

    st.switch_page("pages/Quarterly.py")