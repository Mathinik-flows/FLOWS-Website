from flask import Flask, request, jsonify
import rasterio
from rasterio.crs import CRS
from pyproj import Transformer


from flask_cors import CORS


app = Flask(__name__)
CORS(app)

def classify_flood_level(value):
    if value < 0.1:
        return "No Flood"
    elif 0.1 <= value <= 0.24:
        return "Low Flood Level"
    elif 0.25 <= value <= 0.5:
        return "Moderate Flood Level"
    elif value > 0.5:
        return "High Flood Level"
    else:
        return "No Flood"



@app.route("/get-band1", methods=["POST"])
def get_band1_value():

    try: 
        # Load raster once at startup
        tif_path = "hecras/Plan9/Depth (03APR2025 00 00 00).Terrain.SmootherDEM.tif"
        dataset = rasterio.open(tif_path)

        data = request.get_json()
        lng = data["lng"]
        lat = data["lat"]
        #print(f"Received coordinates: lng={lng}, lat={lat}")
        
        with rasterio.open(tif_path) as dataset:
            # Transform coordinate to raster CRS if needed
            if dataset.crs != CRS.from_epsg(4326):
                transformer = Transformer.from_crs("EPSG:4326", dataset.crs, always_xy=True)
                x, y = transformer.transform(lng, lat)
                #print(f"Transformed coordinates: x={x}, y={y}")
            else:
                x, y = lng, lat
                #print(f"No Transformed coordinates: x={x}, y={y}")

            # Convert map coordinates to pixel row/col
            row, col = dataset.index(x, y)
            #print(f"Received coordinates: lng={row}, lat={col}")

            # Read Band 1 value at the given row/col
            band1 = dataset.read(1)  # read band 1 (2D array)
            value = band1[row, col]
            flood_level = classify_flood_level(value-100)

            #print(f"Value at ({lng}, {lat}):", value)
        
        return jsonify({
            "value": float(value),  # ✅ Convert to native float
            "flood_level": flood_level,
            "row": row,
            "col": col,
            "message": "Band1 value retrieved successfully"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


if __name__ == "__main__":
    app.run(debug=True)

