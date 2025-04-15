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
import os

PROJECT_FILE = r"D:\FLOWS\New folder\FLOWS-Website\hecras\flow.prj"
ICON_FOLDER = r"D:\FLOWS\New folder\FLOWS-Website\hecras\pyautogui"

# Configure basic logging
logging.basicConfig(
    filename='hecras_output.log',  # Log to a file
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(message)s'
)

try:
    hec = win32com.client.Dispatch("RAS67.HECRASController")
    logging.info("HEC-RAS Controller initialized.")
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
    depth_but = pyautogui.locateOnScreen(os.path.join(ICON_FOLDER, "depth.png"), confidence=0.8, region=right_half_region)
    pyautogui.moveTo(depth_but)
    time.sleep(10)
    #pyautogui.click(depth_but)


    ok_but = pyautogui.locateOnScreen(os.path.join(ICON_FOLDER, "ok.png"), confidence=0.7)
    pyautogui.click(ok_but)
    time.sleep(10)
    # ok2_but = pyautogui.locate("./pyautogui/ok2.png", "./pyautogui/success.png")
    # print(ok2_but)
    # if ok2_but is None:
    #     print("OK2 button not found")
    # else:
    #     print("OK2 button found")
    # #pyautogui.click(ok2_but)
    
    #hec.QuitRas()

except Exception as e:
    logging.error(f"Error: {e}")
    hec.QuitRas()
    logging.info("HEC-RAS closed successfully.")


