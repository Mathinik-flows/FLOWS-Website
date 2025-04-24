import win32com.client
import pandas as pd
import time
import logging
import subprocess
import h5py
import numpy as np

import os

# Configure logging
logging.basicConfig(
    filename='hecras_simulation.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    # Initialize HEC-RAS Controller
    hec = win32com.client.Dispatch("RAS67.HECRASController")  # Adjust for your HEC-RAS version
    logging.info("HEC-RAS Controller initialized.")
    
    # File paths

    project_file = os.path.abspath(os.path.join(BASE_DIR, '..', 'flows.prj'))
    unsteady_file = os.path.abspath(os.path.join(BASE_DIR, '..', 'flows.u01'))
    csv_file = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'assets', 'flood_predictions.csv'))

    # Load prediction CSV
    df = pd.read_csv(csv_file)

    if 'PredictedFWaterLevel' not in df.columns:
        raise ValueError("❌ 'PredictedFWaterLevel' column not found in CSV.")

    # Get the first 6 predicted water levels
    water_levels = df['PredictedFWaterLevel'].values[:6]
    if len(water_levels) < 6:
        raise ValueError("❌ Not enough predicted water level values (need at least 6).")

    # Optional processing: scale, clip, or adjust as needed
    factor = 1.5
    adjusted_levels = np.clip(water_levels * factor, 0, None)

    # Enforce a minimum of 1.400 for HEC-RAS rendering
    adjusted_levels = np.clip(adjusted_levels, 1.700, None)

    # Create a DataFrame for logging and formatting
    df_levels = pd.DataFrame({"Water_Level": adjusted_levels})

    # Update .u01 unsteady flow file
    def update_unsteady_flow(file_path, levels_df):
        with open(file_path, "r") as f:
            lines = f.readlines()

        stage_count = len(levels_df)
        formatted_stages = ["{:.3f}".format(val) for val in levels_df["Water_Level"]]

        # Unsteady Flow Formatting
        stage_line = "   " + "   ".join(formatted_stages) + "\n"

        # Find and replace Stage Hydrograph block
        for i, line in enumerate(lines):
            if line.strip().startswith("Stage Hydrograph="):
                lines[i] = f"Stage Hydrograph= {stage_count} \n"
                lines[i + 1] = stage_line
                break
        else:
            raise ValueError("'Stage Hydrograph=' section not found in the .u01 file.")

        with open(file_path, "w") as f:
            f.writelines(lines)

        logging.info("Unsteady flow file updated successfully.")
        logging.info(f"Stage Hydrograph= {stage_count}")
        logging.info("Formatted Values:\n" + stage_line)

    # Run HEC-RAS
    def run_hec_ras():
        RAS = win32com.client.Dispatch("RAS67.HECRASController")
        RAS.Project_Open(project_file)
        current_plan = RAS.CurrentPlanFile()
        if not current_plan:
            raise RuntimeError("❌ Failed to load the HEC-RAS project. Check the file path.")
        # Explicitly open the unsteady flow data
        success = RAS.Compute_CurrentPlan()

        if success:
            print("HEC-RAS Unsteady Flow Simulation completed successfully.")
        else:
            print("Error running HEC-RAS Unsteady Flow Simulation.")

    # Execute steps
    update_unsteady_flow(unsteady_file, df_levels)
    run_hec_ras()

except Exception as e:
    logging.error(f"Error: {e}")
    hec.QuitRas()
    logging.info("HEC-RAS closed successfully.")
