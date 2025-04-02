import win32com.client
import time
import logging
import os

# Initialize HEC-RAS Controller
hec = win32com.client.Dispatch("RAS67.HECRASController")  # Adjust for your HEC-RAS version

# Open the HEC-RAS project
project_path = r"C:\Yna\Thesis\FLOWS\hecras\flow.prj"

hec.Project_Open(project_path)
# Open the unsteady flow file
hec.ShowRas()  # Show HEC-RAS UI (optional for debugging)
hec.CurrentPlanFile()  # Ensure the correct plan is loaded
# Get the current unsteady flow file
unsteady_flow_file = hec.CurrentUnSteadyFile()
print(f"Unsteady Flow File: {unsteady_flow_file}")

# Read .u01 file and modify stage hydrograph values
with open(unsteady_flow_file, "r") as file:
    data = file.readlines()

# Example: Inject new stage values from your ML model (Modify lines accordingly)
new_stage_values = [1.50, 1.55, 1.60, 1.65, 1.70, 1.75, 1.9]

# Find where hydrograph data starts and modify it
# Find the "Stage Hydrograph=" line and update the stage values
updated = False
for i, line in enumerate(data):
    if line.strip().startswith("Stage Hydrograph"):
        # This is the line containing the Stage Hydrograph value (e.g., "Stage Hydrograph= 7")
        stage_values_line_index = i + 1  # The next line holds the actual stage values
        # Replace the stage values with the new ones (ensure we match the number of values)
        data[stage_values_line_index] = "     " + "     ".join([f"{value:.2f}" for value in new_stage_values]) + "\n"
        updated = True

        print(f"Updated stage hydrograph with values: {new_stage_values}")
        break

if updated:
    # Save the updated boundary condition file
    with open(unsteady_flow_file, "w") as file:
        file.writelines(data)
    logging.info(f"Updated boundary conditions in '{unsteady_flow_file}'.")
else:
    logging.error(f"Failed to find 'Stage Hydrograph' line in '{unsteady_flow_file}'.")
    raise ValueError("Stage Hydrograph line not found.")

# Save the updated .u01 file
with open(unsteady_flow_file, "w") as file:
    file.writelines(data)


print("Boundary condition updated successfully!")
print(data)

# Run Simulation
hec.Compute_CurrentPlan()  # Runs the unsteady simulation
logging.info("HEC-RAS simulation started.")
time.sleep(10)  # Wait for completion (adjust based on run time)
logging.info("HEC-RAS simulation completed.")

# Export GeoTIFF
ras_mapper = r"C:\Program Files (x86)\HEC\HEC-RAS\6.7 Beta\RasMapper.exe"  # Adjust path if needed
tiff_output = r"C:\Yna\Thesis\FLOWS\hecras\TIFFs\output.tif"
command = f'"{ras_mapper}" -export "{project_path}" "Depth (Max)" "{tiff_output}"'

subprocess.run(command, shell=True)
logging.info(f"GeoTIFF exported to '{tiff_output}'.")

# Close HEC-RAS
hec.QuitRas()
logging.info("HEC-RAS closed successfully.")