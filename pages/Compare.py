import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils import global_sidebar, percent_sidebar

st.set_page_config(layout="wide")

def stock_comparison():
    st.title("Stock Comparison")

    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365))
    with col2:
        end_date = st.date_input("End Date", datetime.now())

    # Stock selection (use the same list as in the main app)
    selected_stocks = st.multiselect(
        "Select stocks to compare",
        options=st.session_state.selected_tickers,
        default=st.session_state.selected_tickers # Default to first 3 stocks
    )

    if selected_stocks:
        # Fetch data
        df = yf.download(selected_stocks, start=start_date, end=end_date)['Adj Close']

        # Calculate percentage change
        df_pct = df.pct_change().cumsum()

        # Create line chart
        fig = go.Figure()
        for stock in selected_stocks:
            fig.add_trace(go.Scatter(
                x=df_pct.index,
                y=df_pct[stock],
                mode='lines',
                name=stock
            ))

        fig.update_layout(
            title="Cumulative Returns Comparison",
            xaxis_title="Date",
            yaxis_title="Cumulative Returns (%)",
            legend_title="Stocks",
            hovermode="x unified"
        )

        st.plotly_chart(fig, use_container_width=True)

        # Display correlation matrix
        st.subheader("Correlation Matrix")
        correlation_matrix = df.pct_change().corr()
        st.dataframe(correlation_matrix.style.background_gradient(cmap='coolwarm'), use_container_width=True)


global_sidebar()
percent_sidebar()
stock_comparison()