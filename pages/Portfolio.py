import streamlit as st
import pandas as pd
import yfinance as yf
from tessa import Symbol
from datetime import datetime, timedelta
import plotly.graph_objects as go
from utils import global_sidebar, percent_sidebar, get_stock_data
import sqlite3
from functools import lru_cache


def init_db():
    conn = sqlite3.connect('portfolio.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS portfolios
                 (id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS stocks
                 (id INTEGER PRIMARY KEY, portfolio_id INTEGER,
                  ticker TEXT, shares INTEGER, purchase_date TEXT,
                  purchase_price REAL,
                  FOREIGN KEY (portfolio_id) REFERENCES portfolios (id))''')
    conn.commit()
    return conn

@lru_cache(maxsize=128)
def get_stock_price(ticker, date):
    try:
        print(f"Fetching price for {ticker} on {date}")
        return Symbol(ticker).price_point(str(date)).price
    except Exception as e:
        print(f"Error fetching price for {ticker} on {date}: {str(e)}")
        return None


def load_portfolios():
    conn = init_db()
    portfolios = pd.read_sql('SELECT * FROM portfolios', conn)
    conn.close()
    return portfolios


def save_portfolio(name):
    conn = init_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO portfolios (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()


def update_portfolio(old_name, new_name):
    conn = init_db()
    cur = conn.cursor()
    cur.execute("UPDATE portfolios SET name = ? WHERE name = ?", (new_name, old_name))
    conn.commit()
    conn.close()


def delete_portfolio(name):
    conn = init_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM portfolios WHERE name = ?", (name,))
    cur.execute("DELETE FROM stocks WHERE portfolio_id = (SELECT id FROM portfolios WHERE name = ?)", (name,))
    conn.commit()
    conn.close()


def add_stock_to_portfolio(portfolio_name, ticker, shares, purchase_date, purchase_price):
    conn = init_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO stocks (portfolio_id, ticker, shares, purchase_date, purchase_price)
        VALUES ((SELECT id FROM portfolios WHERE name = ?), ?, ?, ?, ?)
    """, (portfolio_name, ticker, shares, purchase_date, purchase_price))
    conn.commit()
    conn.close()

def delete_stock_from_portfolio(portfolio_name, stock_id):
    conn = init_db()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM stocks 
        WHERE id = ? AND portfolio_id = (SELECT id FROM portfolios WHERE name = ?)
    """, (stock_id, portfolio_name))
    conn.commit()
    conn.close()

def update_stock_in_portfolio(stock_id, shares, purchase_date, purchase_price):
    conn = init_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE stocks 
        SET shares = ?, purchase_date = ?, purchase_price = ?
        WHERE id = ?
    """, (shares, purchase_date, purchase_price, stock_id))
    conn.commit()
    conn.close()

def portfolio_management():
    st.title("Portfolio Management")

    if 'portfolios' not in st.session_state:
        st.session_state.portfolios = load_portfolios()

    view, create = st.tabs(["View/Edit Existing Portfolio", "Create New Portfolio"])
    with view:
        if not st.session_state.portfolios.empty:
            with st.container(border=True):
                selected_portfolio = st.selectbox("Select a portfolio:",
                                                  options=st.session_state.portfolios['name'])

                new_portfolio_name = st.text_input("Edit portfolio name:", value=selected_portfolio)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Update Portfolio Name", use_container_width=True):
                        if new_portfolio_name != selected_portfolio:
                            update_portfolio(selected_portfolio, new_portfolio_name)
                            st.success(f"Updated portfolio name to: {new_portfolio_name}")
                            st.session_state.portfolios = load_portfolios()
                            st.experimental_rerun()

                with col2:
                    if st.button("Delete Portfolio", use_container_width=True):
                        delete_portfolio(selected_portfolio)
                        st.success(f"Deleted portfolio: {selected_portfolio}")
                        st.session_state.portfolios = load_portfolios()
                        st.experimental_rerun()

            with st.container(border=True):
                st.subheader("Add Stock to Portfolio")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    ticker = st.text_input("Stock Ticker")
                with col2:
                    shares = st.number_input("Number of Shares", min_value=1, step=1)
                with col3:
                    purchase_date = st.date_input("Purchase Date")
                with col4:
                    purchase_price = st.number_input("Purchase Price", min_value=0.01, step=0.01, value=get_stock_price(ticker, purchase_date))

                if st.button("Add Stock to Portfolio"):
                    add_stock_to_portfolio(selected_portfolio, ticker, shares, purchase_date.isoformat(), get_stock_price(ticker, purchase_date))
                    st.success(f"Added {shares} shares of {ticker} to {selected_portfolio}")
                if st.button("Add Stocks from List"):
                    stocks_list = st.session_state.selected_tickers
                    for stock in stocks_list:
                        add_stock_to_portfolio(selected_portfolio, stock, shares, purchase_date.isoformat(), get_stock_price(stock, purchase_date))
                        st.success(f"Added {shares} shares of {stock} to {selected_portfolio}")

            # Display stocks in the selected portfolio
            conn = init_db()
            portfolio_stocks = pd.read_sql(
                f"SELECT * FROM stocks WHERE portfolio_id = (SELECT id FROM portfolios WHERE name = ?)",
                conn, params=(selected_portfolio,))
            conn.close()

            if not portfolio_stocks.empty:
                # st.subheader(f"Stocks in {selected_portfolio}")
                # st.dataframe(portfolio_stocks)
                # Calculate current values and performance
                end_date = datetime.now().date() - timedelta(days=1)
                portfolio_value = 0
                total_cost = 0
                performance_data = []

                with st.container(border=True):
                    st.subheader(f"Stocks in {selected_portfolio}")
                    for _, stock in portfolio_stocks.iterrows():

                        with st.expander(f"{stock['ticker']} - {stock['shares']} shares"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                new_shares = st.number_input("Shares", value=stock['shares'], min_value=1,
                                                             key=f"shares_{stock['id']}")
                            with col2:
                                new_purchase_date = st.date_input("Purchase Date",
                                                                  value=datetime.strptime(stock['purchase_date'],
                                                                                          '%Y-%m-%d').date(),
                                                                  key=f"date_{stock['id']}")
                            with col3:
                                new_purchase_price = st.number_input("Purchase Price", value=stock['purchase_price'],
                                                                     min_value=0.01, step=0.01, key=f"price_{stock['id']}")

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Update Stock", key=f"update_{stock['id']}"):
                                    update_stock_in_portfolio(stock['id'], new_shares, new_purchase_date.isoformat(),
                                                              new_purchase_price)
                                    st.success(f"Updated {stock['ticker']} in {selected_portfolio}")
                                    st.experimental_rerun()
                            with col2:
                                if st.button("Delete Stock", key=f"delete_{stock['id']}"):
                                    delete_stock_from_portfolio(selected_portfolio, stock['id'])
                                    st.success(f"Deleted {stock['ticker']} from {selected_portfolio}")
                                    st.experimental_rerun()
                        ticker = stock['ticker']
                        shares = stock['shares']
                        purchase_price = stock['purchase_price']
                        cost = shares * purchase_price
                        total_cost += cost

                        # Fetch current price (cached)
                        current_price = get_stock_price(ticker, end_date)
                        if current_price:
                            current_value = current_price * shares
                            portfolio_value += current_value
                            gain_loss = (current_price - purchase_price) * shares
                            percent_change = (current_price - purchase_price) / purchase_price * 100

                            performance_data.append({
                                'Ticker': ticker,
                                'Shares': shares,
                                'Purchase Price': purchase_price,
                                'Current Price': current_price,
                                'Current Value': current_value,
                                'Gain/Loss': gain_loss,
                                'Percent Change': percent_change
                            })

                if performance_data:
                    performance_df = pd.DataFrame(performance_data)

                    with st.container(border=True):
                        st.subheader("Portfolio Performance")
                        st.dataframe(performance_df.style.format({
                            'Purchase Price': '${:.2f}',
                            'Current Price': '${:.2f}',
                            'Current Value': '${:.2f}',
                            'Gain/Loss': '${:.2f}',
                            'Percent Change': '{:.2f}%'
                        }), use_container_width=True)

                    with st.container(border=True):
                        # Performance Summary
                        st.subheader("Performance Summary")
                        total_gain_loss = portfolio_value - total_cost
                        total_percent_change = (portfolio_value - total_cost) / total_cost * 100 if total_cost > 0 else 0

                        col1, col2, col3 = st.columns(3)
                        col1.metric("Total Portfolio Value", f"${portfolio_value:.2f}")
                        col2.metric("Total Gain/Loss", f"${total_gain_loss:.2f}")
                        col3.metric("Total Percent Change", f"{total_percent_change:.2f}%")

                        st.write(f"Total Cost Basis: ${total_cost:.2f}")
                        if not performance_df.empty:
                            st.write(
                                f"Best Performing Stock: {performance_df.loc[performance_df['Percent Change'].idxmax(), 'Ticker']} ({performance_df['Percent Change'].max():.2f}%)")
                            st.write(
                                f"Worst Performing Stock: {performance_df.loc[performance_df['Percent Change'].idxmin(), 'Ticker']} ({performance_df['Percent Change'].min():.2f}%)")

                        # Portfolio composition pie chart
                        fig = go.Figure(
                            data=[go.Pie(labels=performance_df['Ticker'], values=performance_df['Current Value'])])
                        fig.update_layout(title="Portfolio Composition")
                        st.plotly_chart(fig)

                else:
                    st.warning("Unable to fetch current prices. Please try again later.")
            else:
                st.info(f"No stocks in {selected_portfolio}. Add some stocks to get started!")
        else:
            st.write("No existing portfolios. Create a new one!")

    with create:
        new_portfolio_name = st.text_input("Enter a name for the new portfolio:")
        if st.button("Create Portfolio"):
            if new_portfolio_name:
                save_portfolio(new_portfolio_name)
                st.success(f"Created new portfolio: {new_portfolio_name}")
                st.session_state.portfolios = load_portfolios()
                st.experimental_rerun()
            else:
                st.error("Please enter a name for the new portfolio.")


global_sidebar()
percent_sidebar()
portfolio_management()