import requests
import boto3
import zipfile
import os
import time

# CONFIGURATION
mapbox_token = 'sk.eyJ1IjoiZ2F2aW5jaWkiLCJhIjoiY205Zjl3NHhkMGlvYzJyc2MwNm05b2c0ayJ9.OTA15_jphYcO85Cj46F4VQ'
username = 'gavincii'
tileset_id = f'{username}.flood'
tileset_name = 'Flood Map'
tif_path = r'assets/map/test_tiff.tif'
zip_path = 'floodmap.zip'

# # 1. ZIP the GeoTIFF
# with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
#     zipf.write(tif_path, arcname=os.path.basename(tif_path))
# print(f"Zipped {tif_path} as {zip_path}")

# 2. Request temporary S3 credentials
cred_res = requests.post(
    f'https://api.mapbox.com/uploads/v1/{username}/credentials?access_token={mapbox_token}'
)
credentials = cred_res.json()
print("Obtained temporary S3 credentials.")
print("Credential response:", credentials)  # 👈 Add this line

# 3. Upload ZIP to S3 using boto3
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
print("Uploaded to S3.")

# 4. Trigger Mapbox tileset upload
upload_payload = {
    "url": credentials["url"],
    "tileset": tileset_id,
    "name": tileset_name
}
upload_res = requests.post(
    f'https://api.mapbox.com/uploads/v1/{username}?access_token={mapbox_token}',
    json=upload_payload
)
upload_job = upload_res.json()
print(f"Triggered upload to Mapbox. Upload ID: {upload_job['id']}")

# 5. (Optional) Poll the upload status
print("Polling upload status...")
while True:
    status_res = requests.get(
        f'https://api.mapbox.com/uploads/v1/{username}/{upload_job["id"]}?access_token={mapbox_token}'
    ).json()
    
    print(f"Status: {status_res['complete']}, Error: {status_res.get('error')}")
    if status_res['complete']:
        if status_res.get('error'):
            print("Upload failed:", status_res['error'])
        else:
            print("Upload successful! Tileset ready.")
        break
    time.sleep(5)
