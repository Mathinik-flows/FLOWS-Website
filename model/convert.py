import rasterio
import numpy as np
from rasterio.crs import CRS
import os

def convert_to_8bit_rasterio(input_path, output_path, scale_min=None, scale_max=None, target_crs='EPSG:32651'):
    with rasterio.open(input_path) as src:
        profile = src.profile.copy()

        # Step 1: Assign CRS if needed
        if not src.crs or src.crs.to_string() != target_crs:
            print(f"Assigning CRS {target_crs} to {os.path.basename(input_path)}...")
            profile.update({'crs': CRS.from_string(target_crs)})
        else:
            print(f"{os.path.basename(input_path)} CRS is already {src.crs}")

        # Step 2: Read and normalize
        data = src.read(1).astype(np.float32)

        if scale_min is None or scale_max is None:
            scale_min = np.nanmin(data)
            scale_max = np.nanmax(data)

        scaled = ((data - scale_min) / (scale_max - scale_min)) * 255
        scaled = np.clip(scaled, 0, 255).astype(np.uint8)

        # Set 0–9 as NoData
        scaled[scaled < 10] = 0

        # Step 4: Update profile
        profile.update({
            'dtype': 'uint8',
            'count': 1,
            'nodata': 0,
            'photometric': 'palette'
        })

        # Step 5: Define colormap
        colormap = {}
        for value in range(10, 25):
            colormap[value] = (244, 180, 0)  # Yellow
        for value in range(25, 51):
            colormap[value] = (251, 140, 0)  # Orange
        for value in range(51, 256):
            colormap[value] = (213, 0, 0)    # Red

    # Step 6: Write to output
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(scaled, 1)
        dst.write_colormap(1, colormap)
        dst.update_tags(scale_min=str(scale_min), scale_max=str(scale_max))

    print(f"✅ Converted: {os.path.basename(input_path)} → {os.path.basename(output_path)}")

# === Batch Conversion ===
input_folder = r"D:\FLOWS\New folder\FLOWS-Website\hecras\testfolder"
output_folder = r"D:\FLOWS\New folder\FLOWS-Website\model\converted_8bit"

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# List all .tif files in input folder
tif_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".tif")]

for idx, tif_file in enumerate(tif_files):
    input_path = os.path.join(input_folder, tif_file)
    output_path = os.path.join(output_folder, f"tif_{idx}.tif")
    convert_to_8bit_rasterio(input_path, output_path)
