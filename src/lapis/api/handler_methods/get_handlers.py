from src.lapis.api.models.http_models import APIRequest, APIResponse
from src.lapis.api.repositories.db import *
from src.lapis.api.services.db.db_services import *
from src.lapis.api.router import router

def get_seed_handler(request: APIRequest) -> APIResponse:
    try:
        seed = retrieve_seed(request.author_id)
        return APIResponse(202, {"seed": seed})
    except UnauthorizedError as e:
        return APIResponse(e.status_code, e.message)
    except NotFoundError as e:
        return APIResponse(e.status_code, e.message)
router.register("GET", "/seed", get_seed_handler)

def get_location_handler(request: APIRequest) -> APIResponse:
    try:
        queryParams = request.query_params or {}
        location_name = queryParams.get("location_name") or request.path_params.get("location_name")
        if not location_name:
            return APIResponse(400, "location_name is required")
        result = retrieve_location(request.author_id, location_name)
        return APIResponse(200, result)
    except UnauthorizedError as e:
        return APIResponse(e.status_code, e.message)
    except ValidationError as e:
        return APIResponse(e.status_code, e.message)
    except NotFoundError as e:
        return APIResponse(e.status_code, e.message)
    except DataAccessError as e:
        return APIResponse(e.status_code, e.message)
router.register("GET", "/locations/{location_name}", get_location_handler)
        

def get_locations_handler(request: APIRequest) -> APIResponse:
    try:
        locations = retrieve_locations(request.author_id)
        return APIResponse(200, {"locations": locations})
    except UnauthorizedError as e:
        return APIResponse(e.status_code, e.message)
    except NotFoundError as e:
        return APIResponse(e.status_code, e.message)
router.register("GET", "/locations", get_locations_handler)