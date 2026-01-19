# Entry point

'''
    This handler is a lot cleaner now that there's a 
    clear separation of concerns. Much more general
    TODO - add the type(Overworld, Nether, etc) to the DB schema
    we also need to make it so tha the coordinates are -> one list(from xCoord, yCoord, zCoord, etc)
    fix the auth stuff
'''

from src.lapis.api.models.http_models import APIRequest, APIResponse
from src.lapis.api.middleware.errors import error_handler_middleware
from src.lapis.api.services.oauth.oauth_services import get_credentials_attempt
# business logic and service stuff happens here in Router

# TODO - eventually, make all the import stuff cleaner
import src.lapis.api.handler_methods.delete_handlers
import src.lapis.api.handler_methods.get_handlers
import src.lapis.api.handler_methods.upsert_handlers
from src.lapis.api.router import router

# auto wraps handler with error middleware
@error_handler_middleware
def handler(event, context):
    try:
        path = event.get("rawPath", "")
        # strip "/prod" prefix before creating request
        if path.startswith("/prod"):
            path = path[len("/prod"):]
            print("path we're matching on", path)
            # Update event with modified path for request parsing
            event_copy = event.copy()
            event_copy["rawPath"] = path
            event = event_copy
        
        request = APIRequest.from_lambda_event(event)
        if request.path != "/auth/callback":
            request.author_id = get_credentials_attempt(request)
        # we reach the backend
        print("Routes we can use:", router.routes)
        print("Request recieved from lapis.site processed on backend", request)
        if (request.method, request.path) in router.routes or \
           any(router.pathPatternsMatch(pattern, request.path) for _, pattern in router.routes.keys()):
            # pass on to respective handler
            print("handler and path from request has matched somewhere")
            response: APIResponse = router.route(request)
            print("Response sent from backend to lapis.site", response.to_lambda_response())
            return response.to_lambda_response()
    except Exception as e:
        print(f"Handler error: {e}")
        return APIResponse(500, {"error": str(e)}).to_lambda_response()