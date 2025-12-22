# Entry point

'''
    This handler is a lot cleaner now that there's a 
    clear separation of concerns. Much more general
    
    TODO 
    - make it so that all service endpoints(dynamo db) return success or an error
'''

from api.models.http_models import APIRequest, APIResponse
from api.middleware.errors import error_handler_middleware
# business logic and service stuff happens here in Router
from api.router import Router

# auto wraps handler with error middleware
@error_handler_middleware
def handler(event, context):
    try:
        request = APIRequest.from_lambda_event(event)
        if (request.method, request.path) in Router.routes or \
           any(Router.pathPatternsMatch(pattern, request.path) for _, pattern in Router.routes.keys()):
            
            if request.cognito_user_id:
                from src.lapis.api.repositories.db import get_credentials
                request.author_id = get_credentials(request.cognito_user_id)
            # pass on to respective handler
            response: APIResponse = Router.route(request)
            return response.to_lambda_response()
    except Exception as e:
        print(f"Handler error: {e}")
        return APIResponse(500, {"error": str(e)}).to_lambda_response()