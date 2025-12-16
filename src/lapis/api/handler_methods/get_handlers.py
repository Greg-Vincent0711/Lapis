from api.models.http_models import APIRequest, APIResponse
from api.repositories.db import get_seed, list_locations
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


def get_locations_handler(request: APIRequest) -> APIResponse:
    if not request.author_id:
        return APIResponse(401, {"error": "Unauthorized"})
    locations = list_locations(request.author_id)
    return APIResponse(200, {"locations": locations})
Router.register("GET", "/locations", get_locations_handler)