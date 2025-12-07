'''
TODO - update the structure of this API in the future...it works but isn't good lol
     - huge refactor coming soon
'''
import json
import asyncio
from botocore.exceptions import ClientError
from src.lapis.backend.oauth import retrieveAccessToken, getAuthorDataFromDiscord
from src.lapis.backend.db import *


# response object used throughout 
def response(status_code: int, body: dict | str):
    return {
        "statusCode": status_code,
        'headers': {
        'Access-Control-Allow-Origin': 'http://localhost:5173',
        'Access-Control-Allow-Credentials': 'true',
        'Content-Type': 'application/json'},
        "body": json.dumps(body if isinstance(body, dict) else {"message": body}),
    }

def extract_location_name(path: str) -> str | None:
    """Extract the {location} from /locations/{location} path. from query parameter"""
    if isinstance(path, str):
        if path.startswith("/locations/"):
            return path.split("/locations/")[1]
        return None
    else:
        if isinstance(path, dict) and "location_name" in path:
            return path["location_name"]
        else:
            return None

'''
Instead of passing the author_ID around(not secure), we now rely on the 
cognito_user_id implicitly when the user signs into the app
'''
def handler(event, context):
    try:
        method = event.get("requestContext", {}).get("http", {}).get("method")
        # http apis have a different payload format
        # rawPath gets the exact string for /locations excluding the query string ?Author_ID = X
        # fixes issue with getting list_locations
        path = event.get("rawPath") or event.get("pathParameters", "")
        # Get cognito_user_id from JWT (decoded by API Gateway)
        cognito_user_id = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {}).get("sub")
        author_ID = get_credentials(cognito_user_id)
        body = {}
        if event.get("body"):
            try:
                body = json.loads(event["body"])
            except json.JSONDecodeError:
                return response(400, {"error": "Invalid JSON body."})

        location_name_from_query_param = extract_location_name(path)
        # Use path parameter if present, fallback to body. 
        location_name = location_name_from_query_param or body.get("location_name")
        # ---------------- POST / PUT ----------------
        if method == "POST":
            if "authCode" in body and path.endswith("/auth/callback"):
                authCode = body.get("authCode")
                accessToken = retrieveAccessToken(authCode)["access_token"]
                newAuthorID = getAuthorDataFromDiscord(accessToken)["id"]
                statusCode, msg = verify_credentials(cognito_user_id, newAuthorID)
                return response(statusCode, msg)

            if not author_ID:
                return response(400, {"error": "Missing required field: Author_ID"})

            if not location_name:
                return response(400, {"error": "Missing location_name in path or body."})
            # remember, errors are handled by the specific methods being called.
            elif "coords" in body:
                msg = save_location(author_ID, location_name, body["coords"])
                return response(200, msg)
            elif "message" in body:
                msg = asyncio.run(save_image_url(author_ID, location_name, body["message"]))
                return response(200, msg)
            elif "seed" in body:
                success, msg = set_seed(author_ID, body["seed"])
                return response(200 if success else 400, msg)
            else:
                return response(400, {"error": "POST request missing required fields."})

        elif method == "PUT":
            if "coords" in body:
                updated_coords = update_location(author_ID, location_name, body["coords"])
                return response(200, {"new_coords": updated_coords})
            return response(400, {"error": "PUT request missing required fields."})

        # ---------------- GET ----------------
        elif method == "GET":
            if not author_ID:
                return response(400, {"error": "Missing required query parameter: Author_ID"})

            if location_name:
                result = get_location(author_ID, location_name)
                return response(200, {"location": result})

            # Strictly "locations" refers to list_locations
            if path.split("/", 2)[-1] == "locations":
                locations = list_locations(author_ID)
                return response(200, {"locations": locations})

            if path == "/seed":
                seed = get_seed(author_ID)
                return response(200, {"seed": seed})

            return response(404, {"error": "GET route not found."})

        # ---------------- DELETE ----------------
        elif method == "DELETE" and location_name:
            if not author_ID:
                return response(400, {"error": "GET/DELETE requests require an Author_ID"})

            elif location_name:
                msg = delete_location(author_ID, location_name)
                return response(200, msg)

            elif path.startswith("/images/"):
                location_name = path.split("/images/")[1]
                msg = asyncio.run(delete_image_url(author_ID, location_name))
                return response(200, msg)
            else:
                return response(404, {"error": "DELETE route not found."})
        else:
            return response(405, {"error": f"Method {method} not allowed."})

    except ClientError as e:
        return response(500, {"error": f"AWS ClientError: {e.response['Error']['Message']}"})
    except Exception as e:
        print(f"Unexpected error: {e}")
        return response(500, {"error": str(e)})
