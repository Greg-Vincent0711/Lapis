'''
UPSERT (POST/PUT) DB route handlers
we need to change the return type of db.py
'''
from src.lapis.api.models.http_models import APIRequest, APIResponse
from src.lapis.api.repositories.db import *
from src.lapis.api.services.db.db_services import *
from src.lapis.api.services.oauth.oauth_services import get_credentials_attempt
from src.lapis.api.router import router

def save_location_handler(request: APIRequest) -> APIResponse:
    try:
        body = request.body
        # connect to business logic layer
        res = create_location(request.author_id, body["location_name"], body["type"], body["coords"])
        return APIResponse(201, res)
    # catch all the errors thrown by the business logic portion
    except UnauthorizedError as e:
        return APIResponse(e.status_code, e.message)
    except ValidationError as e:
        return APIResponse(e.status_code, e.message)
    except InvalidLocationError as e:
        return APIResponse(e.status_code, e.message)
    except LocationLimitExceededError as e:
        return APIResponse(e.status_code, e.message)
    except DataAccessError as e:
        return APIResponse(e.status_code, e.message)
router.register("POST", "/locations", save_location_handler)


def set_seed_handler(request: APIRequest) -> APIResponse:
    try:
        body = request.body
        res = set_seed(request.author_id, body["seed"])
        return APIResponse(201, res)
    except UnauthorizedError as e:
        return APIResponse(e.status_code, e.message)
    except ValidationError as e:
        return APIResponse(e.status_code, e.message)
    except DataAccessError as e:
        return APIResponse(e.status_code, e.message)
router.register("POST", "/seed", set_seed_handler)


def save_image_url_handler(request: APIRequest) -> APIResponse:
    try:
        body = request.body
        # body.message refers to the generated s3 url
        res = create_image(request.author_id, body["location_name"], body['message'])
        return APIResponse(201, res)
    except ValidationError as e:
        return APIResponse(e.status_code, e.message)
    except UnauthorizedError as e:
        return APIResponse(e.status_code, e.message)
    except DataAccessError as e:
        return APIResponse(e.status_code, e.message)
# {} is syntax that matches _matches in router.py
router.register("PUT", "/locations/{location_name}/img", save_image_url_handler)


'''
why do we need credentials_handler?

When clicking connect to discord, we need to post the authcode.
Just a POST. Recieve back the author_id on the backend that requests are made with
'''
def credentials_handler(request: APIRequest) -> APIResponse:
    try:
        body = request.body or {}
        authCode = body.get("authCode")
        if not authCode:
            return APIResponse(400, "authCode is required")
        get_credentials_attempt(request, authCode)
        return APIResponse(204, None)
    except UnauthorizedError as e:
        return APIResponse(e.status_code, e.message)
    except DataAccessError as e:
        return APIResponse(e.status_code, e.message)
router.register("POST", "/auth/callback", credentials_handler)

    
def update_location_handler(request: APIRequest) -> APIResponse:
    try:
        body = request.body
        res = create_location_update(request.author_id, body["location_name"], body["new_coords"])
        return APIResponse(201, res)
    except UnauthorizedError as e:
        return APIResponse(e.status_code, e.message)
    except ValidationError as e:
        return APIResponse(e.status_code, e.message)
router.register("PUT", "/locations/{location_name}", update_location_handler)