import requests
import boto3
import time
import os
import win32com.client
import pandas as pd
import numpy as np
import rasterio
from rasterio.crs import CRS
import pyautogui
import logging
from glob import glob
import re

# === CONFIGURATION ===
mapbox_token = 'sk.eyJ1IjoiZ2F2aW5jaWkiLCJhIjoiY205Zjl3NHhkMGlvYzJyc2MwNm05b2c0ayJ9.OTA15_jphYcO85Cj46F4VQ'
username = 'gavincii'
PROJECT_FILE = r"D:\FLOWS\Ver2\FLOWS-Website\final\flow.prj"
UNSTEADY_FILE = r"D:\FLOWS\Ver2\FLOWS-Website\final\flow.u01"
CSV_FILE = r"D:\FLOWS\Ver2\FLOWS-Website\final\Config\january2025_predictions.csv"
INPUT_FOLDER = r"D:\FLOWS\Ver2\FLOWS-Website\hecras\Plan9" #folder ng mga exported na tif galing hec-ras
OUTPUT_FOLDER = r"D:\FLOWS\Ver2\FLOWS-Website\hecras\converted_8bit" #gagawin niya nalang to pag wala pa
ICON_FOLDER = r"D:\FLOWS\Ver2\FLOWS-Website\hecras\pyautogui"
BASE_ELEVATION = 125
TARGET_CRS = 'EPSG:32651'
batch_size = 6
delay_between_batches = 60  # in seconds

# === LOGGING ===
logging.basicConfig(
    filename='hecras_pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# === FUNCTION: Update Unsteady Flow File ===
def update_unsteady_flow(file_path, df):
    with open(file_path, "r") as f:
        lines = f.readlines()

    stage_count = len(df)
    rounded_stages = [int(round(val)) for val in df["Water_Level"]]
    first_line = "     ".join(str(val) for val in rounded_stages[:10]) + "\n"
    second_line = "     ".join(str(val) for val in rounded_stages[10:]) + "\n"
    first_line = "     " + first_line
    second_line = "     " + second_line

    for i, line in enumerate(lines):
        if line.strip().startswith("Stage Hydrograph="):
            lines[i] = f"Stage Hydrograph= {stage_count} \n"
            lines[i + 1] = first_line
            lines[i + 2] = second_line
            break
    else:
        raise ValueError("Stage Hydrograph section not found!")

    with open(file_path, "w") as f:
        f.writelines(lines)

    logging.info("✅ Unsteady flow file updated.")
    logging.info("Formatted values:\n" + first_line + second_line)

# === FUNCTION: Run HEC-RAS Simulation ===
def run_hec_ras():
    RAS = win32com.client.Dispatch("RAS67.HECRASController")
    RAS.Project_Open(PROJECT_FILE)
    if RAS.Compute_CurrentPlan():
        logging.info("✅ HEC-RAS simulation completed.")
    else:
        logging.error("❌ Simulation failed.")

# === FUNCTION: Use PyAutoGUI to Create Maps ===
def create_maps_with_pyautogui():
    hec = win32com.client.Dispatch("RAS67.HECRASController")
    hec.Project_Open(PROJECT_FILE)
    hec.ShowRas()
    time.sleep(2)

    rasmapper_but = pyautogui.locateCenterOnScreen(os.path.join(ICON_FOLDER, "rasmapper.png"), confidence=0.7)
    pyautogui.click(rasmapper_but)
    time.sleep(2)

    results_but = pyautogui.locateOnScreen(os.path.join(ICON_FOLDER, "results.png"), confidence=0.7)
    pyautogui.rightClick(results_but)
    time.sleep(2)

    createmultimaps_but = pyautogui.locateOnScreen(os.path.join(ICON_FOLDER, "createmultimaps.png"), confidence=0.7)
    pyautogui.click(createmultimaps_but)
    time.sleep(2)

    min_but = pyautogui.locateOnScreen(os.path.join(ICON_FOLDER, "min.png"), confidence=0.7)
    pyautogui.moveTo(min_but)
    pyautogui.move(0, 10)
    pyautogui.drag(0, 160, 4, button='left')

    screen_width, screen_height = pyautogui.size()
    right_half_region = (screen_width // 2, 0, screen_width // 2, screen_height)
    depth_but = pyautogui.locateOnScreen(os.path.join(ICON_FOLDER, "depth.png"), confidence=0.7, region=right_half_region)
    pyautogui.click(depth_but)

    ok_but = pyautogui.locateOnScreen(os.path.join(ICON_FOLDER, "ok.png"), confidence=0.7)
    pyautogui.click(ok_but)
    time.sleep(10)
    logging.info("✅ Flood maps generated via RAS Mapper.")

# === FUNCTION: Convert GeoTIFFs to 8-bit ===
def convert_to_8bit_rasterio(input_path, output_path, scale_min=None, scale_max=None):
    with rasterio.open(input_path) as src:
        profile = src.profile.copy()

        if not src.crs or src.crs.to_string() != TARGET_CRS:
            profile.update({'crs': CRS.from_string(TARGET_CRS)})

        data = src.read(1).astype(np.float32)
        if scale_min is None or scale_max is None:
            scale_min = np.nanmin(data)
            scale_max = np.nanmax(data)

        scaled = ((data - scale_min) / (scale_max - scale_min)) * 255
        scaled = np.clip(scaled, 0, 255).astype(np.uint8)
        scaled[scaled < 10] = 0

        profile.update({
            'dtype': 'uint8',
            'count': 1,
            'nodata': 0,
            'photometric': 'palette'
        })

        colormap = {}
        for value in range(10, 25):
            colormap[value] = (244, 180, 0)
        for value in range(25, 51):
            colormap[value] = (251, 140, 0)
        for value in range(51, 256):
            colormap[value] = (213, 0, 0)

    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(scaled, 1)
        dst.write_colormap(1, colormap)
        dst.update_tags(scale_min=str(scale_min), scale_max=str(scale_max))

    print(f"✅ Converted: {os.path.basename(input_path)} → {os.path.basename(output_path)}")

# === FUNCTION: Upload Single TIFF to Mapbox ===
def upload_single_tif(tif_path, batch_index, tif_index):
    # 1. Request temporary S3 credentials
    cred_res = requests.post(
        f'https://api.mapbox.com/uploads/v1/{username}/credentials?access_token={mapbox_token}'
    )
    credentials = cred_res.json()

    # 2. Upload TIFF to S3
    s3 = boto3.client(
        's3',
        aws_access_key_id=credentials['accessKeyId'],
        aws_secret_access_key=credentials['secretAccessKey'],
        aws_session_token=credentials['sessionToken'],
    )

    bucket = credentials['bucket']
    key = credentials['key']
    with open(tif_path, 'rb') as f:
        s3.upload_fileobj(f, bucket, key)
    print(f"📤 Uploaded {os.path.basename(tif_path)} to S3")

    # 3. Trigger tileset upload
    tileset_id = f'{username}.flood-map-{batch_index}-{tif_index}'
    upload_payload = {
        "url": credentials["url"],
        "tileset": tileset_id,
        "name": f"Flood Map {batch_index}-{tif_index}"
    }
    upload_res = requests.post(
        f'https://api.mapbox.com/uploads/v1/{username}?access_token={mapbox_token}',
        json=upload_payload
    )
    upload_job = upload_res.json()
    print(f"🚀 Upload started for {tileset_id} (Upload ID: {upload_job['id']})")

# === FUNCTION: Extract Number from Filename ===
def extract_number(filename):
    match = re.search(r"(\d+)", filename)
    return int(match.group(1)) if match else -1

# === FUNCTION: Upload TIFFs in Batches ===
def upload_tifs_in_batches():
    tif_files = sorted(glob(os.path.join(OUTPUT_FOLDER, "*.tif")), key=lambda x: extract_number(os.path.basename(x)))
    total = len(tif_files)
    batches = [tif_files[i:i + batch_size] for i in range(0, total, batch_size)]

    for batch_index, batch in enumerate(batches):
        print(f"\n=== 🗂️ Starting batch {batch_index + 1}/{len(batches)} ===")
        for tif_index, tif_path in enumerate(batch):
            upload_single_tif(tif_path, batch_index, tif_index)
            time.sleep(5)

        # Wait before starting next batch
        if batch_index < len(batches) - 1:
            print(f"⏳ Waiting for {delay_between_batches} seconds before starting the next batch...")
            time.sleep(delay_between_batches)

# === MAIN EXECUTION ===
try:
    # Step 1: Update Unsteady Flow
    df = pd.read_csv(CSV_FILE)
    water_levels = df.iloc[0, 1:].values + BASE_ELEVATION
    df = pd.DataFrame({"Water_Level": water_levels})
    update_unsteady_flow(UNSTEADY_FILE, df)

    # Step 2: Run HEC-RAS Simulation
    run_hec_ras()
    time.sleep(60)
    # Step 3: Use PyAutoGUI to Export Depth Maps
    create_maps_with_pyautogui()

    # Step 4: Convert GeoTIFFs to 8-bit
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    tif_files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(".tif")]
    for idx, tif_file in enumerate(tif_files):
        input_path = os.path.join(INPUT_FOLDER, tif_file)
        output_path = os.path.join(OUTPUT_FOLDER, f"tif_{idx}.tif")
        convert_to_8bit_rasterio(input_path, output_path)

    # Step 5: Upload Converted TIFFs to Mapbox
    upload_tifs_in_batches()

except Exception as e:
    logging.error(f"❌ ERROR: {e}")
    print("❌ An error occurred! Check the log file.")
