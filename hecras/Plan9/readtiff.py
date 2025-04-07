import rasterio

from rasterio.crs import CRS
from pyproj import Transformer

# file path
raster_fp = 'Depth (03APR2025 00 00 00).Terrain.SmootherDEM.tif'

# open file with rasterio
raster = rasterio.open(raster_fp)

lng, lat = 123.169024, 13.619924

# Check type of the variable 'raster'
type(raster)
print(raster.count)
print(raster.crs)
array = raster.read()
print(array.shape)

band1 = raster.read(1)
print(band1.dtype)
#123.152855
#13.622625

with rasterio.open(raster_fp) as dataset:
    # Transform coordinate to raster CRS if needed
    if dataset.crs != CRS.from_epsg(4326):
        transformer = Transformer.from_crs("EPSG:4326", dataset.crs, always_xy=True)
        x, y = transformer.transform(lng, lat)
        print(f"Transformed coordinates: x={x}, y={y}")
    else:
        x, y = lng, lat
        print(f"No Transformed coordinates: x={x}, y={y}")

    # Convert map coordinates to pixel row/col
    row, col = dataset.index(x, y)
    print(f"Received coordinates: lng={row}, lat={col}")

    # Read Band 1 value at the given row/col
    band1 = dataset.read(1)  # read band 1 (2D array)
    value = band1[row, col]

    print(f"Value at ({lng}, {lat}):", value)