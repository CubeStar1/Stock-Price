import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime, timedelta
st.set_page_config(layout="wide")
# soxx_stocks = [
#     'AMD', 'ADI', 'AMAT', 'ASML', 'AVGO', 'CDNS', 'ENTG', 'KLAC', 'LRCX', 'MRVL',
#     'MPWR', 'MCHP', 'MU', 'NXPI', 'ON', 'QCOM', 'SIMO', 'SWKS', 'TER', 'TSM',
#     'TXN', 'UMC', 'XLNX'
# ]


soxx_stocks = ['AVGO', 'NVDA', 'AMD', 'AMAT', 'QCOM', 'LRCX', 'TSM', 'KLAC', 'INTC', 'MRVL', 'MU', 'MPWR', 'TXN', 'ASML', 'NXPI', 'ADI', 'MCHP', 'ON', 'TER', 'ENTG', 'SWKS', 'QRVO', 'STM', 'MKSI', 'ASX', 'LSCC', 'RMBS', 'UMC', 'ACLS', 'WOLF']

conn = sqlite3.connect('soxx_stock_data.db')
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS stocks (
        company TEXT,
        start_date TEXT,
        end_date TEXT,
        percent_change REAL
    )
''')

def get_stock_data(tickers, start_date, end_date):
    data = {}
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date)
        if not hist.empty:
            start_price = hist['Close'][0]
            end_price = hist['Close'][-1]
            percent_change = ((end_price - start_price) / start_price) * 100
            data[ticker] = percent_change
    return data

def store_stock_data(data, start_date, end_date):
    for company, percent_change in data.items():
        c.execute('''
            INSERT INTO stocks (company, start_date, end_date, percent_change) VALUES (?, ?, ?, ?)
        ''', (company, start_date, end_date, percent_change))
    conn.commit()

def fetch_stock_data(start_date, end_date):
    c.execute('''
        SELECT company, percent_change FROM stocks WHERE start_date = ? AND end_date = ?
    ''', (start_date, end_date))
    rows = c.fetchall()
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

st.title("Quarterly Percentage Change in SOXX Stock Prices")
st.write("This dashboard compares the percentage change in stock prices of SOXX component stocks over selected quarters.")

selected_tickers = st.multiselect(
    "Select SOXX component stocks:",
    options=soxx_stocks,
    default=soxx_stocks
)

quarters = ["Q1", "Q2", "Q3", "Q4"]
years = [str(year) for year in range(2015, datetime.now().year + 1)]
col1, col2 = st.columns(2)
selected_quarters = []
for i in range(1, 5):
    if i % 2 != 0:
        with col1:
            with st.container(border=True):
                quarter = st.selectbox(f"Select Quarter {i}:", quarters, key=f"quarter_{i}")
                year = st.selectbox(f"Select Year {i}:", years, key=f"year_{i}")
                selected_quarters.append((quarter, year))
                graph = st.empty()
    else:
        with col2:
            with st.container(border=True):
                quarter = st.selectbox(f"Select Quarter {i}:", quarters, key=f"quarter_{i}")
                year = st.selectbox(f"Select Year {i}:", years, key=f"year_{i}")
                selected_quarters.append((quarter, year))

if selected_tickers:
    fig, axs = plt.subplots(2, 2, figsize=(15, 15))
    axs = axs.flatten()

    for i, (quarter, year) in enumerate(selected_quarters):
        start_date, end_date = get_date_range(year, quarter)

        stock_data = fetch_stock_data(start_date, end_date)

        if not stock_data:
            stock_data = get_stock_data(selected_tickers, start_date, end_date)
            store_stock_data(stock_data, start_date, end_date)

        filtered_stock_data = {ticker: stock_data[ticker] for ticker in selected_tickers if ticker in stock_data}

        df = pd.DataFrame(list(filtered_stock_data.items()), columns=['Company', 'Percentage Change'])

        df = df.sort_values(by='Percentage Change', ascending=False)

        ax = axs[i]
        ax.bar(df['Company'], df['Percentage Change'], color='skyblue')
        ax.set_xlabel("Company")
        ax.set_ylabel("Percentage Change (%)")
        ax.set_title(f"Percentage Change in SOXX Stock Prices ({quarter} {year})")
        ax.tick_params(axis='x', rotation=90)
        if i%2 == 0:
            with col1:
                st.markdown(f"### {quarter} {year}")
                st.bar_chart(x='Company', y='Percentage Change', data=df, use_container_width=True, x_label='Company', y_label='Percentage Change (%)')
        else:
            with col2:
                st.markdown(f"### {quarter} {year}")
                st.bar_chart(x='Company', y='Percentage Change', data=df, use_container_width=True, x_label='Company', y_label='Percentage Change (%)')

    st.pyplot(fig)

conn.close()
