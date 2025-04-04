import pandas as pd
import numpy as np

# Load the elevation CSV (assuming columns 'Hour' and 'Elevation1', 'Elevation2', etc.)
elevation_csv_file = r"C:\Yna\Thesis\FLOWS\hecras\elevation_data.csv"
elevation_data = pd.read_csv(elevation_csv_file, header=None)

# Load the coordinates CSV (assuming columns 'x' and 'y')
coordinates_csv_file = r"C:\Yna\Thesis\FLOWS\hecras\coordinates_data.csv"
coordinates_data = pd.read_csv(coordinates_csv_file, header=None)

# Check the first few rows of both files to inspect the structure
print("Elevation Data:")
print(elevation_data.head())

print("\nCoordinates Data:")
print(coordinates_data.head())
# Manually assign column names (adjust the names based on your data structure)
# Assuming the first column in the elevation data is 'Hour' and remaining are elevation values
elevation_data.columns = ['Hour'] + [f'Elevation{i}' for i in range(1, elevation_data.shape[1])]

# Assuming the coordinates data has two columns: 'x' and 'y' for each elevation point
coordinates_data.columns = ['x', 'y']

# Check the first few rows of both files to inspect the structure
print("Elevation Data (with assigned columns):")
print(elevation_data.head())

print("\nCoordinates Data (with assigned columns):")
print(coordinates_data.head())

# Ensure that the coordinates CSV has only one set of coordinates repeated
if len(coordinates_data) == 1:
    print("Coordinates are the same for all profiles.")
else:
    print("Warning: There seems to be more than one set of coordinates.")

# Flatten the coordinates data (same coordinates for all rows)
coordinates = coordinates_data.iloc[0, :].values  # Extract the first and only coordinate pair

# Compare the coordinates for each profile
elevation_values = elevation_data.iloc[:, 1:].values  # Extract elevation values (ignoring 'Hour' column)

# Now, we will print the coordinates with each elevation profile
for i in range(len(elevation_data)):
    print(f"Hour {elevation_data.iloc[i, 0]}: Coordinates: {coordinates}, Elevation: {elevation_values[i]}")

print(len(coordinates_data))
print(elevation_data.shape[1])
# Check if coordinates are aligned with elevation data
if len(coordinates) == 2 and elevation_values.shape[1] == len(coordinates):
    print("Coordinates and Elevation values align correctly!")
else:
    print("Warning: There may be a mismatch in the data.")
