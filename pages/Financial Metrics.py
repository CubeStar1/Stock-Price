import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from utils import global_sidebar, percent_sidebar

def calculate_financial_metrics(ticker, years=5):
    try:
        stock = yf.Ticker(ticker)
        balance_sheet = stock.balance_sheet
        income_stmt = stock.financials
        metrics = []
        for year in range(years):
            if year < len(balance_sheet.columns) and year < len(income_stmt.columns):
                ebit = income_stmt.loc['EBIT', income_stmt.columns[year]]
                nopat = income_stmt.loc['EBIT', income_stmt.columns[year]] * (1 - 0.21)
                invested_capital = balance_sheet.loc['Invested Capital', balance_sheet.columns[year]]
                total_assets = balance_sheet.loc['Total Assets', balance_sheet.columns[year]]
                total_equity = balance_sheet.loc['Stockholders Equity', balance_sheet.columns[year]]
                net_income = income_stmt.loc['Net Income', income_stmt.columns[year]]

                roic = nopat / invested_capital if invested_capital else 0
                roa = net_income / total_assets if total_assets else 0
                roe = net_income / total_equity if total_equity else 0
                roce = ebit / (total_assets - balance_sheet.loc[
                    'Current Liabilities', balance_sheet.columns[year]]) if (total_assets - balance_sheet.loc[
                    'Current Liabilities', balance_sheet.columns[year]]) else 0

                metrics.append({
                    'Year': balance_sheet.columns[year].year,
                    'NOPAT': nopat,
                    'Invested Capital': invested_capital,
                    'ROIC': roic,
                    'ROA': roa,
                    'ROE': roe,
                    'ROCE': roce
                })

        return pd.DataFrame(metrics)
    except Exception as e:
        st.error(f"Error calculating metrics for {ticker}: {str(e)}")
        return None


def create_metric_graph(df, metric):
    fig = go.Figure()
    for ticker in df['Ticker'].unique():
        ticker_data = df[df['Ticker'] == ticker]
        fig.add_trace(go.Scatter(x=ticker_data['Year'], y=ticker_data[metric],
                                 mode='lines+markers', name=ticker))

    fig.update_layout(title=f'{metric} Over Time',
                      xaxis_title='Year',
                      yaxis_title=metric,
                      yaxis_tickformat='.2%')
    return fig


def financial_metrics_page():
    st.title("Financial Metrics Calculator")
    years = st.slider("Select the number of years to calculate metrics for:", min_value=1, max_value=5, value=5)

    if 'selected_tickers' in st.session_state and st.session_state.selected_tickers:
        all_metrics = []
        latest_metrics = {}
        for ticker in st.session_state.selected_tickers:
            metrics = calculate_financial_metrics(ticker, years=years)
            if metrics is not None:
                metrics['Ticker'] = ticker
                all_metrics.append(metrics)
                latest_metrics[ticker] = metrics.iloc[0]

        if all_metrics:
            combined_metrics = pd.concat(all_metrics, ignore_index=True)

            # Display the metrics table
            st.subheader("Financial Metrics")
            temp_df = combined_metrics.style.format({
                'NOPAT': '${:,.0f}',
                'Invested Capital': '${:,.0f}',
                'ROIC': '{:.2%}',
                'ROA': '{:.2%}',
                'ROE': '{:.2%}',
                'ROCE': '{:.2%}'
            })
            st.dataframe(combined_metrics, use_container_width=True)

            latest_df = pd.DataFrame(latest_metrics).T
            fig = go.Figure(data=[
                go.Bar(name='ROIC', x=latest_df.index, y=latest_df['ROIC']),
                go.Bar(name='ROA', x=latest_df.index, y=latest_df['ROA']),
                go.Bar(name='ROE', x=latest_df.index, y=latest_df['ROE']),
                go.Bar(name='ROCE', x=latest_df.index, y=latest_df['ROCE'])
            ])
            fig.update_layout(
                title='Latest Financial Metrics Comparison',
                xaxis_title='Stocks',
                yaxis_title='Ratio',
                yaxis_tickformat='.2%',
                barmode='group'
            )
            st.plotly_chart(fig)

            metrics_to_plot = ['ROIC', 'ROA', 'ROE', 'ROCE']
            for metric in metrics_to_plot:
                fig = create_metric_graph(combined_metrics, metric)
                st.plotly_chart(fig)

            st.subheader("Metrics Explanation")
            st.write("""
            - **NOPAT**: Net Operating Profit After Tax. Represents a company's after-tax operating profit for all investors.
            - **Invested Capital**: Total amount of money invested in the business by both shareholders and debtholders.
            - **ROIC**: Return on Invested Capital. Measures how efficiently a company uses its capital to generate profits.
            - **ROA**: Return on Assets. Shows how efficiently a company uses its assets to generate earnings.
            - **ROE**: Return on Equity. Measures a corporation's profitability in relation to stockholders' equity.
            - **ROCE**: Return on Capital Employed. Indicates the efficiency and profitability of a company's capital investments.
            """)
    else:
        st.info("Please enter one or more stock tickers to calculate financial metrics.")

global_sidebar()
percent_sidebar()
financial_metrics_page()