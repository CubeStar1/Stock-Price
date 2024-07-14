import streamlit as st
import pandas as pd
from utils import get_last_n_quarters, get_last_n_years, fetch_stock_data, get_stock_data, store_stock_data, get_date_range
from utils import global_sidebar, percent_sidebar
import matplotlib.pyplot as plt
st.set_page_config(layout="wide")

def quarterly_analysis():
    st.title("Quarterly Percentage Change in Stock Prices")

    num_quarters = st.slider("Select the number of quarters to compare:", min_value=2, max_value=20, value=4, step=2)
    last_n_quarters = get_last_n_quarters(num_quarters)

    col1, col2 = st.columns(2)
    selected_quarters = []
    graphs = []
    combined_data = {ticker: [] for ticker in st.session_state.selected_tickers}

    for i in range(1, num_quarters + 1):
        if i % 2 != 0:
            with col1:
                with st.container(border=True):
                    quarter = st.selectbox(f"Select Quarter {i}:", ["Q1", "Q2", "Q3", "Q4"], key=f"quarter_{i}",
                                           index=["Q1", "Q2", "Q3", "Q4"].index(last_n_quarters[i - 1][0]))
                    year = st.selectbox(f"Select Year {i}:", get_last_n_years(10), key=f"year_{i}",
                                        index=get_last_n_years(10).index(last_n_quarters[i - 1][1]))
                    selected_quarters.append((quarter, year))
                    graph = st.empty()
                    graphs.append(graph)
        else:
            with col2:
                with st.container(border=True):
                    quarter = st.selectbox(f"Select Quarter {i}:", ["Q1", "Q2", "Q3", "Q4"], key=f"quarter_{i}",
                                           index=["Q1", "Q2", "Q3", "Q4"].index(last_n_quarters[i - 1][0]))
                    year = st.selectbox(f"Select Year {i}:", get_last_n_years(10), key=f"year_{i}",
                                        index=get_last_n_years(10).index(last_n_quarters[i - 1][1]))
                    selected_quarters.append((quarter, year))
                    graph = st.empty()
                    graphs.append(graph)

    selected_tickers = st.session_state.selected_tickers
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

            filtered_stock_data = {ticker: stock_data[ticker] for ticker in selected_tickers if
                                   ticker in stock_data}

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
        print(selected_quarters)
        print(combined_data)
        combined_df = pd.DataFrame.from_dict(combined_data, orient='index',
                                             columns=[f"{quarter} {year}" for quarter, year in selected_quarters])
        combined_df.reset_index(inplace=True)
        combined_df.rename(columns={'index': 'Company'}, inplace=True)
        combined_df = combined_df.round(2)
        with st.container(border=True):
            st.write("### Combined Percentage Change Table")
            st.dataframe(combined_df.sort_values("Company"), use_container_width=True, hide_index=True)
# This includes fetching data, creating charts, and displaying results

global_sidebar()
percent_sidebar()
quarterly_analysis()