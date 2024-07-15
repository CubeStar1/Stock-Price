import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime, timedelta
import google.generativeai as genai
import os
from tessa import Symbol


# Common functions
def get_stock_data(tickers, start_date, end_date, source="yfinance"):
    data = {}
    if source == "yfinance":
        for ticker in tickers:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            if not hist.empty:
                start_price = hist['Close'][0]
                end_price = hist['Close'][-1]
                percent_change = ((end_price - start_price) / start_price) * 100
                data[ticker] = percent_change
    elif source == "tessa":
        for ticker in tickers:
            try:
                stock = Symbol(ticker)
                start_price = stock.price_point(start_date).price
                end_price = stock.price_point(end_date).price
                if start_price and end_price:
                    percent_change = ((end_price - start_price) / start_price) * 100
                    data[ticker] = percent_change
            except Exception as e:
                print(f"Error fetching data for {ticker}: {e}")
    return data


def store_stock_data(data, start_date, end_date):
    # Database connection and initialization
    conn = sqlite3.connect('all_stock_data.db')
    c = conn.cursor()
    for company, percent_change in data.items():
        if percent_change != 0:
            c.execute('''
                INSERT INTO stocks (company, start_date, end_date, percent_change) VALUES (?, ?, ?, ?)
            ''', (company, start_date, end_date, percent_change))
    conn.commit()
    conn.close()


def fetch_stock_data(tickers, start_date, end_date):
    # Database connection and initialization
    conn = sqlite3.connect('all_stock_data.db')
    c = conn.cursor()
    placeholders = ','.join(['?'] * len(tickers))
    query = f'''
        SELECT company, percent_change FROM stocks 
        WHERE start_date = ? AND end_date = ? AND company IN ({placeholders})
    '''
    params = [start_date, end_date] + tickers
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}


def get_date_range(year, quarter):
    if quarter == "Q1":
        return f"{year}-01-01", f"{year}-03-31"
    elif quarter == "Q2":
        return f"{year}-04-01", f"{year}-06-30"
    elif quarter == "Q3":
        return f"{year}-07-01", f"{year}-09-30"
    elif quarter == "Q4":
        return f"{year}-10-01", f"{year}-12-31"


def get_last_n_quarters(n):
    current_date = datetime.now()
    quarters = []
    for i in range(n):
        year = current_date.year
        quarter = (current_date.month - 1) // 3 + 1
        quarters.append((f"Q{quarter}", str(year)))
        current_date -= timedelta(days=90)
    return quarters[::-1]


def get_last_n_years(n):
    current_year = datetime.now().year
    return [str(current_year - i) for i in range(n)][::-1]


def save_stock_list(name, tickers):
    # Database connection and initialization
    conn = sqlite3.connect('all_stock_data.db')
    c = conn.cursor()
    tickers_str = ",".join(tickers)
    c.execute('''
        INSERT INTO stock_lists (list_name, tickers) VALUES (?, ?)
    ''', (name, tickers_str))
    conn.commit()
    conn.close()


def delete_stock_list(name):
    # Database connection and initialization
    conn = sqlite3.connect('all_stock_data.db')
    c = conn.cursor()
    c.execute('''
        DELETE FROM stock_lists WHERE list_name = ?
    ''', (name,))
    conn.commit()
    conn.close()


def load_stock_lists():
    # Database connection and initialization
    conn = sqlite3.connect('all_stock_data.db')
    c = conn.cursor()
    c.execute('''
        SELECT list_name, tickers FROM stock_lists
    ''')
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1].split(",") for row in rows}


def query_llm(prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text


def global_sidebar():
    with st.sidebar:
        with st.container(border=True):
            st.image("static/stocktickr-logo.png")
            with st.expander("Menu", expanded=True):
                st.page_link("pages/Quarterly.py", label="Quarterly", icon="📊")
                st.page_link("pages/Yearly.py", label = "Yearly", icon="📅")
                st.page_link("pages/Stock Price.py", label="Stock Price", icon="💹")
                st.page_link("pages/Compare.py", label="Compare", icon="🔍")
                st.page_link("pages/Sentiment Analysis.py", label="Sentiment Analysis", icon="📈")
                st.page_link("pages/News Feed.py", label="News Feed", icon="📰")
                st.page_link("pages/Earnings Report.py", label="Earnings Report", icon="💰")
                st.page_link("pages/Investment Calculator.py", label="Investment Calculator", icon="🧮")
                # st.page_link("pages/Stock Prediction.py", label="Stock Prediction", icon="🔮")
                st.page_link("pages/Portfolio.py", label="Portfolio", icon="💼")
                # st.page_link("pages/Alerts.py", label="Alerts", icon="🚨")
                st.page_link("pages/Financial Metrics.py", label="Financial Metrics", icon="📈")


def percent_sidebar():
    with st.sidebar:
        with st.container(border=True):
            st.title("Stock Selection")

            if 'stock_lists' not in st.session_state:
                st.session_state.stock_lists = load_stock_lists()
            with st.container(border=True):
                stock_entry_mode = st.radio("Select Stock Entry Mode",
                                            ("Select SOXX Stocks", "Manage Stock Lists", "Query LLM"),
                                            key="stock_way")

            if stock_entry_mode == "Select SOXX Stocks":
                soxx_stocks = ['AVGO', 'NVDA', 'AMD', 'AMAT', 'QCOM', 'LRCX', 'TSM', 'KLAC', 'INTC', 'MRVL', 'MU', 'MPWR',
                               'TXN', 'ASML', 'NXPI', 'ADI', 'MCHP', 'ON', 'TER', 'ENTG', 'SWKS', 'QRVO', 'STM', 'MKSI',
                               'ASX',
                               'LSCC', 'RMBS', 'UMC', 'ACLS', 'WOLF', '8035.T']
                st.session_state.selected_tickers = st.multiselect("Select SOXX component stocks:", options=soxx_stocks,
                                                                   default=['AMAT', 'ASML', 'KLAC', '8035.T', 'LRCX'])

            elif stock_entry_mode == "Manage Stock Lists":
                with st.container(border=True):
                    st.subheader("Manage Stock Lists")

                    list_action = st.radio("Choose an action:", ("Select Existing List", "Create New List"))

                    if list_action == "Select Existing List":
                        if st.session_state.stock_lists:
                            selected_list = st.selectbox("Select a stock list:",
                                                         options=list(st.session_state.stock_lists.keys()))
                            st.session_state.selected_tickers = st.session_state.stock_lists[selected_list]

                            ticker_string = ", ".join(st.session_state.selected_tickers)
                            new_ticker_string = st.text_area("Edit tickers (comma-separated):", value=ticker_string)

                            if st.button("Update List", use_container_width=True):
                                new_tickers = [ticker.strip() for ticker in new_ticker_string.split(",")]
                                save_stock_list(selected_list, new_tickers)
                                st.session_state.stock_lists[selected_list] = new_tickers
                                st.session_state.selected_tickers = new_tickers
                                st.success(f"Updated {selected_list}")

                            if st.button("Delete List", use_container_width=True):
                                delete_stock_list(selected_list)
                                del st.session_state.stock_lists[selected_list]
                                st.success(f"Deleted {selected_list}")
                                st.rerun()
                        else:
                            st.write("No existing lists. Create a new one!")

                    elif list_action == "Create New List":
                        new_list_name = st.text_input("Enter a name for the new stock list:")
                        new_ticker_string = st.text_area("Enter the tickers for the new stock list (comma-separated)")

                        if st.button("Create List"):
                            if new_list_name and new_ticker_string:
                                new_tickers = [ticker.strip() for ticker in new_ticker_string.split(",")]
                                save_stock_list(new_list_name, new_tickers)
                                st.session_state.stock_lists[new_list_name] = new_tickers
                                st.session_state.selected_tickers = new_tickers
                                st.success(f"Created new list: {new_list_name}")
                            else:
                                st.error("Please enter both a name and tickers for the new list.")

            elif stock_entry_mode == "Query LLM":
                with st.container(border=True):
                    st.subheader("Query LLM for Tickers")
                    with st.form("Query LLM"):
                        llm_prompt = "Please provide me with the tickers for the following companies separated by commas. Strictly follow this prompt and respond only with tickers separated by commas, only provide me with tickers for US companies in this prompt: "
                        user_prompt = st.text_area("Enter a prompt for the LLM:")
                        submit_button = st.form_submit_button("Get Tickers")

                        if submit_button:
                            try:
                                response = query_llm(llm_prompt + user_prompt)
                                st.write(response)
                                selected_tickers = [ticker.strip() for ticker in response.split(",")]
                                st.session_state.selected_tickers = selected_tickers
                                st.success("Tickers retrieved successfully!")
                            except Exception as e:
                                st.error(f"Error fetching data: {e}")

            with st.container(border=True):
                st.subheader("Selected Tickers")
                st.write(", ".join(st.session_state.selected_tickers))

