import win32com.client
import h5py
import numpy as np
from osgeo import gdal


# Connect to HEC-RAS Controller
RASController = win32com.client.Dispatch("RAS67.HECRASController")  # Adjust version if needed

hdf_file = r"C:\Yna\Thesis\FLOWS\hecras\flow.p09.hdf"

# Define output GeoTIFF file
output_tiff = r"C:\Yna\Thesis\FLOWS\hecras\TIFFs\Output.tif"

with h5py.File(hdf_file, "r") as f:
    # Navigate through HDF structure (use f.keys() to explore)
    depth_data = f["Results/Unsteady/Depth"][:]  # Adjust path if needed

# Save depth data as GeoTIFF
gdal_array.SaveArray(depth_data, output_tiff, format="GTiff")

print(f"✅ GeoTIFF exported: {output_tiff}")