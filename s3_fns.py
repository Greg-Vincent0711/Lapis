import requests
import boto3
import os
import re
from io import BytesIO

BUCKET = os.getenv('BUCKET_NAME')
s3Instance = boto3.resource('s3')
fileNameRegex = r"https://[^/]+\.s3\.amazonaws\.com/(.+)"
async def uploadImage(message) -> str:
    if message.author.bot:
        return
    
    if message.attachment.content_type.startswith("image/"):
        img_data = requests.get(message.attachment.url).content
        filename = f"uploads/{message.attachment.filename}"
        try:
            s3Instance.upload_fileobj(BytesIO(img_data), BUCKET, filename, ExtraArgs={"ACL": "public-read"})
            return f"https://{BUCKET}.s3.amazonaws.com/{filename}"
        except Exception as e:
            return f"There was an error uploading your file: {e}"
            

async def deleteImage(message, file_url):
    if message.author.bot:
        return
    matchingFileName = re.match(r"https://[^/]+\.s3\.amazonaws\.com/(.+)", file_url)
    if matchingFileName:
        fileName = matchingFileName.group(1)
        try:
            s3Instance.delete_object(Bucket=BUCKET, Key=fileName)
            return f"Successfully deleted https://{BUCKET}.s3.amazonaws.com/{fileName}"
        except Exception as e:
            return f"There was an error deleting your image: {e}"
    else:
        return "Could not find the image you were looking for. Be sure it exists with !list."