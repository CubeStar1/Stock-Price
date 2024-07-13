import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime, timedelta
st.set_page_config(layout="wide")


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

if 'combined_quarterly' not in st.session_state:
    st.session_state['combined_quarterly'] = pd.DataFrame()

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

# Function to get the last four quarters based on the current date
def get_last_four_quarters():
    current_date = datetime.now()
    quarters = []
    for i in range(4):
        year = current_date.year
        quarter = (current_date.month - 1) // 3 + 1
        quarters.append((f"Q{quarter}", str(year)))
        current_date -= timedelta(days=90)  # Move to the previous quarter
    return quarters[::-1]  # Reverse the list to get the last four quarters in order


st.title("Quarterly Percentage Change in SOXX Stock Prices")
st.write("This dashboard compares the percentage change in stock prices of SOXX component stocks over selected quarters.")
colu1, colu2 = st.columns([1,3])

with st.sidebar:
    st.markdown("### Instructions")
    st.write("1. Select the SOXX component stocks you want to compare.")
    st.write("2. Select the quarters you want to compare.")
    st.write("3. Click the 'Compare' button to display the percentage change in stock prices.")
    st.write("4. The percentage change in stock prices will be displayed as a bar chart.")
    st.write("5. The data will be stored in a SQLite database for future use.")
    with st.popover("Select the SOXX component stocks you want to compare.", use_container_width=True):
        selected_tickers = st.multiselect(
            "Select SOXX component stocks:",
            options=soxx_stocks,
            default=soxx_stocks
        )

    with st.container(border=True):
        compare_option = st.radio("Compare by:", ("Quarters", "Entire Year"))


if compare_option == "Quarters":
    last_four_quarters = get_last_four_quarters()

    quarters = ["Q1", "Q2", "Q3", "Q4"]
    years = [str(year) for year in range(2015, datetime.now().year + 1)]
    col1, col2 = st.columns(2)
    selected_quarters = []
    graphs = []
    # Initialize a dictionary to hold the percentage changes
    combined_data = {ticker: [] for ticker in selected_tickers}
    for i in range(1, 5):
        if i % 2 != 0:
            with col1:
                with st.container(border=True):
                    quarter = st.selectbox(f"Select Quarter {i}:", quarters, key=f"quarter_{i}",
                                           index=quarters.index(last_four_quarters[i - 1][0]))
                    year = st.selectbox(f"Select Year {i}:", years, key=f"year_{i}",
                                        index=years.index(last_four_quarters[i - 1][1]))
                    selected_quarters.append((quarter, year))
                    graph = st.empty()
                    graphs.append(graph)
        else:
            with col2:
                with st.container(border=True):
                    quarter = st.selectbox(f"Select Quarter {i}:", quarters, key=f"quarter_{i}",
                                           index=quarters.index(last_four_quarters[i - 1][0]))
                    year = st.selectbox(f"Select Year {i}:", years, key=f"year_{i}",
                                        index=years.index(last_four_quarters[i - 1][1]))
                    selected_quarters.append((quarter, year))
                    graph = st.empty()
                    graphs.append(graph)

    if selected_tickers:
        data = []
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

            data.append(df)
            # Update combined_data with the percentage changes
            for ticker in selected_tickers:
                combined_data[ticker].append(filtered_stock_data.get(ticker, 0.0))

            ax = axs[i]
            ax.bar(df['Company'], df['Percentage Change'], color='skyblue')
            ax.set_xlabel("Company")
            ax.set_ylabel("Percentage Change (%)")
            ax.set_title(f"Percentage Change in SOXX Stock Prices ({quarter} {year})")
            ax.tick_params(axis='x', rotation=90)


        for i, graph in enumerate(graphs):

            with graph:
                st.markdown(f"### {selected_quarters[i][0]} {selected_quarters[i][1]}")
                st.bar_chart(data[i].set_index('Company'))
        with st.expander("Show Combined Plot", expanded=True):
            st.pyplot(fig)

        combined_df = pd.DataFrame.from_dict(combined_data, orient='index',
                                             columns=[f"{quarter} {year}" for quarter, year in selected_quarters])
        combined_df.reset_index(inplace=True)
        combined_df.rename(columns={'index': 'Company'}, inplace=True)
        combined_df = combined_df.round(2)
        st.session_state['combined_quarterly'] = combined_df
        st.write("### Combined Percentage Change Table")
        st.dataframe(st.session_state['combined_quarterly'].sort_values("Company"), use_container_width=True, hide_index=True)
elif compare_option == "Entire Year":
    # Dropdowns for user to select the years
    years = [str(year) for year in range(2015, datetime.now().year + 1)]
    selected_years = []
    graphs = []
    col1, col2 = st.columns(2)
    for i in range(1, 5):

        if i % 2 != 0:
            with col1:
                with st.container(border=True):
                    year = st.selectbox(f"Select Year {i}:", years, key=f"year_{i}_entire")
                    selected_years.append(year)
                    graph = st.empty()
                    graphs.append(graph)
        else:
            with col2:
                with st.container(border=True):
                    year = st.selectbox(f"Select Year {i}:", years, key=f"year_{i}_entire")
                    selected_years.append(year)
                    graph = st.empty()
                    graphs.append(graph)

    if selected_tickers:
        data = []
        for i, year in enumerate(selected_years):
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"

            # Check if data exists in database
            stock_data = fetch_stock_data(start_date, end_date)

            # If no data in database, fetch from API and store in database
            if not stock_data:
                stock_data = get_stock_data(selected_tickers, start_date, end_date)
                store_stock_data(stock_data, start_date, end_date)

            # Filter the data based on selected tickers
            filtered_stock_data = {ticker: stock_data[ticker] for ticker in selected_tickers if ticker in stock_data}

            # Create a DataFrame
            df = pd.DataFrame(list(filtered_stock_data.items()), columns=['Company', 'Percentage Change'])

            # Sort DataFrame by percentage change
            df = df.sort_values(by='Percentage Change', ascending=False)
            data.append(df)


        for i, graph in enumerate(graphs):
            with graph:
                st.markdown(f"### {selected_years[i]}")
                st.bar_chart(data[i].set_index('Company'))
conn.close()
