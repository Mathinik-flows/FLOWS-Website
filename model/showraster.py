import matplotlib.pyplot as plt
import rasterio

with rasterio.open("elevation_8bit.tif") as src:
    img = src.read(1)
    plt.imshow(img, cmap='gray')
    plt.colorbar()
    plt.show()
