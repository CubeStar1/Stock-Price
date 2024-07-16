# news_feed.py
import streamlit as st
import pandas as pd
from newsapi import NewsApiClient
from datetime import datetime, timedelta
import plotly.graph_objects as go
from utils import global_sidebar, stock_selector

st.set_page_config(layout="wide")

# Initialize NewsAPI client
newsapi = NewsApiClient(api_key=st.secrets["NEWSAPI_API_KEY"])


def fetch_news(query, days=7):
    """Fetch news articles for a given query over the past few days."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    articles = newsapi.get_everything(
        q=query,
        from_param=start_date.strftime('%Y-%m-%d'),
        to=end_date.strftime('%Y-%m-%d'),
        language='en',
        sort_by='publishedAt',
        page_size=100
    )
    return articles['articles']


def plot_news_timeline(df):
    """Create a timeline plot of news articles."""
    # Create a mapping of unique sources to numeric values
    source_map = {source: i for i, source in enumerate(df['source'].unique())}

    fig = go.Figure(data=[go.Scatter(
        x=df['publishedAt'],
        y=[1] * len(df),
        mode='markers',
        marker=dict(
            size=10,
            color=[source_map[source] for source in df['source']],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(
                title='News Source',
                tickvals=list(source_map.values()),
                ticktext=list(source_map.keys()),
                lenmode='fraction',
                len=0.75
            )
        ),
        text=df.apply(lambda row: f"{row['source']}: {row['title']}", axis=1),
        hoverinfo='text+x'
    )])

    fig.update_layout(
        title='News Timeline',
        xaxis_title='Publication Date',
        yaxis_visible=False,
        height=400,
        margin=dict(l=10, r=10, t=30, b=10)
    )

    return fig


def news_feed_integration():
    st.title("News Feed ")

    # Stock/ETF selection
    selected_asset = st.selectbox(
        "Select a stock or ETF to analyze",
        options=st.session_state.selected_tickers
    )

    if selected_asset:
        st.subheader(f"Recent News for {selected_asset}")

        # Fetch news
        news_articles = fetch_news(selected_asset)

        if news_articles:
            # Create DataFrame
            df = pd.DataFrame(news_articles)
            df['publishedAt'] = pd.to_datetime(df['publishedAt'])
            df['source'] = df['source'].apply(lambda x: x['name'])

            # Plot news timeline
            st.plotly_chart(plot_news_timeline(df), use_container_width=True)

            # Display news articles
            st.subheader("Recent News Articles")
            for idx, article in df.iterrows():
                with st.container(border=True):
                    st.write(f"**[{article['title']}]({article['url']})**")
                    st.write(f"Source: {article['source']} | Date: {article['publishedAt'].strftime('%Y-%m-%d %H:%M')}")
                    with st.expander("Article Preview"):
                        st.write(article['description'])
                        st.write(f"[Read full article]({article['url']})")

            # News source distribution
            st.subheader("News Source Distribution")
            source_counts = df['source'].value_counts()
            fig = go.Figure(data=[go.Pie(labels=source_counts.index, values=source_counts.values)])
            fig.update_layout(height=400, title='Distribution of News Sources')
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning("No recent news articles found for this asset.")
    else:
        st.info("Please select a stock or ETF from the dropdown menu.")

global_sidebar()
stock_selector()


news_feed_integration()