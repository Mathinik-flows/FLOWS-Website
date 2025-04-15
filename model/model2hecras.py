import win32com.client
import pandas as pd
import time
import logging
import subprocess
import h5py
import numpy as np

# Configure basic logging
logging.basicConfig(
    filename='hecras_simulation.log',  # Log to a file
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(message)s'
)

try:
    # Initialize HEC-RAS Controller
    hec = win32com.client.Dispatch("RAS67.HECRASController")  # Adjust for your HEC-RAS version
    logging.info("HEC-RAS Controller initialized.")
    
    # Open the HEC-RAS project
    project_file = r"D:\FLOWS\New folder\FLOWS-Website\hecras\flow.prj"
    unsteady_file = r"D:\FLOWS\New folder\FLOWS-Website\hecras\flow.u02"
    csv_file = r"D:\FLOWS\New folder\FLOWS-Website\model\january2025_predictions.csv"
    hdf_file = r"D:\FLOWS\New folder\FLOWS-Website\hecras\flow.p09.hdf"

    # Define output GeoTIFF file
    output_tiff = r"D:\FLOWS\New folder\FLOWS-Website\hecras\FloodMap.tif"

    # Load water level data from CSV
    df = pd.read_csv(csv_file)

    # Get the first batch (first row)
    first_batch = df.iloc[0]

    # Extract only the Hour1–Hour6 values (skip 'Batch' column)
    water_levels = first_batch[1:].values  # This gives you a 1D array of 12 values

    # Convert to a DataFrame so it's compatible with update_unsteady_flow
    df = pd.DataFrame({"Water_Level": water_levels})
    base_elevation = 125
    df["Water_Level"] = df["Water_Level"] + base_elevation
    df["Water_Level"] = df["Water_Level"].clip(lower=0)
    
    hec.Project_Open(project_file)
    hec.ShowRas()  # Show HEC-RAS UI (optional for debugging)
    hec.CurrentPlanFile()  # Ensure the correct plan is loaded
    logging.info(f"Project '{project_file}' opened.")

    # Modify the Unsteady Flow File (.u01) with new stage values
    def update_unsteady_flow(file_path, df):
        with open(file_path, "r") as f:
            lines = f.readlines()

        stage_count = len(df)
        rounded_stages = [int(round(val)) for val in df["Water_Level"]]

        # Join numbers with exactly 5 spaces in between
        first_line = "     ".join(str(val) for val in rounded_stages[:10]) + "\n"
        second_line = "     ".join(str(val) for val in rounded_stages[10:]) + "\n"

        # Add 5 leading spaces to each line to match format
        first_line = "     " + first_line
        second_line = "     " + second_line

        # Find and update Stage Hydrograph section
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

        logging.info("✅ Unsteady flow file updated successfully.")
        logging.info(f"Stage Hydrograph= {stage_count}")
        logging.info("Formatted Values:\n" + first_line + second_line)

    # Run HEC-RAS Simulation
    def run_hec_ras():
        """ Runs HEC-RAS simulation using RASController """
        RAS = win32com.client.Dispatch("RAS67.HECRASController")  # Adjust for your version
        RAS.Project_Open(project_file)
        current_plan = RAS.CurrentPlanFile()
        if not current_plan:
            raise RuntimeError("❌ Failed to load the HEC-RAS project. Check the file path.")
        # Explicitly open the unsteady flow data
        success = RAS.Compute_CurrentPlan()

        if success:
            print("✅ HEC-RAS Unsteady Flow Simulation completed successfully.")
        else:
            print("❌ Error running HEC-RAS Unsteady Flow Simulation.")

        # Close HEC-RAS
        # RAS.Project_save()
        # RAS.QuitRAS()
        # del RAS

    # Execute the workflow
    update_unsteady_flow(unsteady_file, df)
    run_hec_ras()

    
except Exception as e:
    logging.error(f"Error: {e}")
    hec.QuitRas()
    logging.info("HEC-RAS closed successfully.")
