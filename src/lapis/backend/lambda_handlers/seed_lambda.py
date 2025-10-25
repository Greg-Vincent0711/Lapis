import json
from src.lapis.backend.seed_impl import *

def response(status_code: int, body: dict):
    """
    Formats the response for API Gateway.
    """
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body)
    }

def handler(event, context):
    """
    Lambda entry point for API Gateway.
    """
    try:
        method = event.get("requestContext", {}).get("http", {}).get("method", "")
        queryParams = event.get("queryStringParameters") or {}
        
        author_id = queryParams.get("Author_ID")
        if not author_id:
            return response(400, {"Error": "Missing required field: Author_ID."})
        
        if method == "GET":
            if queryParams.get("requestType") == "nearest":
                feature = queryParams.get("feature")
                x_coord = queryParams.get("x_coord")
                z_coord = queryParams.get("z_coord")
                radius = queryParams.get("radius")
                if not all([feature, x_coord, z_coord, radius]):
                    return response(400, {"Error": "Missing query parameters for nearest."})
                
                res = nearest_impl(author_id, feature, x_coord, z_coord, radius)
                return response(200, res)
            
            elif queryParams.get("requestType") == "spawn-near":
                numseeds = queryParams.get("numseeds")
                range_val = queryParams.get("range_val")
                biome = queryParams.get("biome", None)
                structure = queryParams.get("structure", None)
                
                if not all([numseeds, range_val]) or (biome == None and structure == None):
                    return response(400, {"Error": "Missing query parameters for spawn-near."})
                
                res = spawn_near_impl(author_id, numseeds, range_val, biome, structure)
                return response(200, res)
            else:
                return response(400, {"Error": "Invalid query parameter type."})
        else:
            return response(405, {"Error": f"Method not allowed. No handler for method={method}."})
    
    except Exception as e:
        print(f"Error caught when using seed routes: {e}")
        return response(500, {"Error": str(e)})