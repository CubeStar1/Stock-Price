import streamlit as st
import pandas as pd
from utils import get_last_n_years, fetch_stock_data, get_stock_data, store_stock_data
from utils import global_sidebar, stock_selector
st.set_page_config(layout="wide")

def yearly_analysis():
    st.title("Yearly Percentage Change in Stock Prices")

    num_years = st.slider("Select the number of years to compare:", min_value=2, max_value=20, value=4, step=1)
    years = get_last_n_years(num_years)

    selected_years = []
    graphs = []
    combined_data = {ticker: [] for ticker in st.session_state.selected_tickers}

    col1, col2 = st.columns(2)

    for i, year in enumerate(years):
        if i % 2 == 0:
            with col1:
                with st.container(border=True):
                    selected_year = st.selectbox(f"Select Year {i + 1}:", years, key=f"year_{i + 1}_entire", index=i)
                    selected_years.append(selected_year)
                    graph = st.empty()
                    graphs.append(graph)
        else:
            with col2:
                with st.container(border=True):
                    selected_year = st.selectbox(f"Select Year {i + 1}:", years, key=f"year_{i + 1}_entire", index=i)
                    selected_years.append(selected_year)
                    graph = st.empty()
                    graphs.append(graph)

    selected_tickers = st.session_state.selected_tickers
    if selected_tickers:
        data = []
        for i, year in enumerate(selected_years):
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"

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

global_sidebar()
stock_selector()
yearly_analysis()
