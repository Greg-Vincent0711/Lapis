# Entry point

'''
    This handler is a lot cleaner now that there's a 
    clear separation of concerns. Much more general
    TODO - add the type(Overworld, Nether, etc) to the DB schema
    we also need to make it so tha the coordinates are -> one list(from xCoord, yCoord, zCoord, etc)
    fix the auth stuff
'''

import logging
import re
from src.lapis.api.models.http_models import APIRequest, APIResponse
from src.lapis.api.middleware.errors import error_handler_middleware, APIError
from src.lapis.api.services.oauth.oauth_services import get_credentials_attempt
# business logic and service stuff happens here in Router

# These look unused but aren't: importing each module runs its router.register(...) calls.
# Without them every request is a 404, so keep them even if an editor flags them.
import src.lapis.api.handler_methods.delete_handlers  # noqa: F401
import src.lapis.api.handler_methods.get_handlers     # noqa: F401
import src.lapis.api.handler_methods.upsert_handlers  # noqa: F401
from src.lapis.api.router import router

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def _safe_path(path: str) -> str:
    # location names are user data (stored encrypted), so they never go into the logs
    return re.sub(r"^/locations/[^/]+", "/locations/{name}", path)

def _log(method: str, path: str, status: int):
    # one line per request: enough to debug with, without names, coordinates, tokens or images
    logger.info("%s %s -> %s", method, _safe_path(path), status)

# auto wraps handler with error middleware
@error_handler_middleware
def handler(event, context):
    path = event.get("rawPath", "")
    try:
        # strip "/prod" prefix before creating request
        if path.startswith("/prod"):
            path = path[len("/prod"):]
            # Update event with modified path for request parsing
            event_copy = event.copy()
            event_copy["rawPath"] = path
            event = event_copy
        
        request = APIRequest.from_lambda_event(event)
        if request.path != "/auth/callback":
            request.author_id = get_credentials_attempt(request)
        if (request.method, request.path) in router.routes or \
           any(router.pathPatternsMatch(pattern, request.path) for _, pattern in router.routes.keys()):
            # pass on to respective handler
            response: APIResponse = router.route(request)
        else:
            response = APIResponse(404, {"error": f"No route for {request.method} {_safe_path(request.path)}"})
    except APIError as e:
        # errors a handler didn't catch itself keep their real status code (401, 404, ...) instead of becoming a 500
        response = APIResponse(e.status_code, {"error": e.message})
    except Exception as e:
        # the exception type is enough to find the bug; its text can contain user data
        logger.error("Unhandled %s on %s %s", type(e).__name__, event.get("requestContext", {}).get("http", {}).get("method", ""), _safe_path(path))
        response = APIResponse(500, {"error": "Internal server error"})
    _log(event.get("requestContext", {}).get("http", {}).get("method", ""), path, response.status_code)
    return response.to_lambda_response()