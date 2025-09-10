import json
import asyncio
from botocore.exceptions import ClientError
from src.lapis.backend.db import *


def response(status_code: int, body: dict | str):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body if isinstance(body, dict) else {"message": body}),
    }


def handler(event, context):
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

        if method == "POST":
            author_id = body.get("author_id")
            if not author_id:
                return response(400, {"error": "Missing required field in body: author_id"})
            if "location_name" in body and "coords" in body:
                msg = save_location(author_id, body["location_name"], body["coords"])
                return response(200, msg)
            elif "location_name" in body and "message" in body:
                msg = asyncio.run(save_image_url(author_id, body["location_name"], body["message"]))
                return response(200, msg)
            elif "seed" in body:
                success, msg = set_seed(author_id, body["seed"])
                return response(200 if success else 400, msg)
            else:
                return response(400, {"error": "POST request missing required fields."})

        if method == "PUT":
            author_id = body.get("author_id")
            if not author_id:
                return response(400, {"error": "Missing required field: author_id"})
            if "location_name" in body and "coords" in body:
                updated_coords = update_location(author_id, body["location_name"], body["coords"])
                return response(200, {"new_coords": updated_coords})
            return response(400, {"error": "PUT request missing required fields."})
        
        # GET/DELETE use query params instead of method bodies, better practice for Lambda/API GW
        if method == "GET":
            author_id = query_params.get("author_id")
            if author_id is None:
                return response(400, {"error": "Missing required query parameter: author_id"})
            if path.startswith("/locations/"):
                location_name = path.split("/locations/")[1]
                result = get_location(author_id, location_name)
                return response(200, {"location": result})

            if path == "/locations":
                locations = list_locations(author_id)
                return response(200, {"locations": locations})

            if path == "/seed":
                seed = get_seed(author_id)
                return response(200, {"seed": seed})
            return response(404, {"error": "GET route not found."})

        if method == "DELETE":
            author_id = query_params.get("author_id")
            if author_id is None:
                return response(400, {"error": "GET/DELETE requests require an author_id"})
            if path.startswith("/locations/"):
                location_name = path.split("/locations/")[1]
                msg = delete_location(author_id, location_name)
                return response(200, msg)
            if path.startswith("/images/"):
                location_name = path.split("/images/")[1]
                msg = asyncio.run(delete_image_url(author_id, location_name))
                return response(200, msg)
            return response(404, {"error": "DELETE route not found."})
        
        return response(405, {"error": f"Method {method} not allowed."})
    except ClientError as e:
        return response(500, {"error": f"AWS ClientError: {e.response['Error']['Message']}"})
    except Exception as e:
        print(f"Unexpected error: {e}")
        return response(500, {"error": str(e)})
