import json
import asyncio
from botocore.exceptions import ClientError
from src.lapis.helpers.exceptions import *
from src.lapis.backend.s3_fns import storeImageInS3

fileNameRegex = r"https://[^/]+\.s3\.amazonaws\.com/(.+)"

def response(status_code: int, body: dict | str):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body if isinstance(body, dict) else {"message": body}),
    }

def lambda_handler(event, context):
    try:
        method = event.get("httpMethod")
        path = event.get("path", "")
        query_params = event.get("queryStringParameters") or {}
        body = {}

        if event.get("body"):
            try:
                body = json.loads(event["body"])
            except json.JSONDecodeError:
                return response(400, {"error": "Invalid JSON body."})

        author_id = body.get("author_id") or query_params.get("author_id")
        if not author_id:
            return response(400, {"error": "Missing required field: author_id"})
        if method == "POST":
            if "message" in body and "location_name" in body:
                msg = asyncio.run(storeImageInS3(body["message"]))
                return response(200, {"image_url": msg})
            return response(400, {"error": "POST request missing required fields: location_name and message"})
        return response(405, {"error": f"Method {method} not allowed."})

    except (InvalidImageFormatError, ImageDownloadError, S3UploadError, S3DeleteError) as e:
        return response(400, {"error": str(e)})

    except ClientError as e:
        return response(500, {"error": f"AWS ClientError: {e.response['Error']['Message']}"})

    except Exception as e:
        print(f"Unexpected error: {e}")
        return response(500, {"error": str(e)})
