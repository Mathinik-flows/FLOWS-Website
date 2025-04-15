import rasterio
from rasterio.crs import CRS

input_file = r"D:\FLOWS\New folder\FLOWS-Website\model\output_8bit.tif"
output_file = r"D:\FLOWS\New folder\FLOWS-Website\model\new_output_8bit.tif"

with rasterio.open(input_file) as src:
    profile = src.profile
    profile.update(crs=CRS.from_epsg(32651))

    with rasterio.open(output_file, 'w', **profile) as dst:
        dst.write(src.read())

with rasterio.open(output_file) as src:
    print("CRS:", src.crs)
    print("Bounds:", src.bounds)
