# Entry point

'''
    This handler is a lot cleaner now that there's a 
    clear separation of concerns. Much more general
    TODO - get this into Lambda, start testing + tests in the future
'''

from src.lapis.api.models.http_models import APIRequest, APIResponse
from src.lapis.api.middleware.errors import error_handler_middleware
from src.lapis.api.services.oauth.oauth_services import get_credentials_attempt
# business logic and service stuff happens here in Router
from src.lapis.api.router import router

# auto wraps handler with error middleware
@error_handler_middleware
def handler(event, context):
    try:
        request = APIRequest.from_lambda_event(event)
        request.author_id = get_credentials_attempt(request)
        print("Request recieved from lapis.site processed on backend", request)
        if (request.method, request.path) in router.routes or \
           any(router.pathPatternsMatch(pattern, request.path) for _, pattern in router.routes.keys()):
            # pass on to respective handler
            response: APIResponse = router.route(request)
            return response.to_lambda_response()
    except Exception as e:
        print(f"Handler error: {e}")
        return APIResponse(500, {"error": str(e)}).to_lambda_response()