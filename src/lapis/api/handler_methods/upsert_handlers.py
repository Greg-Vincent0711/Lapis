'''
UPSERT (POST/PUT) DB route handlers
we need to change the return type of db.py
'''
from api.models.http_models import APIRequest, APIResponse
from src.lapis.api.repositories.db import *
from src.lapis.api.services.db.db_services import *
from src.lapis.api.repositories.oauth import retrieveAccessToken, getAuthorDataFromDiscord
from api.router import Router

def save_location_handler(request: APIRequest) -> APIResponse:
    try:
        body = request.body
        # connect to business logic layer
        res = create_location(request.author_id, body.location_name, body.coords)
        return APIResponse(201, res)
    # catch all the errors thrown by the business logic portion
    except UnauthorizedError as e:
        return APIResponse(401, {"error": str(e)})
    
    except ValidationError as e:
        return APIResponse(400, {"error": str(e)})
    
    except InvalidLocationError as e:
        return APIResponse(422, {"error": str(e)})

    except LocationLimitExceededError as e:
        return APIResponse(409, {"error": str(e)})

    except DataAccessError as e:
        return APIResponse(500, {"error": str(e)})
Router.register("POST", "/locations", save_location_handler)

def set_seed_handler(request: APIRequest) -> APIResponse:
    try:
        body = request.body
        res = set_seed(request.author_id, body.seed)
        return APIResponse(202, res)
    except UnauthorizedError as e:
        return APIResponse(401, {"error": str(e)})
    except ValidationError as e:
        return APIResponse(400, {"error": str(e)})
    except DataAccessError as e:
        return APIResponse(500, {"error" : str(e)})
Router.register("POST", "/seed", set_seed_handler)

def save_image_url_handler(request: APIRequest) -> APIResponse:
    try:
        body = request.body
        # body.message refers to the generated s3 url
        res = create_image(request.author_id, body.location_name, body.message)
        return APIResponse(201, res)
    except ValidationError as e:
        return APIResponse(400, {"error": str(e)})
    except UnauthorizedError as e:
        return APIResponse(401, {"error": str(e)})
    except DataAccessError as e:
        return APIResponse(500, {"error" : str(e)})
# {} is syntax that matches _matches in router.py
Router.register("POST", "/locations/{location_name}", save_image_url_handler)

# def set_seed_handler(request: APIRequest) -> APIResponse:
#     if not request.author_id:
#         return APIResponse(401, {"error": "Unauthorized"})
#     res = set_seed(request.author_id, request.body.seed)
#     return APIResponse(202, {"Output of 'set_seed' operation": res})
# Router.register("POST", "/seed", set_seed_handler)


def credentials_handler(request: APIRequest) -> APIResponse:
    body = request.body
    accessToken = retrieveAccessToken(body.accessToken)["id"]
    storedAuthorID = getAuthorDataFromDiscord(accessToken)["id"]
    statusCode, msg = verify_credentials(request.cognito_user_id, storedAuthorID)
    
def update_location_handler(request: APIRequest) -> APIResponse:
    try:
        body = request.body
        res = create_location_update(request.author_id, body.location_name, body.new_coords)
        return APIResponse(201, res)
    except UnauthorizedError as e:
        return APIResponse(401, {"error" : str(e)})
    except ValidationError as e:
        return APIResponse(400, {"error" : str(e)})
Router.register("PUT", "/locations/{location_name}", update_location_handler)





