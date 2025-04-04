import pandas as pd

# Load the elevation CSV (without headers)
elevation_csv_file = r"C:\Yna\Thesis\FLOWS\hecras\elevation_data.csv"
elevation_data = pd.read_csv(elevation_csv_file, header=None)

# Load the coordinates CSV (without headers)
coordinates_csv_file = r"C:\Yna\Thesis\FLOWS\hecras\fcoordinates_data.csv"
coordinates_data = pd.read_csv(coordinates_csv_file, header=None)

print("Elevation Data:")
print(elevation_data.head())

print("\nCoordinates Data:")
print(coordinates_data.head())

print(len(coordinates_data))
print(elevation_data.shape[0])
# Manually assign column names to the elevation data
elevation_data.columns = [f'Elevation{i}' for i in range(0, elevation_data.shape[1])]

# Assign column names to the coordinates data (assuming only two columns for x and y)
coordinates_data.columns = ['x', 'y']

# # Print out the first few rows to inspect the data
# print("Elevation Data:")
# print(elevation_data.head())

# print("\nCoordinates Data:")
# print(coordinates_data.head())

# Extract the first row of elevation data (i.e., the first profile's elevation values)
for i in range(0, 6):
    elevation = elevation_data.iloc[i, :]  # Extract all elevation values from the first row

    # Add the first row of elevation values as a new column to the coordinates data
    # Name the new column (e.g., 'Elevation_Hour_1')
    coordinates_data[f'Elevation'] = elevation.values
    # Print the final coordinates data with the added elevation values
    print("\nCoordinates Data with Elevation Added:")
    print(coordinates_data.head())

    # Save the updated coordinates data to a new CSV file if needed
    coordinates_data.to_csv(f"C:\Yna\Thesis\FLOWS\hecras\Elevation{i}.csv", index=False)

 
