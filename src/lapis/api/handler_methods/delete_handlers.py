'''
DELETE DB handlers
'''
from src.lapis.api.models.http_models import APIRequest, APIResponse
from src.lapis.api.services.db.db_services import *
from src.lapis.api.router import router

def delete_location_handler(request: APIRequest) -> APIResponse:
    try:
        params = request.query_params or {}
        location_name = params.get("location_name") or request.path_params.get("location_name")
        if not location_name:
            return APIResponse(400, "location_name is required")
        res = delete_location_attempt(request.author_id, location_name)
        return APIResponse(201, res)
    except UnauthorizedError as e:
        return APIResponse(e.status_code, e.message)
    except ValidationError as e:
        return APIResponse(e.status_code, e.message)
    except NotFoundError as e:
        return APIResponse(e.status_code, e.message)
router.register("DELETE", "/locations/{location_name}", delete_location_handler)


async def delete_image_url_handler(request: APIRequest) -> APIResponse:
    try:
        params = request.query_params or {}
        location_name = params.get("location_name") or request.path_params.get("location_name")
        if not location_name:
            return APIResponse(400, "location_name is required")
        res = await delete_image_url_attempt(request.author_id, location_name)
        return APIResponse(201, res)
    except UnauthorizedError as e:
        return APIResponse(e.status_code, e.message)
    except ValidationError as e:
        return APIResponse(e.status_code, e.message)
    except NotFoundError as e:
        return APIResponse(e.status_code, e.message)
# add this route to api gateway
router.register("DELETE", "/locations/{location_name}/img", delete_image_url_handler)
    
    