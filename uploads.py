import requests
import boto3
import zipfile
import os
import time

import requests
import boto3
import time
import os
# import zipfile # Not needed based on your active S3 upload code

# --- Configuration ---
username = 'gavincii' # Replace with your actual Mapbox username
mapbox_token = 'sk.eyJ1IjoiZ2F2aW5jaWkiLCJhIjoiY205Zjl3NHhkMGlvYzJyc2MwNm05b2c0ayJ9.OTA15_jphYcO85Cj46F4VQ' # Replace with your secret Mapbox API token (keep this secure!)
base_tif_path = r'assets/map' # Base directory containing your TIF files

# --- Loop through file numbers 1 to 11 ---
for i in range(0, 1): # range(1, 12) generates numbers 1, 2, ..., 11
    file_index = i
    tileset_id = f'{username}.tif_rgb_{i}' # Dynamic tileset ID, e.g., username.tif_1
    tileset_name = f'Flood_Map {file_index}'   # Dynamic tileset name, e.g., Flood Map 1
    tif_path = os.path.join(base_tif_path, f'tif_rgb_{file_index}.tif') # Construct full path, e.g., assets/map/tif_1.tif

    print(f"\n--- Processing file {i}: {tif_path} ---")
    print(f"Target Tileset ID: {tileset_id}, Name: {tileset_name}")

    # 1. Check if the TIF file exists before proceeding
    if not os.path.exists(tif_path):
        print(f"ERROR: File not found: {tif_path}. Skipping.")
        continue # Move to the next iteration of the loop

    # Note: Your original code had a commented-out section for zipping,
    # but the active S3 upload part uploads the TIF directly.
    # This script follows the active code (uploading TIF directly).

    try:
        # 2. Request temporary S3 credentials for each upload
        print("Requesting temporary S3 credentials...")
        cred_res = requests.post(
            f'https://api.mapbox.com/uploads/v1/{username}/credentials?access_token={mapbox_token}'
        )
        cred_res.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        credentials = cred_res.json()
        print("Obtained temporary S3 credentials.")
        # print("Credential response:", credentials) # Optional: for debugging

        # 3. Upload TIF to S3 using boto3
        print("Uploading to S3...")
        s3 = boto3.client(
            's3',
            aws_access_key_id=credentials['accessKeyId'],
            aws_secret_access_key=credentials['secretAccessKey'],
            aws_session_token=credentials['sessionToken'],
        )

        bucket = credentials['bucket']
        key = credentials['key'] # This key is unique for each credential request
        with open(tif_path, 'rb') as f:
            s3.upload_fileobj(f, bucket, key)
        print("Uploaded to S3.")

        # 4. Trigger Mapbox tileset upload
        print("Triggering Mapbox tileset creation...")
        upload_payload = {
            "url": credentials["url"], # The S3 URL provided by Mapbox creds API
            "tileset": tileset_id,     # Use the dynamic tileset ID
            "name": tileset_name       # Use the dynamic tileset name
        }
        upload_res = requests.post(
            f'https://api.mapbox.com/uploads/v1/{username}?access_token={mapbox_token}',
            json=upload_payload
        )
        upload_res.raise_for_status()
        upload_job = upload_res.json()
        print(f"Triggered upload to Mapbox. Upload ID: {upload_job['id']}")

        # 5. Poll the upload status for the current job
        print("Polling upload status...")
        while True:
            status_res = requests.get(
                f'https://api.mapbox.com/uploads/v1/{username}/{upload_job["id"]}?access_token={mapbox_token}'
            )
            status_res.raise_for_status()
            status_data = status_res.json()

            print(f"Status: {status_data['complete']}, Progress: {status_data.get('progress', 'N/A')*100:.1f}%, Error: {status_data.get('error')}")

            if status_data['complete']:
                if status_data.get('error'):
                    print(f"ERROR: Upload failed for {tileset_id}:", status_data['error'])
                else:
                    print(f"SUCCESS: Upload successful! Tileset {tileset_id} should be ready.")
                break # Exit the polling loop for this file
            time.sleep(10) # Wait longer between polls for batch jobs

    except requests.exceptions.RequestException as e:
        print(f"ERROR: API Request failed for file {i}: {e}")
        # Optionally decide if you want to stop or continue with the next file
        # continue
    except KeyError as e:
        print(f"ERROR: Missing expected key in API response for file {i}: {e}")
        # continue
    except Exception as e: # Catch other potential errors (like boto3 issues)
        print(f"ERROR: An unexpected error occurred for file {i}: {e}")
        # continue

print("\n--- Batch upload process finished. ---")
