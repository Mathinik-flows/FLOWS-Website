import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.losses import mse
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta
import os

#------ CONFIG ---------
# Base directory (where the script is located)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CSV_LOCATION = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'assets', 'finaldata2.csv'))
MODEL_LOCATION = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'assets', 'flows_modelv4.h5'))
LOG_PATH = os.path.join(BASE_DIR, "prediction_log.txt")
OUTPUT_CSV = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'assets', 'flood_predictions.csv'))

# Parameters
n_y, n_u = 48, 48
PREDICT_HOURS = 6
START_DATETIME = datetime(2024, 10, 24, 0, 0) #add plus two days to desired day
START_YEAR = START_DATETIME.year
START_MONTH = START_DATETIME.month
START_DAY = START_DATETIME.day

# Load dataset
data = pd.read_csv(CSV_LOCATION)

# Scale training data (before the specified date and time)
def load_historical_data(year, month, day):
    start_dt = datetime(year, month, day)

    historical_data = data.copy()
    historical_data['Datetime'] = pd.to_datetime(
        historical_data[['Year', 'Month', 'Day', 'Hour']], errors='coerce'
    )

    historical_data = historical_data.dropna(subset=['Datetime'])
    historical_data = historical_data[historical_data['Datetime'] < start_dt]

    return historical_data

rainfall = None
waterlevel = None
fwaterlevel = None

scaler_rainfall = None
scaler_waterlevel = None
scaler_fwaterlevel = None

def apply_scaling(historical_data):
    global rainfall, waterlevel, fwaterlevel, scaler_rainfall, scaler_waterlevel, scaler_fwaterlevel

    rainfall = historical_data['Rainfall'].values
    waterlevel = historical_data['WaterLevel'].values
    fwaterlevel = historical_data['FWaterLevel'].values

    scaler_rainfall = MinMaxScaler().fit(rainfall.reshape(-1, 1))
    scaler_waterlevel = MinMaxScaler().fit(waterlevel.reshape(-1, 1))
    scaler_fwaterlevel = MinMaxScaler().fit(fwaterlevel.reshape(-1, 1))

model = tf.keras.models.load_model(MODEL_LOCATION, custom_objects={'mse': mse})

def apply_scaling_to_data(monthly_data):
    monthly_data['Rainfall_scaled'] = scaler_rainfall.transform(monthly_data['Rainfall'].values.reshape(-1, 1)).flatten()
    monthly_data['WaterLevel_scaled'] = scaler_waterlevel.transform(monthly_data['WaterLevel'].values.reshape(-1, 1)).flatten()
    return monthly_data

def load_data_for_month(year, month):
    monthly_data = data[(data['Year'] == year) & (data['Month'] == month)].copy()
    monthly_data['Datetime'] = pd.to_datetime(monthly_data[['Year', 'Month', 'Day', 'Hour']])
    monthly_data.dropna(subset=['Datetime'], inplace=True)
    monthly_data = monthly_data.sort_values('Datetime').reset_index(drop=True)
    return monthly_data

def create_narx_input(dataframe, n_y, n_u, prediction_step=1):
    sequences = []
    timestamps = []
    for i in range(len(dataframe) - max(n_y, n_u) - prediction_step + 1):
        y_input = dataframe['WaterLevel_scaled'].values[i:i+n_y]
        u_input = dataframe['Rainfall_scaled'].values[i:i+n_u]
        seq = np.concatenate((y_input, u_input))
        sequences.append(seq)

        # Predict for the time right after input
        target_time = dataframe['Datetime'].iloc[i + max(n_y, n_u) + prediction_step - 1]
        timestamps.append(target_time)
    return np.array(sequences), pd.to_datetime(timestamps)

def get_start_index(ts_all):
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r') as f:
            last_index = int(f.read().strip())
    else:
        # Try to find exact match first
        match_idx = np.where(ts_all == pd.Timestamp(START_DATETIME))[0]
        if len(match_idx) == 0:
            print(f"START_DATETIME {START_DATETIME} not found in data. Using first available timestamp: {ts_all[0]}")
            last_index = 0
        else:
            last_index = match_idx[0]
    return last_index

def move_to_next_month(current_year, current_month):
    next_month = current_month + 1
    next_year = current_year
    if next_month > 12:
        next_month = 1
        next_year += 1
    return next_year, next_month

# === Run Prediction Sequence ===

current_year = START_YEAR
current_month = START_MONTH
current_day = START_DAY

historical_data = load_historical_data(current_year, current_month, current_day)
apply_scaling(historical_data)

data_load = load_data_for_month(current_year, current_month)
data_load = apply_scaling_to_data(data_load)

X_all, ts_all = create_narx_input(data_load, n_y, n_u)

# Get start index based on log or START_DATETIME
start_idx = get_start_index(ts_all)
end_idx = start_idx + PREDICT_HOURS

if end_idx > len(X_all):
    print("No more predictions available in current month, moving to the next month.")
    current_year, current_month = move_to_next_month(current_year, current_month)
    historical_data = load_historical_data(current_year, current_month, 1)  # Fallback to day=1
    if len(historical_data) == 0:
        print("Warning: No historical data available for the next month.")
        exit()

    apply_scaling(historical_data)
    data_load = load_data_for_month(current_year, current_month)

    if len(data_load) == 0:
        print("Warning: No data available for the next month.")
        exit()
    else:
        data_load = apply_scaling_to_data(data_load)
        X_all, ts_all = create_narx_input(data_load, n_y, n_u)
        start_idx = 0
        end_idx = start_idx + PREDICT_HOURS

X_batch = X_all[start_idx:end_idx]
ts_batch = ts_all[start_idx:end_idx]

# Predict
pred_scaled = model.predict(X_batch)
pred = scaler_fwaterlevel.inverse_transform(pred_scaled).flatten()

# Offset timestamps by 2 days
ts_batch_offset = ts_batch - pd.Timedelta(days=2)

result_df = pd.DataFrame({
    'Year': ts_batch_offset.year,
    'Month': ts_batch_offset.month,
    'Day': ts_batch_offset.day,
    'Hour': ts_batch_offset.hour,
    'PredictedFWaterLevel': pred
})

# Save predictions to CSV
result_df.to_csv(OUTPUT_CSV, mode='w', header=True, index=False)

# Update log
with open(LOG_PATH, 'w') as f:
    f.write(str(end_idx))

print(f"Saved predictions for {ts_batch[0]} to {ts_batch[-1]} -> {OUTPUT_CSV}")
