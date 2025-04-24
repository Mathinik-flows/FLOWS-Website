import subprocess
import time
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
SCRIPT_DIR = BASE_DIR / 'final' / 'Scripts'

# List of scripts to run in sequence (relative paths)
scripts = [
    SCRIPT_DIR / "prediction.py",
    SCRIPT_DIR / "simulation.py",
    SCRIPT_DIR / "exporttif.py",
    SCRIPT_DIR / "convert.py"
    # SCRIPT_DIR / "upload.py" # Uncomment this if you want to include the upload script
]
#remove last value if wala ung upload script
delays = [10, 60, 20] #,30]  # Note: len(delays) = len(scripts) - 1

def run_scripts_with_custom_delays(scripts, delays):
    for idx, script in enumerate(scripts):
        print(f"Running script: {script}")
        try:
            result = subprocess.run(["python", script], capture_output=True, text=True)
            print(result.stdout)

            if result.returncode == 0:
                print(f"Script finished: {script}")
            else:
                print(f"Script failed: {script}")
                print(result.stderr)

        except Exception as e:
            print(f"Error running {script}: {e}")

        if idx < len(delays):
            delay = delays[idx]
            print(f"Waiting {delay} seconds before next script...\n")
            time.sleep(delay)

# Run the scripts with custom delays
run_scripts_with_custom_delays(scripts, delays)
