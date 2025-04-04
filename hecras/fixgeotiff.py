from osgeo import gdal

# Input CSV (with x, y, elevation values)
input_csv = r"C:\Yna\Thesis\FLOWS\hecras\merged_data.csv"
output_tif = r"C:\Yna\Thesis\FLOWS\hecras\elevation_no_gaps.tif"

# Reduce cell size (higher resolution)
xRes = 1  # Adjust as needed (smaller = less gaps)
yRes = 1  # Adjust as needed

# Convert CSV to Raster with adjusted cell size
gdal.Grid(output_tif, input_csv, algorithm="nearest", outputType=gdal.GDT_Float32, zfield="Elevation_Hour_1", xRes=xRes, yRes=yRes)

print(f"Raster created with no gaps: {output_tif}")
