import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.losses import mse 
from sklearn.preprocessing import MinMaxScaler

# Load your dataset
data = pd.read_csv("finaldata2.csv")  # Replace with your actual dataset file

# Assuming your dataset has columns: 'Year', 'Month', 'Day', 'Rainfall', 'WaterLevel', 'FWaterLevel'
# Filter the data to get the relevant historical data before January 2025
historical_data = data[(data['Year'] < 2025) | ((data['Year'] == 2025) & (data['Month'] == 1) & (data['Day'] == 1))]

# Prepare the data for scaling
rainfall = historical_data['Rainfall'].values
waterlevel = historical_data['WaterLevel'].values
fwaterlevel = historical_data['FWaterLevel'].values

# Scale the data using the same scalers as during training
scaler_rainfall = MinMaxScaler()
scaler_waterlevel = MinMaxScaler()
scaler_fwaterlevel = MinMaxScaler()

rainfall_scaled = scaler_rainfall.fit_transform(rainfall.reshape(-1, 1))
waterlevel_scaled = scaler_waterlevel.fit_transform(waterlevel.reshape(-1, 1))
fwaterlevel_scaled = scaler_fwaterlevel.fit_transform(fwaterlevel.reshape(-1, 1))

# Create the NARX dataset for the model
def create_narx_dataset(waterlevel, rainfall, fwaterlevel, n_y, n_u):
    X, y = [], []
    for i in range(len(waterlevel) - max(n_y, n_u)):
        y_input = waterlevel[i:i+n_y].flatten()
        u_input = rainfall[i:i+n_u].flatten()
        X.append(np.concatenate((y_input, u_input)))
        y.append(fwaterlevel[i+n_y])
    return np.array(X), np.array(y)

n_y = 48  # Number of previous water levels to use
n_u = 48  # Number of previous rainfall values to use
X, _ = create_narx_dataset(waterlevel_scaled, rainfall_scaled, fwaterlevel_scaled, n_y, n_u)

# Load your trained model (assuming you have saved it)
from tensorflow.keras.models import load_model
model = tf.keras.models.load_model("flows_modelv4.h5", custom_objects={'mse': mse})

# Prepare input for January 2025 prediction
# Assuming you have rainfall data for January 2025
january_rainfall = data[(data['Year'] == 2025) & (data['Month'] == 1)]['Rainfall'].values
january_waterlevel = data[(data['Year'] == 2025) & (data['Month'] == 1)]['WaterLevel'].values

# Scale the January data
january_rainfall_scaled = scaler_rainfall.transform(january_rainfall.reshape(-1, 1))
january_waterlevel_scaled = scaler_waterlevel.transform(january_waterlevel.reshape(-1, 1))

# Create input sequences for January 2025
X_january = create_narx_dataset(january_waterlevel_scaled, january_rainfall_scaled, fwaterlevel_scaled, n_y, n_u)

# Make predictions for January 2025
predictions_scaled = model.predict(X_january[0])

# Inverse transform the predictions to get the original FWaterLevel values
predictions_original = scaler_fwaterlevel.inverse_transform(predictions_scaled)

# Flatten predictions to 1D array
flat_predictions = predictions_original.flatten()

# Split into 12-hour chunks
chunk_size = 12
chunks = [flat_predictions[i:i+chunk_size] for i in range(0, len(flat_predictions), chunk_size)]

# Only keep full 12-hour chunks
chunks = [chunk for chunk in chunks if len(chunk) == chunk_size]

# Convert to DataFrame
chunks_df = pd.DataFrame(chunks, columns=[f'Hour{i+1}' for i in range(chunk_size)])
chunks_df.insert(0, "Batch", range(1, len(chunks_df)+1))

# Save to CSV
chunks_df.to_csv("january2025_predictions.csv", index=False)

print("Saved 12-hour chunk predictions to 'january2025_predictions.csv'")

# Output the predictions
#print("Predicted FWaterLevel for January 2025:")
#print(predictions_original)
