# stock_sentiment.py

import streamlit as st
import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from newsapi import NewsApiClient
import matplotlib.pyplot as plt
import seaborn as sns
from utils import global_sidebar, percent_sidebar

@st.cache_resource
def download_nltk_resources():
    nltk.download('vader_lexicon')

download_nltk_resources()

# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()

# Initialize NewsAPI client (you'll need to sign up for a free API key at newsapi.org)
newsapi = NewsApiClient(api_key=st.secrets["NEWSAPI_API_KEY"])


def get_news(ticker):
    """Fetch news articles for a given stock ticker."""
    articles = newsapi.get_everything(q=ticker, language='en', sort_by='publishedAt', page_size=10)
    return articles['articles']


def analyze_sentiment(text):
    """Analyze the sentiment of a given text."""
    return sia.polarity_scores(text)['compound']


def stock_sentiment_analysis():
    st.title("Stock Sentiment Analysis")

    # Stock selection
    selected_stock = st.selectbox(
        "Select a stock to analyze",
        options=st.session_state.selected_tickers
    )

    if selected_stock:
        st.subheader(f"Sentiment Analysis for {selected_stock}")

        # Fetch news
        news_articles = get_news(selected_stock)

        if news_articles:
            # Analyze sentiment
            sentiments = []
            for article in news_articles:
                sentiment = analyze_sentiment(article['title'] + ' ' + article['description'])
                sentiments.append({
                    'title': article['title'],
                    'description': article['description'],
                    'url': article['url'],
                    'sentiment': sentiment
                })

            # Create DataFrame
            df = pd.DataFrame(sentiments)

            # Plot sentiment distribution
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.histplot(df['sentiment'], kde=True, ax=ax)
            ax.set_title(f'Sentiment Distribution for {selected_stock}')
            ax.set_xlabel('Sentiment Score')
            ax.set_ylabel('Frequency')
            st.pyplot(fig)

            # Display average sentiment
            avg_sentiment = df['sentiment'].mean()
            st.metric("Average Sentiment", f"{avg_sentiment:.2f}", delta=None)

            # Display news articles with sentiment
            st.subheader("Recent News Articles")
            for idx, row in df.iterrows():
                with st.container(border=True):
                    st.write(f"**[{row['title']}]({row['url']})**")
                    st.write(f"Sentiment Score: {row['sentiment']:.2f}")
                    if row['sentiment'] > 0.05:
                        st.success("Positive sentiment")
                    elif row['sentiment'] < -0.05:
                        st.error("Negative sentiment")
                    else:
                        st.info("Neutral sentiment")

                    # Article preview
                    with st.expander("Article Preview"):
                        st.write(row['description'])
                        st.write(f"[Read full article]({row['url']})")

        else:
            st.warning("No recent news articles found for this stock.")

global_sidebar()
percent_sidebar()
stock_sentiment_analysis()