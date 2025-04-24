import requests
import boto3
import time
import os
from glob import glob

# CONFIGURATION
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
mapbox_token = 'sk.eyJ1IjoiZ2F2aW5jaWlpIiwiYSI6ImNtOXJxYzBieTFsamsya3I3a3RkaXRidmoifQ.AKsqwHhiw5MMo66QVQeIRw'
username = 'gavinciii'
input_folder = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'assets', 'converted_rgb'))

def upload_single_tif(tif_path, index):
    try:
        # 1. Request temporary S3 credentials
        cred_res = requests.post(
            f'https://api.mapbox.com/uploads/v1/{username}/credentials?access_token={mapbox_token}'
        )
        credentials = cred_res.json()

        # 2. Upload TIFF to S3
        s3 = boto3.client(
            's3',
            aws_access_key_id=credentials['accessKeyId'],
            aws_secret_access_key=credentials['secretAccessKey'],
            aws_session_token=credentials['sessionToken'],
        )

        bucket = credentials['bucket']
        key = credentials['key']
        with open(tif_path, 'rb') as f:
            s3.upload_fileobj(f, bucket, key)
        print(f"Uploaded {os.path.basename(tif_path)} to S3")

        # 3. Trigger tileset upload
        tileset_id = f'{username}.flood-map-{index}'
        upload_payload = {
            "url": credentials["url"],
            "tileset": tileset_id,
            "name": f"Flood Map {index}"
        }
        upload_res = requests.post(
            f'https://api.mapbox.com/uploads/v1/{username}?access_token={mapbox_token}',
            json=upload_payload
        )
        upload_job = upload_res.json()
        print(f"Upload started for {tileset_id} (Upload ID: {upload_job['id']})")
    
    except Exception as e:
        print(f"Error uploading {os.path.basename(tif_path)}: {e}")

def upload_all_tifs():
    tif_files = sorted(glob(os.path.join(input_folder, "*.tif")))
    print(f"Found {len(tif_files)} TIFF files to upload.\n")

    for index, tif_path in enumerate(tif_files):
        print(f"Processing {index+1}/{len(tif_files)}: {os.path.basename(tif_path)}")
        upload_single_tif(tif_path, index)
        time.sleep(10)  # optional delay to avoid rate limits

upload_all_tifs()
