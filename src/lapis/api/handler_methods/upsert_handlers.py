'''
UPSERT (POST/PUT) DB route handlers
we need to change the return type of db.py
'''
from types import SimpleNamespace
import base64
import binascii
import mimetypes
from src.lapis.api.models.http_models import APIRequest, APIResponse
from src.lapis.api.services.db.db_services import *
from src.lapis.api.services.oauth.oauth_services import get_credentials_attempt
from src.lapis.api.router import router

def save_location_handler(request: APIRequest) -> APIResponse:
    try:
        body = request.body or {}
        # connect to business logic layer
        res = create_location(request.author_id, body.get("location_name"), body.get("type"), body.get("coords"))
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
    except ConflictError as e:
        return APIResponse(e.status_code, e.message)
    except DataAccessError as e:
        return APIResponse(e.status_code, e.message)
router.register("POST", "/locations", save_location_handler)


def set_seed_handler(request: APIRequest) -> APIResponse:
    try:
        body = request.body or {}
        res = set_seed(request.author_id, body.get("seed"))
        return APIResponse(201, res)
    except UnauthorizedError as e:
        return APIResponse(e.status_code, e.message)
    except ValidationError as e:
        return APIResponse(e.status_code, e.message)
    except DataAccessError as e:
        return APIResponse(e.status_code, e.message)
router.register("POST", "/seed", set_seed_handler)


# API Gateway caps request bodies at 10 MB and Lambda at 6 MB; base64 adds a third
MAX_IMAGE_BYTES = 4 * 1024 * 1024

def _image_from_body(body: dict):
    """
    Two ways to send an image:
      {"image_base64": "<base64 or data: URL>", "content_type": "image/png"}  - a file picked in the browser
      {"image_url": "https://..."}                                            - a link to copy from
    Returns an object shaped like a Discord attachment, or an error string.
    """
    encoded = body.get("image_base64")
    if encoded:
        content_type = body.get("content_type")
        if encoded.startswith("data:"):
            # "data:image/png;base64,AAAA..." as produced by FileReader.readAsDataURL
            header, _, encoded = encoded.partition(",")
            content_type = content_type or header[5:].split(";")[0]
        try:
            data = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError):
            return "image_base64 is not valid base64"
        if len(data) > MAX_IMAGE_BYTES:
            return "Image is too large. The limit is 4 MB."
        return SimpleNamespace(data=data, url=None, content_type=content_type)
    image_url = body.get("image_url") or body.get("message")
    if not image_url or not str(image_url).startswith("https://"):
        return "Send image_base64 with content_type, or an https image_url"
    return SimpleNamespace(url=image_url, content_type=mimetypes.guess_type(image_url.split("?")[0])[0])

async def save_image_url_handler(request: APIRequest) -> APIResponse:
    try:
        body = request.body or {}
        location_name = (request.path_params or {}).get("location_name") or body.get("location_name")
        if not location_name:
            return APIResponse(400, "location_name is required")
        image = _image_from_body(body)
        if isinstance(image, str):
            return APIResponse(400, image)
        res = await create_image(request.author_id, location_name, image)
        return APIResponse(201, res)
    except (InvalidImageFormatError, ImageDownloadError) as e:
        return APIResponse(400, str(e))
    except S3UploadError as e:
        return APIResponse(502, str(e))
    except InvalidLocationError as e:
        return APIResponse(e.status_code, e.message)
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
        # the website's callback page treats exactly 200 as success
        return APIResponse(200, "Discord account linked.")
    except (UnauthorizedError, ForbiddenError) as e:
        return APIResponse(e.status_code, e.message)
    except DataAccessError as e:
        return APIResponse(e.status_code, e.message)
router.register("POST", "/auth/callback", credentials_handler)

    
def update_location_handler(request: APIRequest) -> APIResponse:
    try:
        body = request.body or {}
        location_name = body.get("location_name") or (request.path_params or {}).get("location_name")
        # the website sends "coords", older callers send "new_coords"
        new_coords = body.get("new_coords") or body.get("coords")
        res = create_location_update(request.author_id, location_name, new_coords)
        return APIResponse(200, {"message": f"Updated '{location_name}'.", "coords": res})
    except UnauthorizedError as e:
        return APIResponse(e.status_code, e.message)
    except ValidationError as e:
        return APIResponse(e.status_code, e.message)
    except InvalidLocationError as e:
        return APIResponse(e.status_code, e.message)
router.register("PUT", "/locations/{location_name}", update_location_handler)
# the website sends its edits to PUT /locations with the name in the body
router.register("PUT", "/locations", update_location_handler)