import pyautogui
import keyboard
import time

import win32com.client
import pandas as pd
import time
import logging
import subprocess
import h5py
import numpy as np
from osgeo import gdal

# Configure basic logging
logging.basicConfig(
    filename='hecras_output.log',  # Log to a file
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(message)s'
)

try:
    hec = win32com.client.Dispatch("RAS67.HECRASController")  # Adjust for your HEC-RAS version
    logging.info("HEC-RAS Controller initialized.")

    project_file = r"C:\Yna\Thesis\FLOWS\hecras\flow.prj"
    logging.info("FLOW Project Loaded In.")

    hec.Project_Open(project_file)
    hec.ShowRas()  # Show HEC-RAS UI (optional for debugging)
    hec.CurrentPlanFile()  # Ensure the correct plan is loaded
    logging.info(f"Project '{project_file}' opened.")


    rasmapper_but = pyautogui.locateCenterOnScreen("./pyautogui/rasmapper.png")
    pyautogui.click(rasmapper_but)
    time.sleep(2)

    results_but = pyautogui.locateOnScreen("./pyautogui/results.png")
    pyautogui.rightClick(results_but)
    time.sleep(1)
    
    createmultimaps_but = pyautogui.locateOnScreen("./pyautogui/createmultimaps.png")
    pyautogui.click(createmultimaps_but)
    time.sleep(1)

    min_but = pyautogui.locateOnScreen("./pyautogui/min.png")
    pyautogui.moveTo(min_but)
    pyautogui.move(0, 10)
    pyautogui.drag(0, 80, 2, button='left') 

    depth_but = pyautogui.locateOnScreen("./pyautogui/depth.png")
    pyautogui.click(depth_but)

    ok_but = pyautogui.locateOnScreen("./pyautogui/ok.png")
    pyautogui.click(ok_but)
    # ok2_but = pyautogui.locate("./pyautogui/ok2.png", "./pyautogui/success.png")
    # print(ok2_but)
    # if ok2_but is None:
    #     print("OK2 button not found")
    # else:
    #     print("OK2 button found")
    # #pyautogui.click(ok2_but)
    hec.QuitRas()

except Exception as e:
    logging.error(f"Error: {e}")
    hec.QuitRas()
    logging.info("HEC-RAS closed successfully.")


