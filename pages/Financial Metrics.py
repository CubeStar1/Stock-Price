import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from utils import global_sidebar, percent_sidebar


def calculate_roic(ticker):
    try:
        stock = yf.Ticker(ticker)

        # Get financial data
        balance_sheet = stock.balance_sheet
        income_stmt = stock.financials
        cash_flow = stock.cashflow

        # Calculate ROIC components
        nopat = income_stmt.loc['Net Income'] + income_stmt.loc['Interest Expense'] * (
                    1 - 0.21)  # Assuming 21% tax rate
        invested_capital = balance_sheet.loc['Total Assets'] - balance_sheet.loc['Total Current Liabilities']

        # Calculate ROIC
        roic = (nopat / invested_capital).iloc[0]  # Get the most recent value

        return roic
    except Exception as e:
        st.error(f"Error calculating ROIC for {ticker}: {str(e)}")
        return None


def get_financial_metrics(ticker):
    try:
        stock = yf.Ticker(ticker)

        # Get key statistics
        pe_ratio = stock.info.get('trailingPE', None)
        forward_pe = stock.info.get('forwardPE', None)
        debt_to_equity = stock.info.get('debtToEquity', None)
        eps = stock.info.get('trailingEps', None)

        # Calculate ROIC
        roic = calculate_roic(ticker)

        return {
            'P/E Ratio': pe_ratio,
            'Forward P/E': forward_pe,
            'Debt-to-Equity': debt_to_equity,
            'EPS (TTM)': eps,
            'ROIC': roic
        }
    except Exception as e:
        st.error(f"Error fetching metrics for {ticker}: {str(e)}")
        return None


def financial_metrics_page():
    st.title("Financial Metrics Calculator")

    if 'selected_tickers' in st.session_state and st.session_state.selected_tickers:
        metrics_data = {}
        for ticker in st.session_state.selected_tickers:
            metrics = get_financial_metrics(ticker)
            if metrics:
                metrics_data[ticker] = metrics

        if metrics_data:
            # Create a DataFrame from the metrics data
            df = pd.DataFrame(metrics_data).T

            # Display the metrics table
            st.subheader("Financial Metrics")
            st.dataframe(df.style.format({
                'P/E Ratio': '{:.2f}',
                'Forward P/E': '{:.2f}',
                'Debt-to-Equity': '{:.2f}',
                'EPS (TTM)': '{:.2f}',
                'ROIC': '{:.2%}'
            }))

            # Create a bar chart for ROIC comparison
            fig = go.Figure(data=[
                go.Bar(name='ROIC', x=df.index, y=df['ROIC'])
            ])
            fig.update_layout(title='Return on Invested Capital (ROIC) Comparison',
                              xaxis_title='Stocks',
                              yaxis_title='ROIC',
                              yaxis_tickformat='.2%')
            st.plotly_chart(fig)

            # Add explanations for each metric
            st.subheader("Metrics Explanation")
            st.write("""
            - **P/E Ratio**: Price-to-Earnings ratio. A higher P/E suggests higher growth expectations.
            - **Forward P/E**: Based on forecasted earnings. Useful for comparing current and future valuations.
            - **Debt-to-Equity**: Measures a company's financial leverage. A higher ratio indicates more risk.
            - **EPS (TTM)**: Earnings Per Share (Trailing Twelve Months). A company's profit divided by outstanding shares.
            - **ROIC**: Return on Invested Capital. Measures how efficiently a company uses its capital to generate profits.
            """)
    else:
        st.info("No tickers selected. Please select tickers in the sidebar.")


global_sidebar()
percent_sidebar()
financial_metrics_page()