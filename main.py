import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime, timedelta
import google.generativeai as genai
import os
from tessa import Symbol

st.set_page_config(layout="wide", page_icon="📈", page_title="Stock Tikr")

api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

if "selected_tickers" not in st.session_state:
    st.session_state.selected_tickers = ["AAPL", "GOOGL", "AMZN", "MSFT", "TSLA", "FB"]

def init_db():
    # Database connection and initialization
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


init_db()

st.switch_page("pages/Quarterly.py")
