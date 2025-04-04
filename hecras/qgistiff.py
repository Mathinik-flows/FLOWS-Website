import sys
import os

# ✅ SET QGIS INSTALLATION PATH (Update this if needed)
QGIS_PATH = r"C:\Program Files\QGIS 3.34\apps\qgis"
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(QGIS_PATH, "qt5", "plugins")
os.environ["GDAL_DATA"] = os.path.join(QGIS_PATH, "share", "gdal")
os.environ["PYTHONPATH"] = os.path.join(QGIS_PATH, "python")

sys.path.append(os.path.join(QGIS_PATH, "python"))
sys.path.append(os.path.join(QGIS_PATH, "python", "plugins"))

# ✅ Import QGIS modules
from qgis.core import (
    QgsApplication,
    QgsRasterLayer,
    QgsProject,
    QgsStyle,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsSymbol,
)
from PyQt5.QtGui import QColor

# ✅ Initialize QGIS application (run without GUI)
qgs = QgsApplication([], False)
qgs.initQgis()

# ✅ Path to your GeoTIFF file
geotiff_path = r"C:\path\to\your\geotiff.tif"

# ✅ Load the GeoTIFF layer
raster_layer = QgsRasterLayer(geotiff_path, "Flood Map", "gdal")
if not raster_layer.isValid():
    print("Failed to load the raster layer!")
    qgs.exitQgis()
    sys.exit(1)

# ✅ Create flood level symbology
categories = [
    QgsRendererCategory(0, QgsSymbol.defaultSymbol(raster_layer.geometryType()), "No Data"),
    QgsRendererCategory(1, QgsSymbol.defaultSymbol(raster_layer.geometryType()), "Low Flood Level 0.1-0.5m"),
    QgsRendererCategory(2, QgsSymbol.defaultSymbol(raster_layer.geometryType()), "Moderate Flood Level 0.6-1.5m"),
    QgsRendererCategory(3, QgsSymbol.defaultSymbol(raster_layer.geometryType()), "High Flood Level >1.5m"),
]

# Assign colors to the categories
categories[1].symbol().setColor(QColor("#FFD166"))  # Yellow
categories[2].symbol().setColor(QColor("#F9844A"))  # Orange
categories[3].symbol().setColor(QColor("#EF233C"))  # Red

# ✅ Apply symbology to the layer
renderer = QgsCategorizedSymbolRenderer("VALUE", categories)
raster_layer.setRenderer(renderer)

# ✅ Add the layer to the project
QgsProject.instance().addMapLayer(raster_layer)

# ✅ Save the project (optional)
project_path = r"C:\path\to\save\project.qgz"
QgsProject
