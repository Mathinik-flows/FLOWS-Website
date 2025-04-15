import requests
import boto3
import time
import os
from glob import glob
import re

# CONFIGURATION
mapbox_token = 'sk.eyJ1IjoiZ2F2aW5jaWkiLCJhIjoiY205Zjl3NHhkMGlvYzJyc2MwNm05b2c0ayJ9.OTA15_jphYcO85Cj46F4VQ'
username = 'gavincii'
input_folder = r'D:\FLOWS\New folder\FLOWS-Website\model\converted_8bit'
batch_size = 6
delay_between_batches = 60  # in seconds

def upload_single_tif(tif_path, batch_index, tif_index):
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
    print(f"📤 Uploaded {os.path.basename(tif_path)} to S3")

    # 3. Trigger tileset upload
    tileset_id = f'{username}.flood-map-{batch_index}-{tif_index}'
    upload_payload = {
        "url": credentials["url"],
        "tileset": tileset_id,
        "name": f"Flood Map {batch_index}-{tif_index}"
    }
    upload_res = requests.post(
        f'https://api.mapbox.com/uploads/v1/{username}?access_token={mapbox_token}',
        json=upload_payload
    )
    upload_job = upload_res.json()
    print(f"🚀 Upload started for {tileset_id} (Upload ID: {upload_job['id']})")

def extract_number(filename):
    match = re.search(r"(\d+)", filename)
    return int(match.group(1)) if match else -1
    
def upload_tifs_in_batches():
    tif_files = sorted(glob(os.path.join(input_folder, "*.tif")), key=lambda x: extract_number(os.path.basename(x)))
    total = len(tif_files)
    batches = [tif_files[i:i + batch_size] for i in range(0, total, batch_size)]

    for batch_index, batch in enumerate(batches):
        print(f"\n=== 🗂️ Starting batch {batch_index + 1}/{len(batches)} ===")
        for tif_index, tif_path in enumerate(batch):
            upload_single_tif(tif_path, batch_index, tif_index)
            time.sleep(5)  # Slight delay between individual uploads to avoid token rate limits
        if batch_index < len(batches) - 1:
            print(f"⏳ Waiting {delay_between_batches} seconds before next batch...")
            time.sleep(delay_between_batches)

upload_tifs_in_batches()
