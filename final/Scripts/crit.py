import geopandas as gpd
import rasterio
import pandas as pd
import os
from datetime import datetime
import numpy as np # For handling NaN potentially

# --- Configuration ---

# --- INPUTS ---
# Path to the GeoJSON file with critical facility points
facilities_geojson_path = "assets/map/Camaligan_Crit_Facilities.geojson"
# Column name in your GeoJSON 'properties' that holds the facility names
facility_name_column = 'name' # <--- IMPORTANT: Change this to match your file's property name!
amenity_name_column = 'amenity' # <--- IMPORTANT: Change this to match your file's property name!
# Directory containing your GeoTIFF flood maps
geotiff_directory = "assets/original"
# List GeoTIFF filenames IN THE SAME ORDER as the rows in datetime_csv_path
geotiff_files = [
    "tif_rgb_0.tif",
    "tif_rgb_1.tif",
    "tif_rgb_2.tif",
    "tif_rgb_3.tif",
    "tif_rgb_4.tif",
    "tif_rgb_5.tif",
    # Add all relevant GeoTIFF filenames IN ORDER
]
# Path to the CSV containing Year, Month, Day, Hour data
datetime_csv_path = "assets/flood_predictions.csv"

# --- OUTPUT ---
output_report_csv = "assets/reports/critical_facilities_flood_report.csv"

# --- ANALYSIS SETTINGS ---
# Base name for statistic column - header will be the date/time
stats_output_name = 'Flood Depth (m)' # Assuming GeoTIFF units are meters


def classify_flood_level(value):
    """Classifies the flood level based on raster value."""
    # Check for potential NoData values if your raster uses them
    # nodata_value = -9999 # Example NoData value
    # if value == nodata_value:
    #     return "No Data"
    if value <= 0:
        return "None"
    elif 0 < value <= 0.24:
        return "Low"
    elif 0.25 <= value < 0.5:
        return "Moderate"
    elif value >= 0.5:
        return "High"
    else:
        # This case might indicate an issue or NoData if not handled explicitly
        return "Not in Scope"
    
# --- Function to load and format Date/Time from CSV (Same as before) ---
def load_and_format_datetime_csv(csv_path):
    """Reads the CSV and returns a list of formatted datetime strings."""
    try:
        print(f"Loading datetime data from: {csv_path}")
        dtype_spec = {'Year': int, 'Month': int, 'Day': int, 'Hour': int}
        df = pd.read_csv(csv_path, dtype=dtype_spec, low_memory=False)
        formatted_strings = []
        print("Formatting datetime strings...")
        for index, row in df.iterrows():
            try:
                year_int = int(row['Year'])
                month_int = int(row['Month'])
                day_int = int(row['Day'])
                hour_int = int(row['Hour'])
                dt_obj = datetime(year=year_int, month=month_int, day=day_int, hour=hour_int) # Use datetime.datetime if needed based on import
                hour12 = dt_obj.hour % 12
                if hour12 == 0: hour12 = 12
                ampm = dt_obj.strftime('%p')
                formatted = f"{dt_obj.strftime('%B %d, %Y')} {hour12}:00 {ampm}"
                formatted_strings.append(formatted)
            except (ValueError, TypeError) as e:
                print(f"Warning: Could not process row {index + 1} in {os.path.basename(csv_path)}. Error: {e}. Skipping row.")
                formatted_strings.append(f"Error_Row_{index+1}")
        print(f"Generated {len(formatted_strings)} datetime strings.")
        return formatted_strings
    except FileNotFoundError:
        print(f"Error: Datetime CSV file not found at {csv_path}")
        return None
    except Exception as e:
        print(f"Error reading or processing datetime CSV {csv_path}: {e}")
        return None

# --- Main Script ---

# 1. Load Date/Time strings first
date_time_headers = load_and_format_datetime_csv(datetime_csv_path)
if date_time_headers is None:
    print("Exiting due to error loading datetime CSV.")
    exit()

# ** Crucial Check **: Ensure number of headers matches number of GeoTIFFs
if len(date_time_headers) != len(geotiff_files):
    print(f"Error: Mismatch between number of datetime entries ({len(date_time_headers)}) and GeoTIFF files ({len(geotiff_files)}).")
    print("Please ensure the datetime CSV and the geotiff_files list correspond correctly.")
    exit()

# 2. Load Critical Facilities Data
try:
    print(f"Loading critical facilities from: {facilities_geojson_path}")
    gdf_facilities = gpd.read_file(facilities_geojson_path)
    # Ensure the name column exists
    if facility_name_column not in gdf_facilities.columns:
        raise ValueError(f"Column '{facility_name_column}' not found in {facilities_geojson_path}. Available properties: {list(gdf_facilities.columns)}")
        
    print(f"Loaded {len(gdf_facilities)} facility features.")
    print(f'Available properties: {list(gdf_facilities.columns)}')
    # Ensure geometry is points
    if not gdf_facilities.geom_type.isin(['Point']).all():
         print("Warning: GeoJSON contains non-point geometries. Sampling will only work for points.")
         # Optionally filter: gdf_facilities = gdf_facilities[gdf_facilities.geom_type == 'Point']

except Exception as e:
    print(f"Error loading facilities GeoJSON data: {e}")
    exit()

# Create the base report DataFrame with facility names
report_df = gdf_facilities[[facility_name_column]].copy()
report_df.rename(columns={facility_name_column: 'Critical Facility'}, inplace=True)
# Optional: Add other attributes from the GeoJSON to the report
report_df['Amenity'] = gdf_facilities[[amenity_name_column]].copy()

# 3. Process each GeoTIFF using an index
print("\nProcessing GeoTIFF files for point sampling...")
for i, filename in enumerate(geotiff_files):
    raster_path = os.path.join(geotiff_directory, filename)
    if not os.path.exists(raster_path):
        print(f"Warning: File not found, assigning 'File Not Found': {raster_path}")
        report_df[date_time_headers[i]] = 'File Not Found'
        continue

    # Use the formatted date/time string from the list as the column header
    col_name = date_time_headers[i]
    print(f"  Sampling raster: {filename} -> Column: '{col_name}'")

    try:
        with rasterio.open(raster_path) as src:
            raster_crs = "EPSG:32651"
            nodata_val = src.nodata # Get the raster's NoData value

            # Ensure facilities are in the same CRS as the raster
            gdf_facilities_reprojected = gdf_facilities
            if gdf_facilities.crs != raster_crs:
                print(f"    Reprojecting points from {gdf_facilities.crs} to {raster_crs}...")
                gdf_facilities_reprojected = gdf_facilities.to_crs(raster_crs)

            # Extract coordinates in the raster's CRS
            coords = [(p.x, p.y) for p in gdf_facilities_reprojected.geometry]

            # Sample the raster at the facility coordinates
            # src.sample returns a generator yielding lists (one value per band)
            sampled_values_generator = src.sample(coords)

            # Extract value from the first band, handle NoData
            flood_levels = []
            for val_list in sampled_values_generator:
                val = val_list[0] # Get value from first band
                if nodata_val is not None and val == nodata_val:
                    flood_levels.append(None) # Use None if it's NoData
                else:
                    flood_levels.append(val)

            # Add results to the report DataFrame
            if len(flood_levels) == len(report_df):
                report_df[col_name] = flood_levels
                
            else:
                print(f"Warning: Mismatch in feature count during sampling for {filename}. Assigning 'Error'.")
                report_df[col_name] = 'Error'

    except Exception as e:
        print(f"Error sampling raster {filename}: {e}")
        report_df[col_name] = 'Sampling Error'


# 4. Clean up and Export Report
print("\nFinalizing report...")
# Replace None values (NoData or errors) with 'N/A' or 0.0
# Using 0.0 might be better if 0 represents no flood depth
report_df.fillna(0.0, inplace=True) # Or use 'N/A'

# Optional: Round numeric values (be careful with 'N/A' or 'Error')
for col in report_df.columns:
    if col != 'Critical Facility' and col != 'Amenity':
        report_df[col] = pd.to_numeric(report_df[col], errors='ignore') # Ignore non-numeric
        # Check dtype before rounding
        if pd.api.types.is_numeric_dtype(report_df[col]):
            report_df[col] = report_df[col].round(2) # Example: 2 decimal places
        report_df[col] = report_df[col].apply(classify_flood_level) # Classify flood levels

# Add units description to column headers
#report_df.columns = ['Critical Facility'] + [f'{col} ({stats_output_name})' for col in report_df.columns if col != 'Critical Facility']

# Export to CSV
try:
    report_df.to_csv(output_report_csv, index=False)
    print(f"\nReport successfully saved to: {output_report_csv}")
except Exception as e:
    print(f"\nError saving report to CSV: {e}")

# Optional: Print to console
print("\n--- Critical Facilities Flood Report Preview ---")
with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 1000):
    print(report_df)
print("--- End Report ---")