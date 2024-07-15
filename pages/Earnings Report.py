import streamlit as st
import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime
from utils import global_sidebar, percent_sidebar
import plotly.graph_objects as go


def init_db():
    conn_fs = sqlite3.connect('financial_statements.db')
    c_fs = conn_fs.cursor()
    c_fs.execute('''
    CREATE TABLE IF NOT EXISTS annual_income_statement (
        ticker TEXT,
        date TIMESTAMP,
        data TEXT
    )
    ''')
    c_fs.execute('''
    CREATE TABLE IF NOT EXISTS quarterly_income_statement (
        ticker TEXT,
        date TIMESTAMP,
        data TEXT
    )
    ''')
    c_fs.execute('''
    CREATE TABLE IF NOT EXISTS annual_balance_sheet (
        ticker TEXT,
        date TIMESTAMP,
        data TEXT
    )
    ''')
    c_fs.execute('''
    CREATE TABLE IF NOT EXISTS quarterly_balance_sheet (
        ticker TEXT,
        date TIMESTAMP,
        data TEXT
    )
    ''')
    c_fs.execute('''
    CREATE TABLE IF NOT EXISTS annual_cashflow (
        ticker TEXT,
        date TIMESTAMP,
        data TEXT
    )
    ''')
    c_fs.execute('''
    CREATE TABLE IF NOT EXISTS quarterly_cashflow (
        ticker TEXT,
        date TIMESTAMP,
        data TEXT
    )
    ''')
    conn_fs.commit()
    conn_fs.close()

init_db()


# # Helper function to retrieve data from the database
# def get_data_from_db(table, ticker):
#     c_fs.execute(f'SELECT data FROM {table} WHERE ticker = ? ORDER BY date DESC LIMIT 1', (ticker,))
#     result = c_fs.fetchone()
#     if result:
#         return pd.read_json(result[0])
#     else:
#         return None

def get_data_from_db(table, ticker):
    conn_fs = sqlite3.connect('financial_statements.db')
    c_fs = conn_fs.cursor()
    c_fs.execute(f'SELECT data FROM {table} WHERE ticker = ? ORDER BY date DESC LIMIT 1', (ticker,))
    result = c_fs.fetchone()
    if result:
        return pd.read_json(result[0])
    else:
        return None

# # Helper function to store data in the database
# def store_data_in_db(table, ticker, data):
#     c_fs.execute(f'INSERT INTO {table} (ticker, date, data) VALUES (?, ?, ?)', (ticker, datetime.now(), data.to_json()))
#     conn_fs.commit()


def store_data_in_db(table, ticker, data):
    conn_fs = sqlite3.connect('financial_statements.db')
    c_fs = conn_fs.cursor()
    c_fs.execute(f'INSERT INTO {table} (ticker, date, data) VALUES (?, ?, ?)', (ticker, datetime.now(), data.to_json()))
    conn_fs.commit()
    conn_fs.close()

# Streamlit app for Financial Statements
def earnings_report():
    st.title("Financial Statements")

    ticker = st.text_input("Enter a stock ticker (e.g. AAPL)", "LRCX")
    # if st.button("Submit"):
    if not ticker.strip():
        st.error("Please provide a valid stock ticker.")
    else:
        try:
            with st.spinner('Please wait...'):
                stock = yf.Ticker(ticker)
                with st.container(border=True):
                    # Income Statement
                    st.subheader("Income Statement (Annual)")
                    annual_income_stmt = get_data_from_db('annual_income_statement', ticker)
                    if annual_income_stmt is None:
                        annual_income_stmt = stock.financials.transpose()
                        store_data_in_db('annual_income_statement', ticker, annual_income_stmt)
                    st.dataframe(annual_income_stmt.transpose(), use_container_width=True)

                    st.subheader("Income Statement (Quarterly)")
                    quarterly_income_stmt = get_data_from_db('quarterly_income_statement', ticker)
                    if quarterly_income_stmt is None:
                        quarterly_income_stmt = stock.quarterly_financials.transpose()
                        store_data_in_db('quarterly_income_statement', ticker, quarterly_income_stmt)
                    st.dataframe(quarterly_income_stmt.transpose() , use_container_width=True)


                with st.container(border=True):
                    # Balance Sheet
                    st.subheader("Balance Sheet (Annual)")
                    annual_balance_sheet = get_data_from_db('annual_balance_sheet', ticker)
                    if annual_balance_sheet is None:
                        annual_balance_sheet = stock.balance_sheet.transpose()
                        store_data_in_db('annual_balance_sheet', ticker, annual_balance_sheet)
                    st.dataframe(annual_balance_sheet.transpose(), use_container_width=True)

                    st.subheader("Balance Sheet (Quarterly)")
                    quarterly_balance_sheet = get_data_from_db('quarterly_balance_sheet', ticker)
                    if quarterly_balance_sheet is None:
                        quarterly_balance_sheet = stock.quarterly_balance_sheet.transpose()
                        store_data_in_db('quarterly_balance_sheet', ticker, quarterly_balance_sheet)
                    st.dataframe(quarterly_balance_sheet.transpose(), use_container_width=True)


                with st.container(border=True):
                    # Cash Flow Statement
                    st.subheader("Cash Flow Statement (Annual)")
                    annual_cashflow = get_data_from_db('annual_cashflow', ticker)
                    if annual_cashflow is None:
                        annual_cashflow = stock.cashflow.transpose()
                        store_data_in_db('annual_cashflow', ticker, annual_cashflow)
                    st.dataframe(annual_cashflow.transpose(), use_container_width=True)

                    st.subheader("Cash Flow Statement (Quarterly)")
                    quarterly_cashflow = get_data_from_db('quarterly_cashflow', ticker)
                    if quarterly_cashflow is None:
                        quarterly_cashflow = stock.quarterly_cashflow.transpose()
                        store_data_in_db('quarterly_cashflow', ticker, quarterly_cashflow)
                    st.dataframe(quarterly_cashflow.transpose(), use_container_width=True)

                # Sankey Chart for Annual Income Statement
                # if annual_income_stmt is not None:
                #     st.subheader("Sankey Chart (Annual Income Statement)")
                #     sankey_data = create_sankey_chart(annual_income_stmt)
                #     st.plotly_chart(sankey_data)

        except Exception as e:
            st.exception(f"An error occurred: {e}")

def create_sankey_chart(df):
    labels = []
    source = []
    target = []
    value = []

    for i, column in enumerate(df.columns):
        labels.append(column)
        if i > 0:
            source.append(i - 1)
            target.append(i)
            value.append(df.iloc[0, i])

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels
        ),
        link=dict(
            source=source,
            target=target,
            value=value
        )
    )])

    fig.update_layout(title_text="Sankey Diagram of Annual Income Statement", font_size=10)
    return fig


global_sidebar()
earnings_report()