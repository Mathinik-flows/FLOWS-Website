import rasterio
import numpy as np
from rasterio.crs import CRS
import os
import shutil

def convert_to_8bit_rasterio(input_path, output_path_colormap, scale_min=None, scale_max=None, target_crs='EPSG:32651'):
    with rasterio.open(input_path) as src:
        profile = src.profile.copy()

        # Assign CRS if missing or incorrect
        if not src.crs or src.crs.to_string() != target_crs:
            print(f"Assigning CRS {target_crs} to {os.path.basename(input_path)}...")
            profile.update({'crs': CRS.from_string(target_crs)})
        else:
            print(f"{os.path.basename(input_path)} CRS is already {src.crs}")

        # Read data and mask NoData
        data = src.read(1).astype(np.float32)
        nodata_value = src.nodata if src.nodata is not None else -9999
        valid_mask = data != nodata_value
        data_valid = data[valid_mask]

        if scale_min is None or scale_max is None:
            scale_min = np.nanmin(data_valid)
            scale_max = np.nanmax(data_valid)

        # Scale valid data to 0–255
        scaled = np.zeros_like(data, dtype=np.uint8)
        scaled[valid_mask] = np.clip(
            ((data_valid - scale_min) / (scale_max - scale_min)) * 255, 0, 255
        ).astype(np.uint8)

        # Update profile
        profile.update({
            'dtype': 'uint8',
            'count': 1,
            'nodata': 0,
            'photometric': 'palette'
        })

        # Define colormap
        colormap = {}
        for value in range(1, 22):       # Yellow
            colormap[value] = (244, 180, 0)
        for value in range(23, 43):     # Orange
            colormap[value] = (251, 140, 0)
        for value in range(44, 256):    # Red
            colormap[value] = (213, 0, 0)

    # Write colormapped 8-bit output
    with rasterio.open(output_path_colormap, 'w', **profile) as dst:
        dst.write(scaled, 1)
        dst.write_colormap(1, colormap)
        dst.update_tags(scale_min=str(scale_min), scale_max=str(scale_max))

    print(f"Converted to 8-bit with colormap: {os.path.basename(output_path_colormap)}")

def convert_colormap_to_rgb(input_path_colormap, output_path_rgb):
    with rasterio.open(input_path_colormap) as src:
        band = src.read(1)
        colormap = src.colormap(1)

        # Convert colormap to RGB bands
        rgb = np.zeros((3, band.shape[0], band.shape[1]), dtype=np.uint8)
        for value, color in colormap.items():
            mask = band == value
            rgb[0][mask] = color[0]  # Red
            rgb[1][mask] = color[1]  # Green
            rgb[2][mask] = color[2]  # Blue

        # Update profile
        profile = src.profile.copy()
        profile.update({
            'count': 3,
            'dtype': 'uint8',
            'photometric': 'RGB',
            'nodata': 0
        })

        # Write RGB output
        with rasterio.open(output_path_rgb, 'w', **profile) as dst:
            dst.write(rgb[0], 1)
            dst.write(rgb[1], 2)
            dst.write(rgb[2], 3)

    print(f"Converted to RGB: {os.path.basename(output_path_rgb)}")

# === Batch Processing ===

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

input_folder = os.path.abspath(os.path.join(BASE_DIR, '..', 'test'))
output_folder = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'assets', 'converted_rgb'))
copied_folder = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'assets', 'original'))

os.makedirs(copied_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)

tif_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".tif")]

for idx, tif_file in enumerate(tif_files):
    input_path = os.path.join(input_folder, tif_file)
    temp_colormap_path = os.path.join(output_folder, f"temp_colormap_{idx}.tif")
    final_rgb_path = os.path.join(output_folder, f"tif_rgb_{idx}.tif")

    convert_to_8bit_rasterio(input_path, temp_colormap_path)
    convert_colormap_to_rgb(temp_colormap_path, final_rgb_path)

    os.remove(temp_colormap_path)
    print(f"Removed temp file: {os.path.basename(temp_colormap_path)}")
    
    renamed_original_path = os.path.join(copied_folder, f"tif_rgb_{idx}.tif")
    shutil.copy2(input_path, renamed_original_path)
    
    print(f"Original copied and renamed: {os.path.basename(renamed_original_path)}")

print("\nAll files converted to RGB for Mapbox upload.")
