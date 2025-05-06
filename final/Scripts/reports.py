import datetime
import geopandas as gpd
import rasterio
from rasterstats import zonal_stats
import pandas as pd
import os # To handle multiple files

# --- Configuration ---

# --- INPUTS ---
# Path to the vector file with barangay boundaries
# Make sure this file contains *only* Camaligan barangays or has a column to filter by.
barangay_vector_path = "assets/map/Camaligan_Barangay_Boundary" # Or .shp, etc.
datetime_csv_path = "assets/flood_predictions.csv"
# Directory containing your GeoTIFF flood maps
geotiff_directory = "assets/original"
# List of specific GeoTIFF filenames to process (or find them automatically)
geotiff_files = [
    "tif_rgb_0.tif",
    "tif_rgb_1.tif",
    "tif_rgb_2.tif",
    "tif_rgb_3.tif",
    "tif_rgb_4.tif",
    "tif_rgb_5.tif",
    # Add all relevant GeoTIFF filenames here
]
# Column name in your vector file that holds the Barangay names
barangay_name_column = 'name_bgy' # <--- IMPORTANT: Change this to match your file's column name!

# --- OUTPUT ---
output_report_csv = "assets/reports/barangay_flood_report.csv"

# --- ANALYSIS SETTINGS ---
stats_to_calculate = ['max'] # Calculate maximum value within each zone
# Rename the statistic column in the output for clarity
stats_rename = {'max': 'Max Flood Depth (m)'} # Assuming GeoTIFF units are meters

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

# --- Function to load and format Date/Time from CSV ---
def load_and_format_datetime_csv(csv_path):
    """Reads the CSV and returns a list of formatted datetime strings."""
    try:
        print(f"Loading datetime data from: {csv_path}")
        # Keep dtype_spec, it's still good practice
        dtype_spec = {'Year': int, 'Month': int, 'Day': int, 'Hour': int}
        # Use low_memory=False potentially if CSV is large and has mixed types causing issues
        df = pd.read_csv(csv_path, dtype=dtype_spec, low_memory=False) # Added low_memory

        formatted_strings = []
        print("Formatting datetime strings...")
        for index, row in df.iterrows():
            try:
                # --- FIX: Explicitly cast to int ---
                # Cast each value needed by datetime.datetime to an integer
                year_int = int(row['Year'])
                month_int = int(row['Month'])
                day_int = int(row['Day'])
                hour_int = int(row['Hour'])
                # ------------------------------------

                # Create datetime object using the integer variables
                dt_obj = datetime.datetime(year=year_int, month=month_int, day=day_int, hour=hour_int)

                # Format the string (adjust format as needed)
                hour12 = dt_obj.hour % 12
                if hour12 == 0: hour12 = 12 # Handle midnight/noon
                ampm = dt_obj.strftime('%p')
                formatted = f"{dt_obj.strftime('%B %d, %Y')} {hour12}:00 {ampm}" # Assuming :00 minutes
                formatted_strings.append(formatted)

            except (ValueError, TypeError) as e: # Catch potential errors during int() conversion or datetime creation
                print(f"Warning: Could not process row {index + 1} in {os.path.basename(csv_path)}. Error: {e}. Value(Y,M,D,H):({row.get('Year')},{row.get('Month')},{row.get('Day')},{row.get('Hour')}). Skipping row.")
                formatted_strings.append(f"Error_Row_{index+1}") # Add placeholder

        print(f"Generated {len(formatted_strings)} datetime strings.")
        return formatted_strings
    except FileNotFoundError:
         print(f"Error: Datetime CSV file not found at {csv_path}")
         return None
    except Exception as e:
        print(f"Error reading or processing datetime CSV {csv_path}: {e}")
        return None

# --- Function to perform zonal stats for one raster ---
def get_flood_stats(vector_path, raster_path, stats_list, nodata_val=None):
    """Calculates zonal stats for a given vector and raster file."""
    try:
        with rasterio.open(raster_path) as src:
            affine = src.transform
            array = src.read(1) # Read the first band
            # Use the GeoDataFrame directly if CRS matches, otherwise path is safer
            stats = zonal_stats(
                vector_path, # Use path to handle potential CRS differences initially
                # array, # Using array directly is faster if CRS matches
                # affine=affine,
                raster=raster_path, # Let rasterstats handle CRS check/reprojection if needed
                stats=stats_list,
                nodata=nodata_val if nodata_val is not None else src.nodata, # Use nodata value from raster
                all_touched=True # Include pixels touched by the boundary
            )
        # Extract the primary stat (e.g., 'max')
        return [s.get(stats_list[0]) if s else None for s in stats]
    except Exception as e:
        print(f"Error processing {raster_path}: {e}")
        # Return None for all features if this raster fails
        try:
            gdf_tmp = gpd.read_file(vector_path)
            return [None] * len(gdf_tmp)
        except:
            return [] # Or handle error differently

# --- Main Script ---
date_time_headers = load_and_format_datetime_csv(datetime_csv_path)
if date_time_headers is None:
    print("Exiting due to error loading datetime CSV.")
    exit()

# ** Crucial Check **: Ensure number of headers matches number of GeoTIFFs
if len(date_time_headers) != len(geotiff_files):
    print(f"Error: Mismatch between number of datetime entries ({len(date_time_headers)}) and GeoTIFF files ({len(geotiff_files)}).")
    print("Please ensure the datetime CSV and the geotiff_files list correspond correctly.")
    exit()


# 2. Load Barangay Data
try:
    print(f"Loading barangay boundaries from: {barangay_vector_path}")
    gdf_barangays = gpd.read_file(barangay_vector_path)
    if barangay_name_column not in gdf_barangays.columns:
        raise ValueError(f"Column '{barangay_name_column}' not found in {barangay_vector_path}. Available columns: {gdf_barangays.columns.tolist()}")
    print(f"Loaded {len(gdf_barangays)} barangay features.")
except Exception as e:
    print(f"Error loading barangay data: {e}")
    exit()

# Create the base report DataFrame
report_df = gdf_barangays[[barangay_name_column]].copy()
report_df.rename(columns={barangay_name_column: 'Barangay'}, inplace=True)

# 3. Process each GeoTIFF using an index
print("\nProcessing GeoTIFF files and assigning datetime headers...")
for i, filename in enumerate(geotiff_files):
    raster_path = os.path.join(geotiff_directory, filename)
    if not os.path.exists(raster_path):
        print(f"Warning: File not found, skipping: {raster_path}")
        # Assign 'File Not Found' to the corresponding column
        report_df[date_time_headers[i]] = 'File Not Found'
        continue

    # Use the formatted date/time string from the list as the column header
    col_name = date_time_headers[i]
    print(f"  Calculating stats for: {filename} -> Column: '{col_name}'")

    # Calculate stats for the current raster
    flood_levels = get_flood_stats(gdf_barangays, raster_path, stats_to_calculate) # Pass gdf for CRS check

    # Add results to the report DataFrame with the datetime header
    if len(flood_levels) == len(report_df):
         # Add the statistic description to the value? Or keep header clean? Keep header clean for now.
         # Maybe add units to header later?
        report_df[col_name] = flood_levels
    else:
        print(f"Warning: Mismatch in feature count for {filename}. Assigning 'Error'.")
        report_df[col_name] = 'Error'
        



# 4. Clean up and Export Report
print("\nFinalizing report...")
report_df.fillna(0, inplace=True) # Replace None with 'N/A' (no overlap or NoData)

# Optional: Round numeric values (be careful with 'N/A' or 'Error')
for col in report_df.columns:
    if col != 'Barangay':
        report_df[col] = pd.to_numeric(report_df[col], errors='ignore') # Ignore non-numeric
        # Check dtype before rounding
        if pd.api.types.is_numeric_dtype(report_df[col]):
            report_df[col] = report_df[col].round(2) # Example: 2 decimal places
        #report_df[col] = report_df[col].apply(classify_flood_level) # Classify flood levels

count = 0
for hour in report_df.columns[1:]:
    # Sort by flood value (descending), get top 5
    top5 = report_df[['Barangay', hour]].sort_values(by=hour, ascending=False).head(5)
    
    
    filename = f"assets/reports/top5_{count}.csv"
    count += 1
    
    # Save to CSV
    top5.to_csv(filename, index=False)

for col in report_df.columns:
    if col != 'Barangay':
        report_df[col] = report_df[col].apply(classify_flood_level) # Classify flood levels

# Add units description somewhere? Maybe as a note or modify headers slightly?
# Example: Add units to column names AFTER processing
# report_df.columns = ['Barangay'] # + [f'{col} ({stats_rename})' for col in report_df.columns if col != 'Barangay']


# Export to CSV
try:
    report_df.to_csv(output_report_csv, index=False)
    print(f"\nReport successfully saved to: {output_report_csv}")
except Exception as e:
    print(f"\nError saving report to CSV: {e}")

# Optional: Print to console
# print("\n--- Flood Report Preview ---")
# # Increase display width for potentially long headers
# with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 1000):
#     print(report_df)
# print("--- End Report ---")


# # 1. Load Barangay Data
# try:
#     print(f"Loading barangay boundaries from: {barangay_vector_path}")
#     gdf_barangays = gpd.read_file(barangay_vector_path)
#     # Ensure the name column exists
#     if barangay_name_column not in gdf_barangays.columns:
#         raise ValueError(f"Column '{barangay_name_column}' not found in {barangay_vector_path}. Available columns: {gdf_barangays.columns.tolist()}")
#     print(f"Loaded {len(gdf_barangays)} barangay features.")
#     # Optional: Filter for specific municipality if needed
#     # gdf_barangays = gdf_barangays[gdf_barangays['MUNICIPALITY_COLUMN'] == 'Camaligan'] # Adjust filter logic
# except Exception as e:
#     print(f"Error loading barangay data: {e}")
#     exit()

# # Create a DataFrame for the report, starting with barangay names
# report_df = gdf_barangays[[barangay_name_column]].copy()
# report_df.rename(columns={barangay_name_column: 'Barangay'}, inplace=True)

# # 2. Process each GeoTIFF
# print("\nProcessing GeoTIFF files...")
# for filename in geotiff_files:
#     raster_path = os.path.join(geotiff_directory, filename)
#     if not os.path.exists(raster_path):
#         print(f"Warning: File not found, skipping: {raster_path}")
#         continue

#     print(f"  Calculating stats for: {filename}...")
#     # Calculate stats for the current raster
#     flood_levels = get_flood_stats(gdf_barangays, raster_path, stats_to_calculate) # Pass gdf for CRS matching

#     # Define column name for this specific raster's results
#     # Extracts base name like 'tif_rgb_0' and uses the desired stat name
#     base_name = os.path.splitext(filename)[0]
#     col_name = f"{stats_rename[stats_to_calculate[0]]} ({base_name})"

#     # Add results to the report DataFrame
#     if len(flood_levels) == len(report_df):
#         report_df[col_name] = flood_levels
#     else:
#         print(f"Warning: Mismatch in feature count for {filename}. Skipping results.")
#         report_df[col_name] = 'Error' # Indicate error


# # 3. Clean up and Export Report
# print("\nFinalizing report...")
# # Replace None/NaN values (e.g., if a barangay didn't overlap the raster)
# report_df.fillna(0, inplace=True) # Or use 0 if appropriate

# # Optional: Round numeric values (be careful with 'N/A' or 'Error')
# for col in report_df.columns:
#     if col != 'Barangay':
#          report_df[col] = pd.to_numeric(report_df[col], errors='ignore') # Ignore non-numeric
#          # Check dtype before rounding
#          if pd.api.types.is_numeric_dtype(report_df[col]):
#              report_df[col] = report_df[col].round(2) # Example: 2 decimal places

# # Export to CSV
# try:
#     report_df.to_csv(output_report_csv, index=False)
#     print(f"\nReport successfully saved to: {output_report_csv}")
# except Exception as e:
#     print(f"\nError saving report to CSV: {e}")

# # Optional: Print to console
# print("\n--- Flood Report Preview ---")
# print(report_df.to_string(index=False))
# print("--- End Report ---")