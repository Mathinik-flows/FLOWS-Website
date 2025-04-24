import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.losses import mse 
from sklearn.preprocessing import MinMaxScaler

#------ CONFIG ---------
CSV_LOCATION = r"D:\FLOWS\Ver2\FLOWS-Website\final\Config\finaldata2.csv"
MODEL_LOCATION = r"D:\FLOWS\Ver2\FLOWS-Website\final\Config\flows_modelv4.h5"

# Load dataset
data = pd.read_csv(CSV_LOCATION)

# === Filter data for training/history ===
historical_data = data[(data['Year'] < 2024) | ((data['Year'] == 2024) & (data['Month'] < 10))]

# Prepare the data for scaling
rainfall = historical_data['Rainfall'].values
waterlevel = historical_data['WaterLevel'].values
fwaterlevel = historical_data['FWaterLevel'].values

# Scale the data
scaler_rainfall = MinMaxScaler()
scaler_waterlevel = MinMaxScaler()
scaler_fwaterlevel = MinMaxScaler()

rainfall_scaled = scaler_rainfall.fit_transform(rainfall.reshape(-1, 1))
waterlevel_scaled = scaler_waterlevel.fit_transform(waterlevel.reshape(-1, 1))
fwaterlevel_scaled = scaler_fwaterlevel.fit_transform(fwaterlevel.reshape(-1, 1))

# Create the NARX dataset
def create_narx_dataset(waterlevel, rainfall, fwaterlevel, n_y, n_u):
    X, y = [], []
    for i in range(len(waterlevel) - max(n_y, n_u)):
        y_input = waterlevel[i:i+n_y].flatten()
        u_input = rainfall[i:i+n_u].flatten()
        X.append(np.concatenate((y_input, u_input)))
        y.append(fwaterlevel[i+n_y])
    return np.array(X), np.array(y)

n_y = 48
n_u = 48
X, _ = create_narx_dataset(waterlevel_scaled, rainfall_scaled, fwaterlevel_scaled, n_y, n_u)

# Load model
from tensorflow.keras.models import load_model
model = tf.keras.models.load_model(MODEL_LOCATION, custom_objects={'mse': mse})

# === Prepare data for October 2024 prediction ===
october_data = data[(data['Year'] == 2024) & (data['Month'] == 10)]

oct_rainfall = october_data['Rainfall'].values
oct_waterlevel = october_data['WaterLevel'].values

# Scale October inputs
oct_rainfall_scaled = scaler_rainfall.transform(oct_rainfall.reshape(-1, 1))
oct_waterlevel_scaled = scaler_waterlevel.transform(oct_waterlevel.reshape(-1, 1))

# Create input sequences for October 2024
X_october, _ = create_narx_dataset(oct_waterlevel_scaled, oct_rainfall_scaled, fwaterlevel_scaled, n_y, n_u)

# Make predictions
predictions_scaled = model.predict(X_october)
predictions_original = scaler_fwaterlevel.inverse_transform(predictions_scaled)
flat_predictions = predictions_original.flatten()

# Chunk into 12-hour segments
chunk_size = 12
chunks = [flat_predictions[i:i+chunk_size] for i in range(0, len(flat_predictions), chunk_size)]
chunks = [chunk for chunk in chunks if len(chunk) == chunk_size]

# Save to CSV
chunks_df = pd.DataFrame(chunks, columns=[f'Hour{i+1}' for i in range(chunk_size)])
chunks_df.insert(0, "Batch", range(1, len(chunks_df)+1))
chunks_df.to_csv("october2024_predictions2.csv", index=False)

print("✅ Saved 12-hour chunk predictions to 'october2024_predictions2.csv'")
