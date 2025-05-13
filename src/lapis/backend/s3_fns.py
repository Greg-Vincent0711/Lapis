import requests
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import os
import re
from io import BytesIO
import mimetypes
from lapis.helpers.exceptions import *

BUCKET = os.getenv('BUCKET_NAME')
s3Instance = boto3.client('s3')
fileNameRegex = r"https://[^/]+\.s3\.amazonaws\.com/(.+)"

async def storeImageInS3(message) -> str | None:
    image = message.attachments[0]
    fileName = image.filename.lower()
    fileExtension = mimetypes.guess_extension(image.content_type)
    if not image.content_type or fileExtension not in {".jpg", ".jpeg", ".png"}:
        raise InvalidImageFormatError("Attachment you're trying to upload is not in the correct format.")
    else:
        try:
            imgFromChannel = requests.get(image.url, timeout=10)
            imgFromChannel.raise_for_status()
            img_data = imgFromChannel.content
        except requests.exceptions.RequestException as e:
            raise ImageDownloadError(f"Image download failed: {e}")
        fileName = f"uploads/{image.filename}"
        try:
            s3Instance.upload_fileobj(
                BytesIO(img_data),
                BUCKET,
                fileName,
            )
            return f"https://{BUCKET}.s3.amazonaws.com/{fileName}"
        except (BotoCoreError, ClientError, Exception) as e:
            raise S3UploadError(f"S3 upload failed: {e}")

async def deleteImage(file_url):
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