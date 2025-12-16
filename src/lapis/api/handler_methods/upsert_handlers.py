'''
UPSERT (POST/PUT) DB handlers
'''
from api.models.http_models import APIRequest, APIResponse
from src.lapis.api.repositories.db import *
from src.lapis.api.repositories.oauth import retrieveAccessToken, getAuthorDataFromDiscord
from api.router import Router

def save_location_handler(request: APIRequest) -> APIResponse:
    body = request.body
    res = save_location(request.author_id, body.location_name, body.coords)
    # this 202 portion will change
    return APIResponse(202, res)
Router.register("POST", "/locations", save_location_handler)

def set_seed_handler(request: APIRequest) -> APIResponse:
    body = request.body
    res = set_seed(request.author_id, body.seed)
    return APIResponse(202, res)
Router.register("POST", "/seed", set_seed_handler)

def save_image_url_handler(request: APIRequest) -> APIResponse:
    body = request.body
    # body.message refers to the generated s3 url
    res = save_image_url(request.author_id, body.location_name, body.message)
    return APIResponse(202, res)
# {} is syntax that matches _matches in router.py
Router.register("POST", "/locations/{location_name}", save_image_url_handler)

def set_seed_handler(request: APIRequest) -> APIResponse:
    if not request.author_id:
        return APIResponse(401, {"error": "Unauthorized"})
    res = set_seed(request.author_id, request.body.seed)
    return APIResponse(202, {"Output of 'set_seed' operation": res})
Router.register("POST", "/seed", set_seed_handler)


def credentials_handler(request: APIRequest) -> APIResponse:
    body = request.body
    accessToken = retrieveAccessToken(body.accessToken)["id"]
    storedAuthorID = getAuthorDataFromDiscord(accessToken)["id"]
    statusCode, msg = verify_credentials(request.cognito_user_id, storedAuthorID)
    


def update_location_handler(request: APIRequest) -> APIResponse:
    body = request.body
    res = update_location(request.author_id, body.location_name, body.new_coords)
    return APIResponse(202, res)
Router.register("PUT", "/locations/{location_name}", update_location_handler)





