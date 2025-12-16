'''
DELETE DB handlers
'''
from api.models.http_models import APIRequest, APIResponse
from src.lapis.api.repositories.db import *
from api.router import Router
import asyncio

def delete_location_handler(request: APIRequest) -> APIResponse:
    params = request.query_params
    res = delete_location(request.author_id, params.location_name)
    return APIRequest(202, res)
Router.register("/DELETE", "/locations/{location_name}", delete_location_handler)


def delete_image_url_handler(request: APIRequest) -> APIResponse:
    params = request.query_params
    
    