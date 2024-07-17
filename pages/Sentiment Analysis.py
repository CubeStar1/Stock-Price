import streamlit as st
import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from utils import global_sidebar, stock_selector

st.set_page_config(layout="wide")


@st.cache_resource
def download_nltk_resources():
    nltk.download('vader_lexicon')


download_nltk_resources()

# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()


def get_news(ticker):
    """Fetch news articles for a given stock ticker using yfinance."""
    stock = yf.Ticker(ticker)
    return stock.news


def analyze_sentiment(text):
    """Analyze the sentiment of a given text."""
    return sia.polarity_scores(text)['compound']


def get_thumbnail_url(thumbnail_data):
    """Extract the thumbnail URL from the thumbnail data."""
    if thumbnail_data and 'resolutions' in thumbnail_data:
        # Try to get the original resolution first
        original = next((item for item in thumbnail_data['resolutions'] if item['tag'] == 'original'), None)
        if original:
            return original['url']
        # If original is not available, return the first available resolution
        elif thumbnail_data['resolutions']:
            return thumbnail_data['resolutions'][0]['url']
    return None  # Return None if no thumbnail is available


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
                sentiment = analyze_sentiment(article['title'])
                sentiments.append({
                    'title': article['title'],
                    'publisher': article.get('publisher', 'Unknown'),
                    'link': article['link'],
                    'publish_time': datetime.fromtimestamp(article['providerPublishTime']).strftime(
                        '%Y-%m-%d %H:%M:%S'),
                    'sentiment': sentiment,
                    'thumbnail': get_thumbnail_url(article.get('thumbnail'))
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
                    col1, col2 = st.columns([1, 3])

                    with col1:
                        if row['thumbnail']:
                            with st.container(border=True):
                                st.image(row['thumbnail'], use_column_width=True)
                        else:
                            st.write("No thumbnail available")

                    with col2:
                        st.write(f"**[{row['title']}]({row['link']})**")
                        st.write(f"Published by: {row['publisher']} on {row['publish_time']}")
                        st.write(f"Sentiment Score: {row['sentiment']:.2f}")
                        if row['sentiment'] > 0.05:
                            st.success("Positive sentiment")
                        elif row['sentiment'] < -0.05:
                            st.error("Negative sentiment")
                        else:
                            st.info("Neutral sentiment")

        else:
            st.warning("No recent news articles found for this stock.")

global_sidebar()
stock_selector()
stock_sentiment_analysis()