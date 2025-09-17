# himachal_disaster_predictor.py

import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import matplotlib.pyplot as plt

# ---------- CONFIG ----------
API_KEY = "b382c0303d2cf4c1bd7245371bc5becd"  # Replace with your free OpenWeatherMap API Key
LAT = 31.1048  # Shimla lat
LON = 77.1734  # Shimla lon

# ---------- DATA COLLECTION ----------
def fetch_rainfall(lat=LAT, lon=LON):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()
    rainfall = data.get("rain", {}).get("1h", 0)
    return {
        "timestamp": datetime.utcnow(),
        "latitude": lat,
        "longitude": lon,
        "rainfall_mm": rainfall
    }

def fetch_earthquakes_hp():
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=3650)
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": start_time.strftime("%Y-%m-%d"),
        "endtime": end_time.strftime("%Y-%m-%d"),
        "minlatitude": 30.0,
        "maxlatitude": 33.5,
        "minlongitude": 75.5,
        "maxlongitude": 79.0
    }
    response = requests.get(url, params=params)
    data = response.json()
    events = []
    for e in data["features"]:
        props = e["properties"]
        coords = e["geometry"]["coordinates"]
        events.append({
            "timestamp": datetime.utcfromtimestamp(props["time"] / 1000),
            "latitude": coords[1],
            "longitude": coords[0],
            "depth": coords[2],
            "magnitude": props["mag"],
            "place": props["place"]
        })
    return pd.DataFrame(events)

# ---------- DATA PREPARATION ----------
def prepare_dataset():
    eq_df = fetch_earthquakes_hp()
    rain_data = fetch_rainfall()
    rain_df = pd.DataFrame([rain_data])
    rain_df['event_type'] = 'rain'
    eq_df['event_type'] = 'quake'
    combined_df = pd.concat([
        eq_df[['timestamp', 'latitude', 'longitude', 'magnitude', 'depth', 'event_type']],
        rain_df[['timestamp', 'latitude', 'longitude', 'rainfall_mm', 'event_type']]
    ], ignore_index=True).sort_values(by='timestamp')
    return combined_df

# ---------- MODEL TRAINING ----------
def train_lstm_model(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    df_numeric = df.select_dtypes(include=[np.number])
    df = df_numeric.resample('D').mean().fillna(0)

    df['disaster_risk'] = ((df['rainfall_mm'] > 20) | (df['magnitude'] > 4)).astype(int)  # pseudo label

    features = df[['rainfall_mm', 'magnitude']].values
    scaler = MinMaxScaler()
    features_scaled = scaler.fit_transform(features)

    X, y = [], []
    for i in range(len(features_scaled) - 7):
        X.append(features_scaled[i:i+7])
        y.append(df['disaster_risk'].values[i+7])
    X, y = np.array(X), np.array(y)

    model = Sequential()
    model.add(LSTM(64, return_sequences=False, input_shape=(X.shape[1], X.shape[2])))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    model.fit(X, y, epochs=10, batch_size=8, verbose=0)

    return model, scaler, df

# ---------- STREAMLIT DASHBOARD ----------
st.set_page_config(page_title="Himachal Disaster Predictor", layout="wide")
st.title("🌋 Real-Time Disaster Prediction in Himachal Pradesh")

st.info("Fetching real-time rainfall and earthquake data...")
df = prepare_dataset()
st.dataframe(df.tail(10))

model, scaler, df_daily = train_lstm_model(df.copy())

st.success("✅ Model trained. Forecasting next 7-day risk...")
latest = df_daily[['rainfall_mm', 'magnitude']].values[-7:]
scaled_input = scaler.transform(latest)
input_seq = np.expand_dims(scaled_input, axis=0)

predicted_risks = []
predicted_coords = []
for i in range(7):
    pred = model.predict(input_seq)[0][0]
    predicted_risks.append(pred)
    predicted_coords.append((LAT, LON))
    # dummy rainfall prediction
    new_day = np.array([[pred * 50, 3]])  # Assume magnitude = 3
    new_input = np.append(input_seq[0][1:], new_day, axis=0)
    input_seq = np.expand_dims(new_input, axis=0)

future_dates = pd.date_range(df_daily.index[-1] + timedelta(days=1), periods=7)
forecast_df = pd.DataFrame({
    "Date": future_dates,
    "Disaster Risk (0-1)": predicted_risks,
    "Latitude": [LAT]*7,
    "Longitude": [LON]*7
})

st.subheader("📅 7-Day Disaster Risk Forecast")
st.dataframe(forecast_df)
st.line_chart(forecast_df.set_index("Date")["Disaster Risk (0-1)"])

st.markdown("---")
st.caption("Model uses rainfall + quake magnitude to assess risk of floods, landslides, or earthquakes.")
