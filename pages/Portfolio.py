# portfolio_management.py
import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
from utils import global_sidebar, percent_sidebar


def portfolio_management():
    st.title("Portfolio Management")

    # Initialize session state for portfolio
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = pd.DataFrame(columns=['Ticker', 'Shares', 'Purchase Date', 'Purchase Price'])

    # Add stock to portfolio
    with st.expander("Add Stock to Portfolio"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            ticker = st.text_input("Stock Ticker")
        with col2:
            shares = st.number_input("Number of Shares", min_value=1, step=1)
        with col3:
            purchase_date = st.date_input("Purchase Date")
        with col4:
            purchase_price = st.number_input("Purchase Price", min_value=0.01, step=0.01)

        if st.button("Add to Portfolio"):
            new_stock = pd.DataFrame({
                'Ticker': [ticker],
                'Shares': [shares],
                'Purchase Date': [purchase_date],
                'Purchase Price': [purchase_price]
            })
            st.session_state.portfolio = pd.concat([st.session_state.portfolio, new_stock], ignore_index=True)
            st.success(f"Added {shares} shares of {ticker} to your portfolio.")

    # Display current portfolio
    if not st.session_state.portfolio.empty:
        st.subheader("Current Portfolio")
        st.dataframe(st.session_state.portfolio)

        # Calculate current values and performance
        end_date = datetime.now().date()-timedelta(days=1)
        start_date = end_date - timedelta(days=1)  # Get yesterday's date for most recent closing price
        portfolio_value = 0
        performance_data = []

        for _, row in st.session_state.portfolio.iterrows():
            ticker = row['Ticker']
            shares = row['Shares']
            purchase_price = row['Purchase Price']

            # Fetch current price
            stock_data = yf.download(ticker, start=start_date, end=end_date)
            if not stock_data.empty:
                current_price = stock_data['Close'].iloc[-1]
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
            st.subheader("Portfolio Performance")
            st.dataframe(performance_df.style.format({
                'Purchase Price': '${:.2f}',
                'Current Price': '${:.2f}',
                'Current Value': '${:.2f}',
                'Gain/Loss': '${:.2f}',
                'Percent Change': '{:.2f}%'
            }))

            # Portfolio summary
            st.subheader("Portfolio Summary")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Portfolio Value", f"${portfolio_value:.2f}")
            col2.metric("Total Gain/Loss", f"${performance_df['Gain/Loss'].sum():.2f}")
            col3.metric("Average Percent Change", f"{performance_df['Percent Change'].mean():.2f}%")

            # Portfolio composition pie chart
            fig = go.Figure(data=[go.Pie(labels=performance_df['Ticker'], values=performance_df['Current Value'])])
            fig.update_layout(title="Portfolio Composition")
            st.plotly_chart(fig)

        else:
            st.warning("Unable to fetch current prices. Please try again later.")
    else:
        st.info("Your portfolio is empty. Add some stocks to get started!")

    # Option to clear portfolio
    if st.button("Clear Portfolio"):
        st.session_state.portfolio = pd.DataFrame(columns=['Ticker', 'Shares', 'Purchase Date', 'Purchase Price'])
        st.success("Portfolio cleared.")


global_sidebar()
percent_sidebar()
portfolio_management()