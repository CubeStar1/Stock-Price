import time

import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime, timedelta
import google.generativeai as genai
import os
from tessa import Symbol

st.set_page_config(layout="wide")


soxx_stocks = ['AVGO', 'NVDA', 'AMD', 'AMAT', 'QCOM', 'LRCX', 'TSM', 'KLAC', 'INTC', 'MRVL', 'MU', 'MPWR', 'TXN', 'ASML', 'NXPI', 'ADI', 'MCHP', 'ON', 'TER', 'ENTG', 'SWKS', 'QRVO', 'STM', 'MKSI', 'ASX', 'LSCC', 'RMBS', 'UMC', 'ACLS', 'WOLF', '7203.T']

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
# Create table for storing custom stock lists if it doesn't exist
c.execute('''
    CREATE TABLE IF NOT EXISTS stock_lists (
        list_name TEXT,
        tickers TEXT
    )
''')


if 'combined_quarterly' not in st.session_state:
    st.session_state['combined_quarterly'] = pd.DataFrame()

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
        return data

    elif source == "tessa":
        for ticker in tickers:
            try:
                stock = Symbol(ticker)
                start_date_str = start_date
                end_date_str = end_date

                start_price = stock.price_point(start_date_str).price
                end_price = stock.price_point(end_date_str).price

                print(f"Ticker: {ticker}, Start Price: {start_price}, End Price: {end_price}")

                if start_price and end_price:
                    percent_change = ((end_price - start_price) / start_price) * 100
                    data[ticker] = percent_change
            except Exception as e:
                print(f"Error fetching data for {ticker}: {e}")
        return data

def store_stock_data(data, start_date, end_date):
    for company, percent_change in data.items():
        if percent_change != 0:  # Skip storing if the percent change is 0
            c.execute('''
                INSERT INTO stocks (company, start_date, end_date, percent_change) VALUES (?, ?, ?, ?)
            ''', (company, start_date, end_date, percent_change))
    conn.commit()

def fetch_stock_data(tickers, start_date, end_date):
    placeholders = ','.join(['?'] * len(tickers))
    query = f'''
        SELECT company, percent_change FROM stocks 
        WHERE start_date = ? AND end_date = ? AND company IN ({placeholders})
    '''
    params = [start_date, end_date] + tickers
    c.execute(query, params)
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
def get_last_n_quarters(n):
    current_year = datetime.now().year
    current_month = datetime.now().month
    current_quarter = (current_month - 1) // 3 + 1
    quarters_list = []

    for _ in range(n):
        quarters_list.append((quarters[current_quarter - 1], str(current_year)))
        current_quarter -= 1
        if current_quarter == 0:
            current_quarter = 4
            current_year -= 1

    return quarters_list[::-1]

def get_last_n_years(n):
    current_year = datetime.now().year
    years_list = [str(current_year - i) for i in range(n)]
    return years_list[::-1]

# Function to save custom stock list
def save_stock_list(name, tickers):
    tickers_str = ",".join(tickers)
    c.execute('''
        INSERT INTO stock_lists (list_name, tickers) VALUES (?, ?)
    ''', (name, tickers_str))
    conn.commit()
# Function to delete custom stock list
def delete_stock_list(name):
    c.execute('''
        DELETE FROM stock_lists WHERE list_name = ?
    ''', (name,))
    conn.commit()
# Function to load custom stock lists
def load_stock_lists():
    c.execute('''
        SELECT list_name, tickers FROM stock_lists
    ''')
    rows = c.fetchall()
    return {row[0]: row[1].split(",") for row in rows}

# Function to query the LLM (e.g., Gemini)
def query_llm(prompt):
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    print(response.text)
    return response.text

st.title("Quarterly Percentage Change in SOXX Stock Prices")
st.write("This dashboard compares the percentage change in stock prices of SOXX component stocks over selected quarters.")
quarters = ["Q1", "Q2", "Q3", "Q4"]
years = [str(year) for year in range(2015, datetime.now().year + 1)]
with st.sidebar:
    with st.container(border=True):
        stock_entry_mode = st.radio("Select Stock Entry Mode", ("Select SOXX Stocks", "Create Custom Stock List", "Query LLM"))
    if stock_entry_mode == "Select SOXX Stocks":
        with st.container(border=True):
            st.header("Select Stocks")
            with st.popover("Select the SOXX component stocks you want to compare.", use_container_width=True):
                selected_tickers = st.multiselect(
                    "Select SOXX component stocks:",
                    options=soxx_stocks,
                    default=['AMAT', 'ASML', 'KLAC', '7203.T', 'LRCX']
                )
                select_all = st.checkbox("Select All")
                if select_all:
                    selected_tickers = soxx_stocks
    elif stock_entry_mode == "Create Custom Stock List":
        with st.container(border=True):
            st.header("Custom Stock Lists")
            stock_lists = load_stock_lists()
            with st.form(key="create_stock_list_form"):
                # new_list_name = st.text_input("New List Name", value=st.session_state.get('selected_list_name', ""))
                # current_list_stocks = stock_lists.get(st.session_state.get('selected_list_name', ""), "")
                # current_tickers = ", ".join(current_list_stocks) if current_list_stocks else ""
                # new_list_tickers = st.text_area("Tickers (comma-separated)", value=current_tickers)
                # submit_button = st.form_submit_button("Create List", use_container_width=True)
                new_list_name = st.text_input("New List Name")
                new_list_tickers = st.text_area("Tickers (comma-separated)")
                submit_button = st.form_submit_button("Create List", use_container_width=True)
                if submit_button and new_list_name and new_list_tickers:
                    save_stock_list(new_list_name, [ticker.strip() for ticker in new_list_tickers.split(",")])
                    st.success(f"List '{new_list_name}' created successfully!")
                    st.rerun()

            with st.container(border=True):
                # Select an existing custom stock list
                selected_list_name = st.selectbox("Select Stock List", options= list(stock_lists.keys()))
                st.session_state['selected_list_name'] = selected_list_name
                selected_tickers = stock_lists.get(selected_list_name, [])
                # Delete a custom stock list
                if selected_list_name:
                    if st.button("Delete Selected List", use_container_width=True):
                        delete_stock_list(selected_list_name)
                        st.success(f"List '{selected_list_name}' deleted successfully!")
                        st.rerun()
    elif stock_entry_mode == "Query LLM":
        with st.container(border=True):
            llm_prompt = "Please provide me with the tickers for the following companies separated by commas. Striclty follow this prompt and respond only with tickers separated by commas, only provide me with tikcers for US companies in this prompt: "
            user_prompt = st.text_area("Enter a prompt for the LLM:")
            response = query_llm(llm_prompt + user_prompt)
            selected_tickers = []
            if st.button("Get Tickers", use_container_width=True):
                selected_tickers = response.split(", ")
    with st.container(border=True):
        compare_option = st.radio("Compare by:", ("Quarters", "Calendar Year"))




if compare_option == "Quarters":
    num_quarters = st.slider("Select the number of quarters to compare:", min_value=2, max_value=20, value=4, step=2)
    last_four_quarters = get_last_four_quarters()
    last_n_quarters = get_last_n_quarters(num_quarters)

    col1, col2 = st.columns(2)
    selected_quarters = []
    graphs = []
    # Initialize a dictionary to hold the percentage changes
    combined_data = {ticker: [] for ticker in selected_tickers}
    for i in range(1, num_quarters + 1):
        if i % 2 != 0:
            with col1:
                with st.container(border=True):
                    quarter = st.selectbox(f"Select Quarter {i}:", quarters, key=f"quarter_{i}",
                                           index=quarters.index(last_n_quarters[i - 1][0]))
                    year = st.selectbox(f"Select Year {i}:", years, key=f"year_{i}",
                                        index=years.index(last_n_quarters[i - 1][1]))
                    selected_quarters.append((quarter, year))
                    graph = st.empty()
                    graphs.append(graph)
        else:
            with col2:
                with st.container(border=True):
                    quarter = st.selectbox(f"Select Quarter {i}:", quarters, key=f"quarter_{i}",
                                           index=quarters.index(last_n_quarters[i - 1][0]))
                    year = st.selectbox(f"Select Year {i}:", years, key=f"year_{i}",
                                        index=years.index(last_n_quarters[i - 1][1]))
                    selected_quarters.append((quarter, year))
                    graph = st.empty()
                    graphs.append(graph)

    if selected_tickers:
        data = []
        fig, axs = plt.subplots(num_quarters, 1, figsize=(15, 9 * num_quarters))
        axs = axs.flatten()

        for i, (quarter, year) in enumerate(selected_quarters):
            start_date, end_date = get_date_range(year, quarter)

            stock_data = fetch_stock_data(selected_tickers, start_date,
                                          end_date)

            missing_tickers = [ticker for ticker in selected_tickers if ticker not in stock_data]
            if missing_tickers:
                api_stock_data = get_stock_data(missing_tickers, start_date, end_date, source="yfinance")
                store_stock_data(api_stock_data, start_date, end_date)
                stock_data.update(api_stock_data)

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
        st.write("### Combined Percentage Change Table")
        with st.container(border=True):
            st.dataframe(combined_df.sort_values("Company"), use_container_width=True, hide_index=True)
elif compare_option == "Calendar Year":

    num_years = st.slider("Select the number of years to compare:", min_value=2, max_value=10, value=4, step=1)
    # Dropdowns for user to select the years
    years = [str(year) for year in range(2000, datetime.now().year + 1)]
    selected_years = []
    graphs = []
    combined_data = {ticker: [] for ticker in selected_tickers}
    col1, col2 = st.columns(2)

    for i in range(1, num_years + 1):
        if i % 2 != 0:
            with col1:
                with st.container(border=True):
                    year = st.selectbox(f"Select Year {i}:", years, key=f"year_{i}_entire", index=len(years) - i)
                    selected_years.append(year)
                    graph = st.empty()
                    graphs.append(graph)
        else:
            with col2:
                with st.container(border=True):
                    year = st.selectbox(f"Select Year {i}:", years, key=f"year_{i}_entire", index=len(years) - i)
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
            for ticker in selected_tickers:
                combined_data[ticker].append(filtered_stock_data.get(ticker, 0.0))

        combined_df = pd.DataFrame.from_dict(combined_data, orient='index',
                                             columns=selected_years)
        combined_df.reset_index(inplace=True)
        combined_df.rename(columns={'index': 'Company'}, inplace=True)
        combined_df = combined_df.round(2)

        for i, graph in enumerate(graphs):
            with graph:
                st.markdown(f"### {selected_years[i]}")
                st.bar_chart(data[i].set_index('Company'))

        with st.container(border=True):
            st.write("### Combined Percentage Change Table")
            st.dataframe(combined_df.sort_values("Company"), use_container_width=True, hide_index=True)

conn.close()
