import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
from keras import models
from keras import Sequential
from keras import layers
import plotly.graph_objs as go
from utils import global_sidebar, stock_selector
st.set_page_config(layout="wide")

if not os.path.exists('saved_models'):
    os.makedirs('saved_models')
@st.cache_data
def load_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    data.reset_index(inplace=True)
    data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')
    return data


def prepare_data(df):
    df['Date'] = pd.to_datetime(df['Date'])

    data_training = pd.DataFrame(df['Close'][0:int(len(df) * 0.70)])
    data_testing = pd.DataFrame(df['Close'][int(len(df) * 0.70): int(len(df))])

    scaler = MinMaxScaler(feature_range=(0, 1))
    data_training_array = scaler.fit_transform(data_training)

    x_train = []
    y_train = []
    for i in range(100, data_training_array.shape[0]):
        x_train.append(data_training_array[i - 100:i])
        y_train.append(data_training_array[i, 0])

    x_train, y_train = np.array(x_train), np.array(y_train)

    past_100_days = data_training.tail(100)
    final_df = pd.concat([past_100_days, data_testing], ignore_index=True)
    input_data = scaler.transform(final_df)

    x_test = []
    y_test = []
    for i in range(100, input_data.shape[0]):
        x_test.append(input_data[i - 100:i])
        y_test.append(input_data[i, 0])

    x_test, y_test = np.array(x_test), np.array(y_test)

    return x_train, y_train, x_test, y_test, scaler


def create_model(input_shape):
    model = Sequential()
    model.add(layers.LSTM(units=50, activation='relu', return_sequences=True, input_shape=input_shape))
    model.add(layers.Dropout(0.2))
    model.add(layers.LSTM(units=60, activation='relu', return_sequences=True))
    model.add(layers.Dropout(0.3))
    model.add(layers.LSTM(units=80, activation='relu', return_sequences=True))
    model.add(layers.Dropout(0.4))
    model.add(layers.LSTM(units=120, activation='relu'))
    model.add(layers.Dropout(0.5))
    model.add(layers.Dense(units=1))
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model


def plot_price_and_ema(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name="Close Price"))
    fig.update_layout(title='Closing Price vs Time Chart', xaxis_title='Date', yaxis_title='Price')
    return fig


def plot_predictions(y_test, y_pred, dates):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=y_test, name="Actual Price"))
    fig.add_trace(go.Scatter(x=dates, y=y_pred, name="Predicted Price"))
    fig.update_layout(title='Predictions vs Actual', xaxis_title='Date', yaxis_title='Price')
    return fig

def plot_price_and_predictions(df, predictions, future_dates):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name="Historical Close Price"))
    fig.add_trace(go.Scatter(x=future_dates, y=predictions, name="Predicted Price"))
    fig.update_layout(title='Historical and Predicted Stock Prices', xaxis_title='Date', yaxis_title='Price')
    return fig

def predict_future(model, scaler, last_100_days, num_days):
    future_predictions = []
    current_batch = last_100_days[-100:].reshape((1, 100, 1))

    for _ in range(num_days):
        future_price = model.predict(current_batch)[0][0]
        future_predictions.append(future_price)
        current_batch = np.roll(current_batch, -1, axis=1)
        current_batch[0, -1, 0] = future_price

    future_predictions = scaler.inverse_transform(np.array(future_predictions).reshape(-1, 1))
    return future_predictions.flatten()


def stock_prediction():
    st.title('Stock Trend Prediction using LSTM')

    st.write("""
    ### Disclaimer
    This tool uses machine learning (LSTM) to predict stock trends based on historical data. 
    Stock markets are influenced by many factors, and past performance does not guarantee future results. 
    These predictions should not be used as the sole basis for any financial decisions.
    """)

    with st.container(border=True):
        selected_stock = st.text_input('Enter Stock Ticker', 'AAPL')
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date", datetime.now() - timedelta(days=5 * 365))
        with col2:
            end_date = st.date_input("End date", datetime.now())

    data_load_state = st.text('Loading data...')
    df = load_data(selected_stock, start_date, end_date)
    data_load_state.text('Loading data... done!')

    with st.expander("Show/hide raw data", expanded=False):
        st.subheader('Raw data')
        st.dataframe(df.head(), use_container_width=True)

    with st.expander("Show/hide price chart", expanded=False):
        st.subheader('Closing Price vs Time Chart')
        fig_price = plot_price_and_ema(df)
        st.plotly_chart(fig_price, use_container_width=True)

    # Prepare data for LSTM
    x_train, y_train, x_test, y_test, scaler = prepare_data(df)

    # Check if a saved model exists
    model_path = f'saved_models/{selected_stock}_model.h5'
    if os.path.exists(model_path):
        st.write(f"Loading saved model for {selected_stock}...")
        model = models.load_model(model_path)
    else:
        st.write(f"No saved model found for {selected_stock}. Training a new model...")
        model = create_model((x_train.shape[1], 1))
        model.fit(x_train, y_train, epochs=5, batch_size=32, verbose=0)
        model.save(model_path)

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            retrain = st.button("Retrain Model", use_container_width=True)
        with col2:
            epochs = st.number_input("Number of epochs for retraining", min_value=1, max_value=200, value=5)

    if retrain:
        st.write(f"Retraining model for {selected_stock}...")
        model = create_model((x_train.shape[1], 1))
        model.fit(x_train, y_train, epochs=epochs, batch_size=32, verbose=0)
        model.save(model_path)
        st.write("Retraining complete!")

    # Make predictions
    y_predicted = model.predict(x_test)

    # Scale back to original price
    scale_factor = 1 / scaler.scale_[0]
    y_predicted = y_predicted * scale_factor
    y_test = y_test * scale_factor

    with st.expander("Show/hide model prediction details", expanded=True):
        # Plot predictions
        st.subheader('LSTM Model: Predictions vs Original')
        test_dates = df['Date'].iloc[-len(y_test):]
        fig_pred = plot_predictions(y_test, y_predicted.flatten(), test_dates)
        st.plotly_chart(fig_pred, use_container_width=True)

        # Calculate and display metrics
        st.subheader("Model Performance Metrics")
        mae = np.mean(np.abs(y_predicted - y_test))
        mape = np.mean(np.abs((y_test - y_predicted) / y_test)) * 100
        col1, col2 = st.columns(2)
        col1.metric("Mean Absolute Error", f"${mae:.2f}")
        col2.metric("Mean Absolute Percentage Error", f"{mape:.2f}%")

        st.write("""
        ### Interpretation of Metrics
        - **Mean Absolute Error (MAE)**: On average, the model's predictions deviate from the actual stock price by this amount.
        - **Mean Absolute Percentage Error (MAPE)**: On average, the model's predictions deviate from the actual stock price by this percentage.
    
        A lower value for both metrics indicates better model performance.
        """)


    with st.expander("Show/hide future price predictions", expanded=True):
        # Future predictions
        st.subheader("Future Price Predictions")
        num_future_days = st.slider("Number of days to predict:", 1, 30, 7)

        last_100_days = df['Close'].values[-100:]
        last_100_days_scaled = scaler.transform(last_100_days.reshape(-1, 1))

        future_predictions = predict_future(model, scaler, last_100_days_scaled, num_future_days)

        future_dates = pd.date_range(start=df['Date'].iloc[-1], periods=num_future_days + 1)[1:].strftime('%Y-%m-%d')

        prediction_df = pd.DataFrame({'Date': future_dates, 'Predicted Price': future_predictions})
        st.dataframe(prediction_df, use_container_width=True)

        # Plot historical and future predictions
        st.subheader('Historical and Future Price Predictions')
        fig_future = go.Figure()
        fig_future.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name="Historical Close Price"))
        fig_future.add_trace(go.Scatter(x=future_dates, y=future_predictions, name="Predicted Future Price"))
        fig_future.update_layout(title='Historical and Predicted Stock Prices', xaxis_title='Date', yaxis_title='Price')
        st.plotly_chart(fig_future, use_container_width=True)
global_sidebar()
stock_selector()
stock_prediction()
