import requests
import boto3
import os
from io import BytesIO

BUCKET = os.getenv('BUCKET_NAME')
s3Instance = boto3.resource('s3')
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
            return str(e)
            

async def deleteImage():
    pass