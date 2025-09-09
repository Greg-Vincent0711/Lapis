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

def lambda_handler(event, context):
    try:
        method = event.get("httpMethod")
        path = event.get("path", "")
        body = {}
        query = event.get("queryStringParameters") or {}

        if event.get("body"):
            try:
                body = json.loads(event["body"])
            except json.JSONDecodeError:
                return response(400, {"error": "Invalid JSON body."})
            
        author_id = body.get("author_id")
        if not author_id:
            return response(400, {"error": "Missing required field: author_id"})

        # ---------------- POST ----------------
        if method == "POST":
            if "location_name" in body and "coords" in body:
                try:
                    save_location(author_id, body["location_name"], body["coords"])
                    return response(200, "Location saved")
                except Exception as e:
                    return f"Error saving your location: {e}"

            # Save an image URL for a location
            if "location_name" in body and "message" in body:
                msg = asyncio.run(save_image_url(author_id, body["location_name"], body["message"]))
                return response(200, msg)

            # Set world seed
            if "seed" in body:
                success, msg = set_seed(author_id, body["seed"])
                return response(200 if success else 400, msg)

            return response(400, "POST request missing required fields.")

        # ---------------- PUT ----------------
        if method == "PUT":
            # Update a location's coordinates
            if "location_name" in body and "coords" in body:
                updated_coords = update_location(author_id, body["location_name"], body["coords"])
                return response(200, {"new_coords": updated_coords})

            return response(400, "PUT request missing required fields.")

        # ---------------- GET ----------------
        if method == "GET":
            # Get a specific location
            if path.startswith("/locations/"):
                location_name = path.split("/locations/")[1]
                res = get_location(author_id, location_name)
                return response(200, {"location": res})

            # Get world seed
            if path == "/seed":
                res = get_seed(author_id)
                return response(200, {"seed": res})

            # List all locations
            if path == "/locations":
                res = list_locations(author_id)
                return response(200, {"locations": res})

            return response(404, "GET route not found.")

        # ---------------- DELETE ----------------
        if method == "DELETE":
            # Delete a location
            if path.startswith("/locations/"):
                location_name = path.split("/locations/")[1]
                msg = delete_location(author_id, location_name)
                return response(200, msg)

            # Delete a location's image
            if path.startswith("/images/"):
                location_name = path.split("/images/")[1]
                asyncio.run(delete_image_url(author_id, location_name))
                return response(200, "Deleted image URL")

            return response(404, "DELETE route not found.")

        return response(405, f"Method {method} not allowed.")

    except ClientError as e:
        return response(500, f"AWS ClientError: {e.response['Error']['Message']}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        return response(500, str(e))
