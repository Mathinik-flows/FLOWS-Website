import rasterio
import numpy as np
from rasterio.crs import CRS

def convert_to_8bit_rasterio(input_path, output_path, scale_min=None, scale_max=None, target_crs='EPSG:32651'):
    with rasterio.open(input_path) as src:
        profile = src.profile.copy()

        # Step 1: If the CRS is missing or incorrect, assign the correct one
        if not src.crs or src.crs.to_string() != target_crs:
            print(f"Assigning CRS {target_crs} (no reprojection)...")
            profile.update({'crs': CRS.from_string(target_crs)})
        else:
            print(f"CRS is already {src.crs}")

        # Step 2: Read data as float for scaling
        data = src.read(1).astype(np.float32)

        # Auto-determine scale range
        if scale_min is None or scale_max is None:
            scale_min = np.nanmin(data)
            scale_max = np.nanmax(data)

        # Step 3: Normalize and convert to 8-bit
        scaled = ((data - scale_min) / (scale_max - scale_min)) * 255
        scaled = np.clip(scaled, 0, 255).astype(np.uint8)

        # Set 0–9 as NoData
        scaled[scaled < 10] = 0

        # Step 4: Update profile for 8-bit output
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

    # Step 6: Write the output raster
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(scaled, 1)
        dst.write_colormap(1, colormap)
        dst.update_tags(scale_min=str(scale_min), scale_max=str(scale_max))

    print(f"Converted {input_path} to 8-bit at {output_path} using range {scale_min}-{scale_max}")

# Example usage
input_file = r"D:\FLOWS\New folder\FLOWS-Website\model\Depth (03APR2025 00 00 00).Terrain.SmootherDEM.tif"
output_file = r"D:\FLOWS\New folder\FLOWS-Website\model\test.tif"

convert_to_8bit_rasterio(input_file, output_file)
