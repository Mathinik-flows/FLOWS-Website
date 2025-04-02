import win32com.client
import pandas as pd
import time
import logging
import subprocess

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
    project_file = r"C:\Yna\Thesis\FLOWS\hecras\flow.prj"
    unsteady_file = r"C:\Yna\Thesis\FLOWS\hecras\flow.u02"
    csv_file = r"C:\Yna\Thesis\FLOWS\hecras\waterlevels.csv"

    # Load water level data from CSV
    df = pd.read_csv(csv_file)


    hec.Project_Open(project_file)
    hec.ShowRas()  # Show HEC-RAS UI (optional for debugging)
    hec.CurrentPlanFile()  # Ensure the correct plan is loaded
    logging.info(f"Project '{project_file}' opened.")

    # Modify the Unsteady Flow File (.u01) with new stage values
    def update_unsteady_flow(file_path, df):
        with open(file_path, "r") as f:
            lines = f.readlines()

        # Find the section where stage hydrograph data starts
        for i, line in enumerate(lines):
            if "Stage Hydrograph=" in line:
                start_index = i + 1  # Values start on the next line
                break
        else:
            raise ValueError("Stage Hydrograph section not found!")


        # Replace the stage values while keeping the count
        stage_count = len(df)
        stage_values = "     ".join(f"{stage:.3g}" for stage in df["Water_Level"])

        # Insert the new line after the hydrograph values
        # Update the Stage Hydrograph section
        lines[start_index - 1] = f"Stage Hydrograph= {stage_count} \n"
        lines[start_index] = "    " + f"{stage_values}"+ "\n"
       

        # Write back the modified file
        with open(file_path, "w") as f:
            f.writelines(lines)


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
        # RAS.ShowRas()  # Show GUI to verify it loads correctly
        # RAS.UnsteadyFlow_UnsteadyFlowFile_Open(UnsteadyFlowFile)
        # print("🚀 Running HEC-RAS Simulation...")

        # # Fix: Ensure correct argument format
        # success = RAS.Compute_CurrentPlan(None, True)  # Use (None, True) instead of (0,1)

        if success == 0:
            print("❌ Simulation failed!")
        else:
            print("✅ Simulation completed.")

    # Execute the workflow
    update_unsteady_flow(unsteady_file, df)
    run_hec_ras()
    
    # # Execute the workflow
    # update_unsteady_flow(unsteady_file, df)
    # run_hec_ras()
    # # Modify Boundary Conditions (e.g., update stage hydrograph file)
    # boundary_file = r"C:\Yna\Thesis\FLOWS\hecras\flow.u01"
    # new_stage_values = [1.5, 1.55, 1.6, 1.65, 1.7, 1.75, 1.8, 1.4]  # Example from ML model (7 values)

    # # Open and read the boundary condition file
    # with open(boundary_file, "r") as file:
    #     data = file.readlines()
    
    # logging.info(f"Boundary conditions file '{boundary_file}' read successfully.")

    # # Find the "Stage Hydrograph=" line and update the stage values
    # updated = False
    # for i, line in enumerate(data):
    #     if line.strip().startswith("Stage Hydrograph"):
    #         # This is the line containing the Stage Hydrograph value (e.g., "Stage Hydrograph= 7")
    #         stage_values_line_index = i + 1  # The next line holds the actual stage values
    #         # Replace the stage values with the new ones (ensure we match the number of values)
    #         data[stage_values_line_index] = "     " + "     ".join([f"{value:.2f}" for value in new_stage_values]) + "\n"
    #         updated = True
    #         logging.info(f"Updated stage hydrograph with values: {new_stage_values}")
    #         break
    
    # if updated:
    #     # Save the updated boundary condition file
    #     with open(boundary_file, "w") as file:
    #         file.writelines(data)
    #     logging.info(f"Updated boundary conditions in '{boundary_file}'.")
    # else:
    #     logging.error(f"Failed to find 'Stage Hydrograph' line in '{boundary_file}'.")
    #     raise ValueError("Stage Hydrograph line not found.")
    
    # # Run Simulation
    # hec.Compute_CurrentPlan()  # Runs the unsteady simulation
    # logging.info("HEC-RAS simulation started.")
    # time.sleep(10)  # Wait for completion (adjust based on run time)
    # logging.info("HEC-RAS simulation completed.")
    
    # # Export GeoTIFF
    # ras_mapper = r"C:\Program Files (x86)\HEC\HEC-RAS\6.7 Beta\RasMapper.exe"   # Adjust path if needed
    # tiff_output = r"C:\Yna\Thesis\FLOWS\hecras\TIFFs\output.tif"
    # command = f'"{ras_mapper}" -export "{project_path}" "Depth (Max)" "{tiff_output}"'
    
    # subprocess.run(command, shell=True)
    # logging.info(f"GeoTIFF exported to '{tiff_output}'.")
    
    # # Close HEC-RAS
    # hec.QuitRas()
    # logging.info("HEC-RAS closed successfully.")
    
except Exception as e:
    logging.error(f"Error: {e}")
    hec.QuitRas()
    logging.info("HEC-RAS closed successfully.")
