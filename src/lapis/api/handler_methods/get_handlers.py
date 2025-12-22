from api.models.http_models import APIRequest, APIResponse
from src.lapis.api.repositories.db import *
from src.lapis.api.services.db.db_services import *
from api.router import Router

def get_seed_handler(request: APIRequest) -> APIResponse:
    """Get the user's seed value"""
    if not request.author_id:
        # presentation layer
        return APIResponse(401, {"error": "Unauthorized"})
    #  business logic layer, get_seed connects to data access layer
    seed = get_seed(request.author_id)
    # presentation layer
    return APIResponse(200, {"seed": seed})
Router.register("GET", "/seed", get_seed_handler)

def get_location_handler(request: APIRequest) -> APIResponse:
    try:
        queryParams = request.query_params
        retrieve_location(request.author_id, queryParams.location_name)
    except UnauthorizedError as e:
        return APIResponse(401, str(e))
    except ValidationError as e:
        return APIResponse(400, str(e))
    except DataAccessError as e:
        return APIResponse(500, str(e))
Router.register("GET", "/location/{location_name}", get_location_handler)
        

def get_locations_handler(request: APIRequest) -> APIResponse:
    try:
        locations = retrieve_locations(request.author_id)
        return APIResponse(201, {"locations": locations})
    except UnauthorizedError as e:
        return APIResponse(401, str(e))
    except NotFoundError as e:
        return APIResponse(404, str(e))
Router.register("GET", "/locations", get_locations_handler)