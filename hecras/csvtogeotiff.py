import pandas as pd
import numpy as np
from osgeo import gdal, osr

# Load the CSV file (make sure it contains 'x', 'y', 'elevation' columns)
csv_file = r"C:\Yna\Thesis\FLOWS\hecras\elevation_data.csv"  # Update with your CSV file path
data = pd.read_csv(csv_file)

elevation_data = data.iloc[:, 1:].values  # Assuming 'Hour' is the first column

# Set the grid dimensions
profiles = elevation_data.shape[0]  # Number of profiles (rows)
grid_size = elevation_data.shape[1]  # Number of grid cells (columns per profile)

# Assume the grid size corresponds to the number of columns in the raster
cols = grid_size
rows = profiles

# Create an empty raster initialized to NaN
raster = np.full((rows, cols), np.nan)

# Populate the raster with elevation data from CSV (each row corresponds to a profile)
for i in range(profiles):
    raster[i, :] = elevation_data[i, :]

# Create the GeoTIFF output file
driver = gdal.GetDriverByName('GTiff')
output_tif = r"C:\Yna\Thesis\FLOWS\hecras\output_raster.tif"  # Set the output path

# Create the raster dataset
out_ds = driver.Create(output_tif, cols, rows, 1, gdal.GDT_Float32)

# Set the geotransform (mapping from pixel coordinates to geospatial coordinates)
x_min, y_max = 0, 0  # Set these values based on your data's location
cell_size = 1  # You can adjust this value based on your data resolution
geotransform = (x_min, cell_size, 0, y_max, 0, -cell_size)
out_ds.SetGeoTransform(geotransform)

# Set the projection (assuming WGS84, you can modify this based on your data's CRS)
srs = osr.SpatialReference()
srs.SetWellKnownGeogCS('WGS84')  # Modify this if using a different CRS
out_ds.SetProjection(srs.ExportToWkt())

# Write the elevation data to the raster band
out_band = out_ds.GetRasterBand(1)
out_band.WriteArray(raster)

# Close the dataset
out_band.FlushCache()
out_ds = None

print(f"✅ Successfully converted CSV to GeoTIFF: {output_tif}")