'''
DELETE DB handlers
'''
from src.lapis.api.models.http_models import APIRequest, APIResponse
from src.lapis.api.services.db.db_services import *
from src.lapis.api.router import router

def delete_location_handler(request: APIRequest) -> APIResponse:
    try:
        params = request.query_params
        res = delete_location_attempt(request.author_id, params.location_name)
        return APIResponse(201, res)
    except UnauthorizedError as e:
        return APIResponse(401, str(e))
    except ValidationError as e:
        return APIResponse(400, str(e))
    except NotFoundError as e:
        return APIResponse(404, str(e))
router.register("DELETE", "/locations/{location_name}", delete_location_handler)


async def delete_image_url_handler(request: APIRequest) -> APIResponse:
    try:
        params = request.query_params
        res = await delete_image_url_attempt(request.author_id, params.location_name)
        return APIResponse(201, res)
    except UnauthorizedError as e:
        return APIResponse(401, str(e))
    except ValidationError as e:
        return APIResponse(400, str(e))
# add this route to api gateway
router.register("DELETE", "/locations/{location_name}/img", delete_image_url_attempt)
    
    