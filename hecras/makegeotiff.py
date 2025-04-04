import pandas as pd
import numpy as np
from osgeo import gdal, osr

# Load the merged coordinates and elevation data
coordinates_csv_file = r"C:\Yna\Thesis\FLOWS\hecras\Elevation4.csv"
merged_data = pd.read_csv(coordinates_csv_file)

# Check the first few rows of the data
print(merged_data.head())

# Reshape the data into a grid of coordinates and corresponding elevation values
unique_x = np.unique(merged_data['x'])
unique_y = np.unique(merged_data['y'])
print(unique_x, unique_y)
# Create a 2D grid of elevation values
elevation_grid = np.zeros((len(unique_y), len(unique_x)))

# Populate the elevation grid
for _, row in merged_data.iterrows():
    x_index = np.where(unique_x == row['x'])[0][0]
    y_index = np.where(unique_y == row['y'])[0][0]
    elevation_grid[y_index, x_index] = row['Elevation']

# Define the desired cell size (resolution) in meters
cell_size_x =2.5 # meters (change as needed)
cell_size_y = 3  # meters (change as needed)

# Create a new GDAL dataset to write the GeoTIFF
# Define the output file path for the GeoTIFF
output_geotiff = r"C:\Yna\Thesis\FLOWS\hecras\elevation_map.tif"

# Get the raster size (number of rows and columns)
rows, cols = elevation_grid.shape

# Create a new raster file with GDAL (1 band for elevation data)
driver = gdal.GetDriverByName('GTiff')
dataset = driver.Create(output_geotiff, cols, rows, 1, gdal.GDT_Float32)

# Set the projection to UTM 51N
srs = osr.SpatialReference()
srs.SetUTM(51, True)  # UTM Zone 51N
dataset.SetProjection(srs.ExportToWkt())

# Define the affine transformation to map (top-left corner) to (x, y)
# Adjust the GeoTransform to reflect the desired cell size
transform = [unique_x.min(), cell_size_x, 0, unique_y.min(), 0, -cell_size_y]
dataset.SetGeoTransform(transform)

# Write the elevation data to the raster band
band = dataset.GetRasterBand(1)
band.WriteArray(elevation_grid)

# Set NoData value (optional)
band.SetNoDataValue(-1)

# Close the dataset
dataset = None

print(f"GeoTIFF saved at: {output_geotiff}")
