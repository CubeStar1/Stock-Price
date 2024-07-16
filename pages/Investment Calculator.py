# investment_calculator.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from utils import global_sidebar, stock_selector

st.set_page_config(layout="wide")


@st.cache_data(ttl=3600)
def fetch_stock_data(ticker, years=10):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    data = yf.Ticker(ticker).history(start=start_date, end=end_date)
    return data


def calculate_cagr(start_value, end_value, num_years):
    return (end_value / start_value) ** (1 / num_years) - 1


def compound_interest(principal, rate, time, contributions=0, frequency=12):
    """Calculate compound interest with optional regular contributions."""
    total = principal
    for _ in range(time * frequency):
        total = total * (1 + rate / (100 * frequency)) + (contributions * (12 / frequency))
    return total


def retirement_savings(current_age, retirement_age, life_expectancy, current_savings,
                       monthly_contribution, annual_return, inflation_rate, compound_frequency):
    """Calculate retirement savings and required withdrawals."""
    years_to_retirement = retirement_age - current_age
    years_in_retirement = life_expectancy - retirement_age

    retirement_savings = compound_interest(current_savings, annual_return, years_to_retirement,
                                           contributions=monthly_contribution, frequency=compound_frequency)

    withdrawal_rate = (annual_return - inflation_rate) / (1 + inflation_rate)
    annual_withdrawal = retirement_savings * withdrawal_rate

    return retirement_savings, annual_withdrawal


def plot_compound_interest(principal, rate, time, contributions, frequency, stock_data=None):
    years = list(range(time + 1))
    totals = [compound_interest(principal, rate, t, contributions, frequency) for t in years]
    contributions_total = [principal + contributions * 12 * t for t in years]
    interest_earned = [total - contrib for total, contrib in zip(totals, contributions_total)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=totals, name='Total Balance', mode='lines'))
    fig.add_trace(go.Scatter(x=years, y=contributions_total, name='Contributions', fill='tozeroy'))
    fig.add_trace(go.Scatter(x=years, y=interest_earned, name='Interest Earned', fill='tonexty'))

    if stock_data is not None:
        stock_performance = [principal * (1 + stock_data['yearly_return']) ** t for t in years]
        fig.add_trace(go.Scatter(x=years, y=stock_performance, name='Stock Performance', line=dict(dash='dash')))

    fig.update_layout(title='Investment Growth Comparison', xaxis_title='Years', yaxis_title='Amount ($)')
    return fig


def investment_calculator():
    st.title("Investment Calculator")
    with st.container(border=True):
        st.subheader("Compound Interest Calculator")
        col1, col2 = st.columns(2)
        with col1:
            principal = st.number_input("Initial Investment ($)", min_value=0, value=10000, step=1000)
            time = st.number_input("Investment Period (years)", min_value=1, max_value=50, value=10)
            contributions = st.number_input("Monthly Contributions ($)", min_value=0, value=100, step=50)
        with col2:
            stock_ticker = st.selectbox("Compare with Stock (optional)", [""] + st.session_state.selected_tickers)
            compound_frequency = st.selectbox("Compound Frequency", ["Annually", "Monthly"], index=1)
            rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, max_value=100.0, value=7.0, step=0.1)

    freq_map = {"Annually": 1, "Monthly": 12}
    frequency = freq_map[compound_frequency]

    col3, col4 = st.columns([1,3])


    with col3:
        with st.container(border=True):

            stock_data = None
            if stock_ticker:
                with st.spinner(f"Fetching data for {stock_ticker}..."):
                    stock_history = fetch_stock_data(stock_ticker, time)
                    start_price = stock_history['Close'].iloc[0]
                    end_price = stock_history['Close'].iloc[-1]
                    stock_cagr = calculate_cagr(start_price, end_price, time)
                    stock_data = {'yearly_return': stock_cagr}
                    stock_performance = [principal * (1 + stock_cagr) ** t for t in range(time + 1)]
                    st.markdown(f"Stock performance for {stock_ticker}")
                    st.write(f"- Historical annual return for {stock_ticker}: {stock_cagr:.2%}")
                    st.markdown(f'- Start Price: ${start_price:.2f}'
                                f'\n- End Price: ${end_price:.2f}'
                                f'\n- CAGR: {stock_cagr:.2%}'
                                f"\n- Total value after {time} years: ${stock_performance[-1]:,.2f}"
                                )
                    # rate = stock_cagr * 100
            # else:
            # rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, max_value=100.0, value=7.0, step=0.1)

            total = compound_interest(principal, rate, time, contributions, frequency)

            st.markdown("---")
            st.markdown("Compound Interest")
            st.write(f"- Total value after {time} years: ${total:,.2f}")
            st.write(f"- Compound Frequency: {compound_frequency}")

    with col4:
        with st.container(border=True):
            fig = plot_compound_interest(principal, rate, time, contributions, frequency, stock_data)
            st.plotly_chart(fig, use_container_width=True)



global_sidebar()
stock_selector()


investment_calculator()