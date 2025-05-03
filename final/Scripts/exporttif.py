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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_FILE = os.path.abspath(os.path.join(BASE_DIR, '..', 'flows.prj'))
ICON_FOLDER = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'final', 'pyautogui'))

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
    print("rasmapper.png found")
    pyautogui.click(rasmapper_but)
    time.sleep(5)

    results_but = pyautogui.locateOnScreen(os.path.join(ICON_FOLDER, "results.png"), confidence=0.7)
    print("results.png found")
    pyautogui.rightClick(results_but)
    time.sleep(10)

    createmultimaps_but = pyautogui.locateOnScreen(os.path.join(ICON_FOLDER, "createmultimaps.png"), confidence=0.7)
    print("createmultimaps.png found")
    pyautogui.click(createmultimaps_but)
    time.sleep(5)

    min_but = pyautogui.locateOnScreen(os.path.join(ICON_FOLDER, "min.png"), confidence=0.7)
    print("min.png found")
    pyautogui.moveTo(min_but)
    pyautogui.move(0, 10)
    pyautogui.drag(0, 80, 2, button='left')
    
    screen_width, screen_height = pyautogui.size()
    depth_but = pyautogui.locateCenterOnScreen(os.path.join(ICON_FOLDER, "depth2.png"), confidence=0.7)
    print("depth2.png found")
    pyautogui.moveTo(depth_but)
    pyautogui.click(depth_but)

    ok_but = pyautogui.locateOnScreen(os.path.join(ICON_FOLDER, "ok.png"), confidence=0.8)
    print("ok.png found")
    pyautogui.click(ok_but)
    time.sleep(10)

except Exception as e:
    logging.error(f"Error: {e}")
    hec.QuitRas()
    logging.info("HEC-RAS closed successfully.")


