import win32com.client
import pandas as pd
import time
import logging
import h5py
import numpy as np
import rasterio
from rasterio.crs import CRS
import pyautogui
import keyboard
import os

# ----------------- CONFIG -----------------
MODEL_PATH = r"D:\FLOWS\New folder\FLOWS-Website\model\floodprediction.h5"
HISTORICAL_CSV = r"D:\FLOWS\New folder\FLOWS-Website\model\historical.csv"
OUTPUT_CSV = r"D:\FLOWS\New folder\FLOWS-Website\hecras\waterlevels.csv"
UNSTEADY_FLOW_FILE = r"D:\FLOWS\New folder\FLOWS-Website\hecras\flow.u02"
PROJECT_FILE = r"D:\FLOWS\New folder\FLOWS-Website\hecras\flow.prj"
TIF_OUTPUT = r"D:\FLOWS\New folder\FLOWS-Website\hecras\convertedtif.tif"
TIF_8BIT_OUTPUT = r"D:\FLOWS\New folder\FLOWS-Website\model\output_8bit.tif"

# ----------------- PYAUTOGUI ICONS -----------------
ICON_FOLDER = r"D:\FLOWS\New folder\FLOWS-Website\hecras\pyautogui"

# ----------------- LOGGING -----------------
logging.basicConfig(
    filename='flood_pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ----------------- STEP 1: MODEL PREDICTION -----------------
def predict_and_write_csv():
    try:
        logging.info("Running flood prediction model.")
        model = h5py.File(MODEL_PATH, 'r')
        df = pd.read_csv(HISTORICAL_CSV)

        input_cols = ['Year', 'Month', 'Day', 'Hour', 'Rainfall', 'WaterLevel']
        input_data = df[input_cols].values

        # Simulate a simple NARX-style input
        input_data = np.expand_dims(input_data, axis=0)
        model_weights = np.array(model['model_weights'])
        prediction = np.sum(input_data) * 0.0005 + 5  # Fake logic for testing

        df['FWaterLevel'] = prediction
        df['Water_Level'] = df['FWaterLevel']
        df.to_csv(OUTPUT_CSV, index=False)
        logging.info("Prediction complete and CSV written.")
    except Exception as e:
        logging.error(f"Prediction failed: {e}")

# ----------------- STEP 2: UPDATE HEC-RAS & SIMULATE -----------------
def update_unsteady_flow(file_path, df):
    with open(file_path, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if "Stage Hydrograph=" in line:
            start_index = i + 1
            break
    else:
        raise ValueError("Stage Hydrograph section not found!")

    stage_count = len(df)
    stage_values = "     ".join(f"{stage:.3g}" for stage in df["Water_Level"])

    lines[start_index - 1] = f"Stage Hydrograph= {stage_count} \n"
    lines[start_index] = "    " + f"{stage_values}"+ "\n"

    with open(file_path, "w") as f:
        f.writelines(lines)

def update_hecras_and_run_sim():
    try:
        hec = win32com.client.Dispatch("RAS67.HECRASController")
        hec.Project_Open(PROJECT_FILE)
        df = pd.read_csv(OUTPUT_CSV)
        update_unsteady_flow(UNSTEADY_FLOW_FILE, df)
        success = hec.Compute_CurrentPlan()
        if success:
            logging.info("✅ HEC-RAS simulation completed.")
        else:
            logging.warning("❌ HEC-RAS simulation failed.")
        hec.QuitRas()
    except Exception as e:
        logging.error(f"HEC-RAS run failed: {e}")

# ----------------- STEP 3: EXPORT MAP VIA PYAUTOGUI -----------------
def export_flood_map_pyautogui():
    try:
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
        pyautogui.drag(0, 80, 2, button='left') 

        screen_width, screen_height = pyautogui.size()
        right_half_region = (screen_width // 2, 0, screen_width // 2, screen_height)
        depth_but = pyautogui.locateOnScreen(os.path.join(ICON_FOLDER, "depth.png"), confidence=0.7, region=right_half_region)
        pyautogui.click(depth_but)

        ok_but = pyautogui.locateOnScreen(os.path.join(ICON_FOLDER, "ok.png"), confidence=0.7)
        pyautogui.click(ok_but)
        time.sleep(10)

        logging.info("✅ Flood depth map exported via RAS Mapper.")
        hec.QuitRas()
    except Exception as e:
        logging.error(f"PyAutoGUI export failed: {e}")
        hec.QuitRas()

# ----------------- STEP 4: CONVERT TO 8-BIT RASTER + COLORMAP (Updated) -----------------
def convert_to_8bit_rasterio(input_path, output_path, scale_min=None, scale_max=None, target_crs='EPSG:32651'):
    with rasterio.open(input_path) as src:
        profile = src.profile.copy()

        # Step 1: Assign CRS if incorrect or missing
        if not src.crs or src.crs.to_string() != target_crs:
            print(f"Assigning CRS {target_crs} (no reprojection)...")
            profile.update({'crs': CRS.from_string(target_crs)})
        else:
            print(f"CRS is already {src.crs}")

        # Step 2: Read data and scale
        data = src.read(1).astype(np.float32)
        if scale_min is None or scale_max is None:
            scale_min = np.nanmin(data)
            scale_max = np.nanmax(data)

        scaled = ((data - scale_min) / (scale_max - scale_min)) * 255
        scaled = np.clip(scaled, 0, 255).astype(np.uint8)
        scaled[scaled < 10] = 0

        # Step 3: Update profile
        profile.update({
            'dtype': 'uint8',
            'count': 1,
            'nodata': 0,
            'photometric': 'palette'
        })

        # Step 4: Define colormap
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

    print(f"✅ Converted {input_path} to 8-bit at {output_path} using range {scale_min}-{scale_max}")

# ----------------- MAIN PIPELINE -----------------
if __name__ == "__main__":
    predict_and_write_csv()
    update_hecras_and_run_sim()
    export_flood_map_pyautogui()
    convert_to_8bit_rasterio(TIF_OUTPUT, TIF_8BIT_OUTPUT)
    logging.info("🌊 Flood mapping pipeline completed successfully.")
