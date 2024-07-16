import streamlit as st
import yfinance as yf
import pandas as pd
import sqlite3
from contextlib import closing
from utils import global_sidebar
import plotly.graph_objects as go
import streamlit_antd_components as sac
st.set_page_config(layout="wide")

# Function to get a new database connection
def get_db_connection():
    return sqlite3.connect('stock_price_data.db')

global_sidebar()
# Create table to store stock data if it doesn't exist
with closing(get_db_connection()) as conn:
    with conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS stock_info (
            ticker TEXT,
            name TEXT,
            country TEXT,
            sector TEXT,
            industry TEXT,
            market_cap REAL,
            enterprise_value REAL,
            employees INTEGER,
            current_price REAL,
            prev_close REAL,
            day_high REAL,
            day_low REAL,
            ft_week_high REAL,
            ft_week_low REAL,
            forward_eps REAL,
            forward_pe REAL,
            peg_ratio REAL,
            dividend_rate REAL,
            dividend_yield REAL,
            recommendation TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')


with st.sidebar:
    with st.container(border=True):
        ticker = st.text_input("Enter a stock ticker (e.g. AAPL)", "LRCX")
        # period = st.selectbox("Enter a time frame", ("1D", "5D", "1MO", "6MO", "YTD", "1Y", "5Y"), index=2)

# Format market cap and enterprise value into something readable
def format_value(value):
    if value is None or value == 'N/A':
        return 'N/A'
    suffixes = ["", "K", "M", "B", "T"]
    suffix_index = 0
    while value >= 1000 and suffix_index < len(suffixes) - 1:
        value /= 1000
        suffix_index += 1
    return f"${value:.1f}{suffixes[suffix_index]}"

# Check if data for the stock ticker already exists in the database
def get_stock_data_from_db(ticker):
    with closing(get_db_connection()) as conn:
        with conn:
            c = conn.cursor()
            c.execute('SELECT * FROM stock_info WHERE ticker = ?', (ticker,))
            return c.fetchone()

# Store data into the database
def store_stock_data_in_db(data):
    with closing(get_db_connection()) as conn:
        with conn:
            c = conn.cursor()
            c.execute('''
            INSERT INTO stock_info (ticker, name, country, sector, industry, market_cap, enterprise_value, employees, 
                                    current_price, prev_close, day_high, day_low, ft_week_high, ft_week_low, 
                                    forward_eps, forward_pe, peg_ratio, dividend_rate, dividend_yield, recommendation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', data)

# If Submit button is clicked
#if button:
title = st.empty()


period = sac.chip(
    items=[
        sac.ChipItem(label='1D'),
        sac.ChipItem(label='5D'),
        sac.ChipItem(label='1MO'),
        sac.ChipItem(label='6MO'),
        sac.ChipItem(label='YTD'),
        sac.ChipItem(label='1Y'),
        sac.ChipItem(label='5Y'),
    ], label='', index=[2,2], align='center', radius='md')

if not ticker.strip():
    st.error("Please provide a valid stock ticker.")
else:
    try:
        with st.spinner('Please wait...'):
            # Check if data for the ticker exists in the database
            db_data = get_stock_data_from_db(ticker)

            if db_data:
                title.subheader(f"{ticker} - {db_data[1]} (from database)")
                country, sector, industry, market_cap, ent_value, employees, current_price, prev_close, day_high, day_low, ft_week_high, ft_week_low, forward_eps, forward_pe, peg_ratio, dividend_rate, dividend_yield, recommendation = db_data[
                                                                                                                                                                                                                                          2:-1]
                stock = yf.Ticker(ticker)  # Define stock here for historical data plotting
            else:
                # Retrieve stock data from yfinance
                stock = yf.Ticker(ticker)
                info = stock.info

                # Retrieve and format stock information
                country = info.get('country', 'N/A')
                sector = info.get('sector', 'N/A')
                industry = info.get('industry', 'N/A')
                market_cap = info.get('marketCap', 'N/A')
                ent_value = info.get('enterpriseValue', 'N/A')
                employees = info.get('fullTimeEmployees', 'N/A')
                current_price = info.get('currentPrice', 'N/A')
                prev_close = info.get('previousClose', 'N/A')
                day_high = info.get('dayHigh', 'N/A')
                day_low = info.get('dayLow', 'N/A')
                ft_week_high = info.get('fiftyTwoWeekHigh', 'N/A')
                ft_week_low = info.get('fiftyTwoWeekLow', 'N/A')
                forward_eps = info.get('forwardEps', 'N/A')
                forward_pe = info.get('forwardPE', 'N/A')
                peg_ratio = info.get('pegRatio', 'N/A')
                dividend_rate = info.get('dividendRate', 'N/A')
                dividend_yield = info.get('dividendYield', 'N/A')
                recommendation = info.get('recommendationKey', 'N/A')

                stock_data = (
                ticker, info.get('longName', 'N/A'), country, sector, industry, market_cap, ent_value, employees,
                current_price, prev_close, day_high, day_low, ft_week_high, ft_week_low, forward_eps,
                forward_pe, peg_ratio, dividend_rate, dividend_yield, recommendation)

                # Store the data in the database
                store_stock_data_in_db(stock_data)

                title.subheader(f"{ticker} - {info.get('longName', 'N/A')}")


            # Plot historical stock price data
            history = stock.history(period=period)
            chart_data = pd.DataFrame(history["Close"])
            with st.container(border=True):
                # Create line chart
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=chart_data.index,
                    y=chart_data["Close"],
                    mode='lines',
                    name=ticker
                ))

                fig.update_layout(
                    title="Stock Price over time",
                    xaxis_title="Date",
                    yaxis_title="Stock Price",
                    hovermode="x unified"
                )

                st.plotly_chart(fig, use_container_width=True)

            col1, col2, col3 = st.columns(3)

            # Display stock information as a dataframe
            stock_info = [
                ("Stock Info", "Value"),
                ("Country", country),
                ("Sector", sector),
                ("Industry", industry),
                ("Market Cap", format_value(market_cap)),
                ("Enterprise Value", format_value(ent_value)),
                ("Employees", employees)
            ]

            df_stock_info = pd.DataFrame(stock_info[1:], columns=stock_info[0])
            col1.dataframe(df_stock_info, width=400, hide_index=True)

            # Display price information as a dataframe
            price_info = [
                ("Price Info", "Value"),
                ("Current Price", f"${current_price:.2f}" if current_price != 'N/A' else 'N/A'),
                ("Previous Close", f"${prev_close:.2f}" if prev_close != 'N/A' else 'N/A'),
                ("Day High", f"${day_high:.2f}" if day_high != 'N/A' else 'N/A'),
                ("Day Low", f"${day_low:.2f}" if day_low != 'N/A' else 'N/A'),
                ("52 Week High", f"${ft_week_high:.2f}" if ft_week_high != 'N/A' else 'N/A'),
                ("52 Week Low", f"${ft_week_low:.2f}" if ft_week_low != 'N/A' else 'N/A')
            ]

            df_price_info = pd.DataFrame(price_info[1:], columns=price_info[0])
            col2.dataframe(df_price_info, width=400, hide_index=True)

            # Display business metrics as a dataframe
            biz_metrics = [
                ("Business Metrics", "Value"),
                ("EPS (FWD)", f"{forward_eps:.2f}" if forward_eps != 'N/A' else 'N/A'),
                ("P/E (FWD)", f"{forward_pe:.2f}" if forward_pe != 'N/A' else 'N/A'),
                ("PEG Ratio", f"{peg_ratio:.2f}" if peg_ratio != 'N/A' else 'N/A'),
                ("Div Rate (FWD)", f"${dividend_rate:.2f}" if dividend_rate != 'N/A' else 'N/A'),
                ("Div Yield (FWD)", f"{dividend_yield * 100:.2f}%" if dividend_yield != 'N/A' else 'N/A'),
                ("Recommendation", recommendation.capitalize() if recommendation != 'N/A' else 'N/A')
            ]

            df_biz_metrics = pd.DataFrame(biz_metrics[1:], columns=biz_metrics[0])
            col3.dataframe(df_biz_metrics, width=400, hide_index=True)

    except Exception as e:
        st.exception(f"An error occurred: {e}")
