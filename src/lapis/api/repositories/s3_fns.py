import requests
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import os
import re
from io import BytesIO
import uuid
from src.lapis.helpers.exceptions import *
fileNameRegex = r"https://[^/]+\.s3\.amazonaws\.com/(.+)"

def getS3Instance():
    s3Instance = boto3.client('s3', region_name=os.getenv("REGION_NAME"))
    return s3Instance

def getBucket():
    return os.getenv('BUCKET_NAME')

ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png"}

'''
image is anything with .content_type and either .data (the file's bytes, from a website upload)
or .url (a Discord attachment from the bot, or a link sent to the API) to download it from.
Each upload gets its own key under the author's folder so two users (or two locations)
uploading "image.png" can't overwrite each other.
'''
async def storeImageInS3(image, author_id: str) -> str | None:
    s3Instance = getS3Instance()
    BUCKET = getBucket() 
    content_type = (image.content_type or "").split(";")[0].strip().lower()
    fileExtension = ALLOWED_IMAGE_TYPES.get(content_type)
    if fileExtension is None:
        raise InvalidImageFormatError("Attachment you're trying to upload is not in the correct format. Use a .png or .jpg image.")
    else:
        img_data = getattr(image, "data", None)
        if img_data is None:
            try:
                imgFromChannel = requests.get(image.url, timeout=10)
                imgFromChannel.raise_for_status()
                img_data = imgFromChannel.content
            except requests.exceptions.RequestException as e:
                raise ImageDownloadError(f"Image download failed: {e}")
        fileName = f"uploads/{author_id}/{uuid.uuid4().hex}{fileExtension}"
        try:
            s3Instance.upload_fileobj(
                BytesIO(img_data),
                BUCKET,
                fileName,
                # without this S3 serves the file as a generic download and Discord won't preview it
                ExtraArgs={"ContentType": content_type},
            )
            return f"https://{BUCKET}.s3.amazonaws.com/{fileName}"
        except (BotoCoreError, ClientError, Exception) as e:
            raise S3UploadError(f"S3 upload failed: {e}")

def deleteImageObject(file_url):
    s3Instance = getS3Instance()
    BUCKET = getBucket()
    matchingFileName = re.match(fileNameRegex, file_url)
    if matchingFileName:
        fileName = matchingFileName.group(1)
        try:
            s3Instance.delete_object(Bucket=BUCKET, Key=fileName)
            return f"Successfully deleted https://{BUCKET}.s3.amazonaws.com/{fileName}"
        except Exception as e:
            raise S3DeleteError(f"There was an error deleting your image: {e}")
    else:
        raise ValueError("Could not find the image you were looking for. Be sure it exists with !list.")

# kept async so existing callers can keep awaiting it
async def deleteImage(file_url):
    return deleteImageObject(file_url)
